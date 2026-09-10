"""Read-only audit of the built object corpus and saved RL runs; prints JSON.

Run in the LeRobot environment with the same FTL_PROJ / FTL_RL as training.
Does not train, modify checkpoints, or overwrite historical evaluations.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

import common as C
import labels as L
from agents import AgentConfig, make_agent
from eval_critic import auc, critic_values
from nets import Normalizer
from replay import OfflineData
from segments import SegmentSupervision


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="Optional path for the audit JSON")
    options = parser.parse_args()
    torch.set_num_threads(1)
    data = OfflineData(C.RL / "datasets" / "object_v1", device="cpu")
    ep = data.ep_id.numpy()
    frame = data.frame_index.numpy()
    end = np.r_[ep[1:] != ep[:-1], True]
    checks = {
        "finite_arrays": all(torch.isfinite(getattr(data, k)).all().item()
                             for k in ("obs", "next_obs", "action", "reward", "done")),
        "done_exactly_at_episode_end": bool(np.array_equal(data.done.numpy() > 0, end)),
        "terminal_reward_matches_outcome": bool(np.array_equal(
            data.reward.numpy(), end * data.success.numpy())),
        "next_obs_matches_next_frame": bool(np.array_equal(
            data.next_obs.numpy()[~end], data.obs.numpy()[1:][~end[:-1]])),
        "actions_in_bounds": bool((data.action.abs() <= 1).all()),
        "train_val_episodes_disjoint": not bool(set(ep[data.train_idx]) & set(ep[data.val_idx])),
        "normalisation_excludes_validation": bool(np.allclose(
            data.norm_mean, data.obs[data.train_idx].mean(0).numpy(), atol=1e-5)),
        "frame_indices_contiguous": all(np.array_equal(frame[ep == e], np.arange((ep == e).sum()))
                                        for e in np.unique(ep)),
    }
    sl = L.load("object_v1", "oracle_labels_r6_object.parquet")
    events = {"per_frame_event_columns": bool(sl.has_event_frames)}
    if sl.has_event_frames:
        er = SegmentSupervision._event_reward(sl)
        succ_frame = data.success.numpy() > 0
        events.update({
            "grasp_chunks": int((np.r_[True, (sl.chunk[1:] != sl.chunk[:-1]) | (frame[1:] == 0)]
                                 & (sl.event == L.EVENT_IDX["grasp"])).sum()),
            "target_grasp_events": int(((sl.event_at == L.EVENT_IDX["grasp"]) & sl.event_target).sum()),
            "grasps_rewarded": int((er > 0).sum()),
            "release_penalties_total": int((er == -0.5).sum()),
            "release_penalties_on_success_frames": int(((er == -0.5) & succ_frame).sum()),
            "drop_penalties": int((er == -1).sum()),
        })
    # Shaping must telescope to zero on every episode: sum_t gamma^t (gamma Phi_{t+1} - Phi_t) = 0.
    gamma = 0.995
    horizon = SegmentSupervision._horizon(data, ep)
    phi, phi_next = SegmentSupervision._potential(sl, frame, end, horizon)
    shaped = gamma * phi_next - phi
    returns = np.array([np.sum(gamma ** frame[ep == e] * shaped[ep == e]) for e in np.unique(ep)])
    events.update({
        "nonzero_initial_potential_episodes": int((phi[frame == 0] != 0).sum()),
        "max_abs_shaped_episode_return": float(np.abs(returns).max()),
    })
    runs = {}
    states = {}
    for directory in sorted((C.RL / "runs").iterdir()):
        if not (directory / "final.pt").exists():
            continue
        sd = torch.load(directory / "final.pt", map_location="cpu", weights_only=False)
        args = sd["args"]
        log_path = directory / "train_log.csv"
        log = pd.read_csv(log_path)
        row = {"seed": args["seed"], "eval_seed": args["eval_seed"],
               "completed_steps": int(log.iloc[-1]["step"]), "configured_steps": args["steps"]}
        ev_path = directory / "eval_final.json"
        if ev_path.exists():
            ev = json.loads(ev_path.read_text())
            row["successes"] = sum(r["n_success"] for r in ev.values())
            row["episodes"] = sum(r["n_episodes"] for r in ev.values())
            row["rates_consistent"] = all(abs(r["success_rate"] - r["n_success"] / r["n_episodes"]) < 1e-12
                                          for r in ev.values())
            row["episode_records_retained"] = all("episodes" in r for r in ev.values())
        if sd["algo"] == "iql":
            states[directory.name] = sd["state"]
        if directory.name in ("iql_terminal", "iql_sign", "iql_events", "iql_decisive"):
            cfg = AgentConfig(**sd["agent_config"])
            agent = make_agent("iql", cfg, Normalizer(sd["obs_mean"], sd["obs_std"]), "cpu")
            agent.load_state_dict(sd["state"])
            v, adv = critic_values(agent, data, data.val_idx)
            take = data.val_idx.numpy()
            ve, vs = ep[take], data.success.numpy()[take] > 0
            starts = np.r_[True, ve[1:] != ve[:-1]]
            sup = sl.sign[take] != 0
            agree = (adv > 0) == (sl.sign[take] > 0)
            row.update(outcome_auc=auc(v[starts], vs[starts]),
                       v_gap=float(v[vs].mean() - v[~vs].mean()),
                       adv_sign_agree=float(agree[sup].mean()),
                       adv_sign_agree_positive=float(agree[sup & (sl.sign[take] > 0)].mean()),
                       adv_sign_agree_negative=float(agree[sup & (sl.sign[take] < 0)].mean()),
                       constant_negative_sign_accuracy=float((sl.sign[take][sup] < 0).mean()),
                       constant_positive_sign_accuracy=float((sl.sign[take][sup] > 0).mean()))
            # Independent O(n^2) pairwise AUC, half credit for ties: the reference the rank-based
            # `auc` in eval_critic.py has to match, tie handling included.
            positive, negative = v[starts][vs[starts]], v[starts][~vs[starts]]
            row["outcome_auc_pairwise"] = float((
                (positive[:, None] > negative).astype(float)
                + 0.5 * (positive[:, None] == negative)).mean())
            margins = []
            for e in np.unique(ve):
                m = (ve == e) & ~vs & (sl.decisive[take] >= 0)
                inside = m & (sl.chunk[take] == sl.decisive[take])
                outside = m & ~inside
                if inside.any() and outside.any():
                    margins.append(float(adv[outside].mean() - adv[inside].mean()))
            row["paired_episode_decisive_margin"] = float(np.mean(margins))
        runs[directory.name] = row
    equality = {}
    for name, state in states.items():
        if not (name.startswith("iql_mask") or name == "iql_awr"):
            continue
        base = "iql_terminal" + name.removeprefix("iql_mask") if name.startswith("iql_mask") else "iql_terminal"
        equality[name] = all(torch.equal(value, states[base][module][key])
                             for module in ("q", "v") for key, value in state[module].items())
    report = {"dataset": {"frames": data.n, "episodes": len(data.episodes),
                           "successes": int(data.episodes.success.sum()), "checks": checks},
              "events_and_potential": events, "auc_all_tied": auc(np.ones(4), np.array([True, False, True, False])),
              "actor_only_critics_bit_identical": equality, "runs": runs}
    encoded = json.dumps(report, indent=2)
    print(encoded)
    if options.out:
        options.out.parent.mkdir(parents=True, exist_ok=True)
        options.out.write_text(encoded + "\n")
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
