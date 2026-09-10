"""Offline learners: behaviour cloning baselines and IQL with a sparse terminal reward.

Stage 4 of the proposal (`docs/proposal_overview.md`, section 14): the data-use and offline-RL baselines
that the segment-aware method has to beat. Nothing here reads a segment label; the only reward is
1.0 on a successful terminal transition. `segments.py` plugs the annotation losses into `IQL` through
`seg_loss`, so the baseline and the method share one critic implementation.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field

import torch
import torch.nn.functional as F

from nets import ACTORS, Normalizer, TwinQ, ValueNet, count_params


@dataclass
class AgentConfig:
    obs_dim: int = 90
    act_dim: int = 7
    hidden: int = 256
    n_layers: int = 3
    actor_dist: str = "gauss"          # gauss | deterministic
    lr: float = 3e-4
    lr_actor: float = 3e-4
    # IQL
    gamma: float = 0.995               # episodes run ~250 steps; 0.99 discounts the terminal reward away
    expectile: float = 0.7             # tau in L_V; 0.5 = mean, ->1 = optimistic
    beta: float = 3.0                  # AWR temperature
    adv_clip: float = 100.0            # omega_max
    adv_normalize: bool = True         # divide the advantage by its batch std before exp(beta * A)
    tau_target: float = 0.005          # target-Q EMA rate
    actor_lr_schedule: bool = True     # cosine decay, as in the IQL paper
    n_steps: int = 200_000
    grad_clip: float = 1.0
    # BC
    bc_weight_mode: str = "none"       # none | outcome
    bc_failure_weight: float = 0.1     # weight of failed-episode frames when bc_weight_mode=outcome
    extras: dict = field(default_factory=dict)


def expectile_loss(diff: torch.Tensor, expectile) -> torch.Tensor:
    """`expectile` may be a scalar or a per-sample tensor (segment-conditional expectile)."""
    w = torch.where(diff < 0, 1.0 - expectile, expectile)
    return w * diff.pow(2)


class SegmentHooks:
    """The five places segment supervision can enter the learner. `segments.py` subclasses this.

    Every hook is a no-op here, so `IQL(hooks=SegmentHooks())` is exactly the reward-only baseline.
    """

    def reward(self, batch, reward):
        """Modify the per-transition reward entering the TD target."""
        return reward

    def done(self, batch, done):
        """Modify the bootstrap mask (e.g. cut the trajectory at the decisive error)."""
        return done

    def expectile(self, batch, expectile):
        """Per-sample expectile for L_V."""
        return expectile

    def critic_loss(self, batch, adv):
        """Extra term added to L_V, plus metrics. Returns (tensor_or_None, dict)."""
        return None, {}

    def actor_weight(self, batch, w):
        """Modify the advantage-weighted BC weights."""
        return w


class BC:
    """Behaviour cloning. `data_filter` (all | success) is applied by the trainer when it picks indices;
    this class only decides how each sampled frame is weighted."""

    def __init__(self, cfg: AgentConfig, normalizer: Normalizer, device, hooks: SegmentHooks | None = None):
        self.cfg, self.device = cfg, device
        self.hooks = hooks or SegmentHooks()
        self.norm = normalizer.to(device)
        self.actor = ACTORS[cfg.actor_dist](cfg.obs_dim, cfg.act_dim, cfg.hidden, cfg.n_layers).to(device)
        self.opt = torch.optim.AdamW(self.actor.parameters(), lr=cfg.lr_actor)
        self.sched = (torch.optim.lr_scheduler.CosineAnnealingLR(self.opt, cfg.n_steps)
                      if cfg.actor_lr_schedule else None)

    def parameters_summary(self) -> str:
        return f"actor {count_params(self.actor) / 1e6:.2f}M params"

    def weights(self, batch) -> torch.Tensor:
        if self.cfg.bc_weight_mode == "outcome":
            w = torch.where(batch["success"] > 0.5, 1.0, self.cfg.bc_failure_weight)
        else:
            w = torch.ones_like(batch["reward"])
        return self.hooks.actor_weight(batch, w)

    def update(self, batch) -> dict:
        obs = self.norm(batch["obs"])
        w = self.weights(batch)
        lp = self.actor.log_prob(obs, batch["action"])
        loss = -(w * lp).sum() / w.sum().clamp_min(1e-6)
        self.opt.zero_grad(set_to_none=True)
        loss.backward()
        gn = torch.nn.utils.clip_grad_norm_(self.actor.parameters(), self.cfg.grad_clip)
        self.opt.step()
        if self.sched:
            self.sched.step()
        return {"actor_loss": loss.item(), "logp": lp.mean().item(), "w_mean": w.mean().item(),
                "grad_norm": float(gn)}

    @torch.no_grad()
    def eval_metrics(self, batch) -> dict:
        obs = self.norm(batch["obs"])
        mse = F.mse_loss(self.actor.mean_action(obs), batch["action"]).item()
        return {"val_action_mse": mse, "val_logp": self.actor.log_prob(obs, batch["action"]).mean().item()}

    def state_dict(self) -> dict:
        return {"actor": self.actor.state_dict(), "norm": self.norm.state_dict()}

    def load_state_dict(self, sd: dict) -> None:
        self.actor.load_state_dict(sd["actor"])
        self.norm.load_state_dict(sd["norm"])

    def act(self, obs: torch.Tensor) -> torch.Tensor:
        return self.actor.act(self.norm(obs))


class IQL(BC):
    """Implicit Q-Learning: expectile value regression, TD critic, advantage-weighted actor.

    Segment supervision enters only through `hooks` (a `SegmentHooks`), so the reward-only baseline and
    every segment variant share this one implementation.
    """

    def __init__(self, cfg: AgentConfig, normalizer: Normalizer, device, hooks: SegmentHooks | None = None):
        super().__init__(cfg, normalizer, device, hooks)
        self.q = TwinQ(cfg.obs_dim, cfg.act_dim, cfg.hidden, cfg.n_layers).to(device)
        self.q_target = copy.deepcopy(self.q).requires_grad_(False)
        self.v = ValueNet(cfg.obs_dim, cfg.hidden, cfg.n_layers).to(device)
        self.q_opt = torch.optim.AdamW(self.q.parameters(), lr=cfg.lr)
        self.v_opt = torch.optim.AdamW(self.v.parameters(), lr=cfg.lr)

    def parameters_summary(self) -> str:
        return (f"actor {count_params(self.actor) / 1e6:.2f}M + critic "
                f"{count_params(self.q, self.v) / 1e6:.2f}M params")

    def update(self, batch) -> dict:
        cfg = self.cfg
        obs = self.norm(batch["obs"])
        next_obs = self.norm(batch["next_obs"])
        act = batch["action"]
        rew = self.hooks.reward(batch, batch["reward"])
        done = self.hooks.done(batch, batch["done"])

        # ---- V: expectile regression towards the frozen Q of the dataset action
        with torch.no_grad():
            q_t = self.q_target(obs, act)
            target = rew + cfg.gamma * (1.0 - done) * self.v(next_obs)
        v = self.v(obs)
        adv = q_t - v
        v_loss = expectile_loss(adv, self.hooks.expectile(batch, cfg.expectile)).mean()

        # ---- Q: one-step TD towards r + gamma (1-d) V(s')
        q1, q2 = self.q.both(obs, act)
        q_loss = F.mse_loss(q1, target) + F.mse_loss(q2, target)

        # ---- annotation constraints, on the LIVE advantage so the gradient reaches both Q and V.
        # Using the frozen target Q here would turn "this action was good" into "lower this state's
        # value", which is not the constraint proposal section 5.5 states.
        adv_live = torch.minimum(q1, q2) - v
        extra, seg_metrics = self.hooks.critic_loss(batch, adv_live)
        critic_loss = v_loss + q_loss + (extra if extra is not None else 0.0)

        self.v_opt.zero_grad(set_to_none=True)
        self.q_opt.zero_grad(set_to_none=True)
        critic_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.v.parameters(), cfg.grad_clip)
        torch.nn.utils.clip_grad_norm_(self.q.parameters(), cfg.grad_clip)
        self.v_opt.step()
        self.q_opt.step()
        with torch.no_grad():
            for p, tp in zip(self.q.parameters(), self.q_target.parameters()):
                tp.mul_(1 - cfg.tau_target).add_(cfg.tau_target * p)
            for b, tb in zip(self.q.buffers(), self.q_target.buffers()):
                tb.copy_(b)

        # ---- actor: advantage-weighted behaviour cloning
        with torch.no_grad():
            # A sparse terminal reward discounted over a ~250-step episode leaves |A| ~ 1e-2, so
            # exp(beta * A) is 1 for every transition and the actor silently collapses to plain BC.
            # Standardising A by its batch spread makes beta a real temperature at any value scale.
            a_w = adv.detach()
            if cfg.adv_normalize:
                a_w = a_w / a_w.std().clamp_min(1e-6)
            w = torch.exp(a_w * cfg.beta).clamp(max=cfg.adv_clip)
            w = self.hooks.actor_weight(batch, w)
        lp = self.actor.log_prob(obs, act)
        actor_loss = -(w * lp).mean()
        self.opt.zero_grad(set_to_none=True)
        actor_loss.backward()
        gn = torch.nn.utils.clip_grad_norm_(self.actor.parameters(), cfg.grad_clip)
        self.opt.step()
        if self.sched:
            self.sched.step()

        m = {
            "v_loss": v_loss.item(), "q_loss": q_loss.item(), "actor_loss": actor_loss.item(),
            "adv_live_mean": adv_live.mean().item(),
            "q_mean": q_t.mean().item(), "v_mean": v.mean().item(),
            "adv_mean": adv.mean().item(), "adv_std": adv.std().item(),
            "adv_pos_frac": (adv > 0).float().mean().item(),
            "target_mean": target.mean().item(), "w_mean": w.mean().item(), "w_max": w.max().item(),
            "logp": lp.mean().item(), "grad_norm": float(gn),
        }
        m.update(seg_metrics)
        return m

    @torch.no_grad()
    def eval_metrics(self, batch) -> dict:
        m = super().eval_metrics(batch)
        obs = self.norm(batch["obs"])
        q = self.q(obs, batch["action"])
        v = self.v(obs)
        adv = q - v
        m.update({"val_q": q.mean().item(), "val_v": v.mean().item(), "val_adv": adv.mean().item()})
        # Does the critic rank successful episodes above failed ones at the same point in time?
        s = batch["success"] > 0.5
        if s.any() and (~s).any():
            m["val_v_success"] = v[s].mean().item()
            m["val_v_failure"] = v[~s].mean().item()
            m["val_v_gap"] = m["val_v_success"] - m["val_v_failure"]
        return m

    def state_dict(self) -> dict:
        sd = super().state_dict()
        sd.update({"q": self.q.state_dict(), "v": self.v.state_dict()})
        return sd

    def load_state_dict(self, sd: dict) -> None:
        super().load_state_dict(sd)
        if "q" in sd:
            self.q.load_state_dict(sd["q"])
            self.q_target = copy.deepcopy(self.q).requires_grad_(False)
            self.v.load_state_dict(sd["v"])


def make_agent(algo: str, cfg: AgentConfig, normalizer: Normalizer, device, hooks: SegmentHooks | None = None):
    if algo == "bc":
        return BC(cfg, normalizer, device, hooks)
    if algo == "iql":
        return IQL(cfg, normalizer, device, hooks)
    raise ValueError(f"unknown algo {algo}")
