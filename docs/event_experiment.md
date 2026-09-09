# Observable-event experiment

Follow-up: [iterative segmentation findings and reproducible loop](segmentation_iteration_results.md).

This experiment tests whether Qwen can detect visible attachment/detachment events before asking it for
failure causes or ordinal advantage labels. It does not modify production annotations or train a policy.

The first reference is the user's review of `full_shift8__t0` episode 0: chunk 11 was fine; the slip happened
at the end of chunk 12. The exact frame has not been adjudicated. That reference lives separately in
`scripts/annotate/references/full_shift8__t0_ep0000.json` and is read only after inference.

## Protocol

- Local recognition: show chunks 10–13, selected with human knowledge of the event neighborhood.
- Episode scan: fixed four-chunk windows with two-chunk overlap across the entire episode. The shared
  10–13 window is identical to the local query and reused, not counted as an independent model trial.
- Sample every second recorded frame plus each chunk's first and last frame. At 20 Hz this retains at
  least 10 Hz evidence, including chunk boundaries. Each camera remains at native 256×256 resolution;
  the two views are concatenated to 512×256 without resizing or labels covering the image.
- Model inputs contain only images, frame numbers, timestamps, and generic event questions. No task,
  outcome, object glossary, telemetry, previous diagnosis, or privileged state is supplied. This isolates
  visual event recognition; task-conditioned semantics should be evaluated separately later.
- One greedy response per window, temperature zero. Store raw responses, validation errors, exact input
  bundles and image hashes. Invalid responses remain failures; no hidden retries or repaired timestamps.
- Output: visible object appearance, evidence, event type, and the last-before/first-after observed frames.
  These are temporal brackets, not invented exact timestamps. Null endpoints and uncertain are allowed.

## Run

From the repository root in WSL, using the LeRobot environment:

```bash
PY=/home/aliu/projects/fail-traj-learn/lerobot/.venv/bin/python
$PY scripts/annotate/event_experiment.py full_shift8__t0 0 \
  --tag event_qwen_v1 --local 10 13 --run \
  --reference scripts/annotate/references/full_shift8__t0_ep0000.json
```

Omit `--run` to export images and prompts without loading a model. Use a new `--tag` and `--model` to
compare another locally available Qwen-compatible checkpoint. The current backend is Qwen-specific;
hosted/other architectures require an adapter that consumes the same exported bundle. No hosted calls
are made by this script. Compare matching `input_sha256` values before comparing model responses.

Re-running resumes saved responses. Changed configuration or changed image/prompt hashes cause an
explicit failure rather than silently mixing trials. Responses with parse errors remain saved for audit;
use a new tag for a fresh experiment.

## Inspect

First run (`event_qwen_v1`, Qwen3-VL-8B-Instruct): 13 unique windows, 12 valid responses, one invalid.
The human-selected 10–13 window correctly describes a blue/yellow can detaching between frames 128 and
130 (6.4–6.5 s), consistent with the user's late-chunk-12 reference. The fixed scan includes that same window.
However, window 12–15 denies holding the object and outputs `observed` with no events (rejected). Early
windows also claim attachment/detachment of a white mug, and window 8–11 suggests detachment without a
first-detached frame. These need review; there is no exhaustive reference to compute precision yet.
Six late windows (14–17 through 24–27) report no change. Peak allocated GPU memory was about 17.5 GiB.

Interpretation: Qwen can detect this slip with native-resolution local evidence, but its answers change
with window context. This single episode does not establish robust detection, cause attribution, or
superiority over another model. Keep the v1 prompt fixed for a comparative benchmark rather than tuning
it to this example's known frame numbers.

Outputs are on Windows under:

```text
outputs/event_experiments/<tag>/<dataset>/ep0000/
  config.json
  report.json
  index.html
  window_010_013/
    input.json
    frame_000100.png ...
    response.json
```

Open `index.html` to compare each response with the exact frames it received. `report.json` separates
the local query and full scan and lists all detachment candidates. A bracket overlapping chunk 12 is
only a preliminary timing check: verify the object and whether the bracket really encloses the slip.
Broad brackets can overlap by chance. The reference is not exhaustive, so other candidates cannot yet
be counted as false alarms. Multiple overlapping windows can describe the same physical event.

The next benchmark should include approximately 20 independently reviewed episodes, including successful
placements and harmless re-grasps, and a held-out subset. Measure missed events, false alarms, object
identification and timing against exhaustive event references before deciding whether to change models.

CPU regression checks:

```bash
$PY -m unittest discover -s scripts/annotate -p 'test_*.py'
```
