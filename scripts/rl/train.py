"""Train an offline learner on the recorded corpus and evaluate it closed-loop in LIBERO.

Stage 4 baselines (`docs/proposal_overview.md` section 14) with a strictly episode-level reward:

  --algo bc   --data success            success-only behaviour cloning
  --algo bc   --data all                behaviour cloning on everything
  --algo bc   --data all --bc-weight outcome    outcome-weighted behaviour cloning
  --algo iql  --data all                IQL with the sparse terminal success reward

Nothing in this file reads a segment label. `--segments <mode>` (see `segments.py`) adds the ordinal
advantage supervision on top of the same critic once the baseline is trusted.

  train.py --algo iql --tag iql_base --steps 200000 --eval-every 50000
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.setdefault("PYOPENGL_PLATFORM", "egl")

import numpy as np  # noqa: E402
import torch  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
from agents import AgentConfig, make_agent  # noqa: E402
from nets import Normalizer  # noqa: E402
from replay import OfflineData  # noqa: E402


def build_argparser():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dataset", default="object_v1", help="tag under $FTL_RL/datasets")
    ap.add_argument("--tag", required=True, help="run name under $FTL_RL/runs")
    ap.add_argument("--algo", default="iql", choices=["bc", "iql"])
    ap.add_argument("--data", default="all", choices=["all", "success", "failure"],
                    help="which episodes the actor trains on (the critic always sees everything)")
    ap.add_argument("--steps", type=int, default=200_000)
    ap.add_argument("--batch-size", type=int, default=1024)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--val-frac", type=float, default=0.05)
    ap.add_argument("--device", default="cuda")
    # agent
    ap.add_argument("--hidden", type=int, default=256)
    ap.add_argument("--n-layers", type=int, default=3)
    ap.add_argument("--actor-dist", default="gauss", choices=["gauss", "deterministic"])
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--gamma", type=float, default=0.995)
    ap.add_argument("--expectile", type=float, default=0.7)
    ap.add_argument("--beta", type=float, default=3.0)
    ap.add_argument("--adv-clip", type=float, default=100.0)
    ap.add_argument("--no-adv-normalize", action="store_true",
                    help="use the raw advantage in exp(beta*A) instead of standardising it")
    ap.add_argument("--grad-clip", type=float, default=1.0)
    ap.add_argument("--bc-weight", default="none", choices=["none", "outcome"])
    ap.add_argument("--bc-failure-weight", type=float, default=0.1)
    # segments (phase 2; inert unless a mode is given)
    ap.add_argument("--segments", default=None, help="segment-supervision mode, see segments.py --help-modes")
    ap.add_argument("--labels", default="oracle_labels.parquet", help="label parquet under $FTL_PROJ/bench")
    ap.add_argument("--seg-lambda", type=float, default=0.1,
                    help="weight of L_ann against the TD losses; needs a sweep, see docs/rl_results.md")
    ap.add_argument("--seg-lambda0", type=float, default=1.0, help="weight of the neutral term")
    ap.add_argument("--seg-margin", type=float, default=0.05)
    ap.add_argument("--seg-tau", type=float, default=0.25, help="smoothness of the sign hinge")
    ap.add_argument("--seg-kappa", type=float, default=3.0, help="t* decay in chunks; 0 disables rho_t")
    ap.add_argument("--seg-use-q", action="store_true", help="weight by the oracle ambiguity q_t")
    ap.add_argument("--seg-reward-scale", type=float, default=0.05, help="pm1: size of the dense +-1 reward")
    ap.add_argument("--seg-shaping-scale", type=float, default=1.0, help="potential: scale of Phi")
    ap.add_argument("--seg-event-scale", type=float, default=0.2, help="events: scale of the event rewards")
    ap.add_argument("--seg-decisive-penalty", type=float, default=-1.0, help="decisive: reward at t*")
    ap.add_argument("--seg-drop-post-decisive", action="store_true",
                    help="decisive: also stop sampling frames after t*")
    ap.add_argument("--seg-expectile-hi", type=float, default=0.9, help="expectile: on progress/recovery")
    ap.add_argument("--seg-expectile-lo", type=float, default=0.3, help="expectile: on failure/aftermath")
    ap.add_argument("--seg-mask-aftermath", type=float, default=0.0)
    ap.add_argument("--seg-mask-failure", type=float, default=0.1)
    ap.add_argument("--seg-mask-neutral", type=float, default=0.5)
    ap.add_argument("--seg-drop-aftermath", action="store_true",
                    help="mask: remove aftermath frames from sampling entirely")
    ap.add_argument("--seg-awr-penalty", type=float, default=2.0, help="awr: exp(-p*w) on failure frames")
    ap.add_argument("--seg-awr-boost", type=float, default=1.0, help="awr: 1+b*w on productive frames")
    # logging / eval
    ap.add_argument("--log-every", type=int, default=2000)
    ap.add_argument("--eval-every", type=int, default=0, help="0 = only at the end")
    ap.add_argument("--eval-family", default="full_shift8", choices=sorted(C.INIT_PROTOCOL))
    ap.add_argument("--eval-tasks", type=int, nargs="*", default=[0, 3, 8])
    ap.add_argument("--eval-episodes", type=int, default=5, help="per task, during training")
    ap.add_argument("--final-eval-families", nargs="*", default=["full_shift4", "full_shift8", "full_shift12"])
    ap.add_argument("--final-eval-tasks", type=int, nargs="*", default=list(range(10)))
    ap.add_argument("--final-eval-episodes", type=int, default=10)
    ap.add_argument("--eval-seed", type=int, default=90000,
                    help="seeds the shifted-init draw only; the base LIBERO layout comes from "
                         "--eval-init-state-offset, which the seed does not touch")
    ap.add_argument("--eval-init-state-offset", type=int, default=0,
                    help="first stored LIBERO initial state to evaluate from; 30 and up are base "
                         "layouts the recorded corpus never used (it took ids 0..29 per task)")
    ap.add_argument("--render-size", type=int, default=128)
    ap.add_argument("--eval-workers", type=int, default=10,
                    help="parallel LIBERO processes; the simulator is CPU-bound and the actor is tiny")
    ap.add_argument("--no-final-eval", action="store_true")
    return ap


class CsvLogger:
    def __init__(self, path: Path):
        self.path = path
        self.fh = open(path, "w", newline="")
        self.writer = None

    def log(self, row: dict):
        if self.writer is None:
            self.writer = csv.DictWriter(self.fh, fieldnames=list(row))
            self.writer.writeheader()
        self.writer.writerow({k: row.get(k) for k in self.writer.fieldnames})
        self.fh.flush()

    def close(self):
        self.fh.close()


def save_checkpoint(agent, args, path: Path, cfg=None, data=None) -> None:
    """Everything `eval_env.load_agent` needs to rebuild the policy in a fresh process.

    The normalisation stored is always the agent's own, never the corpus statistics from meta.json:
    those two are no longer the same array (the agent is whitened on the training split only), and
    writing the corpus one here would silently re-introduce held-out observations at evaluation time.
    """
    torch.save({
        "algo": args.algo, "agent_config": asdict(cfg or agent.cfg), "state": agent.state_dict(),
        "obs_mean": agent.norm.mean.cpu().numpy().tolist(),
        "obs_std": agent.norm.std.cpu().numpy().tolist(),
        "obs_norm_fit": "train_split",
        "spec_version": data.meta["spec_version"] if data is not None else "obs_v1",
        # Which observation the actor expects, so eval_env rebuilds the same one. A v2 checkpoint is
        # useless without knowing which frozen encoder produced its features.
        "obs_spec": data.meta.get("obs_spec", "v1") if data is not None else getattr(args, "obs_spec", "v1"),
        "encoder": data.meta.get("encoder") if data is not None else getattr(args, "encoder", None),
        "args": vars(args),
    }, path)


def actor_indices(data: OfflineData, which: str) -> torch.Tensor:
    if which == "all":
        return data.train_idx
    want = 1.0 if which == "success" else 0.0
    return data.subset(data.success == want)


def main():
    args = build_argparser().parse_args()
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    device = torch.device(args.device if torch.cuda.is_available() or args.device == "cpu" else "cpu")

    data = OfflineData(C.RL / "datasets" / args.dataset, device=device, val_frac=args.val_frac, seed=args.seed)
    # Carried onto every checkpoint this run writes, including the temporary one the parallel evaluator
    # rebuilds the policy from, so evaluation never guesses which observation the actor was trained on.
    args.obs_spec = data.meta.get("obs_spec", "v1")
    args.encoder = data.meta.get("encoder")
    print(f"data: {data.summary()}  (obs spec {args.obs_spec}"
          + (f", encoder {args.encoder}" if args.encoder else "") + ")")

    cfg = AgentConfig(
        obs_dim=data.obs_dim, act_dim=data.act_dim, hidden=args.hidden, n_layers=args.n_layers,
        actor_dist=args.actor_dist, lr=args.lr, lr_actor=args.lr, gamma=args.gamma,
        expectile=args.expectile, beta=args.beta, adv_clip=args.adv_clip, n_steps=args.steps,
        grad_clip=args.grad_clip,
        adv_normalize=not args.no_adv_normalize,
        bc_weight_mode=args.bc_weight, bc_failure_weight=args.bc_failure_weight,
    )
    hooks = None
    if args.segments:
        from segments import make_hooks  # lazily imported: only the segment experiments need labels
        hooks = make_hooks(args, data, device)
        cfg.extras["segments"] = args.segments
        print(f"segments: {hooks.describe()}")

    norm = Normalizer(data.norm_mean, data.norm_std)  # fit on the training episodes only, see replay.py
    agent = make_agent(args.algo, cfg, norm, device, hooks)
    print(f"agent: {args.algo} ({args.data} data) — {agent.parameters_summary()}")

    run_dir = C.RL / "runs" / args.tag
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "config.json").write_text(json.dumps({"args": vars(args), "agent": asdict(cfg)}, indent=1,
                                                    default=str))
    logger = CsvLogger(run_dir / "train_log.csv")

    gen = torch.Generator(device=device).manual_seed(args.seed)
    train_idx = actor_indices(data, args.data)
    if hooks is not None:
        keep = torch.as_tensor(hooks.sample_mask(), dtype=torch.bool, device=device)
        n_before = len(train_idx)
        train_idx = train_idx[keep[train_idx]]
        if len(train_idx) != n_before:
            print(f"segments dropped {n_before - len(train_idx)} of {n_before} frames from sampling")
    if args.algo == "iql" and args.data != "all":
        print(f"note: --data {args.data} restricts BOTH critic and actor for iql "
              f"({len(train_idx)} of {len(data.train_idx)} frames)")
    print(f"training on {len(train_idx)} frames for {args.steps} steps")
    stream = data.batches(train_idx, args.batch_size, gen)
    val_stream = data.batches(data.val_idx, 4096, torch.Generator(device=device).manual_seed(1234))

    t0 = time.time()
    acc: dict[str, float] = {}
    n_acc = 0
    for step in range(1, args.steps + 1):
        m = agent.update(next(stream))
        for k, v in m.items():
            acc[k] = acc.get(k, 0.0) + v
        n_acc += 1
        if step % args.log_every == 0 or step == args.steps:
            row = {"step": step, "seconds": round(time.time() - t0, 1)}
            row.update({k: round(v / n_acc, 5) for k, v in acc.items()})
            row.update({k: round(v, 5) for k, v in agent.eval_metrics(next(val_stream)).items()})
            acc, n_acc = {}, 0
            logger.log(row)
            print("  " + "  ".join(f"{k}={v}" for k, v in row.items()), flush=True)
        if args.eval_every and step % args.eval_every == 0 and step < args.steps:
            res = run_eval(agent, args, device, [args.eval_family], args.eval_tasks, args.eval_episodes)
            print(f"  [closed-loop @ {step}] " + "  ".join(
                f"{k}={v['success_rate']:.1%}" for k, v in res.items()), flush=True)
            (run_dir / f"eval_step{step}.json").write_text(json.dumps(res, indent=1))
    logger.close()

    final = run_dir / "final.pt"
    save_checkpoint(agent, args, final, cfg, data)
    print(f"saved {final}  ({time.time() - t0:.0f}s training)")

    if not args.no_final_eval:
        res = run_eval(agent, args, device, args.final_eval_families, args.final_eval_tasks,
                       args.final_eval_episodes, ckpt_path=final)
        (run_dir / "eval_final.json").write_text(json.dumps(res, indent=1))
        print("\n== closed-loop success ==")
        for fam, r in res.items():
            print(f"  {fam:14s} {r['n_success']:3d}/{r['n_episodes']:3d} = {r['success_rate']:.1%}   "
                  + ", ".join(f"t{k}={v:.0%}" for k, v in r["per_task"].items()))


def run_eval(agent, args, device, families, task_ids, n_episodes, ckpt_path=None) -> dict:
    """Closed-loop success per family. Parallel evaluation spawns processes that rebuild the policy from
    a checkpoint, so one is written first when the caller did not supply a path.

    The per-episode rows are kept. They are the only record of which initial state each episode ran
    from (seed, `init_state_id`, the shift draw and whether it fell back, the settled-state hash), and
    without them a saved evaluation cannot be reproduced episode by episode or compared across runs.
    """
    from eval_env import ActorPolicy, evaluate

    was_training = agent.actor.training
    agent.actor.eval()
    if args.eval_workers > 1 and ckpt_path is None:
        ckpt_path = C.RL / "runs" / args.tag / "eval_tmp.pt"
        save_checkpoint(agent, args, ckpt_path)
    policy = ActorPolicy(agent, device)
    out = {}
    for fam in families:
        out[fam] = evaluate(policy, fam, task_ids, n_episodes, args.eval_seed,
                            args.render_size, args.render_size, verbose=False,
                            workers=args.eval_workers, ckpt=str(ckpt_path) if ckpt_path else None,
                            init_state_offset=args.eval_init_state_offset,
                            obs_spec=getattr(args, "obs_spec", "v1"),
                            encoder=getattr(args, "encoder", "") or "")
    if was_training:
        agent.actor.train()
    return out


if __name__ == "__main__":
    main()
