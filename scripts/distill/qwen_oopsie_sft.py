"""Qwen2.5-VL QLoRA SFT, input audit, and generation for frozen OopsieData.

All assistant exclusions use real tokenizer character offsets. The model receives
its native processor outputs, including image_grid_thw and multimodal positions.
No Gemma token IDs, simulator telemetry heuristics, or silent truncation.
"""
import argparse
import importlib.metadata
import json
import math
from pathlib import Path
import random
import time

import oopsie_common as common

MODEL = "Qwen/Qwen2.5-VL-7B-Instruct"
REVISION = "cc594898137f460bfe9f0759e9844b3ce807cfb5"


def processor_for(cfg):
    from transformers import AutoProcessor, AutoTokenizer
    revision = cfg.get("revision", REVISION)
    processor = AutoProcessor.from_pretrained(cfg["model"], revision=revision,
                      min_pixels=cfg["min_pixels"], max_pixels=cfg["max_pixels"], use_fast=False,
                      local_files_only=cfg.get('local_files_only',False))
    # Keep the pinned image implementation, but require the fast tokenizer for
    # Unicode offsets. AutoProcessor's use_fast flag otherwise affects both.
    processor.tokenizer = AutoTokenizer.from_pretrained(cfg["model"], revision=revision, use_fast=True,
                                                       local_files_only=cfg.get('local_files_only',False))
    if not processor.tokenizer.is_fast:
        raise ValueError("A fast tokenizer is required to honor Unicode loss masks")
    return processor


def load_images(root, messages):
    from PIL import Image
    images = []
    for message in messages:
        for item in message["content"] if isinstance(message["content"], list) else []:
            if item["type"] == "image":
                with Image.open(common.inside(root, item["image"])) as image:
                    images.append(image.convert("RGB"))
    return images


def encoded_prompt(processor, root, messages):
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    return processor(text=[text], images=load_images(root, messages), return_tensors="pt")


def text_labels(token_ids, offsets, assistant_start, assistant, excluded, special_ids, eos_id):
    """Return full-text-token labels; expanded prompt images are handled separately.

    Overlap with any excluded Unicode-character range masks the whole token,
    including tokens that straddle an allowed/excluded boundary.
    """
    end = assistant_start + len(assistant)
    labels = []
    for tid, (start, stop) in zip(token_ids, offsets):
        if start >= assistant_start and stop <= end and stop > start and tid not in special_ids:
            local_start, local_end = start - assistant_start, stop - assistant_start
            bad = any(local_start < r["end"] and local_end > r["start"] for r in excluded)
            labels.append(-100 if bad else tid)
        else:
            labels.append(-100)
    # Only the first native end-of-turn token after the exact assistant content.
    for index, (tid, (start, _)) in enumerate(zip(token_ids, offsets)):
        if start >= end and tid == eos_id:
            labels[index] = tid
            break
    return labels


def encode_train(processor, root, record, max_length):
    import torch
    user = record["messages"][:-1]
    assistant = record["messages"][-1]["content"]
    prompt = processor.apply_chat_template(user, tokenize=False, add_generation_prompt=True)
    full = processor.apply_chat_template(record["messages"], tokenize=False, add_generation_prompt=False)
    if not full.startswith(prompt + assistant):
        raise ValueError("Chat template rewrites the target or changes the assistant prefix")
    plain = processor.tokenizer(full, add_special_tokens=False, return_offsets_mapping=True)
    labels = text_labels(plain["input_ids"], plain["offset_mapping"], len(prompt), assistant,
                         record["supervision"]["assistant_excluded_char_ranges"],
                         set(processor.tokenizer.all_special_ids), processor.tokenizer.eos_token_id)
    # The real processor expands image placeholders. Align the entire assistant
    # suffix against its output, proving that offsets match the actual sequence.
    first = next((i for i, (_, end) in enumerate(plain["offset_mapping"]) if end > len(prompt)), None)
    if first is None or plain["offset_mapping"][first][0] != len(prompt):
        raise ValueError("Assistant boundary is not an exact tokenizer boundary")
    batch = processor(text=[full], images=load_images(root, user), return_tensors="pt")
    tail = plain["input_ids"][first:]
    if batch["input_ids"][0, -len(tail):].tolist() != tail:
        raise ValueError("Assistant tokens differ after multimodal image expansion")
    size = batch["input_ids"].shape[1]
    if size > max_length:
        raise ValueError(f"{record['id']}: {size} tokens exceeds {max_length}; revise the input contract, never truncate targets")
    batch["labels"] = torch.tensor([[-100] * (size - len(tail)) + labels[first:]], dtype=torch.long)
    if not bool((batch["labels"] != -100).any()):
        raise ValueError("No supervised tokens remain")
    return batch


