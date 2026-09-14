"""Causal chunk encoder, category-query pooling, and separately supervised heads."""
from __future__ import annotations
from dataclasses import dataclass, asdict
import torch
from torch import nn
from torch.nn import functional as F


@dataclass
class FailureConfig:
    obs_dim: int
    action_dim: int
    chunk_size: int
    categories: int
    events: int
    width: int = 256
    layers: int = 2
    heads: int = 4
    max_chunks: int = 64
    dropout: float = 0.1
    pooling: str = "query"


class FailureModel(nn.Module):
    def __init__(self, cfg: FailureConfig):
        super().__init__()
        self.cfg = cfg
        if cfg.pooling not in ("query", "last"):
            raise ValueError("pooling must be query or last")
        if min(cfg.obs_dim, cfg.action_dim, cfg.chunk_size, cfg.categories, cfg.events,
               cfg.layers, cfg.width, cfg.heads, cfg.max_chunks) <= 0 or cfg.width % cfg.heads:
            raise ValueError("invalid dimensions or attention head count")
        dim = cfg.obs_dim + cfg.chunk_size * (cfg.action_dim + 1) + 1
        self.chunk_encoder = nn.Sequential(nn.Linear(dim, cfg.width), nn.GELU(),
                                           nn.Linear(cfg.width, cfg.width))
        self.position = nn.Embedding(cfg.max_chunks, cfg.width)
        block = nn.TransformerEncoderLayer(cfg.width, cfg.heads, cfg.width * 4,
            cfg.dropout, activation="gelu", batch_first=True, norm_first=True)
        self.temporal = nn.TransformerEncoder(block, cfg.layers, norm=nn.LayerNorm(cfg.width),
                                               enable_nested_tensor=False)
        self.queries = nn.Parameter(torch.randn(cfg.categories, cfg.width) * 0.02)
        self.key = nn.Linear(cfg.width, cfg.width)
        self.value = nn.Linear(cfg.width, cfg.width)
        self.category_readout = nn.Parameter(torch.randn(cfg.categories, cfg.width) * 0.02)
        self.category_bias = nn.Parameter(torch.zeros(cfg.categories))
        self.role_head = nn.Linear(cfg.width, 5)
        self.event_head = nn.Linear(cfg.width, cfg.events)

    def forward(self, obs, action, action_valid, duration, valid):
        b, t, _ = obs.shape
        if t > self.cfg.max_chunks or not valid[:, 0].all() or (valid[:, 1:] & ~valid[:, :-1]).any():
            raise ValueError("expected nonempty right-padded windows within max_chunks")
        # Mask BEFORE projection so arbitrary padded inputs have no influence.
        obs = obs.masked_fill(~valid[..., None], 0)
        action = action.masked_fill(~(action_valid & valid[..., None])[..., None], 0)
        av = action_valid & valid[..., None]
        duration = duration.masked_fill(~valid[..., None], 0)
        x = torch.cat([obs, action.flatten(2), av.to(obs.dtype), duration], dim=-1)
        z = self.chunk_encoder(x) + self.position(torch.arange(t, device=obs.device))
        future = torch.ones(t, t, dtype=torch.bool, device=obs.device).triu(1)
        h = self.temporal(z, mask=future, src_key_padding_mask=~valid)
        h = h.masked_fill(~valid[..., None], 0)
        if self.cfg.pooling == "query":
            scores = torch.einsum("bjd,fd->bfj", self.key(h), self.queries) / self.cfg.width ** 0.5
            scores = scores[:, None].expand(b, t, self.cfg.categories, t)
            blocked = future[None, :, None, :] | ~valid[:, None, None, :]
            attention = scores.masked_fill(blocked, float("-inf")).softmax(-1)
            pooled = torch.einsum("btfj,bjd->btfd", attention, self.value(h))
        else:
            pooled = h[:, :, None, :].expand(-1, -1, self.cfg.categories, -1)
            attention = None
        category = torch.einsum("btfd,fd->btf", pooled, self.category_readout) + self.category_bias
        return dict(role=self.role_head(h), event=self.event_head(h), category=category,
                    contextual=h, attention=attention)

    def config_dict(self):
        return asdict(self.cfg)


def model_inputs(batch):
    return {k: batch[k] for k in ("obs", "action", "action_valid", "duration", "valid")}


def failure_loss(pred, batch, role_scale=1., event_scale=1., category_scale=1.):
    losses = {}
    for name in ("role", "event", "category"):
        y, w = batch[name], batch[name + "_weight"]
        mask = batch["valid"] if name == "role" else batch["valid"][..., None]
        w = w * ((y >= 0) & mask)
        if name == "role":
            raw = F.cross_entropy(pred[name].transpose(1, 2), y.clamp_min(0), reduction="none")
        else:
            raw = F.binary_cross_entropy_with_logits(pred[name], y.clamp_min(0), reduction="none")
        losses[name] = (raw * w).sum() / w.sum().clamp_min(1)
    total = role_scale * losses["role"] + event_scale * losses["event"] + category_scale * losses["category"]
    return total, losses
