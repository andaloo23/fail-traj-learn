# Segmentation benchmark: 50 failure episodes, strict per-episode correctness

Goal: decide which VLM annotation method produces fully correct segment annotations, measured on a fixed set
of 50 failure episodes against references derived from the simulator's privileged state. "Correct" is defined
per level below; an episode passes a method only if every applicable level passes. The scoreboard reports the
fraction of episodes that pass, per level and overall, per failure mode.

Everything under `scripts/annotate/bench/`. Benchmark data under `$FTL_PROJ/bench/` (WSL side), reports
mirrored to `outputs/bench/` (Windows side).

## 1. Reference (ground truth) per episode: `bench/references/<dataset>/episode_XXXXXX.json`

Built by `bench/oracle_reference.py` from `priv.*` columns only (never shown to any model). Version `r3`
(r2: annotation granularity, a hold has to be visible at the 10-frame chunk scale to count; r3: short holds that
lift the object or end in a finger collapse are slips with events, and episodes without a decisive chunk are
labelled from their events; see Changelog).

```
{
  "reference_version": "r3",
  "dataset", "episode_index", "suite", "task_id", "task", "success": false,
  "n_frames", "fps", "n_chunks", "chunks": [[start, end_exclusive], ...],      # from chunk.index
  "object_slots": [...], "target_slot": "<name>", "goal_slot": "<name or null>", "fixtures": [...],

  "held_runs": [ {"start", "end", "state": "held"|"empty"|"ambiguous", "object": "<slot or null>"}, ... ],
      # per-frame state, run-length encoded, frames [start, end] inclusive.
      # hold      = priv.obj_grasped[slot] == 1 (both fingers), debounced (>= 3 consecutive frames, DEBOUNCE), then
      #             holds of the same slot separated by <= 4 frames merged (HOLD_GAP_FRAMES), then runs of
      #             >= 8 frames kept (HOLD_MIN_FRAMES) plus (r3) shorter runs that are SLIPS: the object was airborne
      #             (no support contact and no object-object contact) at some frame of the run, OR the run ends with
      #             the command still CLOSE and the aperture falls below 0.8 cm within 10 frames after it
      #             (SLIP_COLLAPSE_FRAMES: the fingers closed on nothing after losing the object). Only holds drive
      #             "held", the events and the failure mode.
      # held      = inside a hold, grasped flag on, not a transition frame
      # ambiguous = exactly one finger in contact with an object (obj_left/right_finger_contact XOR); the 2 frames on
      #             each side of a hold boundary (transition frames); grasped-flag blips and debounced holds shorter
      #             than 8 frames that are not slips (pushing a bowl with the fingertips, a both-pad brush: no event);
      #             flag gaps inside a hold (including merged gaps)
      # empty     = otherwise
  "events": [ {"index", "type": "grasp"|"release"|"drop", "object", "last_before", "first_after", "chunk",
               "gripper_cmd_open": bool, "hold_frames": int}, ... ],
      # transitions of the hold state. release = held->empty while the commanded gripper is opening
      # (action[6] <= 0 in the transition frame window); drop = held->empty while the command is still CLOSE.
      # chunk = chunk containing last_before. A hold whose last frame is within 3 frames of the episode end
      # (DEBOUNCE) is "held at end" and produces no release/drop event (the state never re-stabilises).
      # hold_frames < 8 marks a slip (r3).
  "close_on_nothing": [ {"start", "end", "chunk"} ],   # cmd CLOSE, aperture < 0.8 cm, no hold, no gripper contact, >= 2 frames
  "post_slip_closure": [ {"start", "end", "chunk", "after_drop"} ],
      # r3: close-on-nothing runs that begin within 12 frames (POST_SLIP_FRAMES) after a drop (after_drop = the
      # drop's last_before): the empty gripper finishing the closing motion of the attempt that just lost the object.
      # Listed for transparency, never an error of their own (not in close_on_nothing, no failure_inducing chunk,
      # not a failed closure for the missed_grasp decisive chunk).
  "wrong_object_contacts": [ {"object", "start", "end"} ],      # gripper contact with a non-target slot, >= 3 frames
  "collisions": [ {"start", "end"} ],                            # priv.arm_contacts > 0 runs, >= 3 frames
  "fixture_motion": [ {"joint", "start", "end", "delta"} ],       # fixture_qpos changes > 1e-3, if any
  "stage_frames": {"reached", "grasped", "lifted", "transported", "placed"},   # -1 when never (episode_progress.py rules)
  "final": {"target_in_goal": bool, "target_resting": bool, "target_dist_to_goal_xy_m": float|null,
            "target_z_m": float, "target_moved_m": float},

  "failure_mode": one of
      "never_reached"      # no gripper contact with target, no wrong-object contact
      "wrong_object"       # wrong-object contact or grasp before any target contact
      "missed_grasp"       # target contacted, never a hold (or every hold ended without ever lifting the object)
      "drop_transport"     # the last hold ended in a drop while lifted/transported, never placed
      "release_miss"       # the last hold ended in a release outside the goal (rim, table, wrong region), never placed
      "hold_no_release"    # held at episode end (last hold ends within 3 frames of the end), never released; whatever
                           # happened before (r1 blamed the last prior drop when the arm was still moving at timeout)
      "stall_after_grasp"  # held at end, no motion (< 2 mm/frame) for >= 40 frames before timeout, far from the goal
      "collision"          # arm contact >= 10 frames that precedes the first other error
      "other",
  "cause": OOPSIE cause implied by failure_mode
      (never_reached->reaching, wrong_object->sequencing_semantic, missed_grasp->grasp, drop_transport->grasp,
       release_miss->manipulation, hold_no_release->manipulation, stall_after_grasp->manipulation,
       collision->collision, other->unclear),
  "decisive_chunk": int|null,      # chunk of the decisive event:
      # drop_transport -> chunk of the LAST drop that is not followed by a later successful hold;
      # release_miss -> chunk of the last release; wrong_object -> chunk of the first wrong-object contact;
      # missed_grasp -> chunk of the first close-on-nothing (cmd CLOSE, aperture < 0.8 cm, no hold) after contact;
      # hold_no_release / stall_after_grasp -> chunk where motion stops (first of the final idle run, >= 10 frames);
      #     null when the arm is still moving with the object at timeout (no such chunk; r3: the chunk labels still
      #     come from the events, see below);
      # never_reached -> null (no localised event); collision -> chunk of the first collision run.
  "chunk_labels": [ {"chunk", "allowed": [...], "primary": "<label>", "rule": "<rule id>", "scorable": bool}, ... ]
      # allowed sets (a prediction is correct if it is IN the set):
      #   before decisive chunk, stage advancing (contact/hold/lift/transport newly reached in or after this
      #     chunk, or eef distance to target decreasing by >= 2 cm over the chunk while empty) -> {progress}
      #   before decisive chunk, idle (eef speed < 2 mm/frame all chunk) -> {neutral}
      #   before decisive chunk, otherwise -> {progress, neutral}            (rule "pre_other")
      #   decisive chunk -> {failure_inducing}
      #   chunks of other drop (incl. slip) / wrong-object grasp / close-on-nothing events -> {failure_inducing}
      #     (post_slip_closure runs are not events: the error stays in the drop's chunk)
      #   chunk with a grasp event that follows an earlier drop/miss -> {recovery}
      #   after decisive chunk, target held (any frame of the chunk inside a hold, no event in the chunk)
      #     -> {progress, recovery, neutral, aftermath}   (rule "post_held_unscorable": the oracle cannot judge a
      #        late carry; scorable in the sense that failure_inducing fails)
      #   after decisive chunk, target still within 25 cm of eef and >= 40 frames remaining -> {neutral, aftermath, recovery}
      #   after decisive chunk, otherwise -> {aftermath, neutral}
      #   decisive null but events known (r3: hold still moving at timeout; "other" with an unresolved multi-target /
      #     fixture-atom release): the pre-decisive rules over the whole episode (drop/slip/close-on-nothing/wrong grasp
      #     -> {failure_inducing}, re-grasp after an error -> {recovery}, stage advance -> {progress}, idle ->
      #     {neutral}, otherwise {progress, neutral}); chunks during the final hold that are neither an advance nor
      #     idle -> {progress, neutral} (rule "final_hold_active", primary progress)
      #   never_reached episodes: all chunks -> {failure_inducing, neutral, progress}  (unscorable, rule "unlocalised");
      #     episodes without usable events (missed_grasp with neither a hold nor a closure, "other" because the
      #     grasped flag missed an airborne hold, fixture-only tasks): all five labels, rule "unlocalised_<mode>",
      #     unscorable
}
```