def load_model(cfg, trainable=False, adapter=None, quantized=True):
    import torch
    from transformers import Qwen2_5_VLForConditionalGeneration, BitsAndBytesConfig
    from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training

    if not torch.cuda.is_available():
        raise ValueError("CUDA PyTorch is required for the 7B model; CPU input audits work separately")
    kwargs = dict(revision=cfg.get("revision", REVISION), torch_dtype=torch.bfloat16,
                  device_map={"": 0}, attn_implementation="sdpa",local_files_only=cfg.get('local_files_only',False))
    if quantized:
        kwargs["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16)
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(cfg["model"], **kwargs)
    if trainable:
        if quantized:
            model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True,
                                                    gradient_checkpointing_kwargs={"use_reentrant": False})
        model.config.use_cache = False
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        model.enable_input_require_grads()
    if adapter:
        model = PeftModel.from_pretrained(model, adapter, is_trainable=trainable)
    elif trainable:
        # Match decoder layers only. Vision attention uses some of the same
        # projection names and must remain frozen in this baseline.
        targets = [name for name, _ in model.named_modules() if ".layers." in name and ".visual." not in name
                   and name.rsplit(".", 1)[-1] in {"q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"}]
        if not targets:
            raise ValueError("No Qwen language decoder LoRA targets found")
        model = get_peft_model(model, LoraConfig(r=cfg["lora_rank"], lora_alpha=cfg["lora_alpha"],
                    lora_dropout=0.05, target_modules=targets, bias="none", task_type="CAUSAL_LM"))
    if trainable and any(p.requires_grad for name, p in model.named_parameters() if ".visual." in name):
        raise ValueError("Vision tower must be frozen")
    return model


def sft_loss(model, batch, chunk_size=128):
    """Token-summed shifted CE without materializing prompt x vocabulary logits.

    Run the native Qwen multimodal core, then project only supervised positions.
    Chunked, checkpointed projection bounds the large vocabulary activations.
    """
    import torch
    from torch.utils.checkpoint import checkpoint

    base = model.get_base_model() if hasattr(model, "get_base_model") else model
    labels = batch["labels"][0]
    inputs = {k: v for k, v in batch.items() if k != "labels"}
    hidden = base.model(**inputs, use_cache=False).last_hidden_state[0]
    positions = (labels[1:] != -100).nonzero().flatten()
    if not len(positions):
        raise ValueError("No supervised next tokens")
    targets = labels[1:][positions]
    selected = hidden[positions]

    def project_loss(states, weight, target):
        logits = torch.nn.functional.linear(states, weight).float()
        return torch.nn.functional.cross_entropy(logits, target, reduction="sum")

    losses = [checkpoint(project_loss, selected[i:i + chunk_size], base.lm_head.weight,
                         targets[i:i + chunk_size], use_reentrant=False)
              for i in range(0, len(positions), chunk_size)]
    return torch.stack(losses).sum(), len(positions)


def audit_inputs(run, processor=None):
    manifest = common.verify(run)
    cfg = manifest["config"]["student"]
    processor = processor or processor_for(cfg)
    rows = []
    for episode in manifest["episodes"]:
        encoded = encoded_prompt(processor, run, common.messages(run, manifest, episode))
        length = encoded["input_ids"].shape[1]
        rows.append(dict(episode=episode["id"], split=episode["split"], prompt_tokens=length,
                         images=len(episode["images"]), max_length=cfg["max_length"],
                         available_target_tokens=cfg["max_length"] - length))
        print(json.dumps(rows[-1]), flush=True)
    return dict(model=cfg["model"], revision=cfg.get("revision", REVISION), episodes=rows,
                model_weights_loaded=False, api_calls=0)


