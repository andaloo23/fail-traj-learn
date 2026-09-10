"""Small networks for the offline learner: twin Q, value, and a tanh-Gaussian actor.

Everything here operates on the low-dimensional observation from `obs.py`, so the whole trainable stack
is a few hundred thousand parameters and a training run fits comfortably on one 3090.
"""
from __future__ import annotations

import math

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

LOG_STD_MIN, LOG_STD_MAX = -5.0, 2.0


def mlp(in_dim: int, hidden: int, out_dim: int, n_layers: int = 3, layernorm: bool = True) -> nn.Sequential:
    layers: list[nn.Module] = []
    d = in_dim
    for _ in range(n_layers):
        layers.append(nn.Linear(d, hidden))
        if layernorm:
            layers.append(nn.LayerNorm(hidden))
        layers.append(nn.GELU())
        d = hidden
    layers.append(nn.Linear(d, out_dim))
    return nn.Sequential(*layers)


class Normalizer(nn.Module):
    """Fixed observation whitening, stored with the checkpoint so eval matches training exactly."""

    def __init__(self, mean: np.ndarray, std: np.ndarray):
        super().__init__()
        self.register_buffer("mean", torch.as_tensor(np.asarray(mean, np.float32)))
        self.register_buffer("std", torch.as_tensor(np.asarray(std, np.float32)))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return (x - self.mean) / self.std


class TwinQ(nn.Module):
    """Two Q heads; the minimum is used for targets and for the advantage."""

    def __init__(self, obs_dim: int, act_dim: int, hidden: int = 256, n_layers: int = 3):
        super().__init__()
        self.q1 = mlp(obs_dim + act_dim, hidden, 1, n_layers)
        self.q2 = mlp(obs_dim + act_dim, hidden, 1, n_layers)

    def both(self, obs: torch.Tensor, act: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        x = torch.cat([obs, act], dim=-1)
        return self.q1(x).squeeze(-1), self.q2(x).squeeze(-1)

    def forward(self, obs: torch.Tensor, act: torch.Tensor) -> torch.Tensor:
        a, b = self.both(obs, act)
        return torch.minimum(a, b)


class ValueNet(nn.Module):
    def __init__(self, obs_dim: int, hidden: int = 256, n_layers: int = 3):
        super().__init__()
        self.v = mlp(obs_dim, hidden, 1, n_layers)

    def forward(self, obs: torch.Tensor) -> torch.Tensor:
        return self.v(obs).squeeze(-1)


class TanhGaussianActor(nn.Module):
    """Squashed Gaussian over the 7-dim action box.

    The gripper dimension of the recorded actions sits exactly at +-1; `ATANH_CLIP` keeps atanh finite
    when scoring those actions.
    """

    ATANH_CLIP = 0.999

    def __init__(self, obs_dim: int, act_dim: int, hidden: int = 256, n_layers: int = 3,
                 state_dependent_std: bool = True):
        super().__init__()
        self.act_dim = act_dim
        self.state_dependent_std = state_dependent_std
        self.net = mlp(obs_dim, hidden, act_dim * (2 if state_dependent_std else 1), n_layers)
        if not state_dependent_std:
            self.log_std = nn.Parameter(torch.zeros(act_dim) - 1.0)

    def _mu_logstd(self, obs: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        out = self.net(obs)
        if self.state_dependent_std:
            mu, log_std = out.chunk(2, dim=-1)
        else:
            mu, log_std = out, self.log_std.expand_as(out)
        return mu, log_std.clamp(LOG_STD_MIN, LOG_STD_MAX)

    def log_prob(self, obs: torch.Tensor, act: torch.Tensor) -> torch.Tensor:
        """log pi(a|s) of a dataset action, with the tanh change-of-variables term."""
        mu, log_std = self._mu_logstd(obs)
        a = act.clamp(-self.ATANH_CLIP, self.ATANH_CLIP)
        pre = torch.atanh(a)
        std = log_std.exp()
        lp = -0.5 * ((pre - mu) / std) ** 2 - log_std - 0.5 * math.log(2 * math.pi)
        lp = lp - torch.log1p(-a.pow(2) + 1e-6)  # tanh jacobian
        return lp.sum(-1)

    @torch.no_grad()
    def act(self, obs: torch.Tensor, deterministic: bool = True) -> torch.Tensor:
        mu, log_std = self._mu_logstd(obs)
        pre = mu if deterministic else mu + log_std.exp() * torch.randn_like(mu)
        return torch.tanh(pre)

    def mean_action(self, obs: torch.Tensor) -> torch.Tensor:
        mu, _ = self._mu_logstd(obs)
        return torch.tanh(mu)


class DeterministicActor(nn.Module):
    """tanh-MLP trained with advantage-weighted MSE; the simple, very stable alternative."""

    def __init__(self, obs_dim: int, act_dim: int, hidden: int = 256, n_layers: int = 3, **_):
        super().__init__()
        self.net = mlp(obs_dim, hidden, act_dim, n_layers)

    def log_prob(self, obs: torch.Tensor, act: torch.Tensor) -> torch.Tensor:
        """Negative squared error, so maximising it is the weighted-regression objective."""
        return -F.mse_loss(torch.tanh(self.net(obs)), act, reduction="none").sum(-1)

    @torch.no_grad()
    def act(self, obs: torch.Tensor, deterministic: bool = True) -> torch.Tensor:
        return torch.tanh(self.net(obs))

    def mean_action(self, obs: torch.Tensor) -> torch.Tensor:
        return torch.tanh(self.net(obs))


ACTORS = {"gauss": TanhGaussianActor, "deterministic": DeterministicActor}


def count_params(*modules: nn.Module) -> int:
    return sum(p.numel() for m in modules for p in m.parameters())