Rules are deliberately conservative: where the oracle cannot decide between two labels the allowed set contains
both, so "correct" never depends on a judgment the oracle cannot make.

**Successful episodes** (`"success": true`, `failure_mode: "success"`) get the same record; they are not scored by the
benchmark but are the bulk of the training labels (see below). Their chunk labels are the pre-decisive rules with the
outcome known: a stage advance (`advance_*`, including `placed` = the chunk whose action first satisfies the success
predicate) or a carry towards the goal -> {progress}; idle -> {neutral}; otherwise {progress, neutral} (`pre_other`).
A drop / close-on-nothing (away from fixtures) / wrong grasp that is followed by a later grasp of a task object is a
recovered error ({failure_inducing}, `other_event`) and that grasp is {recovery} (`regrasp`), with {progress,
recovery, neutral} (`pre_recovering`) in between; the first recovered error is the episode's `decisive_chunk` and gives
the cause (drop, close_on_nothing -> grasp; wrong_grasp -> sequencing_semantic), otherwise `decisive_chunk` is null and
the cause `unclear`. The release that lets go of a task object for good is its placement ({progress},
`place_release`); a drop never followed by a re-grasp cannot be told from a placement ({progress, neutral},
`drop_final`); putting a wrongly grasped object back down is {recovery, neutral, progress} (`wrong_release`). Chunks
starting after the success frame -> {neutral, aftermath} (`post_success`). In two-object tasks lift/transport credit
follows whichever task object is held and approach credit goes towards the next object grasped.

