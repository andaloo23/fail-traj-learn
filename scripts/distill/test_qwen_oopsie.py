"""Real Qwen processor/mask integration and small-model gradient checks.

Requires requirements-oopsie.txt. Downloads only the pinned processor/tokenizer,
never the 7B weights. Synthetic targets stay in temporary test directories.
"""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import torch
from PIL import Image
import oopsie_common as common
import qwen_oopsie_sft as sft
import oopsie_markdown as md
from test_oopsie_pipeline import answer


class TokenMaskTests(unittest.TestCase):
    def test_overlap_and_unicode_offsets_mask_boundary_tokens(self):
        text = 'A\u00e9\U0001f916BC'
        ids = [11, 12, 13, 14, 99]
        offsets = [(0, 5), (5, 7), (7, 9), (9, 10), (10, 11)]
        result = sft.text_labels(ids, offsets, 5, text, [{"start": 1, "end": 3}], set(), 99)
        self.assertEqual(result, [-100, -100, -100, 14, 99])

    def test_special_input_and_padding_tokens_never_supervised(self):
        result = sft.text_labels([1, 2, 3, 9, 0], [(0, 2), (2, 3), (3, 4), (4, 5), (0, 0)],
                                 2, 'ab', [], {0, 1, 2, 9}, 9)
        self.assertEqual(result, [-100, -100, 3, 9, -100])


class RealProcessorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cfg = common.read(common.ROOT / "configs/oopsie_qwen7b.json")["student"]
        cls.processor = sft.processor_for(cfg)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        Image.new("RGB", (56, 56), "blue").save(self.root / "image.jpg")
        value = answer()
        value["segments"][0]["what_happened"] = 'The robot moves the caf\u00e9 object \U0001f916.'
        target, masks = common.target_with_masks(value)
        self.record = dict(id="fixture", messages=[dict(role="user", content=[
            dict(type="text", text="Annotate visible movement; native camera left_wrist."),
            dict(type="image", image="image.jpg")]), dict(role="assistant", content=target)], supervision=masks)

    def test_real_multimodal_expansion_and_exclusion_alignment(self):
        value = json.loads(self.record["messages"][-1]["content"])
        value["segments"][0].update(review_required=True, uncertainty="Unclear caf\u00e9 result \U0001f916.")
        target, masks = common.target_with_masks(value)
        self.record["messages"][-1]["content"] = target
        self.record["supervision"] = masks
        encoded = sft.encode_train(self.processor, self.root, self.record, 4096)
        self.assertIn("image_grid_thw", encoded)
        self.assertTrue(bool((encoded["labels"][encoded["input_ids"] == self.processor.image_token_id] == -100).all()))
        # Compare every actual target label against real Unicode offset overlap.
        prompt = self.processor.apply_chat_template(self.record["messages"][:-1], tokenize=False, add_generation_prompt=True)
        full = self.processor.apply_chat_template(self.record["messages"], tokenize=False, add_generation_prompt=False)
        tokenized = self.processor.tokenizer(full, add_special_tokens=False, return_offsets_mapping=True)
        expected = sft.text_labels(tokenized["input_ids"], tokenized["offset_mapping"], len(prompt), target,
                                   masks["assistant_excluded_char_ranges"], set(self.processor.tokenizer.all_special_ids),
                                   self.processor.tokenizer.eos_token_id)
        actual = encoded["labels"][0].tolist()
        self.assertEqual([x for x in actual if x != -100], [x for x in expected if x != -100])
        excluded = masks["assistant_excluded_char_ranges"][0]
        for label, (start, end) in zip(expected, tokenized["offset_mapping"]):
            if start - len(prompt) < excluded["end"] and end - len(prompt) > excluded["start"]:
                self.assertEqual(label, -100)

    def test_overlength_input_is_rejected_without_truncation(self):
        with self.assertRaisesRegex(ValueError, "never truncate"):
            sft.encode_train(self.processor, self.root, self.record, 2)

    def test_real_markdown_target_and_masked_section_after_image_expansion(self):
        value = json.loads(self.record["messages"][-1]["content"])
        value["segments"][0].update(review_required=True, uncertainty="The café 🤖 result is unresolved.")
        target, masks = md.target_with_masks(value)
        self.record["messages"][-1]["content"] = target
        self.record["supervision"] = masks
        encoded = sft.encode_train(self.processor, self.root, self.record, 4096)
        supervised = encoded["input_ids"][encoded["labels"] != -100].tolist()
        visible = self.processor.tokenizer.decode(supervised)
        self.assertIn("## Identity", visible)
        self.assertNotIn("## Segment 1", visible)
        self.assertNotIn("unresolved", visible)

    def test_field_review_retains_failure_tokens_after_image_expansion(self):
        from test_oopsie_v3 import proposed_failure
        target, masks = md.target_with_masks(proposed_failure())
        self.record["messages"][-1]["content"] = target
        self.record["supervision"] = masks
        encoded = sft.encode_train(self.processor, self.root, self.record, 4096)
        supervised = self.processor.tokenizer.decode(encoded["input_ids"][encoded["labels"] != -100].tolist())
        self.assertIn("Failure: Yes", supervised)
        self.assertIn("Categories: manipulation", supervised)
        for unsupported in ("Frames:", "Action:", "Observed result", "caf\u00e9", "Severity:"):
            self.assertNotIn(unsupported, supervised)

    def test_chunked_multimodal_loss_matches_native_and_has_adapter_gradients(self):
        from transformers import Qwen2_5_VLConfig, Qwen2_5_VLForConditionalGeneration
        from peft import LoraConfig, get_peft_model, PeftModel

        torch.manual_seed(4)
        cfg = Qwen2_5_VLConfig(text_config=dict(vocab_size=152064, hidden_size=64, intermediate_size=128,
                    num_hidden_layers=1, num_attention_heads=4, num_key_value_heads=2,
                    rope_scaling=dict(rope_type="default", mrope_section=[2, 3, 3])),
                    vision_config=dict(depth=1, hidden_size=64, intermediate_size=128, num_heads=4,
                    out_hidden_size=64, fullatt_block_indexes=[0]))
        cfg._attn_implementation = "sdpa"
        model = Qwen2_5_VLForConditionalGeneration(cfg)
        targets = [name for name, _ in model.named_modules() if ".layers." in name and name.endswith("q_proj")]
        model = get_peft_model(model, LoraConfig(r=2, lora_alpha=4, target_modules=targets, task_type="CAUSAL_LM"))
        model.eval()
        batch = sft.encode_train(self.processor, self.root, self.record, 4096)
        native = model(**batch, use_cache=False).loss
        summed, count = sft.sft_loss(model, batch)
        self.assertTrue(torch.allclose(summed / count, native, atol=2e-5), (summed / count, native))
        (summed / count).backward()
        gradients = [p.grad for name, p in model.named_parameters() if p.requires_grad]
        self.assertTrue(any(g is not None and torch.isfinite(g).all() and g.abs().sum() > 0 for g in gradients))
        self.assertFalse(any(p.requires_grad for name, p in model.named_parameters() if ".visual." in name))
        saved = self.root / "adapter"
        model.save_pretrained(saved)
        restored = PeftModel.from_pretrained(Qwen2_5_VLForConditionalGeneration(cfg), saved)
        original_state = {k: v for k, v in model.state_dict().items() if "lora_" in k}
        restored_state = {k: v for k, v in restored.state_dict().items() if "lora_" in k}
        self.assertEqual(original_state.keys(), restored_state.keys())
        self.assertTrue(all(torch.equal(original_state[k], restored_state[k]) for k in original_state))

    @unittest.skipUnless(torch.cuda.is_available(), "CUDA is needed for the NF4 integration smoke test")
    def test_cuda_nf4_training_and_adapter_reload(self):
        from transformers import Qwen2_5_VLConfig, Qwen2_5_VLForConditionalGeneration

        cfg = Qwen2_5_VLConfig(text_config=dict(vocab_size=152064, hidden_size=64, intermediate_size=128,
                    num_hidden_layers=1, num_attention_heads=4, num_key_value_heads=2,
                    rope_scaling=dict(rope_type="default", mrope_section=[2, 3, 3])),
                    vision_config=dict(depth=1, hidden_size=64, intermediate_size=128, num_heads=4,
                    out_hidden_size=64, fullatt_block_indexes=[0]))
        base = self.root / "tiny_base"
        Qwen2_5_VLForConditionalGeneration(cfg).save_pretrained(base)
        settings = dict(model=str(base), lora_rank=2, lora_alpha=4)
        model = sft.load_model(settings, trainable=True)
        model.train()
        batch = {k: v.to("cuda") for k, v in sft.encode_train(self.processor, self.root, self.record, 4096).items()}
        loss, count = sft.sft_loss(model, batch)
        (loss / count).backward()
        params = [p for p in model.parameters() if p.requires_grad]
        self.assertTrue(torch.isfinite(loss))
        self.assertTrue(any(p.grad is not None and p.grad.abs().sum() > 0 for p in params))
        self.assertTrue(all(p.grad is None or torch.isfinite(p.grad).all() for p in params))
        torch.optim.AdamW(params, lr=1e-4).step()
        saved = self.root / "quant_adapter"
        model.save_pretrained(saved)
        model.eval()
        with torch.no_grad():
            before, _ = sft.sft_loss(model, batch)
        restored = sft.load_model(settings, adapter=str(saved))
        restored.eval()
        with torch.no_grad():
            after, _ = sft.sft_loss(restored, batch)
        self.assertTrue(torch.allclose(before, after, atol=0.05), (before, after))


if __name__ == "__main__":
    unittest.main()
