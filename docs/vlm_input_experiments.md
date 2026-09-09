# What was tried on the VLM's input side, and what each attempt showed

Scope: Qwen3-VL-8B-Instruct, bf16, local RTX 3090, on the LIBERO recordings (256x256 per camera, 20 fps, 10-step
chunks). Everything below concerns what the model is *shown* and *asked*; the semantic-output ablation (labels,
decisive chunk, cause given correct events) is a separate experiment (`oracle_*` methods). Scores are on the
20-episode dev set against reference r2 unless stated; scoreboards live in `outputs/bench/*.md`.

## 1. Resolution and single-tile perception (2026-09-07, `probe_vlm.py`)

| input | answer about the held can |
|---|---|
| one 512x256 tile (agentview + wrist) at native size | "blue cylindrical can with a red label"; distractors described vaguely |
| same tile at 2x | "cylindrical can with a blue and yellow label"; distractors named correctly (red and green can, dark green bottle, red and white carton) |

Finding: at native size a tile is 128 visual tokens (32 px per token) and colours are misread; at 2x the model reads
a can and the distractors correctly. Consequence: tiles are shown at 1.5x in the whole-episode prompt and at 2x in
every single-frame question. Cost: visual tokens scale with the square of the factor.

## 2. Whole-episode prompt, versions p1 to p8 (`scripts/annotate/prompt.py`)

The model receives one tile per chunk (28 to 40 images), the instruction, the outcome, a per-chunk table of
end-effector position, speed, aperture and gripper command, and a glossary of the scene objects; it returns the full
diagnosis JSON; five samples are majority-voted.

| version | change | effect (full_shift8__t0 ep 0, ground truth: slip of the alphabet soup in chunk 12) |
|---|---|---|
| p1 | baseline | cause "reaching", t* = 4 (the first missed grasp); said a can was grasped "instead of the alphabet soup" |
| p2 | glossary written from memory | called the correct object "tomato sauce" because the glossary said the soup can is red and white; it is dark blue (checked with `object_gallery.py`) |
| p3 | glossary rewritten from actual renders | still "red and green can" for the held object, t* = 4 |
| p4 | tiles at 1.5x, "identify from the wrist camera first" rule | still wrong object story; the model described the held can as "orange/yellow label, not the alphabet soup", which is the glossary's own description of the alphabet soup |
| p5 | two-stage: a separate greedy identification call on 2x wrist close-ups, result injected as a fact | correct: alphabet soup, cause manipulation, t* = 11; but 11 of 12 pilot episodes then had t* = 11 |
| p6 | numeric example JSON replaced by `<chunk>` placeholders | t* = 12 on ep 0 (correct), values episode-specific again; the p5 result was the model copying the example's numbers |
| p7 | softer wording for episodes with no grasp | no change: no-grasp episodes are labelled failure_inducing from chunk 0 |
| p8 (other session) | start/end frame per chunk in grids, aperture caveats, "do not infer an error from the outcome" | production annotator `whole_p8`: 1 of 20 dev episodes pass; events 25 %, chunk labels 17 %, decisive 20 %, cause 40 % |

Findings: (a) the model anchors on a narrative and keeps it across prompt edits until the contradicting fact is
supplied explicitly; (b) any concrete number in an example is copied; (c) any sentence that names an expected label
is applied everywhere; (d) long multi-image reasoning is unreliable even when single-tile perception is fine.

## 3. Per-frame held/empty scans (other session's event-first lab, re-run in-process as `event_first_batched`)

Input: one paired image per call at 2x, every fifth frame with two offsets, object-blind question, greedy. Audited
against the oracle (both-finger contact; one-finger frames excluded).

| episode | target | wrong judged frames |
|---|---|---|
| full_shift8__t0 ep 0 | alphabet soup (can) | 4 of 108 |
| full_shift8__t1 ep 3 | cream cheese (flat box), held four times | 37 of 96: every hold read as empty |
| full_shift16__t5 ep 9 | orange juice (carton) | 79 of 104: empty read as held |
| full_shift12__t2 ep 29 | salad dressing (bottle) | 72 of 110 |
| full_shift16__t4 ep 7 | ketchup (bottle) | 67 of 110 |

Across the dev set the scan was the first failing level in 15 of 20 episodes. Finding: the object-blind held/empty
question works on cans and fails on boxes, cartons and some bottles; both false-empty (box held) and false-held
(housing or object near the fingers) occur.

## 4. Gripper telemetry instead of vision (`bench/telemetry_held.py`, `telem_v3`)

Input to the detector: aperture (finger coordinate) and gripper command only; the VLM is used solely for object
identity on close-ups from the middle of holds.

| variant | frame accuracy (642 refs) | episodes with correct events (dev) | overall (dev) |
|---|---|---|---|
| settle test, lo 0.5 cm, hi 3.6 cm, min run 3 (`telem_v3`) | 0.89 | 11 of 20 | 3 of 20 |
| sweep-tuned: lo 0.6, hi 3.4, min run 8, no settle (`telem_v4nv`) | 0.90 | 7 of 20 | 1 of 20 |

Per-object aperture while held overlaps the closed-on-nothing range: thin objects at 0.5 cm, wide cartons at
3.4 to 4.0 cm, and the reference counts pushes with closed fingers as holds. Finding: telemetry is the most
reliable non-privileged event source and still caps near half the episodes.

## 5. Vision as a gate on telemetry (`fused_v4`, `telem_v4`, `telem_v4s`)

| variant | what the VLM decided | events | held object |
|---|---|---|---|
| fused_v4 | 2-of-3 vote on three frames of each gripper-close run | 25 % | 13 % |
| telem_v4 | veto of a telemetry hold only if all three frames say empty | 30 % | 20 % |
| telem_v4s | same veto, settle thresholds, slot-named identification | 25 % | 0 % |

Finding: every time the held/empty judgment was given authority the result fell below telemetry alone; the veto
removed real holds (all holds vetoed in most telem_v4s episodes). One caveat: fused_v4 also placed two of its
three verification frames before the grasp because the close command precedes the grasp; telem_v4 fixed that and
still lost.

## 6. Object identification (`identify_held_object`)

Works on cans and boxes at 2x when the answer can be matched to a slot; it returned "book" for black_book_1 until
the slot names were listed in the prompt (`telem_v4`), and confused milk with salad dressing once. Identity is the
one visual sub-task with a usable accuracy.

## 7. VLM chunk labels on top of telemetry events (`telem_v3c`)

Per-chunk prompt with four frames, motion telemetry and the telemetry-derived tracker state, three samples each,
393 s per episode. Overall unchanged at 3 of 20; chunk labels 22 % versus 28 % for rules alone. Finding: with the
events fixed, the model's per-chunk labels did not improve on the deterministic completion rules.

## Summary of the input-side evidence

- Resolution matters and 2x is enough for single close-ups of cans; it is not enough for the model to reason over
  30 tiles at once.
- Two prompt artefacts dominated early results: narrative anchoring and copying of example numbers.
- The object-blind held/empty question is the weak component, measured three ways with the same prompt; the
  object-identity question is the strong one.
- Telemetry beats vision for events but cannot pass half the episodes; combining them by letting vision veto made
  things worse.
- Not yet tried on the input side: an object-aware held question, temporal pairs (frame t and t+5 in one image),
  a larger model, and vision as a confidence weight rather than a gate.