**Training export** `bench/oracle_labels.py --datasets ...` -> `$FTL_PROJ/bench/oracle_labels.parquet` (one row per
frame: label = the chunk's primary label, `allowed` "|"-joined, q = 1.0 / 0.5 / 0.25 for allowed sets of size 1 / 2 /
3+, 0.0 for `unlocalised*`, landmarks `decisive_error_chunk` = decisive, `failure_onset_chunk` = first
{failure_inducing} chunk else decisive, `visible_failure_chunk` = decisive, `recoverable_until_chunk` null until the
recovery-branching oracle fills it, `event_type_in_chunk`, `held`, `source` "oracle_r3") and
`oracle_episodes.parquet` (one row per episode).

## 2. Episode set: `bench/episodes.json`

`bench/select_episodes.py` builds references for every failure in the listed dataset families, then picks 50
episodes stratified by failure_mode (target: at least 5 per mode where available, remainder proportional),
spread over suites and tasks, deterministic seed 0. Excludes episodes listed in `scripts/analysis/exclusions.json`.
Also writes `bench/episodes_dev.json` (a disjoint 20-episode set for prompt iteration) so the 50 stay held out.

## 3. Prediction per (method, episode): `bench/predictions/<method>/<dataset>/episode_XXXXXX.json`

Every method adapter writes this normalized record, whatever it does internally:

```
{
  "method": "<name>", "method_config": {...}, "dataset", "episode_index",
  "held_obs": [ {"frame", "state": "held"|"empty"|"uncertain", "object": "<slot or null>"} ],  # every frame the method judged
  "events": [ {"type": "grasp"|"release"|"drop", "object", "last_before", "first_after"} ],
  "held_object": "<slot or null>",             # the object the method believes was held (null if none)
  "chunk_labels": [ "<label>" | null, ... ],    # length n_chunks; null = abstain
  "chunk_q": [float, ...],
  "decisive_chunk": int|null, "cause": "<cause>"|null,
  "n_model_calls", "wall_s", "peak_mem_gb", "raw_dir": "<where raw responses live>"
}
```

## 4. Scoring: `bench/score.py --methods a b c` -> `outputs/bench/scoreboard.md` + `scoreboard.json`

Per episode and method, levels (skip a level when the reference marks it not applicable). Since r2 everything that
counts is at annotation granularity (10-frame chunks); the frame-level held_state check is kept as a diagnostic.

| level | in overall | pass condition |
|---|---|---|
| held_state | no (diagnostic) | every judged frame whose reference state is not ambiguous matches (uncertain counts as wrong); also report accuracy |
| events | yes | every reference grasp/drop/release event is matched one-to-one by a predicted event of the same type with abs(chunk(pred.last_before) - ref.chunk) <= 1 (maximum matching); no unmatched predicted events |
| held_object | yes | equals the reference object of the longest held run (skipped if no held run) |
| chunk_labels | yes | every chunk with a scorable rule has predicted label in the allowed set (abstain = fail); report accuracy |
| chunk_labels_1off | no (diagnostic) | at most one scorable chunk outside its allowed set |
| decisive | yes | predicted decisive_chunk within +-1 of reference (skipped when reference null) |
| cause | yes | equal |
| episode ("overall") | | events, held_object, chunk_labels, decisive and cause all pass (where applicable) |
| semantic (column) | | chunk_labels, decisive and cause all pass |