def train(data_path, out, max_steps=None, max_hours=5.0):
    import torch
    root, manifest, rows = common.load_export(data_path, "train")
    cfg = manifest["config"]["student"]
    rows = [r for r in rows if r["supervision"].get("has_eligible_segment_targets", r["supervision"]["has_unflagged_segment_targets"])]
    if not rows:
        raise ValueError("No eligible segment targets; review/collect more data before training")
    out = Path(out)
    if out.exists():
        raise ValueError("Training requires a fresh output directory")
    processor = processor_for(cfg)
    # Audit every training sequence before loading weights or starting updates.
    for row in rows:
        encode_train(processor, root, row, cfg["max_length"])
    random.seed(cfg["seed"])
    torch.manual_seed(cfg["seed"])
    torch.cuda.manual_seed_all(cfg["seed"])
    model = load_model(cfg, trainable=True)
    parameters = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(parameters, lr=cfg["learning_rate"])
    out.mkdir(parents=True)
    versions = {name: importlib.metadata.version(name) for name in ("torch", "transformers", "peft", "bitsandbytes")}
    common.write(out / "run.json", dict(student=dict(cfg, revision=cfg.get("revision", REVISION)), versions=versions,
                code_sha256={name: common.sha(Path(__file__).parent / name) for name in
                             ("qwen_oopsie_sft.py", "oopsie_common.py", "oopsie_markdown.py")},
                manifest_sha256=common.sha(root / "manifest.json"), export_sha256=common.sha(Path(data_path) / "export.json"),
                train_ids=[r["id"] for r in rows], max_steps=max_steps, max_hours=max_hours,
                adapter_scope="language_decoder_only", optimizer_resume_supported=False))
    accum = cfg["gradient_accumulation"]
    total = math.ceil(len(rows) / accum) * cfg["epochs"]
    if max_steps:
        total = min(total, max_steps)
    start, step = time.monotonic(), 0
    model.train()
    optimizer.zero_grad(set_to_none=True)
    with (out / "train.jsonl").open("x", encoding="utf-8") as log:
        for epoch in range(cfg["epochs"]):
            order = list(rows)
            random.shuffle(order)
            for offset in range(0, len(order), accum):
                group = [encode_train(processor, root, r, cfg["max_length"]) for r in order[offset:offset + accum]]
                n_tokens = sum(int((b["labels"][:, 1:] != -100).sum()) for b in group)
                loss_sum = 0.0
                for batch in group:
                    batch = {k: v.to("cuda") for k, v in batch.items()}
                    loss, _ = sft_loss(model, batch)
                    if not torch.isfinite(loss):
                        raise ValueError("Nonfinite loss; no optimizer update")
                    (loss / n_tokens).backward()
                    loss_sum += loss.detach().item()
                norm = torch.nn.utils.clip_grad_norm_(parameters, 1.0, error_if_nonfinite=True)
                # Short warmup followed by cosine decay, based on optimizer updates.
                warmup = max(1, math.ceil(total * 0.03))
                scale = (step + 1) / warmup if step < warmup else 0.1 + 0.9 * (1 + math.cos(math.pi * (step - warmup) / max(1, total - warmup))) / 2
                for group_config in optimizer.param_groups:
                    group_config["lr"] = cfg["learning_rate"] * scale
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
                step += 1
                entry = dict(step=step, epoch=epoch, loss=loss_sum / n_tokens, supervised_tokens=n_tokens,
                             grad_norm=float(norm), elapsed_seconds=time.monotonic() - start,
                             peak_gpu_gb=torch.cuda.max_memory_allocated() / 1e9)
                log.write(json.dumps(entry) + "\n")
                log.flush()
                print(json.dumps(entry), flush=True)
                if step >= total or time.monotonic() - start >= max_hours * 3600:
                    break
            # Save at each epoch/cap; no false claim of optimizer-resumable state.
            checkpoint = out / f"adapter_step_{step}"
            model.save_pretrained(checkpoint)
            processor.save_pretrained(checkpoint)
            if step >= total or time.monotonic() - start >= max_hours * 3600:
                break
    common.write(out / "completion.json", dict(steps=step, planned_steps=total, adapter=checkpoint.name,
                 completed_schedule=step >= total, elapsed_seconds=time.monotonic() - start))
    return dict(out=str(out), steps=step, adapter=str(checkpoint))


