"""Run a bounded, checkpointed Qwen3.8-27B QLoRA pilot on one Modal L40S."""
from contextlib import nullcontext
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
import tarfile
from tempfile import mkdtemp
import time
from uuid import uuid4

import modal

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS / "distill"))
from qwen_backbone_timing import MODELS, digest, encode, load_qlora, loss_sum, read

MODEL, REVISION = MODELS["candidate"]
ROOT = Path("/astra")
SNAPSHOT = ROOT / "hf" / f"models--{MODEL.replace('/', '--')}" / "snapshots" / REVISION
VOLUME_NAME = "qwen-astra-pilot"
PILOT_DATA = ROOT / "pilot-grouped"
PAIRED_DATA = ROOT / "paired-v2"
volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)
app = modal.App("qwen38-astra-sft-pilot")
image = (
    modal.Image.from_registry("nvidia/cuda:12.8.1-devel-ubuntu24.04", add_python="3.12")
    .apt_install("build-essential", "git")
    .env({"TORCH_CUDA_ARCH_LIST": "8.9", "MAX_JOBS": "4", "TOKENIZERS_PARALLELISM": "false",
          "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
          "PYTHONPATH": "/root/qwen_astra_imports"})
    .pip_install("torch==2.11.0+cu128", "torchvision==0.26.0+cu128",
                 extra_index_url="https://download.pytorch.org/whl/cu128")
    .pip_install_from_requirements(str(SCRIPTS / "distill" / "requirements-backbone-timing-v1.txt"))
    .add_local_file(SCRIPTS / "modal" / "build_causal_conv.py", "/tmp/build_causal_conv.py", copy=True)
    .run_commands("python /tmp/build_causal_conv.py && rm /tmp/build_causal_conv.py")
    .add_local_file(SCRIPTS / "distill" / "qwen_backbone_timing.py",
                    "/root/qwen_astra_imports/qwen_backbone_timing.py")
) if modal.is_local() else None


def failure_intervals(markdown, start, stop):
    section = re.search(r"(?im)^# Failure segments[ \t]*$", markdown)
    if not section:
        raise ValueError("Missing Failure segments heading")
    table = re.split(r"(?m)^#", markdown[section.end():], maxsplit=1)[0]
    rows = re.findall(r"(?im)^\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(Yes|No)\s*\|\s*$", table)
    intervals = []
    cursor = start
    for first, last, failure in rows:
        a, b = int(first), int(last)
        if cursor != a or not a < b <= stop:
            raise ValueError("Segments do not partition the window")
        if failure.lower() == "yes":
            intervals.append((a, b))
        cursor = b
    if cursor != stop:
        raise ValueError("Incomplete segment coverage")
    return intervals


def frame_mask(markdown, start, stop):
    return {frame for a, b in failure_intervals(markdown, start, stop) for frame in range(a, b)}


def generate_text(model, processor, batch):
    import torch

    with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
        generated = model.generate(**batch, do_sample=False, use_cache=True,
                                   max_new_tokens=512, max_time=90)
    return processor.tokenizer.decode(
        generated[0, batch["input_ids"].shape[1]:], skip_special_tokens=True)


def compare(model, processor, data, windows, folder, deadline):
    model.eval()
    scores = {}
    for arm in ("base", "adapter"):
        scores[arm] = []
    for window in windows:
        if time.monotonic() + 210 >= deadline:
            break
        batch = encode(processor, data, window, "SCE", "qwen3_5", include_target=False)
        batch = batch.to("cuda")
        start, stop = window["start"], window["start"] + window["count"]
        gold = frame_mask(window["targets"]["SCE"], start, stop)
        for arm in scores:
            with model.disable_adapter() if arm == "base" else nullcontext():
                text = generate_text(model, processor, batch)
            (folder / f"{window['id']}_{arm}.md").write_text(text, encoding="utf-8")
            try:
                prediction = frame_mask(text, start, stop)
                valid = True
            except ValueError:
                prediction = set()
                valid = False
            scores[arm].append(dict(id=window["id"], segment_table_valid=valid, tp=len(gold & prediction),
                                    fp=len(prediction - gold), fn=len(gold - prediction)))
        del batch
    for arm, rows in scores.items():
        tp, fp, fn = (sum(row[key] for row in rows) for key in ("tp", "fp", "fn"))
        scores[arm] = dict(windows=len(rows), valid=sum(r["segment_table_valid"] for r in rows),
                           failure_f1=2 * tp / (2 * tp + fp + fn) if tp + fp + fn else None,
                           failure_iou=tp / (tp + fp + fn) if tp + fp + fn else None, rows=rows)
    return scores