Scoreboard: per method, percentage of episodes passing each level, semantic and overall, broken down by failure_mode,
plus mean calls and seconds per episode. A per-episode table lists which overall level failed first, so failures can
be inspected with `bench/inspect_episode.py <method> <dataset> <episode>` (side-by-side reference vs prediction,
links to the frames). `score.py --episodes ds:ep ...` scores an explicit list instead of a set.

## 5. Loop

1. Build references and the 50 + 20 episode sets.
2. Run every registered method on the 20-episode dev set; score; inspect the first failing level per episode.
3. Implement an improvement (new method name, never edit a scored method in place), rerun on dev, compare.
4. Only methods that pass >= 90 % of dev episodes are run on the 50 held-out episodes.
5. Stop when a method passes 50/50, or when the remaining failures are all reference ambiguities (then fix the
   reference rules, bump `reference_version`, and rescore everything).

Registered methods (initial):

| name | what it is |
|---|---|
| `whole_p8` | production annotate.py, prompt p8, K=5, identification stage, 1.5x tiles |
| `event_first_v1` | run_segmentation_loop.py protocol (two scans, refinement, two chunk-label passes) |
| `event_first_batched` | same protocol, but held/empty judged with batched single-frame calls (throughput) |
| further variants | added by the loop, one change each |

## 6. Method adapter interface (so methods can be added without touching the harness)

`scripts/annotate/bench/methods/<name>.py` exposes

```python
CONFIG = {...}                      # everything that defines the method; stored in the prediction as method_config
def run(ep, backend, workdir, cfg=CONFIG) -> dict   # returns the normalized prediction (section 3) minus
                                                     # method/dataset/episode_index/wall_s, which the harness fills in
```

`ep` is `common.Episode`, `backend` is a shared `backend_qwen.QwenBackend` (loaded ONCE per harness run),
`workdir` is `$FTL_PROJ/bench/raw/<method>/<dataset>/episode_XXXXXX/` where the adapter must cache every raw
model response keyed by an input hash (so a rerun is free) and may write anything else. Adapters never read
`priv.*` columns and never read the reference files. `bench/methods/__init__.py` holds
`REGISTRY = {"whole_p8": ..., "event_first_v1": ..., "event_first_batched": ...}`.

The harness `bench/run_method.py --method NAME --set dev|heldout|all [--episodes ds:ep ...] [--limit N] [--overwrite]`
iterates the episode set, skips existing predictions, calls the adapter, fills in wall_s / n_model_calls (from
a call counter wrapped around the backend), writes the prediction, and appends one line per episode to
`$FTL_PROJ/logs/bench_<method>.log`. Exactly one GPU process at a time on this machine: the harness refuses
to start if `pgrep -f "run_method.py|annotate.py|segmentation_lab.py"` finds another instance.

Backend addition for throughput: `QwenBackend.generate_many(system, contents, temperature=0.0, max_new_tokens=..., batch=8)`
runs several independent single-image prompts as one left-padded batch (used by the held/empty scans: 57 calls of
~730 tokens become ~8 batched forward passes).

## Changelog

