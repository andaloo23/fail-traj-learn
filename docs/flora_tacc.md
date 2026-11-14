# FLORA on TACC: run and review guide

Read the [experiment results and next steps](flora_results.md) first. The
[2026-10-26 evidence snapshot](experiments/flora/2026-10-26/README.md) contains
preserved outputs and readable Markdown conversions. New work uses **real
OopsieData**; the LIBERO scripts/results are retained for historical reproduction.

At the dated snapshot, replacement ten-episode job **3533752** is pending
scheduler priority. Its CPU compiler audit **3533751** passed. The original
ten-episode job **3530286** was cancelled; the separate three-episode job
**3530163** failed and **must not be resubmitted**. Check current state before
submitting anything. Queue acceptance or CPU preprocessing does not establish
completed GPU inference.

## Models and experiment modes

| Component | Purpose | Local evidence |
| --- | --- | --- |
| Rewarder dense | Native failure / suboptimal / normal timelines, with native segment rationales | Completed historical LIBERO and three-episode Oopsie pilots; corrected reference run pending. |
| Rewarder rubric | Episode-level scores under supplied criteria; retained reasoning and native sample selection | Completed reduced one-sample generic-rubric Oopsie pilot; reference run uses nine samples and task-specific rubrics. |
| Rewarder terminal | Episode outcome scoring | Wrapper prepared; no completed terminal-mode experiment claimed. |
| TempSeg / Captioner | Operation segmentation and intended-action captions | Pinned code and validation/preparation support; no completed model-inference results claimed. |

`scripts/tacc/models.lock.json` pins Rewarder code/weights at
`7de68d22c4a9decec5ddb7f86ddcaee8f82d3367` and Captioner/data-engine code at
`f736ca36925ae55d2f7915993ed1bc9f87288bb3`. The data engine pins its own model
weights in its upstream `batch_utils/models.json`; do not rewrite those revisions.

Original camera MP4s enter the real-data jobs without transcoding. This **does
not mean the model sees every frame**: native dense inference samples windows
(64 frames at 4 FPS, 32 half-second quality groups with native padding/stitching),
and executable rubric inference uses 2 FPS capped at 166 frames per camera.
Source-rate frame scores are stitched outputs, not independent source-rate VLM
judgments. These retrospective labels use future context and do not demonstrate
online failure warning.

## Access and workspace

Authenticate in a real WSL terminal, supplying your own allocated system/user:

```bash
bash scripts/tacc/connect_tacc.sh YOUR_USERNAME login2.ls6.tacc.utexas.edu
```

The helper prompts through SSH/MFA, opens a reusable WSL SSH control connection,
and saves read-only allocation/queue inventory under `outputs/tacc_access/`.
Generic TACC access is insufficient without an active allocation for the selected
system/queue. Enter credentials only at interactive login prompts. To reuse it:

```bash
ssh -S ~/.ssh/tacc-flora-%C YOUR_USERNAME@login2.ls6.tacc.utexas.edu hostname
```

Current site-specific scripts record account `IRI26045`, Lonestar6 paths and
queue settings; override `-A YOUR_PROJECT` at submission on another account.
The collectors additionally assume this workstation's Ubuntu-22.04 WSL setup,
SSH username/host/socket and local media environments. Inspect these values
before reuse elsewhere; they are not portable defaults.

Use a distinct workspace for each version. The replacement ten-episode workspace
is `/scratch/11388/al62479/ftl-flora-oopsie-ten-cuda-v2`; runtime/model cache is
`$SCRATCH/ftl-flora`. Save finished artifacts outside scratch and download promptly.
Never replace frozen inputs, prior request manifests or native model outputs.

## Prepare real OopsieData inputs

1. Obtain access to `OopsieData-Submissions/oopsiedata-v0.1`. Run
   `python scripts/tacc/inspect_oopsiedata.py` to save inventory/access metadata;
   this does not download the entire dataset. The experiment pins release
   `da4b16512b77f7324296a66da7c0067a40539895`, described as v0.1.1 by its card.
2. Download selected HDF5 episodes and referenced original MP4s at that revision
   through an authenticated local Hugging Face client. Preserve release paths
   under `<pilot>/source/`. The recorded `selection.json` specifies exact episodes
   and checksums; the inspector is not an automatic pilot downloader. Use
   `ten_corrected_inputs/selection.json` in the evidence snapshot to reproduce
   these ten. Keep source outcome annotations separate from model inputs.
