"""Segment-aware supervision: eight ways to turn oracle segment labels into value or reward.

Each mode is one hypothesis about *where* a temporal failure diagnosis should enter an offline learner.
They are deliberately not variants of one knob: they act at different points of the algorithm, so their
comparison answers a question the proposal actually asks (sections 5, 6, 14, 15).

  mode        acts on          idea
  ---------------------------------------------------------------------------------------------------
  pm1         reward           Fixed segment reward +1 / -1 / 0, added densely to the TD target. The
                               "VLM writes the reward" straw man of proposal 14.4 / 15: it works only
                               if the numeric scale happens to suit the task.
  sign        critic loss      The proposal method (5.5): the label constrains only the SIGN of the
                               advantage. softplus hinge on progress/recovery (A>m) and
                               failure_inducing (A<-m), squared penalty pulling neutral/aftermath to 0,
                               weighted by w = q * rho. Reward stays episode-level.
  expectile   value target     Segment-conditional expectile. IQL asks "how good could this state be?"
                               with a single optimism level; here productive segments are read
                               optimistically (tau_hi) and failure/aftermath segments pessimistically
                               (tau_lo). The label changes what V *means* per state instead of adding a
                               term. Cheapest possible use of the labels.
  decisive    reward + done    Relocate the failure in time. Instead of a zero terminal reward at the
                               timeout, put -1 at the end of the decisive chunk t* and cut bootstrapping
                               there. Tests H4 in the MDP itself rather than in a loss.
  potential   reward           Shaping from segment progress: r + gamma*Phi(s') - Phi(s) with Phi = the
                               share of the episode's step budget already spent on progress/recovery.
                               Return-preserving per episode (see _potential for exactly what that does
                               and does not guarantee), so it is the control for "is any gain just
                               faster credit assignment?".
  events      reward           Sparse rewards at the physical events the oracle localises, each on the
                               event's own frame: + at a target grasp that holds, - at a drop and at a
                               release that left the target away from the goal. An oracle-derived dense
                               progress reward (offline-RL baseline 14.3) with no hand tuning.
  awr         actor weight     Critic untouched; the advantage weight is multiplied by a per-label
                               factor. Isolates "does the actor need the labels, or the critic?".
  mask        actor weight     Data use only: aftermath dropped, failure_inducing downweighted. The
                               segment-resolution version of "successes plus productive prefixes" (14.3)
                               and the cheapest thing that could possibly work.

Modes compose: `--segments sign,mask` applies both. Sanity: `--segments none` is the baseline.

Not implemented here, and deliberately so — the proposal stages them after the core method (section 9):
cause-matched pairwise Q ranking (section 7) needs a state-similarity retrieval index, and the
cause-specific risk heads (section 8) need their own network and a risk-adjusted advantage. Both are
sketched in docs/rl_pipeline.md.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent))
import labels as L  # noqa: E402
from agents import SegmentHooks  # noqa: E402

PROGRESS, FAILURE, RECOVERY, NEUTRAL, AFTERMATH = range(5)
MODES = ("pm1", "sign", "expectile", "decisive", "potential", "events", "awr", "mask")
# oracle_reference.HOLD_MIN_FRAMES: a (merged) hold shorter than this is a slip, not a grasp that holds.
HOLD_MIN_FRAMES = 8


class SegmentSupervision(SegmentHooks):
    """Holds the per-frame label tensors and applies whichever modes were requested."""

    def __init__(self, modes, sl: L.SegmentLabels, data, args, device):
        self.modes = [m for m in modes if m and m != "none"]
        bad = [m for m in self.modes if m not in MODES]
        if bad:
            raise SystemExit(f"unknown segment mode(s) {bad}; choose from {list(MODES)}")
        self.args, self.device = args, device
        self.sl = sl
        t = lambda a, d=torch.float32: torch.as_tensor(np.asarray(a), dtype=d, device=device)  # noqa: E731

        self.label = t(sl.seg_label, torch.long)          # -1 where unlabelled
        self.labelled = t(sl.labelled, torch.bool)
        self.sign = t(sl.sign)
        self.q = t(sl.q)
        self.chunk = t(sl.chunk, torch.long)
        self.decisive = t(sl.decisive, torch.long)
        rho = sl.rho(args.seg_kappa)
        self.w = t((sl.q if args.seg_use_q else np.ones_like(sl.q)) * rho)
        self.event = t(sl.event, torch.long)
        self.held = t(sl.held, torch.bool)

        # Per-frame arrays that need episode structure are precomputed once, in numpy.
        ep_id = data.ep_id.cpu().numpy()
        fidx = data.frame_index.cpu().numpy()
        done = data.done.cpu().numpy() > 0.5
        self.keep_frame = np.ones(len(sl.seg_label), bool)  # frames the trainer may sample
        if "potential" in self.modes:
            phi, phi_next = self._potential(sl, fidx, done, self._horizon(data, ep_id))
            self.phi, self.phi_next = t(phi), t(phi_next)
        if "decisive" in self.modes:
            dec_end, keep = self._decisive_frames(sl, fidx, data)
            self.dec_end = t(dec_end, torch.bool)
            if args.seg_drop_post_decisive:
                self.keep_frame &= keep
        if "events" in self.modes:
            self.event_reward = t(self._event_reward(sl))
        if "mask" in self.modes and args.seg_drop_aftermath:
            self.keep_frame &= sl.seg_label != AFTERMATH

    # ------------------------------------------------------------ precompute
    @staticmethod
    def _horizon(data, ep_id) -> np.ndarray:
        """Per-frame episode budget (max_steps), falling back to the recorded length when it is unset."""
        eps = data.episodes.sort_values("ep_id")
        budget = eps["max_steps"].to_numpy(np.float32)
        budget = np.where(budget > 0, budget, eps["length"].to_numpy(np.float32))
        return np.maximum(budget, 1.0)[ep_id]

    @staticmethod
    def _potential(sl, fidx, done, horizon):
        """Phi_t = (productive frames STRICTLY BEFORE t in the episode) / (the episode step budget).

        Two boundary choices make the shaping sum to exactly zero over every recorded trajectory, which
        is the property this control exists to have:

          * the count is exclusive, so Phi(s_0) = 0 for every episode. An inclusive count made Phi(s_0)
            nonzero on 1287 of 1300 episodes, and sum_t gamma^t (gamma Phi_{t+1} - Phi_t) then telescopes
            to -Phi(s_0), a per-episode constant added to every return rather than nothing;
          * Phi(terminal successor) = 0, because the episode is over.

        The denominator is the fixed step budget, not the realised episode length: length is a property
        of the trajectory the behaviour policy happened to produce, so dividing by it made Phi depend on
        the outcome it is supposed to be neutral about.

        Honest statement of what this buys. Ng, Harada and Russell's policy-invariance theorem needs Phi
        to be a function of the learner's STATE. Phi here is a function of the labelled prefix of the
        trajectory, which the 90-d observation does not contain, so the theorem does not apply and this
        mode is not a proof of invariance. What it does give, and what the test asserts, is exact return
        preservation on the offline data: every episode's discounted shaped return equals its unshaped
        one, so any change in the learner comes from credit assignment inside the episode and not from
        re-ranking episodes against each other.
        """
        productive = np.isin(sl.seg_label, [PROGRESS, RECOVERY]).astype(np.float32)
        n = len(productive)
        phi = np.zeros(n, np.float32)
        starts = np.flatnonzero(fidx == 0)
        bounds = np.append(starts, n)
        for a, b in zip(bounds[:-1], bounds[1:]):
            phi[a:b] = np.concatenate([[0.0], np.cumsum(productive[a:b - 1])]) / horizon[a]
        phi_next = np.zeros(n, np.float32)
        phi_next[:-1] = phi[1:]
        phi_next[done] = 0.0
        return phi, phi_next

    @staticmethod
    def _decisive_frames(sl, fidx, data):
        """(is the last frame of the decisive chunk, is the frame at or before it) per transition."""
        n = len(fidx)
        dec_end = np.zeros(n, bool)
        keep = np.ones(n, bool)
        starts = np.flatnonzero(fidx == 0)
        bounds = np.append(starts, n)
        success = data.success.cpu().numpy() > 0.5
        for a, b in zip(bounds[:-1], bounds[1:]):
            if success[a]:
                continue
            d = sl.decisive[a:b]
            d = d[d >= 0]
            if not len(d):
                continue
            in_chunk = np.flatnonzero(sl.chunk[a:b] == d[0])
            if not len(in_chunk):
                continue
            last = a + int(in_chunk[-1])
            dec_end[last] = True
            keep[last + 1:b] = False
        return dec_end, keep

    @staticmethod
    def _event_reward(sl, hold_min: int = HOLD_MIN_FRAMES):
        """+1 on the frame a target grasp starts a hold that lasts, -1 on the frame the target is
        dropped, -0.5 on a release that left the target away from the goal. Physical, localised on the
        event's own frame, and oracle-derived.

        The first version of this scored `event_type_in_chunk & held` at the FIRST FRAME of the chunk.
        Those two columns are on different clocks: the event type is the chunk's first event repeated
        across all ten frames, while `held` is per frame and is false at the frame a grasp begins. On
        the object corpus the conjunction was empty - 0 of 1558 grasp chunks paid out - so the mode
        reduced to an all-negative reward, and it also charged -0.5 to every release including the 161
        that placed the object successfully. `oracle_labels.py:event_frames` now exports the event's own
        frame index, its object and its hold length, which is what this needs.
        """
        if not sl.has_event_frames:
            raise SystemExit(
                "--segments events needs the per-frame event columns (event_at_frame, event_target, "
                "event_hold_frames, event_missed_release). Re-export the labels with "
                "scripts/annotate/bench/oracle_labels.py; see docs/rl_verification.md finding 1.")
        r = np.zeros(len(sl.event_at), np.float32)
        grasp = (sl.event_at == L.EVENT_IDX["grasp"]) & sl.event_target & (sl.event_hold >= hold_min)
        drop = (sl.event_at == L.EVENT_IDX["drop"]) & sl.event_target
        missed = (sl.event_at == L.EVENT_IDX["release"]) & sl.event_missed
        r[grasp] = 1.0
        r[drop] = -1.0
        r[missed] = -0.5
        return r

    # ----------------------------------------------------------------- hooks
    def reward(self, batch, reward):
        i = batch["idx"]
        r = reward
        a = self.args
        if "pm1" in self.modes:
            r = r + a.seg_reward_scale * self.sign[i] * self.w[i]
        if "potential" in self.modes:
            r = r + a.seg_shaping_scale * (a.gamma * self.phi_next[i] - self.phi[i])
        if "events" in self.modes:
            r = r + a.seg_event_scale * self.event_reward[i]
        if "decisive" in self.modes:
            r = r + a.seg_decisive_penalty * self.dec_end[i].float()
        return r

    def done(self, batch, done):
        if "decisive" in self.modes:
            return torch.maximum(done, self.dec_end[batch["idx"]].float())
        return done

    def expectile(self, batch, expectile):
        if "expectile" not in self.modes:
            return expectile
        i = batch["idx"]
        lab = self.label[i]
        e = torch.full_like(batch["reward"], float(expectile))
        productive = (lab == PROGRESS) | (lab == RECOVERY)
        pessimistic = (lab == FAILURE) | (lab == AFTERMATH)
        e = torch.where(productive, torch.full_like(e, self.args.seg_expectile_hi), e)
        return torch.where(pessimistic, torch.full_like(e, self.args.seg_expectile_lo), e)

    def critic_loss(self, batch, adv):
        if "sign" not in self.modes:
            return None, {}
        a = self.args
        i = batch["idx"]
        y, w, lab = self.sign[i], self.w[i], self.label[i]
        pos_neg = (y != 0) & self.labelled[i]
        zero = (y == 0) & self.labelled[i]
        # L_sign: softplus(-(y * A - m) / tau) pushes y*A above the margin m.
        # Both terms are means over the whole batch, not over the supervised frames: proposal 5.5 writes
        # them as expectations under D, so partial label coverage must weaken the constraint rather than
        # be renormalised away. (Dividing by the supervised count instead makes L_ann O(1) however few
        # frames carry a label, which at seg_lambda=1 swamps a TD loss of order 1e-2 and inverts the
        # value ordering between successes and failures - observed 2026-09-09 on the 5%-coverage smoke.)
        hinge = F.softplus(-(y * adv - a.seg_margin) / a.seg_tau)
        l_sign = (w * pos_neg.float() * hinge).mean()
        # L_neutral: pull neutral and aftermath advantages to zero.
        l_zero = (w * zero.float() * adv.pow(2)).mean()
        loss = a.seg_lambda * (l_sign + a.seg_lambda0 * l_zero)
        with torch.no_grad():
            correct = ((adv > 0) == (y > 0))[pos_neg]
            m = {
                "seg_sign_loss": l_sign.item(), "seg_zero_loss": l_zero.item(),
                "seg_sign_acc": correct.float().mean().item() if correct.numel() else float("nan"),
                "seg_frac_supervised": pos_neg.float().mean().item(),
            }
            for name, k in (("prog", PROGRESS), ("fail", FAILURE), ("after", AFTERMATH)):
                sel = lab == k
                if sel.any():
                    m[f"adv_{name}"] = adv[sel].mean().item()
        return loss, m

    def actor_weight(self, batch, w):
        i = batch["idx"]
        lab = self.label[i]
        a = self.args
        if "mask" in self.modes:
            f = torch.ones_like(w)
            f = torch.where(lab == AFTERMATH, torch.full_like(f, a.seg_mask_aftermath), f)
            f = torch.where(lab == FAILURE, torch.full_like(f, a.seg_mask_failure), f)
            f = torch.where(lab == NEUTRAL, torch.full_like(f, a.seg_mask_neutral), f)
            w = w * f
        if "awr" in self.modes:
            # Responsibility-graded: a failure_inducing frame right at t* is suppressed hardest, and a
            # productive frame is boosted in proportion to how confident the oracle is about it.
            resp = self.w[i]
            f = torch.ones_like(w)
            f = torch.where(lab == AFTERMATH, torch.zeros_like(f), f)
            f = torch.where(lab == FAILURE, torch.exp(-a.seg_awr_penalty * resp), f)
            f = torch.where((lab == PROGRESS) | (lab == RECOVERY), 1.0 + a.seg_awr_boost * resp, f)
            w = w * f
        return w

    def sample_mask(self) -> np.ndarray:
        """Per-frame boolean: frames the trainer is allowed to sample under the active modes."""
        return self.keep_frame

    def describe(self) -> str:
        cov = self.sl.coverage
        return (f"modes={','.join(self.modes) or 'none'}  source={self.sl.source}  "
                f"labelled {self.labelled.float().mean():.1%} of frames, "
                f"{cov['episodes_labelled']}/{cov['episodes_total']} episodes  "
                f"(kappa={self.args.seg_kappa}, q-weighted={bool(self.args.seg_use_q)})")


def make_hooks(args, data, device) -> SegmentSupervision:
    sl = L.load(args.dataset, args.labels)
    if not sl.labelled.any():
        raise SystemExit(f"{args.labels} covers none of dataset {args.dataset}")
    modes = [m.strip() for m in str(args.segments).split(",")]
    return SegmentSupervision(modes, sl, data, args, device)