**r3 (slips and event-derived labels for episodes without a decisive chunk).** Two problems with r2. (1) A review video
of full_shift8__t1 ep 3 showed a 7-frame hold (frames 150-156: both pads in contact, grasped flag on, the cream cheese
lifted from 0.4 to 1.6 cm and left the table at 156, contact lost at 157 with the command still CLOSE, aperture
collapsing to 0.1 cm) that r2's HOLD_MIN_FRAMES = 8 demoted to "ambiguous" with no event; the close-on-nothing detector
then fired at frame 160 and put the error in chunk 16 instead of 15. `bench/count_short_holds.py` found an isolated
3-7 frame target hold demoted this way in 329/2080 episodes (173 failures: 70 missed_grasp, 32 release_miss, 27
hold_no_release, 16 drop_transport, ...). r3 keeps a debounced hold of any length when it is a slip (the object was
airborne at some frame of it, or it ended with the command still CLOSE and the aperture fell below 0.8 cm within 10
frames); the 8-frame minimum now only removes holds that neither lift nor end in a collapse (brushes, finger pushes).
Gap merging is unchanged, and so is the end-event type (drop if the command is CLOSE at the transition, release
otherwise). A close-on-nothing run that begins within 12 frames after a drop is the same failed attempt: it is
recorded under `post_slip_closure` and is not a second error, so the drop's chunk is the decisive / other_event chunk.
shift8 t1 ep 3 now reads grasp c4 / drop c5 / grasp c9 / drop c11 / grasp c15 (f150) / drop c15 (f156-157) / grasp
c20, with no separate error in chunk 16. (2) Episodes whose last hold reaches the episode end while the arm is still
moving (hold_no_release, reason `active_hold*_no_idle`, decisive null) had every chunk labelled
`unlocalised_hold_no_release` with all five labels, so the whole episode was unscorable and the training export gave it
q = 0 everywhere although the events were known (ep 3 has three drops and three re-grasps). r3 keeps decisive_chunk
null but labels the chunks from the events exactly as for other failures (drops / slips / wrong grasps /
close-on-nothing -> {failure_inducing}, re-grasps after an error -> {recovery}, stage advances -> {progress}, idle ->
{neutral}, otherwise {progress, neutral}; chunks during the final hold that are neither an advance nor idle are
`final_hold_active`, {progress, neutral}, primary progress). The same applies to "other" episodes with an unresolved
multi-target / fixture-atom release (events known, the last release ambiguous -> `other_release`). The unscorable
rule remains for never_reached and for episodes without usable events (missed_grasp with neither hold nor closure,
"other" because the grasped flag missed an airborne hold, fixture-only tasks). The dev and held-out episode sets were
not re-drawn (`select_episodes.py` not rerun). Corpus effect: see `outputs/bench/r2_to_r3_changes.md`.

**r2 (annotation granularity).** r1 emitted an event for every both-finger contact of >= 3 frames and matched events
at +-3 frames, although the benchmark scores annotations (10-frame chunk labels, decisive chunk, cause) and neither the
visual nor the telemetry detector can reproduce a 3-frame contact. Inspection of the dev-set failures showed that r1
"held" included pushing a bowl or plate with the fingertips (aperture 0.3 or 4.0 cm), that the 2 ambiguous transition
frames at the very end of an episode made a held-to-timeout episode look like it ended with a release, and that a
long final carry after earlier drops (full_shift8__t1 ep 3: object held frames 203-277 of 280) was classified as a
"timeout while moving" drop_transport with the tail chunks labelled aftermath while the object was in the gripper. r2
therefore: merges holds separated by <= 4 frames and only counts holds of >= 8 frames (shorter ones stay in held_runs
as ambiguous and produce no event); treats a hold ending within 3 frames of the episode end as held at end, which always
takes the hold_no_release / stall_after_grasp branch (decisive null when the arm never idles); gives every post-decisive
chunk during which the target is held the allowed set {progress, recovery, neutral, aftermath} ("post_held_unscorable");
matches events at chunk granularity (|chunk(pred.last_before) - ref.chunk| <= 1, one-to-one); makes held_state a
diagnostic level outside the episode pass; and adds the diagnostic chunk_labels_1off level. The dev and held-out
episode sets were not re-drawn.

## Status 2026-09-08 (dev set, reference r2)

| method | what it is | events | held_object | chunk_labels (1-off) | decisive | cause | overall |
|---|---|---|---|---|---|---|---|
| whole_p8 | production annotate.py, one diagnosis prompt, K=5 | 25 % | 47 % | 17 % (17 %) | 20 % | 40 % | 1/20 |
| event_first_batched | lab protocol: VLM held/empty scans + chunk passes | 25 % | 53 % | 0 % (0 %) | 0 % | 0 % | 0/20 |
| event_first_v2 | + deterministic label completion, batched chunk passes | 25 % | 53 % | 17 % (28 %) | 33 % | 25 % | 0/20 |
| telem_v3 | telemetry holds (settle test) + VLM identity + completion rules | **55 %** | 47 % | 28 % (39 %) | 33 % | **60 %** | **3/20** |
| telem_v4nv / telem_v4 | sweep-tuned telemetry thresholds, +/- VLM veto | 35 % / 30 % | 47 % / 20 % | 17 % / 22 % | 20 % / 27 % | 55 % / 35 % | 1 / 2 of 20 |
| telem_v4s | settle thresholds + VLM veto + slot-named identification | 25 % | 0 % | 17 % | 27 % | 25 % | 1/20 |
| fused_v4 | CLOSE-command runs verified by a 2-of-3 VLM vote | 25 % | 13 % | 17 % (33 %) | 20 % | 25 % | 0/20 |
| telem_v3c | telem_v3 + VLM chunk passes (393 s/episode) | 55 % | 47 % | 22 % (33 %) | 33 % | 60 % | 3/20 (identical passes to telem_v3: the VLM chunk pass adds nothing over the rules) |