3. Review camera roles visually, including source first/middle/last frames.
   `oopsie_ten_camera_mapping.json` accounts for included and omitted views;
   camera filename/alphabetical order is not a spatial calibration. Write a new
   mapping for new episodes. Do not manufacture missing cameras or claim capture
   sync from matching encoded PTS alone.
4. Run preparation in an environment with PyAV, h5py and NumPy:

```bash
python scripts/tacc/prepare_oopsiedata.py \
  --pilot outputs/oopsiedata_ten_v1 \
  --inventory outputs/oopsiedata_v0_1_access/dataset_info.json \
  --camera-map scripts/tacc/oopsie_ten_camera_mapping.json \
  --rubrics scripts/tacc/oopsie_ten_reference_rubrics.json \
  --out outputs/oopsiedata_ten_reference_v1
```

Choose a fresh `--out` when reproducing or changing anything. Preparation checks
release hashes, decoded frame counts, frame/state alignment, zero-based uniform
PTS and camera timing; it writes dense/rubric jobs and provenance. It refuses to
overwrite prior jobs. Source annotations are archived separately and excluded
from inference. The committed evidence contains prepared metadata, not videos.

## Environments and native fidelity

`setup_flora.sbatch` / `setup_flora.sh rewarder` prepare the **historical
dense/terminal environment**, Python 3.12, pinned upstream requirements (minus
unused Decord), official vLLM 0.24.0 CUDA 12.9 wheel and cached model weights.
They are not a complete fresh reference-rubric setup. `setup_flora_rubric.sh`
adds the historical TorchCodec decoder, which differs from the reference Decord
reader. Preserve these historical environments.

The validated reference environment is `$FLORA_ROOT/venv-reference`. It was
created with the Rewarder Python using `venv --without-pip`; a
`flora_shared_dependencies.pth` points to
`$FLORA_ROOT/venv-rewarder/lib/python3.12/site-packages`, and unmodified Decord
0.6.0 is installed in the reference environment. Its native Decord reader passed
the CPU media audits. This shared environment depends on the original runtime;
changing that runtime requires a fresh audit. Recreating it on a different site
requires installation plus the same audits, not just copying the venv folder.

`audit_flora_reference.py` checks every pinned package requirement, fetched code
hash, tokenizer/config snapshot, actual parser default, reviewed camera mapping,
native media decode, rendered prompt and input hashes. With `--old-dense` and
`--old-jobs`, it also reconstructs original results using native postprocessing.
`--verify-weights` verifies weight shard hashes. The GPU batch verifies all 11
shards again. `published_code.json` and `hub_metadata.json` must accompany the
audit; these are obtained from the pinned release and their recorded copies are
in the experiment receipts.

The publisher's Decord wheel has a platform-tag inconsistency: `pip check` reports
`decord 0.6.0 is not supported on this platform` despite successful imports and
native decode. The wheel is unmodified. Only this exact documented warning is
accepted by the audit; other dependency failures stop the run.

The reference profile follows the **pinned executable batch defaults**. Its
rubric 2 FPS / 166-frame / 98,304-context settings conflict with the model card's
1 FPS / 82-frame / 32,768-context description. Do not describe it as matching both.
`run_flora.py --reference-defaults` rejects inference-setting overrides, retains
dense frame scores/rubric thinking and writes new per-attempt manifests. Task
rubrics are researcher-authored inputs with step maxima summing to 1.

## CUDA checks and submission

`flora_cuda_env.sh` explicitly selects CUDA 12.8 and GCC 13.2, checks compiler
binaries/headers and exposes build tools/libraries. This avoids the broken
compute-node Lmod path responsible for job 3530163's missing-compiler failure.
Override site paths with `FLORA_CUDA_HOME` / `FLORA_GCC_ROOT` where necessary;
`check_flora_cuda.py` currently requires CUDA 12.8 and H100 for GPU execution.

The CPU preflight compiles/links the actual FlashInfer H100 sampling module
without loading `libcuda.so.1`. The GPU batch runs a deterministic sampling
check before loading weights. A successful CPU compile cannot certify the GPU
driver, sampler execution, memory headroom or full inference.

For a **new authorized run**, stage and SHA-256-check code, original videos,
jobs, provenance and audit metadata in a new workspace. The native media and
compiler preflights must pass on those inputs/environment before GPU inference.
The commands below illustrate dependencies; **do not execute them to duplicate
the already queued 3533752 or resubmit 3530163**:

