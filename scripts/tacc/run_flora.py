"""Run pinned upstream FLORA inference in a fresh, auditable output directory."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

from check_flora_results import check, check_rubric


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, required=True, help="fetch_flora.py runtime root")
    p.add_argument("--mode", choices=["dense", "terminal", "caption", "rubric"], required=True)
    p.add_argument("--jobs", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True, help="New directory for this attempt")
    p.add_argument("--plan", action="store_true", help="Print command; no inference or model downloads")
    p.add_argument("--dry-run", action="store_true", help="Upstream media/prompt validation; no inference")
    p.add_argument("--tensor-parallel-size", type=int, help="Omit to use NVIDIA's mode-specific default")
    p.add_argument("--max-num-seqs", type=int, help="Omit to use NVIDIA's default concurrency (8)")
    p.add_argument("--rubric-samples", type=int, help="Omit to use NVIDIA's default (9)")
    p.add_argument("--rubric-max-new-tokens", type=int)
    p.add_argument("--rubric-max-model-len", type=int)
    p.add_argument("--rubric-max-batched-tokens", type=int)
    p.add_argument("--reference-defaults", action="store_true", help="Reject inference overrides; retain upstream defaults")
    a = p.parse_args()
    overrides = (a.tensor_parallel_size, a.max_num_seqs, a.rubric_samples,
                 a.rubric_max_new_tokens, a.rubric_max_model_len, a.rubric_max_batched_tokens)
    if a.reference_defaults and (a.mode == 'caption' or any(v is not None for v in overrides)):
        p.error('--reference-defaults requires a Rewarder mode and no inference overrides')
    root, jobs, out = a.root.resolve(), a.jobs.resolve(), a.out.resolve()
    component = "data-engine" if a.mode == "caption" else "rewarder"
    code = root / component
    spec = json.loads(Path(__file__).with_name("models.lock.json").read_text(encoding="utf-8"))[component]
    receipt = json.loads((code / "fetch_receipt.json").read_text(encoding="utf-8"))
    if any(receipt.get(k) != spec[k] for k in spec):
        raise ValueError("Runtime receipt does not match pinned code revision")
    for name, expected in receipt["files"].items():
        path = (code / name).resolve()
        if not path.is_relative_to(code) or digest(path) != expected:
            raise ValueError(f"Fetched code changed: {name}")
    rows = [json.loads(line) for line in jobs.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows or len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Jobs must have unique episode IDs and be nonempty")
    video_hashes = {}
    for row in rows:
        paths = [row[k] for k in ("video", "left_wrist", "right_wrist") if row.get(k)] if a.mode == "caption" else row["videos"]
        for value in paths:
            path = (jobs.parent / value).resolve(strict=True)
            video_hashes[str(path)] = digest(path)
    command = [sys.executable]
    if a.mode == "caption":
        command += ["infer.py", "--input-jsonl", str(jobs)]
        command += ["--validate-only"] if a.dry_run else ["--output-dir", str(out / "captions"), "--include-audit"]
    else:
        command += ["-m", f"batch_utils.{a.mode}_reward", "--jobs", str(jobs), "--output", str(out / (a.mode + ".jsonl")),
                    "--model", spec["repo"], "--revision", spec["revision"]]
        for flag, value in (("--max-num-seqs", a.max_num_seqs),
                            ("--tensor-parallel-size", a.tensor_parallel_size)):
            if value is not None:
                command += [flag, str(value)]
        if a.mode == "dense":
            command += ["--frame-scores"]
        elif a.mode == "rubric":
            command += ["--keep-thinking"]
            for flag, value in (("--num-samples", a.rubric_samples),
                                ("--max-new-tokens", a.rubric_max_new_tokens),
                                ("--max-model-len", a.rubric_max_model_len),
                                ("--max-num-batched-tokens", a.rubric_max_batched_tokens)):
                if value is not None:
                    command += [flag, str(value)]
        else:
            command += ["--with-rationale"]
        if a.dry_run:
            command += ["--dry-run"]
    print(json.dumps(dict(cwd=str(code), command=command), indent=2), flush=True)
    if a.plan:
        return 0
    out.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    # An absolute Python path does not expose the venv's build-tool executables.
    # FlashInfer invokes ninja by name while compiling its CUDA kernels.
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    env["FLORA_MODEL_CACHE"] = str(root / "models")
    for key in ("FLORA_TEMPSEG_REPO", "FLORA_CAPTIONER_REPO"):
        env.pop(key, None)
    # Do not allow a caller's PYTHONPATH to select the other workflow's batch_utils.
    env.pop("PYTHONPATH", None)
    env["PYTHONUNBUFFERED"] = "1"
    versions = {}
    for name in ("torch", "transformers", "vllm", "peft", "av", "qwen-vl-utils", "torchvision", "torchcodec",
                 "decord", "numpy", "Pillow", "huggingface_hub"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            pass
    manifest = dict(started_utc=datetime.now(timezone.utc).isoformat(), code=spec,
                    jobs_sha256=digest(jobs), video_sha256=video_hashes,
                    command=command, python=sys.version, packages=versions,
                    status="running", human_verified=False,
                    reference_batch_defaults=a.reference_defaults,
                    video_reader=env.get('FORCE_QWENVL_VIDEO_READER', 'upstream_auto'),
                    gpu_visibility=env.get('CUDA_VISIBLE_DEVICES'),
                    environment_overrides={key: env[key] for key in sorted(env)
                                           if key.startswith(('VLLM_', 'TORCHCODEC_', 'FORCE_QWENVL_'))})
    manifest_path = out / "run.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    try:
        result = subprocess.run(command, cwd=code, env=env, check=False)
        status = result.returncode
        if status == 0 and not a.dry_run and a.mode == "dense":
            report = check(out / "dense.jsonl", jobs)
            (out / "validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            if not report["structurally_valid"]:
                status = 2
        if status == 0 and not a.dry_run and a.mode == "rubric":
            report = check_rubric(out / "rubric.jsonl", jobs, a.rubric_samples if a.rubric_samples is not None else 9)
            (out / "validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            if not report["structurally_valid"]:
                status = 2
        if status == 0 and not a.dry_run and a.mode == "caption":
            for row in rows:
                prediction = json.loads((out / "captions" / (row["id"] + ".json")).read_text(encoding="utf-8"))
                if any(s.get("status") != "complete" for s in prediction["segments"]):
                    status = 2
        manifest.update(status=("validated_inputs" if a.dry_run else "completed") if status == 0 else "failed_or_needs_review", exit_code=status)
        return status
    except BaseException:
        manifest["status"] = "interrupted_or_failed"
        raise
    finally:
        manifest["finished_utc"] = datetime.now(timezone.utc).isoformat()
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
