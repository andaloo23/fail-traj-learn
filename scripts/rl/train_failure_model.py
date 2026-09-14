"""Train the retrospective failure-understanding model, not an RL cost/scorer."""
from __future__ import annotations
import argparse
import hashlib
import json
import random
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import DataLoader
from failure_data import FailureCorpus, FailureWindows, ROLES
from failure_nets import FailureConfig, FailureModel, failure_loss, model_inputs


def binary_metrics(logits, targets, weights):
    result = []
    for c in range(logits.shape[-1]):
        known = (targets[:, c] >= 0) & (weights[:, c] > 0)
        y = targets[known, c].astype(bool)
        p = 1 / (1 + np.exp(-np.clip(logits[known, c], -80, 80)))
        if not len(y):
            result.append(dict(known=0, positives=0, average_precision=None, brier=None))
            continue
        # Threshold groups give tied scores identical treatment.
        order = np.argsort(-p, kind="stable")
        s, z = p[order], y[order]
        ends = np.r_[np.flatnonzero(np.diff(s)), len(s)-1]
        tp = np.cumsum(z)[ends]
        ap = float(np.sum(np.diff(np.r_[0, tp]) * tp / (ends+1)) / y.sum()) if y.any() else None
        predicted = p >= .5
        hit = int((predicted & y).sum())
        result.append(dict(known=len(y), positives=int(y.sum()), average_precision=ap,
            brier=float(np.mean((p-y)**2)), precision=hit/max(int(predicted.sum()), 1),
            recall=hit/max(int(y.sum()), 1)))
    return result


@torch.no_grad()
def evaluate(model, loader, device, scales):
    model.eval()
    sums = {n: 0. for n in ("role", "event", "category")}
    denominators = sums.copy()
    saved = {n: [[], [], []] for n in ("event", "category")}
    confusion = np.zeros((5, 5), np.int64)
    for batch in loader:
        batch = {k: v.to(device) for k, v in batch.items()}
        pred = model(**model_inputs(batch))
        _, parts = failure_loss(pred, batch, *scales)
        for name in sums:
            valid = batch["valid"] if name == "role" else batch["valid"][..., None]
            w = batch[name + "_weight"] * (batch[name] >= 0) * valid
            denom = float(w.sum())
            sums[name] += float(parts[name]) * max(denom, 1)
            denominators[name] += denom
        known = batch["valid"] & (batch["role"] >= 0) & (batch["role_weight"] > 0)
        y = batch["role"][known].cpu().numpy()
        p = pred["role"].argmax(-1)[known].cpu().numpy()
        np.add.at(confusion, (y, p), 1)
        for name in saved:
            for dest, value in zip(saved[name], (pred[name], batch[name], batch[name+"_weight"])):
                dest.append(value[batch["valid"]].cpu().numpy())
    losses = {k: sums[k]/max(denominators[k], 1) for k in sums}
    return dict(loss=sum(losses[n]*s for n, s in zip(("role", "event", "category"), scales)),
                losses=losses, supervision_weight=denominators, role_confusion=confusion.tolist(),
                **{n: binary_metrics(*(np.concatenate(x) for x in values)) for n, values in saved.items()})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset", required=True, type=Path)
    p.add_argument("--manifest", required=True, type=Path)
    p.add_argument("--out", type=Path)
    p.add_argument("--audit-only", action="store_true")
    p.add_argument("--allow-privileged", action="store_true")
    p.add_argument("--epochs", type=int, default=20)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--max-chunks", type=int, default=64)
    p.add_argument("--width", type=int, default=256)
    p.add_argument("--layers", type=int, default=2)
    p.add_argument("--heads", type=int, default=4)
    p.add_argument("--pooling", choices=("query", "last"), default="query")
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument("--role-scale", type=float, default=1.)
    p.add_argument("--event-scale", type=float, default=1.)
    p.add_argument("--category-scale", type=float, default=1.)
    args = p.parse_args()
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    corpus = FailureCorpus(args.dataset, args.manifest, args.allow_privileged)
    print(json.dumps(corpus.report(), indent=2))
    if args.audit_only:
        return
    scales = (args.role_scale, args.event_scale, args.category_scale)
    if args.out is None or args.epochs <= 0 or args.batch_size <= 0 or args.lr <= 0:
        p.error("training needs --out and positive epochs, batch size, lr")
    if min(scales) < 0 or sum(scales) <= 0:
        p.error("loss scales must be nonnegative with at least one active")
    sets = {s: FailureWindows(corpus, s, args.max_chunks) for s in ("train", "val")}
    if not all(len(d) for d in sets.values()):
        p.error("nonempty train and val partitions required")
    for split in sets:
        for name, scale in zip(("role", "event", "category"), scales):
            if scale and not any(e[name+"_weight"].sum() > 0 for e in corpus.episodes if e["split"] == split):
                p.error(f"{split} has no {name} supervision; annotate it or disable that loss")
    args.out.mkdir(parents=True, exist_ok=False)
    cfg = FailureConfig(corpus.obs.shape[1], corpus.actions.shape[1], corpus.chunk_size,
        len(corpus.categories), len(corpus.events), width=args.width, layers=args.layers,
        heads=args.heads, max_chunks=args.max_chunks, pooling=args.pooling)
    model = FailureModel(cfg).to(args.device)
    optim = torch.optim.AdamW(model.parameters(), lr=args.lr)
    loaders = {s: DataLoader(d, batch_size=args.batch_size, shuffle=s == "train") for s, d in sets.items()}
    provenance = dict(manifest=corpus.manifest, dataset=str(args.dataset.resolve()),
        dataset_meta=corpus.meta, manifest_sha256=hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
        categories=corpus.categories, event_types=corpus.events, roles=ROLES,
        args={k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
        task="retrospective_window_prefix_recognition", coverage=corpus.report())
    (args.out / "run.json").write_text(json.dumps(provenance, indent=2))
    best = float("inf")
    print(f"parameters={sum(x.numel() for x in model.parameters()):,}", flush=True)
    for epoch in range(args.epochs):
        model.train()
        train_loss = 0.
        for batch in loaders["train"]:
            batch = {k: v.to(args.device) for k, v in batch.items()}
            optim.zero_grad(set_to_none=True)
            loss, _ = failure_loss(model(**model_inputs(batch)), batch, *scales)
            if not torch.isfinite(loss):
                raise RuntimeError("nonfinite training loss")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.)
            optim.step()
            train_loss += float(loss.detach())
        metrics = evaluate(model, loaders["val"], args.device, scales)
        record = dict(epoch=epoch+1, train_loss=train_loss/len(loaders["train"]), val=metrics)
        print(json.dumps(record), flush=True)
        with (args.out / "metrics.jsonl").open("a") as f:
            f.write(json.dumps(record) + "\n")
        checkpoint = dict(config=model.config_dict(), model=model.state_dict(), epoch=epoch+1,
            optimizer=optim.state_dict(), normalization={"mean": corpus.mean.tolist(), "std": corpus.std.tolist()},
            provenance=provenance, validation=metrics)
        torch.save(checkpoint, args.out / "last.pt")
        if metrics["loss"] < best:
            best = metrics["loss"]
            torch.save(checkpoint, args.out / "best.pt")


if __name__ == "__main__":
    main()