def save_checkpoint(model, processor, optimizer, folder, step, plan_sha):
    import torch

    final = folder / f"step-{step:03d}"
    staging = folder / f".checkpoint-{uuid4().hex}"
    adapter_config = model.peft_config["default"]
    adapter_config.base_model_name_or_path = MODEL
    adapter_config.revision = REVISION
    model.save_pretrained(staging, save_embedding_layers=False)
    processor.save_pretrained(staging)
    torch.save(dict(step=step, plan_sha256=plan_sha, optimizer=optimizer.state_dict(),
                    cpu_rng=torch.random.get_rng_state(), cuda_rng=torch.cuda.get_rng_state()),
               staging / "training_state.pt")
    staging.rename(final)
    volume.commit()
    return final.name


def read_pilot(plan_sha, source=PILOT_DATA):
    plan_file = source / "plan.json"
    if digest(plan_file) != plan_sha:
        raise ValueError("Pilot manifest differs from the submitted plan")
    plan = read(plan_file)
    if plan["model"] != [MODEL, REVISION]:
        raise ValueError("Unexpected checkpoint revision")
    if not plan.get("split_manifest_sha256"):
        raise ValueError("Training requires the frozen episode-grouped split")
    windows = plan["windows"]
    labels = {w["split"] for w in windows}
    if labels != {"train", "development"}:
        raise ValueError("Training volumes can contain only train and development windows")
    train_episodes = {w["episode"] for w in windows if w["split"] == "train"}
    dev_episodes = {w["episode"] for w in windows if w["split"] == "development"}
    if train_episodes & dev_episodes or len({w["id"] for w in windows}) != len(windows):
        raise ValueError("Pilot windows must be unique and development episodes disjoint")
    return plan


