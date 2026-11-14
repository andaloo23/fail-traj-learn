# Local sequential full-data distillation

The user approved running the existing first wave sequentially on the local
RTX 3090. The isolated WSL runtime and pinned Qwen2.5-VL-7B weights are ready;
the tested training input configuration peaked at 19.35 GiB on this GPU.

The queue runs the pretrained baseline, binary-only, joint, category auxiliary,
explanation auxiliary, both auxiliary, extra-binary control, joint-then-binary
and failure-balanced replay. Only one worker uses the GPU at a time. Training
and development generation use separate processes to release model memory
between phases.

All 400 training episodes, 50 development episodes, native-frame windows,
targets, seed and 2,688-update schedule are unchanged. The final 50 test
episodes stay sealed. No teacher API calls. Each trained arm has a 72-hour
training ceiling and a six-hour generation ceiling; it exits earlier when its
schedule completes. A ceiling hit is recorded as incomplete. Errors stop the
queue; no silent restart or duplicate retry.

- [Approved local plan](../outputs/oopsie_distillation_local_sequential_v1/plan.md)
- [Live status](../outputs/oopsie_distillation_local_sequential_v1/status.md)
- Development results: `outputs/oopsie_distillation_local_sequential_v1/results.md`
- Logs, adapters, readable predictions and scores are retained under the same run.

The original TACC GPU submissions were canceled after setup failed, before
training began. The user later explicitly approved independent copies of the
same experiments on TACC while the local queue continues. This supersedes the
original no-overlap policy without changing the frozen local code or plan.
Authorization is recorded in
`outputs/oopsie_distillation_local_sequential_v1/parallel_tacc_authorization_v1.json`.
TACC copies use `outputs/oopsie_distillation_tacc_replicates_v2/` for separate
logs, adapters, predictions and scores.

The user authorized recovery after the 2026-10-29 PC reboot. The baseline was
complete; binary training had logged update 1,565 and saved its last complete
checkpoint at 1,500. `scripts/distill/recover_local_full_queue_v1.py` restores
that adapter, AdamW state and Python/PyTorch/CUDA random states into a fresh
`runs/binary/recovery_v1/` directory. The same sample order and 2,688-update
schedule continue from update 1,501, replaying 65 unsaved updates. Prior runtime
still counts toward the original 72-hour ceiling. Subsequent recipes use the
unchanged frozen trainer, sequentially; the completed baseline is skipped.

The original launch code, approvals, logs and checkpoint remain unchanged.
Recovery receipts, code/source hashes, pre-reboot status snapshots and new
phase logs are under `recovery_reboot_v1/`; `status.md` tracks current progress.
This is an explicitly authorized one-shot recovery, with no automatic retry.
Fourteen CPU checks passed, including exact agreement with uninterrupted frozen
training for losses, weights, optimizer state and random state on a toy fixture.
