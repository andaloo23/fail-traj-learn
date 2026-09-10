"""Collect every finished run under $FTL_RL/runs into one comparison table.

Reads `config.json` and `eval_final.json` per run and prints closed-loop success per evaluation family,
plus the last training-log row, so baselines and segment modes can be read side by side.

  collect_results.py                    # markdown table of every run
  collect_results.py --csv results.csv  # also write it
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402


def describe(cfg: dict) -> str:
    a = cfg.get("args", {})
    bits = [a.get("algo", "?")]
    if a.get("data") != "all":
        bits.append(a["data"])
    if a.get("bc_weight") not in (None, "none"):
        bits.append(f"w={a['bc_weight']}")
    if a.get("segments"):
        bits.append(f"seg={a['segments']}")
    return " ".join(bits)


def collect(runs_dir: Path) -> pd.DataFrame:
    rows = []
    for d in sorted(p for p in runs_dir.iterdir() if p.is_dir()):
        cfg_p, ev_p = d / "config.json", d / "eval_final.json"
        if not cfg_p.exists():
            continue
        cfg = json.loads(cfg_p.read_text())
        row = {"run": d.name, "setup": describe(cfg), "steps": cfg.get("args", {}).get("steps")}
        if ev_p.exists():
            ev = json.loads(ev_p.read_text())
            succ = []
            for fam, r in ev.items():
                row[fam] = r["success_rate"]
                succ.append((r["n_success"], r["n_episodes"]))
            row["overall"] = sum(s for s, _ in succ) / max(sum(n for _, n in succ), 1)
            row["n_eval"] = sum(n for _, n in succ)
        log = d / "train_log.csv"
        if log.exists():
            t = pd.read_csv(log)
            if len(t):
                last = t.iloc[-1]
                for k in ("val_action_mse", "val_v_gap", "seg_sign_acc", "adv_std", "q_loss"):
                    if k in t.columns:
                        row[k] = last[k]
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--runs", default=str(C.RL / "runs"))
    ap.add_argument("--csv", default=None)
    ap.add_argument("--sort", default="overall")
    args = ap.parse_args()
    df = collect(Path(args.runs))
    if df.empty:
        raise SystemExit(f"no runs under {args.runs}")
    if args.sort in df.columns:
        df = df.sort_values(args.sort, ascending=False, na_position="last")
    pct = [c for c in df.columns if c.startswith("full_") or c == "overall"]
    show = df.copy()
    for c in show.columns:
        if c in pct:
            show[c] = show[c].map(lambda v: "" if pd.isna(v) else f"{v:.1%}")
        elif show[c].dtype.kind == "f":
            show[c] = show[c].map(lambda v: "" if pd.isna(v) else f"{v:.4g}")
        else:
            show[c] = show[c].astype(str).replace({"nan": "", "None": ""})
    # Plain markdown, so the venv does not need `tabulate` just to print a table.
    w = {c: max(len(c), *(len(v) for v in show[c])) for c in show.columns}
    print("| " + " | ".join(c.ljust(w[c]) for c in show.columns) + " |")
    print("|" + "|".join("-" * (w[c] + 2) for c in show.columns) + "|")
    for _, r in show.iterrows():
        print("| " + " | ".join(str(r[c]).ljust(w[c]) for c in show.columns) + " |")
    if args.csv:
        df.to_csv(args.csv, index=False)
        print(f"\n-> {args.csv}")


if __name__ == "__main__":
    main()
