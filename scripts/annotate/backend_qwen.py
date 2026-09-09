"""Local Qwen3-VL backend (transformers, bf16, no quantization: 8B weights ~16.3 GiB fit the 3090).

Sampling K completions of one prompt is done with ONE prefill (vision tower + 6k prompt tokens run once); the KV cache
is then repeated K times and only the decode runs batched. Plain `generate(num_return_sequences=K)` would expand the
images and the prompt K times before the prefill, which on this card spilled into host memory (25 GiB) and made each
episode take four minutes.

`torch.cuda.set_per_process_memory_fraction` makes an over-allocation raise OOM instead of silently spilling through
the WDDM driver, so the batch can be halved automatically.

Interface (so another backend can be dropped in):
    backend.generate(system: str, content: list[block], k: int, ...) -> list[str]  (k raw completions)
where a block is {"type": "text", "text": str} or {"type": "image", "image": PIL.Image}.
"""
import time

import torch

DEFAULT_MODEL = "Qwen/Qwen3-VL-8B-Instruct"


class QwenBackend:
    def __init__(self, model_id=DEFAULT_MODEL, attn="sdpa", device="cuda", mem_fraction=0.93):
        from transformers import AutoModelForImageTextToText, AutoProcessor

        t = time.time()
        self.model_id = model_id
        self.device = device
        if device.startswith("cuda") and mem_fraction:
            torch.cuda.set_per_process_memory_fraction(mem_fraction)
        self.processor = AutoProcessor.from_pretrained(model_id)
        self.model = AutoModelForImageTextToText.from_pretrained(model_id, dtype=torch.bfloat16, device_map=device, attn_implementation=attn)
        self.model.eval()
        self.load_s = time.time() - t
        self.last = {}

    @staticmethod
    def _split(content):
        images, blocks = [], []
        for b in content:
            if b["type"] == "image":
                images.append(b["image"].convert("RGB"))
                blocks.append({"type": "image"})
            else:
                blocks.append({"type": "text", "text": b["text"]})
        return images, blocks

    def _inputs(self, system, content):
        images, blocks = self._split(content)
        messages = [{"role": "system", "content": [{"type": "text", "text": system}]}, {"role": "user", "content": blocks}]
        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.processor(text=[text], images=images if images else None, return_tensors="pt")
        return inputs.to(self.device)

    @torch.inference_mode()
    def _prefill(self, inputs):
        """Run everything except the last prompt token through the model once; return the KV cache."""
        pre = {}
        for k, v in inputs.items():
            if k in ("input_ids", "attention_mask", "mm_token_type_ids"):
                pre[k] = v[:, :-1]
            else:
                pre[k] = v
        self.model.model.rope_deltas = None  # force fresh M-RoPE deltas for this prompt
        out = self.model(**pre, use_cache=True, logits_to_keep=1)
        return out.past_key_values

    @torch.inference_mode()
    def generate(self, system, content, k=5, temperature=0.7, top_p=0.8, top_k=20, max_new_tokens=1200, batch=5):
        inputs = self._inputs(system, content)
        n_in = int(inputs["input_ids"].shape[1])
        t0 = time.time()
        torch.cuda.reset_peak_memory_stats()
        sample_kwargs = dict(do_sample=True, temperature=temperature, top_p=top_p, top_k=top_k) if temperature > 0 else dict(do_sample=False)

        outs, remaining, oom, prefill_s, rounds = [], k, 0, 0.0, 0
        while remaining > 0:
            b = min(batch, remaining)
            c = None
            try:
                # a fresh prefill per decode round (~3 s) is cheaper in memory than keeping a base cache and copying it
                tp = time.time()
                c = self._prefill(inputs)
                if b > 1:
                    c.batch_repeat_interleave(b)
                    self.model.model.rope_deltas = self.model.model.rope_deltas.repeat(b, 1)
                prefill_s += time.time() - tp
                gen = self.model.generate(input_ids=inputs["input_ids"].repeat(b, 1), attention_mask=inputs["attention_mask"].repeat(b, 1),
                                          past_key_values=c, max_new_tokens=max_new_tokens, pad_token_id=self.processor.tokenizer.pad_token_id,
                                          **sample_kwargs)
            except torch.cuda.OutOfMemoryError:
                del c
                torch.cuda.empty_cache()
                oom += 1
                if batch == 1:
                    raise
                batch = max(1, batch // 2)
                continue
            rounds += 1
            outs += self.processor.batch_decode(gen[:, n_in:], skip_special_tokens=True)
            remaining -= b
            del c, gen
            torch.cuda.empty_cache()
        self.last = {"input_tokens": n_in, "n_images": sum(1 for c in content if c["type"] == "image"), "prefill_s": round(prefill_s, 1),
                     "gen_s": round(time.time() - t0, 1), "batch": batch, "rounds": rounds, "oom_retries": oom,
                     "max_mem_gb": round(torch.cuda.max_memory_allocated() / 2**30, 2)}
        return outs

    @torch.inference_mode()
    def generate_many(self, system, contents, temperature=0.0, top_p=0.8, top_k=20, max_new_tokens=400, batch=8):
        """Run several INDEPENDENT prompts (one content list each, typically one image) as left-padded batches.

        Unlike `generate`, the prompts differ, so there is no shared prefill: each batch is one processor call
        (`padding=True`, left side) and one plain `model.generate`. Qwen3-VL's `get_rope_index` masks each row with
        the attention mask before computing M-RoPE positions and the decode positions are `cumsum(mask) - 1 +
        rope_deltas`, so left padding is exact. Returns one raw string per prompt, in input order. The batch is
        halved on CUDA OOM. `self.last` reports n_prompts, batches, gen_s, max_mem_gb.
        """
        contents = list(contents)
        t0 = time.time()
        if self.device.startswith("cuda"):
            torch.cuda.reset_peak_memory_stats()
        sample_kwargs = dict(do_sample=True, temperature=temperature, top_p=top_p, top_k=top_k) if temperature > 0 else dict(do_sample=False)
        tokenizer = self.processor.tokenizer
        previous_side = tokenizer.padding_side
        tokenizer.padding_side = "left"
        outs, i, batches, oom = [], 0, 0, 0
        try:
            while i < len(contents):
                b = min(batch, len(contents) - i)
                inputs = gen = None
                try:
                    texts, images = [], []
                    for content in contents[i:i + b]:
                        imgs, blocks = self._split(content)
                        messages = [{"role": "system", "content": [{"type": "text", "text": system}]}, {"role": "user", "content": blocks}]
                        texts.append(self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True))
                        images.extend(imgs)
                    inputs = self.processor(text=texts, images=images if images else None, padding=True, padding_side="left",
                                            return_tensors="pt").to(self.device)
                    self.model.model.rope_deltas = None  # fresh M-RoPE deltas for this batch
                    gen = self.model.generate(**inputs, max_new_tokens=max_new_tokens, pad_token_id=tokenizer.pad_token_id, **sample_kwargs)
                except torch.cuda.OutOfMemoryError:
                    del inputs, gen
                    torch.cuda.empty_cache()
                    oom += 1
                    if batch == 1:
                        raise
                    batch = max(1, batch // 2)
                    continue
                n_in = int(inputs["input_ids"].shape[1])  # identical for every row after left padding
                outs += self.processor.batch_decode(gen[:, n_in:], skip_special_tokens=True)
                i += b
                batches += 1
                del inputs, gen
                if self.device.startswith("cuda"):
                    torch.cuda.empty_cache()
        finally:
            tokenizer.padding_side = previous_side
        self.last = {"n_prompts": len(contents), "batches": batches, "batch": batch, "oom_retries": oom,
                     "gen_s": round(time.time() - t0, 1),
                     "max_mem_gb": round(torch.cuda.max_memory_allocated() / 2**30, 2) if self.device.startswith("cuda") else 0.0}
        return outs
