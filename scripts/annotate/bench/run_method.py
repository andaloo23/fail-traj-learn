"""Run one registered method over a benchmark episode set (docs/segmentation_benchmark.md section 6).

  run_method.py --method whole_p8 --set dev|heldout|all [--episodes ds:ep ...] [--limit N] [--overwrite]
                [--model ID] [--dry-run]

Episode sets: $FTL_PROJ/bench/episodes_dev.json (dev) and episodes.json (heldout). --episodes replaces the set
with an explicit list. Existing predictions are skipped unless --overwrite. The Qwen backend is loaded ONCE;
its generate/generate_many are wrapped with a call counter. Predictions go to
$FTL_PROJ/bench/predictions/<method>/<dataset>/episode_XXXXXX.json, raw adapter output to
$FTL_PROJ/bench/raw/<method>/<dataset>/episode_XXXXXX/, one log line per episode to $FTL_PROJ/logs/bench_<method>.log.

Exactly one GPU process at a time on this machine: refuses to start if another run_method.py / annotate.py /
segmentation_lab.py process is running (skipped with --dry-run, which never loads the model).
"""
import argparse
import json
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

BENCH_DIR = Path(__file__).resolve().parent
ANNOTATE_DIR = BENCH_DIR.parent
for _p in (str(ANNOTATE_DIR), str(BENCH_DIR)):
    if _p not in sys.path:
        sys.path.append(_p)

from common import PROJ, Episode, dump_json, open_dataset  # noqa: E402
from methods import REGISTRY, load_method  # noqa: E402

BENCH = PROJ / "bench"
PRED_DIR = BENCH / "predictions"
RAW_DIR = BENCH / "raw"
LOG_DIR = PROJ / "logs"
GPU_PATTERN = "run_method.py|annotate.py|segmentation_lab.py"

PRED_FIELDS = ("held_obs", "events", "held_object", "chunk_labels", "chunk_q", "decisive_chunk", "cause",
               "n_model_calls", "wall_s", "peak_mem_gb", "raw_dir")


def ep_name(ep):
    return f"episode_{int(ep):06d}"


def prediction_path(method, dataset, ep):
    return PRED_DIR / method / dataset / (ep_name(ep) + ".json")


def workdir_for(method, dataset, ep):
    return RAW_DIR / method / dataset / ep_name(ep)


def load_episode_set(which):
    files = {"dev": ["episodes_dev.json"], "heldout": ["episodes.json"], "all": ["episodes_dev.json", "episodes.json"]}[which]
    out, seen = [], set()
    for f in files:
        p = BENCH / f
        if not p.exists():
            sys.exit(f"episode set file missing: {p} (run select_episodes.py first)")
        d = json.loads(p.read_text())
        for e in d["episodes"]:
            key = (e["dataset"], int(e["episode_index"]))
            if key not in seen:
                seen.add(key)
                out.append(key)
    return out


def parse_episode_args(items):
    out = []
    for it in items:
        if ":" not in it:
            sys.exit(f"--episodes expects dataset:episode_index, got {it!r}")
        ds, ep = it.rsplit(":", 1)
        out.append((ds, int(ep)))
    return out


# ------------------------------------------------------------------ GPU guard
def _ancestors():
    pids = set()
    pid = os.getpid()
    while pid > 1:
        pids.add(pid)
        try:
            with open(f"/proc/{pid}/status") as f:
                ppid = next((int(l.split()[1]) for l in f if l.startswith("PPid:")), 0)
        except OSError:
            break
        if ppid == pid:
            break
        pid = ppid
    return pids


def other_gpu_processes(pattern=GPU_PATTERN):
    """PIDs matching the pattern that are neither this process nor its ancestors (the launching shell pipeline)."""
    try:
        out = subprocess.run(["pgrep", "-f", pattern], capture_output=True, text=True, check=False).stdout
    except FileNotFoundError:
        return []
    mine = _ancestors()
    return [int(p) for p in out.split() if p.strip().isdigit() and int(p) not in mine]


def describe_pids(pids):
    lines = []
    for p in pids:
        try:
            cmd = Path(f"/proc/{p}/cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace").strip()
        except OSError:
            cmd = "?"
        lines.append(f"  pid {p}: {cmd[:160]}")
    return "\n".join(lines)


# ------------------------------------------------------------------ call counter
class CallCounter:
    """Wraps backend.generate / generate_many; counts invocations and prompts."""

    def __init__(self, backend):
        self.backend = backend
        self.calls = 0
        self.prompts = 0
        self._orig_generate = backend.generate
        backend.generate = self._generate
        self._orig_many = getattr(backend, "generate_many", None)
        if self._orig_many is not None:
            backend.generate_many = self._generate_many

    def reset(self):
        self.calls = 0
        self.prompts = 0

    def _generate(self, system, content, k=5, **kw):
        self.calls += 1
        self.prompts += int(k)
        return self._orig_generate(system, content, k=k, **kw)

    def _generate_many(self, system, contents, *a, **kw):
        self.calls += 1
        try:
            self.prompts += len(contents)
        except TypeError:
            self.prompts += 1
        return self._orig_many(system, contents, *a, **kw)


# ------------------------------------------------------------------ predictions
def null_prediction(n_chunks):
    n = int(n_chunks or 0)
    return {"held_obs": [], "events": [], "held_object": None, "chunk_labels": [None] * n, "chunk_q": [0.0] * n,
            "decisive_chunk": None, "cause": None, "n_chunks": n, "peak_mem_gb": None, "raw_dir": None}