def stage_frames(plan, source=PILOT_DATA):
    data = Path(mkdtemp(prefix="astra-frames-")).resolve()
    expected = {entry["path"]: entry["sha256"]
                for window in plan["windows"] for entry in window["images"]}
    with tarfile.open(source / "frames.tar", mode="r|", bufsize=1024**2) as archive:
        for member in archive:
            checksum = expected.pop(member.name, None)
            path = data / member.name
            if checksum is None or not member.isfile() or not path.resolve().is_relative_to(data):
                raise ValueError(f"Unexpected frame archive entry: {member.name}")
            with archive.extractfile(member) as stream:
                content = stream.read()
            if sha256(content).hexdigest() != checksum:
                raise ValueError(f"Changed video frame: {member.name}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    if expected:
        raise ValueError(f"Frame archive is missing {len(expected)} inputs")
    return data


def run_training(plan_sha, source, resume_checkpoint, *, train_windows, development_windows,
                 accumulation, learning_rate, train_seconds, evaluation_deadline):
    import causal_conv1d
    import fla.ops.gated_delta_rule
    import torch
    from transformers import AutoProcessor, set_seed

    started = time.monotonic()
    plan = read_pilot(plan_sha, source)
    device = torch.cuda.get_device_properties(0)
    if torch.cuda.device_count() != 1 or "L40S" not in device.name:
        raise ValueError("This pilot requires a single L40S")
    training = [window for window in plan["windows"] if window["split"] == "train"]
    heldout = [window for window in plan["windows"] if window["split"] == "development"]
    if len(training) != train_windows or len(heldout) != development_windows or train_windows % accumulation:
        raise ValueError("Unexpected pilot split")
    print(json.dumps(dict(stage="loading_model", model=MODEL, revision=REVISION, gpu=device.name,
                          gpu_memory_gib=device.total_memory / 1024**3, plan_sha256=plan_sha,
                          recipe=source.name, train_windows=train_windows, accumulation=accumulation,
                          learning_rate=learning_rate)), flush=True)
    audited = read(source / "token-audit.json")
    if audited["plan_sha"] != plan_sha or set(audited["tokens"]) != {w["id"] for w in plan["windows"]}:
        raise ValueError("An exact processor audit is required for this pilot manifest")
    data = stage_frames(plan, source)
    largest = max(training, key=lambda window: audited["tokens"][window["id"]])
    training = [largest, *(window for window in training if window is not largest)]
    set_seed(plan["seed"])
    resume = None
    if resume_checkpoint:
        resume = ROOT / "runs" / resume_checkpoint
        if not resume.resolve().is_relative_to((ROOT / "runs").resolve()):
            raise ValueError("Checkpoint must be inside the run directory")
    processor = AutoProcessor.from_pretrained(SNAPSHOT, local_files_only=True)
    model, _ = load_qlora(SNAPSHOT, require_linear_attention=True, adapter=resume)
    print(json.dumps(dict(stage="model_loaded", seconds=time.monotonic() - started,
                          trainable_parameters=sum(p.numel() for p in model.parameters() if p.requires_grad))),
          flush=True)
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=learning_rate)
    completed = 0
    if resume:
        state = torch.load(resume / "training_state.pt", map_location="cpu", weights_only=True)
        if state["plan_sha256"] != plan_sha:
            raise ValueError("Cannot resume a different pilot manifest")
        completed = state["step"]
        optimizer.load_state_dict(state["optimizer"])
        torch.random.set_rng_state(state["cpu_rng"])
        torch.cuda.set_rng_state(state["cuda_rng"])

    folder = ROOT / "runs" / uuid4().hex
    folder.mkdir(parents=True)
    deadline = started + evaluation_deadline
    model.train()
    steps = []
    checkpoint = None
    for index in range(completed + 1, train_windows // accumulation + 1):
        if time.monotonic() > started + train_seconds:
            break
        tick = time.monotonic()
        optimizer.zero_grad(set_to_none=True)
        torch.cuda.reset_peak_memory_stats()
        group = training[(index - 1) * accumulation:index * accumulation]
        input_tokens = 0
        mean_loss = 0.0
        for window in group:
            batch, audit = encode(processor, data, window, "SCE", "qwen3_5")
            batch = batch.to("cuda")
            with torch.autocast("cuda", dtype=torch.bfloat16):
                loss = loss_sum(model, batch) / accumulation
            loss.backward()
            input_tokens += audit["input_tokens"]
            mean_loss += float(loss.detach())
            del batch, loss
        grad = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0, error_if_nonfinite=True)
        optimizer.step()
        record = dict(step=index, episodes=[w["episode"] for w in group], input_tokens=input_tokens,
                      loss=mean_loss, grad_norm=float(grad), seconds=time.monotonic() - tick,
                      peak_reserved_gib=torch.cuda.max_memory_reserved() / 1024**3)
        steps.append(record)
        completed = index
        with (folder / "train.jsonl").open("a", encoding="utf-8") as log:
            log.write(json.dumps(record) + "\n")
        print(json.dumps(record), flush=True)
        if index == 1 or index % 5 == 0:
            checkpoint = save_checkpoint(model, processor, optimizer, folder, index, plan_sha)

    if steps and checkpoint != f"step-{completed:03d}":
        checkpoint = save_checkpoint(model, processor, optimizer, folder, completed, plan_sha)
    if completed:
        print(json.dumps(dict(stage="development_evaluation", steps=completed, run=folder.name,
                              checkpoint=checkpoint)), flush=True)
    scores = compare(model, processor, data, heldout, folder, deadline) if completed else {}
    report = dict(run=folder.name, model=MODEL, revision=REVISION, steps=completed, recipe=source.name,
                  checkpoint=checkpoint, evaluation=scores, elapsed_seconds=time.monotonic() - started)
    (folder / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    volume.commit()
    return report


@app.function(image=image, gpu="L40S", cpu=(4.0, 4.0), memory=(65536, 65536), timeout=7200, retries=0,
              scaledown_window=5, max_containers=1, volumes={str(ROOT): volume})
def train(plan_sha: str, resume_checkpoint: str = ""):
    return run_training(plan_sha, PILOT_DATA, resume_checkpoint, train_windows=50, development_windows=10,
                        accumulation=1, learning_rate=1e-4, train_seconds=5100, evaluation_deadline=7000)


@app.function(image=image, gpu="L40S", cpu=(4.0, 4.0), memory=(65536, 65536), timeout=5400, retries=0,
              scaledown_window=5, max_containers=1, volumes={str(ROOT): volume})
def train_paired(plan_sha: str):
    return run_training(plan_sha, PAIRED_DATA, "", train_windows=120, development_windows=20,
                        accumulation=2, learning_rate=3e-5, train_seconds=3600, evaluation_deadline=5200)


@app.function(image=image, timeout=360, cpu=(4.0, 4.0), memory=(8192, 8192),
              volumes={str(ROOT): volume})
def verify_runtime(plan_sha: str, recipe: str = "pilot-grouped") -> str:
    import causal_conv1d
    import fla.ops.gated_delta_rule
    import torch
    from transformers import AutoModelForImageTextToText, AutoProcessor

    source = {PILOT_DATA.name: PILOT_DATA, PAIRED_DATA.name: PAIRED_DATA}[recipe]
    plan = read_pilot(plan_sha, source)
    shards = set(read(SNAPSHOT / "model.safetensors.index.json")["weight_map"].values())
    if not shards or any(not (SNAPSHOT / shard).is_file() for shard in shards):
        raise ValueError("The cached snapshot is missing model shards")
    print("Staging the checksummed frames on local disk", flush=True)
    data = stage_frames(plan, source)
    processor = AutoProcessor.from_pretrained(SNAPSHOT, local_files_only=True)
    tokens = {}
    for window in plan["windows"]:
        if window["split"] == "train":
            _, audit = encode(processor, data, window, "SCE", "qwen3_5")
            tokens[window["id"]] = audit["input_tokens"]
        else:
            batch = encode(processor, data, window, "SCE", "qwen3_5", include_target=False)
            tokens[window["id"]] = batch["input_ids"].shape[1]
    checked = dict(torch=torch.__version__, model=MODEL, revision=REVISION, plan_sha=plan_sha,
                   weight_shards=len(shards), tokens=tokens,
                   verified_frames=sum(w["count"] for w in plan["windows"]))
    contents = json.dumps(checked, indent=2) + "\n"
    temporary = source / f".token-audit-{uuid4().hex}.tmp"
    temporary.write_text(contents, encoding="utf-8")
    temporary.replace(source / "token-audit.json")
    volume.commit()
    return contents


@app.function(image=image, gpu="L40S", cpu=(4.0, 4.0), memory=(65536, 65536), timeout=1800,
              retries=0, scaledown_window=5, max_containers=1, volumes={str(ROOT): volume})
def evaluate_early_checkpoints(plan_sha: str, pilot_run: str) -> str:
    import gc
    import torch
    from transformers import AutoProcessor, set_seed

    started = time.monotonic()
    if not re.fullmatch(r"[a-f0-9]{32}", pilot_run):
        raise ValueError("Expected the ID of the completed pilot")
    if torch.cuda.device_count() != 1 or "L40S" not in torch.cuda.get_device_properties(0).name:
        raise ValueError("Checkpoint evaluation requires exactly one L40S")
    source = ROOT / "runs" / pilot_run
    result = read(source / "report.json")
    if result["steps"] != 50 or result["revision"] != REVISION:
        raise ValueError("Expected the completed Qwen3.8-27B pilot")
    plan = read_pilot(plan_sha)
    data = stage_frames(plan)
    heldout = [window for window in plan["windows"] if window["split"] == "development"]
    if len(heldout) != 10:
        raise ValueError("Expected the pinned 10-window development set")
    processor = AutoProcessor.from_pretrained(SNAPSHOT, local_files_only=True)
    output = source / "early-development"
    output.mkdir(exist_ok=False)
    volume.commit()
    for step in (10, 25):
        checkpoint = source / f"step-{step:03d}"
        state = torch.load(checkpoint / "training_state.pt", map_location="cpu", weights_only=True)
        if state["step"] != step or state["plan_sha256"] != plan_sha:
            raise ValueError("Checkpoint belongs to a different training plan")
        del state
        set_seed(plan["seed"])
        model, _ = load_qlora(SNAPSHOT, require_linear_attention=True, adapter=checkpoint)
        model.eval()
        folder = output / checkpoint.name
        folder.mkdir()
        for window in heldout:
            if time.monotonic() + 100 > started + 1770:
                return str(output.relative_to(ROOT))
            batch = encode(processor, data, window, "SCE", "qwen3_5", include_target=False).to("cuda")
            text = generate_text(model, processor, batch)
            (folder / f"{window['id']}_adapter.md").write_text(text, encoding="utf-8")
            del batch
        volume.commit()
        print(f"Compared step {step} on all {len(heldout)} development windows", flush=True)
        del model
        gc.collect()
        torch.cuda.empty_cache()
    return str(output.relative_to(ROOT))


@app.local_entrypoint()
def main(plan_sha: str, resume_checkpoint: str = ""):
    print(json.dumps(train.remote(plan_sha, resume_checkpoint), indent=2))


@app.local_entrypoint()
def paired_main(plan_sha: str):
    print(json.dumps(train_paired.remote(plan_sha), indent=2))


@app.function(image=image, gpu="L40S", cpu=(4.0, 4.0), memory=(65536, 65536), timeout=1800,
              retries=0, scaledown_window=5, max_containers=1, volumes={str(ROOT): volume})
def original_prompt_check():
    import torch
    from transformers import AutoProcessor, set_seed

    started = time.monotonic()
    if torch.cuda.device_count() != 1 or "L40S" not in torch.cuda.get_device_properties(0).name:
        raise ValueError("Expected one L40S")
    source = ROOT / "runs" / "78bfbaf0aec94b6e83f70d88aa01d8a8"
    report = read(source / "report.json")
    if (report["revision"], report["steps"], report["checkpoint"], report["recipe"]) != (
            REVISION, 60, "step-060", "paired-v2"):
        raise ValueError("Unexpected trained adapter")
    plan = read_pilot("861fc9e3da76f1371813e4f51c94f80bb563564e09bc76fb62c4ed9ec4b31497", PAIRED_DATA)
    original = read_pilot("c7d1d56dfacf45d78c9f530da2de0af5de94c915d2bff163a8fecc9be3de4927")
    prior = {w["id"]: w["prompt"] for w in original["windows"] if w["split"] == "development"}
    windows = [w.copy() for w in plan["windows"] if w["split"] == "development"]
    suffix = ("\nMark a failure only when the video shows an unsuccessful action, unintended physical effect, "
              "or observable failure to progress. A clip can end before task completion without showing any "
              "failure. Ground each explanation in a named camera and source frames.")
    for w in windows:
        if not w["prompt"].endswith(suffix):
            raise ValueError("Unexpected paired prompt")
        w["prompt"] = w["prompt"].removesuffix(suffix)
    if len(windows) != 20 or {w["id"]: w["prompt"] for w in windows if w["id"] in prior} != prior:
        raise ValueError("Development prompts differ from the original template")
    folder = source / "original-prompt-check"
    folder.mkdir(exist_ok=False)
    volume.commit()
    data = stage_frames(plan, PAIRED_DATA)
    set_seed(plan["seed"])
    processor = AutoProcessor.from_pretrained(SNAPSHOT, local_files_only=True)
    model, _ = load_qlora(SNAPSHOT, require_linear_attention=True, adapter=source / report["checkpoint"])
    scores = compare(model, processor, data, windows, folder, started + 1760)
    (folder / "report.json").write_text(json.dumps(scores, indent=2) + "\n")
    volume.commit()
    return str(folder.relative_to(ROOT))
