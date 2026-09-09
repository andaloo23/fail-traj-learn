# Qwen segmentation iteration: findings and reproducible loop

This is development on `full_shift8__t0`, episode 0, after the user corrected the visible slip to the end
of chunk 12 and confirmed chunk 11 was fine. It is not a held-out evaluation or a general reliability claim.
The loop saved 373 queries / 595 raw responses across 15 run directories, including unsuccessful approaches.

## What worked

The most useful decomposition was:

1. Show both cameras at 2× rendered size, one observation per model call. The source remains 256×256 per
   camera; enlargement increases visual-token allocation, not captured optical detail.
2. Ask only whether an external object is held, empty, or uncertain. No task outcome, privileged state,
   human reference, or known event time is supplied to this detector.
3. Scan the entire episode at a five-frame stride, then repeat with a two-frame offset.
4. Require consecutive observations before confirming a state change, so isolated misreads remain in
   the raw results but do not become false drops.
5. Match confirmed event brackets across the two independent scans. Do NOT pool their frame observations
   before detecting events: doing that put isolated errors at 115 and 117 next to each other and fabricated
   a drop in chunk 11. A regression test now covers this failure.
6. Densely inspect every frame around the model-proposed event brackets, with three sampled responses.
   Refinement can narrow an agreed event; it cannot introduce an unsupported event elsewhere.
7. Label each action chunk separately using its images, task/glossary, measured non-privileged robot motion,
   commanded gripper action, and explicitly fallible visual-tracker estimates. Keep frame-level event timing
   out of this semantic response; asking for it again led to invented frame indices.
8. Check a second chunk-label pass with changed context, tracker sampling and random seed. Flag conflicts,
   stationary descriptions contradicted by measured motion, and unsupported claims of holding.

The two full scans found the loss at frames 120–125 and 122–127 respectively, both within chunk 12. Their
grasp/empty audit agreed with the simulator on 53/55 and 54/55 scored observations; unilateral-contact
frames were excluded as ambiguous. These are small, class-imbalanced, in-development checks, not calibrated
accuracy estimates. The model still made isolated errors during the stable carry.

Dense refinement proposed frames 124–125 for visible loss. This is a model estimate, not a verified physical
contact timestamp. The recorded contact signal changes earlier within chunk 12, and dense images show
progressive separation. Preserve the distinction between physical contact, visible separation and causal error.

With visual-tracker evidence included, the final local/context variants label chunk 11 as progress and
chunk 12 as failure-inducing in all six sampled answers (three per setting). The shared model and prompts
mean those samples are not independent accuracy evidence. They do demonstrate stability under the tested changes.

## What did not work reliably

- Whole-episode diagnosis and direct multi-frame event narration misplaced changes or invented object identities.
- Agent-only or wrist-only input did not solve the issue. The paired views were useful at the larger rendered size.
- Native-resolution single frames still missed the held object at 110/120; 2× paired views corrected those cases.
- Larger multi-frame windows still let later empty states contaminate judgments of earlier held states.
- Native video tokens improved descriptions of motion but invented successful placement and remained inconsistent
  about release time. Five raw video trials are saved under `lab_v7_video`; JSON parsing is not semantic validation.
- Standard Transformers generation reproduced seven of eight cached-backend responses exactly; both paths
  retained the important errors. This test does not prove numerical equivalence in general, but the tested
  failures are not explained by the custom cache optimization.
- Task-phase semantics remain unreliable before grasping and in parts of the tail. Qwen often calls an
  approach neutral because no object is held, or describes movement as stationary. Motion telemetry helps
  detect those contradictions but cannot by itself determine task progress.

## Final review artifact

Open `outputs/segmentation_lab/event_first_review/full_shift8__t0/ep0000/index.html` for the camera video,
clickable chunk timeline, model/context comparison, flags and experiment counts. `result.json` stores all
combined observations and the provenance of each confirmed event.

The conservative candidate labels chunks 6–11 progress and chunk 12 failure-inducing. Chunks 0–5 and several
tail chunks are marked uncertain where evidence or descriptions conflict. Other tail chunks remain neutral.
These labels do not claim the task became irrecoverable, and no causal decisive-error timestamp is assigned.
All training weights remain zero: this is a development/review artifact, not a production annotation upgrade.

## Reproduce the selected loop

From the repository root in WSL:

```bash
PY=/home/aliu/projects/fail-traj-learn/lerobot/.venv/bin/python
$PY scripts/annotate/run_segmentation_loop.py full_shift8__t0 0 --tag event_first_v1
```

The runner resumes saved calls, performs two full scans, adaptive dense refinement and two full chunk-label
passes, then writes `<tag>_review/result.json`. This repeatable protocol evaluates changed context on every
chunk; the exploratory run above checked changed context on nine chunks. Use a new tag when prompts change.
No human timing or privileged object signal enters its model prompts or evidence combination.

Relevant tools:

- `segmentation_lab.py`: configurable camera, scale, frame density, window, native-backend and repeat ablations;
  privileged columns are used only in its separate post-inference audit.
- `video_segmentation_lab.py`: native video-token comparison.
- `local_segmenter.py`: chunk-local semantic judgments with optional motion and visual-tracker evidence.
- `combine_local_evidence.py`: cross-scan event agreement, constrained refinement and conservative labels.
- `lab_review.py`: visual review page and trial inventory (reuses the smoke episode's existing camera video).

Validation: 19 CPU regression tests pass, Python compilation passes, and the review video contains all 280
frames at 20 fps (14 seconds). Raw experiments and earlier p8 annotations are preserved.

The next necessary test is a fixed set of other episodes with human event and segment references, including
intentional releases and brief re-grasps. Two-observation confirmation can miss very brief events. The current
evidence supports better localization of this episode's loss, not trustworthy automatic labeling of the corpus.