What the loop established:

1. **No method is near 100 %.** The best (telem_v3) passes 3 of 20 dev episodes; the target is 50 of 50.
2. **The bottleneck is event detection, not labelling.** When the events are right, the v2 completion rules put the
   chunk labels within one chunk of the allowed sets (chunk_labels_1off 33-39 %), and decisive/cause follow.
3. **The Qwen3-VL-8B single-frame held/empty judgment is not usable as a gate.** As a scan it is wrong on up to 76 %
   of frames (flat boxes read as empty, gripper housing as held); as a veto it removes true holds (telem_v4s:
   held_object 0/15 because nearly every telemetry hold was vetoed unanimously); as a 2-of-3 vote on command runs it
   rejects real grasps (fused_v4). Single close-ups of cans are read correctly (probe_vlm.py), boxes and bottles are not.
4. **Gripper telemetry alone is the most reliable non-privileged event source but caps out around 55 % of
   episodes**: aperture while held overlaps closed-on-nothing (thin objects at 0.5 cm, wide cartons at 3.4-4.0 cm),
   and the reference's "held" (both-finger contact) includes pushes with closed fingers. Sweeps over thresholds move
   corpus-wide events between 26 % and 35 %; the settle test helps on dev.
5. **Identification** fails when the glossary display word differs from the slot name ("book" vs black_book_1,
   fixed in telem_v4 by listing slot names) and when two similar objects exist (milk vs salad dressing).
6. **Reference definitions matter as much as the model**: r1 emitted an event for every 3-frame contact and
   mis-classified held-to-timeout episodes; r2 (holds >= 8 frames, chunk-level event matching, held_state
   diagnostic) changed 82/642 failure modes and made the scoreboard interpretable.

Recommended next iterations, in order of expected value:

- A stronger VLM for the two visual sub-tasks (held/empty at 2x, identity): Qwen3-VL-32B (AWQ) or an API model, run
  through the same adapters; the benchmark now measures exactly the two quantities that would change.
- An object-aware verification question ("is the light blue box between the finger pads?") instead of the
  object-blind held/empty prompt, since identity is known from the task.
- Telemetry + vision agreement as *confidence*, not as a gate: emit events from telemetry, attach q from VLM
  agreement, and let the learner down-weight disputed events (this matches the proposal's use of q_t).
- Score the 50-episode held-out set only once a method passes >= 90 % of dev; none qualifies yet.

## Oracle-conditioned ablation (2026-09-08, dev set): can the VLM do the semantic part when perception is solved?

All four methods receive the reference's events and held object as verified facts (`oracle_*` methods, marked
`oracle_conditioned`; never production annotators).

| method | VLM asked for | chunk labels (within 1) | decisive | cause | overall |
|---|---|---|---|---|---|
| oracle_rules | nothing (v2 completion rules on the oracle events) | 44 % (67 %) | 67 % | 80 % | 8/20 |
| oracle_whole | full diagnosis JSON, events written into the prompt as facts | 28 % (28 %) | 60 % | 70 % | 6/20 |
| oracle_chunk | per-chunk label with the true tracker state (k=3) | 17 % (17 %) | rules | rules | 4/20 |
| oracle_moment | decisive chunk, cause and a sentence from a window around the true decisive frame | rules | trivial (window = tolerance) | 55 % | 5/20 |

Conclusion: given perfect events, every VLM output is worse than the deterministic rules derived from those same
events; the per-chunk question is the worst (it calls approach chunks neutral and post-error chunks
failure_inducing). The model's one good output at the localized moment is the free-text description ("closed the
gripper around the chocolate pudding box instead of the butter", "attempted to grasp the tomato sauce but closed
the gripper on empty space"), while its category for the same moment is often wrong (grasp for a wrong-object
episode). The rules' own ceiling (8/20) is set by one-chunk disagreements with the reference tail rules, which are
definitional and fixable on the oracle side.

Decision: simulation training labels come from the oracle (`docs/oracle_segmentation.md`); OopsieData labels from
human review of a stratified subset with telemetry pre-localization; the VLM is retained only for object identity
and one-sentence moment descriptions. The benchmark and its scoreboards are kept as the measured noise model for
the label-robustness experiment (proposal H6).