```bash
export FLORA_ROOT="$SCRATCH/ftl-flora"
# Run in the staged workspace; record the returned IDs as MEDIA_JOB / CUDA_JOB.
sbatch --parsable -A YOUR_PROJECT scripts/tacc/preflight_flora_oopsie_ten.sbatch
sbatch --parsable -A YOUR_PROJECT scripts/tacc/preflight_flora_cuda.sbatch
# Substitute the actual successful preflight job IDs, not the variable names.
sbatch --parsable -A YOUR_PROJECT \
  --dependency=afterok:MEDIA_JOB:CUDA_JOB --kill-on-invalid-dep=yes \
  scripts/tacc/reference_flora_oopsie_ten.sbatch
```

The reference ten wrapper selects the ten-episode input/audit directories and
eight-hour limit. Its shared batch runs dense on one H100 then rubric on two
H100s, retaining native inference defaults. The recorded whole-node upper bound
is 48 SUs, not an expected cost; check current accounting/queue limits for future
runs. The existing replacement depends on compiler audit 3533751 and reuses the
already passed 3530285 media audit of unchanged, hash-verified inputs.

Read-only status, using the established SSH connection:

```bash
ssh -S ~/.ssh/tacc-flora-%C YOUR_USERNAME@login2.ls6.tacc.utexas.edu \
  'date -u; sacct -j 3533751,3533752 --format=JobID,State,Elapsed,ExitCode,Start,End -P; squeue -j 3533752'
```

TACC job timestamps in these receipts are CDT; use UTC when comparing local
Pacific timestamps. On failure, preserve logs, run manifests and any partial
outputs before making a new version. A dense pass followed by rubric failure
must be described as partial, not a completed combined experiment.

## Collect and review

The existing Windows collector watches 3533752, validates hardware/weight/input
receipts and native default arguments, downloads complete results, checks all ten
dense outputs and all nine rubric samples per episode, then builds a separate
viewer and annotated MP4s. It does not submit jobs or overwrite historical
results. Its local status/logs are under
`outputs/flora_oopsie_ten_cuda_repair_v2/`; successful review output goes under
`outputs/flora_oopsie_review_3529640/ten_3533752/`. Collection requires this
workstation, media environments and authenticated WSL SSH session to remain
available. Verify whether the collector is already running before restarting it.

For manual viewer construction after a completed run, with the **matching**
local jobs/provenance and original videos available:

```bash
python scripts/tacc/review_flora_rubric.py \
  --rubric outputs/RUN_RUBRIC/rubric.jsonl \
  --jobs outputs/INPUTS/rubric_jobs.jsonl \
  --provenance outputs/INPUTS/provenance.json \
  --out outputs/NEW_REVIEW
python scripts/tacc/serve_flora_review.py --directory outputs/NEW_REVIEW --port 8796
```

The server supports HTTP byte ranges for seeking. The rubric builder constructs
the episode-reasoning view; the reference collector adds validated dense labels,
reference warnings/configuration and review metadata. For individual annotated
videos, run in the PyAV/NumPy/Pillow environment, once per episode:

```bash
python scripts/tacc/export_flora_annotated_video.py \
  --episode O001 --dense outputs/RUN_DENSE/dense.jsonl \
  --dense-jobs outputs/INPUTS/dense_jobs.jsonl \
  --rubric outputs/RUN_RUBRIC/rubric.jsonl \
  --jobs outputs/INPUTS/rubric_jobs.jsonl \
  --provenance outputs/INPUTS/provenance.json \
  --out outputs/NEW_REVIEW/exports/O001
```

The exporter uses original camera frame timing and native per-frame labels,
preserves native boundaries without smoothing, and saves SRT/receipts. It supports
single-camera and multi-camera sources. Native normal spans have no rationale;
none is invented. Rubric reasoning stays episode-level in reference exports.

For review without local videos, the committed derived Markdown presents exact
native intervals/rationales and selected reasoning. It is useful for inspecting
outputs, but semantic validation requires original video playback. Keep failure,
suboptimal and normal separate until the human-reviewed binary adapter is defined.

## Local checks

```bash
python -m unittest discover -s scripts/tacc -p 'test_*.py' -v
```

Nineteen focused tests cover spatial camera manifests, forbidden reference
overrides, invalid-clip fallback rejection, output completeness, retained rubric
reasoning and raw score validation before upstream clamping. Bash syntax checks
cover `.sh` and `.sbatch` scripts; readable reports can be rebuilt without a GPU
using `summarize_flora_results.py`. Structural checks explicitly leave
`human_verified=false` and `training_ready=false`. See the results document for
the planned human evaluation and controlled ablations before distillation.
