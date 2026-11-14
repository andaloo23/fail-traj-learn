# Independent TACC copies of the local recipe study

The user explicitly approved the same experiments running locally and on TACC.
The local RTX 3090 queue continues. The new TACC run reuses the frozen full-data
study and writes independent outputs under
`outputs/oopsie_distillation_tacc_replicates_v2/`.

Setup job **3540122** creates a new isolated environment with NumPy **2.3.5**.
The failed environment had NumPy 2.5.4, whose required x86-64-v2 CPU baseline
is unavailable in the VM. NumPy documents the baseline change in its
[2.4 release notes](https://numpy.org/doc/2.4/release/2.4.0-notes.html#modulate-dispatched-x86-cpu-features).
The other direct model-runtime versions match the original requirements.
Transferred evidence and downloaded pinned weights are reused.

Setup verifies real array/image/HDF5 interoperability, audits all 11,535 input
records, and checks every transferred image and training/development reference
hash. Successful setup releases A100 runtime check **3540125**. It runs
forward/backward passes on representative and largest training windows, then
discards those temporary updates. Successful validation releases array
**3540126**, tasks 0–2.

Each task receives a full A100 node and runs three independent recipes, one
per GPU. Three packs cover pretrained Qwen and all eight SFT recipes once.
Nodes have a 32-hour limit; each trainer has 30 hours for the same 2,688-update
schedule, then up to 1.5 hours for development generation. Time-capped runs are
marked incomplete. No automatic requeue or within-run duplicate retry.

At TACC's published three-GPU node layout and 3-SU/node-hour rate, the packed
GPU ceiling is 3 nodes × 32 hours × 3 SUs = **288 SUs**.
[Node specifications and rates](https://docs.tacc.utexas.edu/hpc/lonestar6/)
Setup and the runtime check bring the launch ceiling to 288.893 SUs;
conservative allowances for earlier failures bring the cumulative ceiling to
**289.179 SUs**, within the original 300-SU cap.

All runs use 400 training episodes, 50 development episodes, the same native
frame windows, targets, auxiliary eligibility, model revision and seed.
The final 50 test episodes stay sealed. No new teacher API calls.
Different hardware and the recorded environment can affect numerical results;
these are replicated recipes, not additional distinct training recipes.

- [Approved plan](../outputs/oopsie_distillation_tacc_replicates_v2/plan.md)
- [Status](../outputs/oopsie_distillation_tacc_replicates_v2/status.md)
- Submission receipts: `outputs/oopsie_distillation_tacc_replicates_v2/submissions/`
- Scripts: `scripts/tacc/oopsie_replicates_v2_*.sbatch`

Validation before submission: six replica tests, shell syntax, local and remote
code/data/approval hashes. Actual VM and GPU runtime validation are Slurm
dependencies, not checks completed at submission time.
