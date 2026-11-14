# Sol frame reduction and adaptive inspection

The user requested pushing frame reduction and allowing Sol to request extra frames
at specific times. This development screen uses R001–R004, with the existing V7
Sol results as an untouched comparison. No Astra, Gemini, or Luna calls are used.

## Conditions

| Arm | Sampling | Pairs in a 280-frame episode |
|---|---|---:|
| Existing V7 | 4 Hz, reused without another call | 57 |
| 2 Hz | Every 10 source frames plus final | 29 |
| 1 Hz | Every 20 source frames plus final | 15 |
| 0.5 Hz | Every 40 source frames plus final | 8 |
| 0.25 Hz | Every 80 source frames plus final | 5 |
| Uniform maximum-budget control | Uniform over the original 4 Hz pool | 24 |
| Adaptive | Start at 0.5 Hz; up to two requests of eight new pairs each | 8–24 |

R002 is shorter: the adaptive seed has five pairs and the uniform control has 21.
Every pair includes external and wrist views. All image bytes are copied from V7;
no crops, resizing, new encoding, or unobserved simulator state are introduced.
Telemetry is supplied only for the selected timestamps, so reductions affect both
visual and telemetry density. All original evidence remains available for review.

The adaptive controller accepts exact source indices from the existing quarter-
second pool (plus final frame), checks uniqueness/availability/budget, and appends
the requested images and telemetry to the conversation. Sol can finalize without
requesting more, after one request, or after two. It can request before/after frames
around contact, release, identity ambiguity, or any other uncertainty. Invalid
requests stop that job without retries. This is an application-level JSON request/
reply protocol, not a native function-calling experiment. Assistant request text
and prior evidence are retained in subsequent turns; hidden reasoning is not replayed.

The uniform control matches the adaptive **maximum** unique-frame budget, not
necessarily its realized count or total tokens. Adaptive costs include every round,
including repeated input, reasoning, request output, final output, and reported
cache reads/writes. Caching is left implicit, matching the previous runs.

## Controls and accounting

- GPT-6.1 Sol, low reasoning, high image detail, 8192 output tokens.
- V7 taxonomy, progress rules, evidence requirements and JSON schema are preserved.
  The inaccurate fixed-4-Hz sentence is replaced by an explicit-frame-list
  description for every arm. Adaptive alone adds the request protocol.
- No V7 answers or human review labels enter requests. Uniform sampling is fixed
  before results; adaptive choices come only from the model's own observations.
- 24 episode/arm jobs; at most 32 generation calls; $16 reservation ceiling.
  Three independent jobs may run concurrently. Each adaptive chain is sequential.
- No automatic retries; exclusive per-call reservations prevent repeat sends.
  Returned raw answers, frame requests, costs and original V7 hashes are preserved.
- Source: `scripts/annotate/api_sol_frame_budget_v10.py`.
- Output: `outputs/sol_frame_budget_v10/`; report: `RESULTS.md` and `comparison.json`.

## Evaluation and review

The report compares four-state frame labels and contiguous per-category failure
bouts against V7. Bouts use one-to-one matching at temporal IoU >= 0.5. A physical
failure and a concurrent semantic failure count separately. The figures describe
agreement, not accuracy, and a stable segment count does not show event preservation.
V7's own labels can be wrong. These are four already inspected development episodes,
one generation per condition, with no held-out or repeat-run estimates.

The [viewer](http://127.0.0.1:8767/) retains original Sol on the left and each new
condition on the right. It shows pair counts, full pipeline generation costs,
clickable requested timestamps and their reasons. Choose left/right sampled evidence
separately: their frame sets differ. Human review should focus on object identity,
short grasp/collision/release failures, and whether sparse sampling changes earlier
approach labels or failure boundaries. Broader task types need subsequent validation.

## Completed development screen

All 24 annotations passed strict schema/evidence/coverage validation. Thirty
generation calls completed without retries or unknown charges. Total generation
estimate: $0.7052633; conservative preflight allowance: $0.381998. The original
four-episode V7 generation cost was $0.2088265 and was not incurred again.

| Condition | Four-episode generation cost | Savings versus V7 | V7 category bouts matched at IoU >= 0.5 |
|---|---:|---:|---:|
| V7 4 Hz | $0.2088 | reference | 5/5 by definition |
| 2 Hz | $0.1409 | 32.5% | 4/5 |
| 1 Hz | $0.1140 | 45.4% | 3/5 |
| 0.5 Hz | $0.0909 | 56.5% | 1/5 |
| 0.25 Hz | $0.0812 | 61.1% | 1/5 |
| Uniform maximum-budget control | $0.1440 | 31.0% | 4/5 |
| Adaptive | $0.1342 | 35.7% | 1/5 |

These five reference bouts are category-specific, not five independent failure
episodes. On R001, 0.5 Hz falsely claims TOMATO SAUCE text. Adaptive R001 also
claims TOMATO SAUCE after requesting wrist frame 185, whose visible inverted text
reads ORANGE JUICE (manually inspected). It did gather useful additional evidence
but failed to revise the identity. Its shortened manipulation interval also fails
the 0.5 IoU match against V7, despite detecting a release problem; an unmatched
bout therefore does not necessarily mean total omission.

The 2 Hz arm preserves four V7 bouts but omits the R004 collision label. The 1 Hz
arm additionally omits R001's manipulation label. Human review is needed to decide
whether these are genuine misses or changes to incorrect baseline judgments.

Adaptive used 19/12/20/14 pairs and 3/2/3/2 calls on R001/R002/R003/R004. Implicit
caching did work across appended conversation turns: 33,708 cached input tokens
in total. Its full pipeline is still only slightly cheaper than the 2 Hz arm,
while agreeing substantially less with V7. This does not establish an effective
adaptive policy. A next candidate is a fresh final pass over selected frames in
chronological order, without the earlier request conversation, to test whether
early interpretations or nonchronological arrivals affect the result. That
candidate has not been run and would change caching/cost behavior.

Sampler/controller tests, one-to-one matching checks, original V7 hash checks,
and headless viewer checks cover the 24 comparisons, exact selected-frame playback,
requested-frame seeking, full coverage, and retained historical comparisons.