def generate(run, out, split="development", adapter=None, max_new_tokens=12288):
    import torch
    manifest = common.verify(run)
    cfg = manifest["config"]["student"]
    if adapter:
        training = common.read(Path(adapter).parent / "run.json")
        if training["manifest_sha256"] != common.sha(Path(run) / "manifest.json"):
            raise ValueError("Adapter was trained against a different evidence/split manifest")
    out = Path(out)
    if out.exists():
        raise ValueError("Generation requires a fresh output directory")
    processor = processor_for(cfg)
    model = load_model(cfg, adapter=adapter)
    model.eval()
    out.mkdir(parents=True)
    common.write(out / "generation.json", dict(model=cfg["model"], revision=cfg.get("revision", REVISION),
                adapter=str(adapter) if adapter else None, split=split, max_new_tokens=max_new_tokens,
                manifest_sha256=common.sha(Path(run) / "manifest.json")))
    for episode in manifest["episodes"]:
        if episode["split"] != split:
            continue
        encoded = encoded_prompt(processor, run, common.messages(run, manifest, episode))
        prompt_length = encoded["input_ids"].shape[1]
        if prompt_length + max_new_tokens > cfg["max_length"]:
            raise ValueError("Prompt plus generation budget exceeds the frozen context cap")
        encoded = encoded.to("cuda")
        started = time.monotonic()
        with torch.inference_mode():
            generated = model.generate(**encoded, do_sample=False, max_new_tokens=max_new_tokens)
        tokens = generated[0, prompt_length:]
        text = processor.tokenizer.decode(tokens, skip_special_tokens=True)
        record = dict(episode=episode["id"], text=text, output_tokens=len(tokens),
                      hit_max=len(tokens) >= max_new_tokens, elapsed_seconds=time.monotonic() - started)
        try:
            common.validate_annotation(common.parse_answer(text, common.annotation_format(manifest)), episode)
            record["schema_valid"] = True
        except (ValueError, KeyError, TypeError) as exc:
            record.update(schema_valid=False, error=str(exc))
        common.write(out / (episode["id"] + ".json"), record)
    return dict(out=str(out), split=split)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("audit-inputs")
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p = sub.add_parser("audit")
    p.add_argument("--data", type=Path, required=True)
    p = sub.add_parser("train")
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--max-steps", type=int)
    p.add_argument("--max-hours", type=float, default=5.0)
    p = sub.add_parser("generate")
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--split", choices=("train", "development", "test"), default="development")
    p.add_argument("--adapter", type=Path)
    p.add_argument("--max-new-tokens", type=int, default=12288)
    args = parser.parse_args()
    if args.command == "audit-inputs":
        result = audit_inputs(args.run)
        common.write(args.out, result)
    elif args.command == "audit":
        root, manifest, rows = common.load_export(args.data)
        cfg = manifest["config"]["student"]
        processor = processor_for(cfg)
        encoded = [encode_train(processor, root, r, cfg["max_length"]) for r in rows
                   if r["supervision"].get("has_eligible_segment_targets", r["supervision"]["has_unflagged_segment_targets"])]
        result = dict(eligible_episodes=len(encoded), skipped_without_eligible_segments=len(rows) - len(encoded),
                      sequences=[b["input_ids"].shape[1] for b in encoded])
    elif args.command == "train":
        if (args.max_steps is not None and args.max_steps <= 0) or args.max_hours <= 0:
            parser.error("Training step/time caps must be positive")
        result = train(args.data, args.out, args.max_steps, args.max_hours)
    else:
        result = generate(args.run, args.out, args.split, args.adapter, args.max_new_tokens)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