def finalize(pred, method, cfg, dataset, ep, wall_s, counter, workdir):
    out = {"method": method, "method_config": cfg, "dataset": dataset, "episode_index": int(ep)}
    out.update(pred)
    out["wall_s"] = round(float(wall_s), 1)
    out["n_model_calls"] = counter.calls if counter is not None else 0
    out["n_prompts"] = counter.prompts if counter is not None else 0
    out.setdefault("raw_dir", str(workdir))
    for k in PRED_FIELDS:
        out.setdefault(k, None)
    return out


def log_line(method, text):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_DIR / f"bench_{method}.log", "a") as f:
        f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {text}\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--method", required=True, choices=sorted(REGISTRY))
    ap.add_argument("--set", dest="which", choices=["dev", "heldout", "all"], default="dev")
    ap.add_argument("--episodes", nargs="*", default=None, help="explicit dataset:episode_index list (replaces --set)")
    ap.add_argument("--limit", type=int, default=None, help="max episodes to run in this invocation (after skipping done ones)")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--model", default=None, help="override the model id in the method CONFIG")
    ap.add_argument("--dry-run", action="store_true", help="print the plan; load neither datasets nor the model")
    args = ap.parse_args(argv)

    method = load_method(args.method)
    cfg = dict(method.CONFIG)
    if args.model:
        cfg["model"] = args.model
    model_id = cfg.get("model") or "Qwen/Qwen3-VL-8B-Instruct"

    episodes = parse_episode_args(args.episodes) if args.episodes else load_episode_set(args.which)
    todo = [(ds, ep) for ds, ep in episodes if args.overwrite or not prediction_path(args.method, ds, ep).exists()]
    n_skip = len(episodes) - len(todo)
    if args.limit is not None:
        todo = todo[: args.limit]
    print(f"method={args.method} set={'explicit' if args.episodes else args.which} episodes={len(episodes)} "
          f"skip_existing={n_skip} todo={len(todo)} model={model_id} dry_run={args.dry_run}", flush=True)
    if args.dry_run:
        for ds, ep in todo:
            print(f"  {ds}:{ep} -> {prediction_path(args.method, ds, ep)}")
        print(f"config={json.dumps(cfg, sort_keys=True)}")
        return
    if not todo:
        print("nothing to do")
        return

    others = other_gpu_processes()
    if others:
        sys.exit(f"refusing to start: another GPU annotator process is running\n{describe_pids(others)}")

    from backend_qwen import QwenBackend

    t_load = time.time()
    backend = QwenBackend(model_id)
    counter = CallCounter(backend)
    print(f"loaded {model_id} in {time.time() - t_load:.0f}s", flush=True)
    log_line(args.method, f"START set={args.which} todo={len(todo)} model={model_id} config={json.dumps(cfg, sort_keys=True)}")

    datasets = {}
    stats = {"ok": 0, "error": 0}
    for ds_name, ep_idx in todo:
        t0 = time.time()
        counter.reset()
        workdir = workdir_for(args.method, ds_name, ep_idx)
        workdir.mkdir(parents=True, exist_ok=True)
        ep = None
        try:
            if ds_name not in datasets:
                datasets[ds_name] = open_dataset(ds_name)
            ep = Episode(datasets[ds_name], ds_name, ep_idx)
            pred = method.run(ep, backend, workdir, cfg)
            pred = finalize(pred, args.method, cfg, ds_name, ep_idx, time.time() - t0, counter, workdir)
            stats["ok"] += 1
        except Exception as e:  # noqa: BLE001 - one bad episode must not stop the run
            tb = traceback.format_exc()
            print(tb, file=sys.stderr, flush=True)
            pred = null_prediction(ep.n_chunks if ep is not None else 0)
            pred["error"] = f"{type(e).__name__}: {e}"
            pred["traceback"] = tb
            pred = finalize(pred, args.method, cfg, ds_name, ep_idx, time.time() - t0, counter, workdir)
            stats["error"] += 1
            if "CUDA" in type(e).__name__ or "OutOfMemory" in type(e).__name__:
                try:
                    import torch

                    torch.cuda.empty_cache()
                except Exception:  # noqa: BLE001
                    pass
        dump_json(pred, prediction_path(args.method, ds_name, ep_idx))
        labels = pred.get("chunk_labels") or []
        n_abstain = sum(1 for l in labels if l is None)
        line = (f"{ds_name} ep{ep_idx:04d} n_chunks={len(labels)} abstain={n_abstain} decisive={pred.get('decisive_chunk')} "
                f"cause={pred.get('cause')} held={pred.get('held_object')} events={len(pred.get('events') or [])} "
                f"held_obs={len(pred.get('held_obs') or [])} calls={pred['n_model_calls']} prompts={pred.get('n_prompts')} "
                f"mem={pred.get('peak_mem_gb')}GB wall={pred['wall_s']}s"
                + (f" ERROR={pred['error']}" if pred.get("error") else "")
                + (" (cache)" if pred.get("reused_cache") else ""))
        print(line, flush=True)
        log_line(args.method, line)
    log_line(args.method, f"DONE {stats}")
    print(f"done {stats}", flush=True)


if __name__ == "__main__":
    main()
