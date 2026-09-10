"""Offline critic quality on held-out episodes (proposal section 16, "critic quality").

Closed-loop success is the headline number but it is noisy at 50-150 episodes and it moves only if the
actor changes. These metrics read the critic directly, on the validation episodes the trainer never
sampled, and will show a segment effect even when the policy has not moved yet:

  outcome_auc        AUC of V(s_0) separating successful from failed episodes. Can the critic tell,
                     from the initial state alone, that this rollout is going to fail? At 0.5 it cannot.
  outcome_auc_mid    the same at the midpoint of the episode, where the failure is usually already set up
  v_gap              mean V on successful frames minus mean V on failed frames
  v_end_above_start  fraction of successful episodes whose V is higher at the last frame than the first
                     (it should be: the discounted terminal reward gets closer). Endpoints only - this
                     is not monotonicity at every step, and was misnamed `v_monotonicity` until
                     2026-09-09.
  adv_sign_agree     fraction of oracle-labelled frames whose advantage sign matches the label
                     (progress/recovery > 0, failure_inducing < 0). The direct read on the ordinal
                     constraint of proposal section 5.5, reported per label so a mode that only learns
                     "everything in a failed episode is bad" is visible. Read it next to
                     `adv_sign_agree_balanced` and the two constant-predictor baselines: the supervised
                     frames are ~94% positive, so the raw number is dominated by the y=+1 class.
  adv_decisive       mean advantage in the decisive chunk vs the rest of the same failed episode. H4:
                     does the critic single out the action that caused the failure? `..._margin` is the
                     within-episode difference averaged over episodes; `..._margin_pooled` is the old
                     across-episode pooling, kept so the historical numbers stay comparable.

  eval_critic.py --ckpt $FTL_RL/runs/iql_sign/final.pt --labels oracle_labels_r6_object.parquet
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
from replay import OfflineData  # noqa: E402


def auc(scores: np.ndarray, positive: np.ndarray) -> float:
    """Rank-based AUC; 0.5 means the score carries no information about the label.

    Ties get the MID-RANK of their group, which is what makes a tied pair count half. Handing tied
    scores consecutive ranks instead resolves every tie in favour of whichever group was concatenated
    first: with the positives first, four identical scores and two positives scored 0.0 rather than 0.5.
    A collapsed critic is the case where this matters most, so it has to be right there.
    """
    pos, neg = scores[positive], scores[~positive]
    if not len(pos) or not len(neg):
        return float("nan")
    both = np.concatenate([pos, neg])
    order = np.argsort(both, kind="stable")
    sorted_scores = both[order]
    ranks = np.empty(len(both), float)
    group_start = np.flatnonzero(np.r_[True, sorted_scores[1:] != sorted_scores[:-1]])
    for a, b in zip(group_start, np.r_[group_start[1:], len(both)]):
        ranks[order[a:b]] = (a + b + 1) / 2.0  # mean of the 1-based ranks a+1 .. b
    return float((ranks[: len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


@torch.no_grad()
def critic_values(agent, data: OfflineData, idx: torch.Tensor, chunk: int = 65536):
    v_parts, a_parts = [], []
    for s in range(0, len(idx), chunk):
        i = idx[s:s + chunk]
        obs = agent.norm(data.obs[i])
        v = agent.v(obs)
        q = agent.q(obs, data.action[i])
        v_parts.append(v.cpu().numpy())
        a_parts.append((q - v).cpu().numpy())
    return np.concatenate(v_parts), np.concatenate(a_parts)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--dataset", default=None, help="defaults to the dataset the run trained on")
    ap.add_argument("--labels", default=None, help="label parquet for the advantage-sign metrics")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    from eval_env import load_agent

    device = torch.device(args.device if torch.cuda.is_available() or args.device == "cpu" else "cpu")
    sd = torch.load(args.ckpt, map_location="cpu", weights_only=False)
    if sd["algo"] != "iql":
        raise SystemExit(f"{args.ckpt} is a {sd['algo']} run; there is no critic to evaluate")
    train_args = sd.get("args", {})
    dataset = args.dataset or train_args.get("dataset", "object_v1")
    agent = load_agent(Path(args.ckpt), device)

    # Same split as training: val_frac and seed come from the run config, so these episodes were held out.
    data = OfflineData(C.RL / "datasets" / dataset, device=device,
                       val_frac=train_args.get("val_frac", 0.05), seed=train_args.get("seed", 0))
    idx = data.val_idx
    v, adv = critic_values(agent, data, idx)
    ep = data.ep_id[idx].cpu().numpy()
    frame = data.frame_index[idx].cpu().numpy()
    succ = data.success[idx].cpu().numpy() > 0.5

    res = {"ckpt": args.ckpt, "dataset": dataset, "n_val_frames": int(len(idx)),
           "n_val_episodes": int(len(np.unique(ep)))}
    res["v_gap"] = float(v[succ].mean() - v[~succ].mean())
    res["v_mean"] = float(v.mean())

    # per-episode: first frame, midpoint, last frame
    eps = np.unique(ep)
    v0, vmid, vend, ep_succ = [], [], [], []
    for e in eps:
        m = ep == e
        order = np.argsort(frame[m])
        vv = v[m][order]
        v0.append(vv[0])
        vmid.append(vv[len(vv) // 2])
        vend.append(vv[-1])
        ep_succ.append(succ[m][0])
    v0, vmid, vend, ep_succ = map(np.asarray, (v0, vmid, vend, ep_succ))
    res["outcome_auc"] = auc(v0, ep_succ)
    res["outcome_auc_mid"] = auc(vmid, ep_succ)
    # Endpoints only: V(last) > V(first). Not monotonicity at every step, which this never measured.
    res["v_end_above_start"] = float((vend[ep_succ] > v0[ep_succ]).mean()) if ep_succ.any() else float("nan")

    if args.labels:
        import labels as L

        sl = L.load(dataset, args.labels)
        take = idx.cpu().numpy()
        lab = sl.seg_label[take]
        sign = sl.sign[take]
        dec = sl.decisive[take]
        chunk = sl.chunk[take]
        sup = (lab >= 0) & (sign != 0)
        agree = (adv > 0) == (sign > 0)
        res["adv_sign_agree"] = float(agree[sup].mean()) if sup.any() else float("nan")
        # The supervised frames are ~94% y=+1, so a constant-positive predictor already scores ~0.94 and
        # a constant-negative one ~0.06. Reporting agreement alone against "chance" is meaningless at
        # that skew; the per-class rates and their unweighted mean are what the ordinal objective moves.
        plus, minus = sup & (sign > 0), sup & (sign < 0)
        res["frac_supervised_positive"] = float(plus.sum() / max(int(sup.sum()), 1))
        res["const_positive_sign_agree"] = res["frac_supervised_positive"]
        res["const_negative_sign_agree"] = 1.0 - res["frac_supervised_positive"]
        if plus.any():
            res["adv_sign_agree_positive"] = float(agree[plus].mean())
        if minus.any():
            res["adv_sign_agree_negative"] = float(agree[minus].mean())
        if plus.any() and minus.any():
            res["adv_sign_agree_balanced"] = 0.5 * (res["adv_sign_agree_positive"]
                                                    + res["adv_sign_agree_negative"])
        for name, k in (("progress", 0), ("failure_inducing", 1), ("recovery", 2),
                        ("neutral", 3), ("aftermath", 4)):
            m = lab == k
            if m.any():
                res[f"adv_{name}"] = float(adv[m].mean())
                res[f"n_{name}"] = int(m.sum())
        # H4: inside a failed episode, is the decisive chunk singled out?
        in_dec = (dec >= 0) & (chunk == dec) & ~succ
        out_dec = (dec >= 0) & (chunk != dec) & ~succ
        if in_dec.any() and out_dec.any():
            res["adv_decisive"] = float(adv[in_dec].mean())
            res["adv_nondecisive"] = float(adv[out_dec].mean())
            res["adv_decisive_margin_pooled"] = res["adv_nondecisive"] - res["adv_decisive"]
            # Pooling frames across episodes lets episodes with more frames, or with a lower overall
            # advantage level, drive the difference. The comparison H4 states is within one episode, so
            # take the difference per episode first and average those.
            per_ep = [float(adv[out_dec & (ep == e)].mean() - adv[in_dec & (ep == e)].mean())
                      for e in np.unique(ep)
                      if (in_dec & (ep == e)).any() and (out_dec & (ep == e)).any()]
            if per_ep:
                res["adv_decisive_margin"] = float(np.mean(per_ep))
                res["adv_decisive_margin_episodes"] = len(per_ep)

    for k, val in res.items():
        print(f"  {k:24s} {val if isinstance(val, str) else round(val, 5)}")
    if args.out:
        Path(args.out).write_text(json.dumps(res, indent=1))
        print(f"-> {args.out}")


if __name__ == "__main__":
    main()
