# Controlled frame-selection experiment

The specific-prompt rerun is documented in
[Prompt revision](frame_selection_prompt_revision.md), with separate artifacts in
`outputs/frame_selection_prompt_v2`. The viewer can switch between this original
run and that revision. The protocol below describes the original run.

Status: user authorized execution with cost tracking on 2026-10-01.
Implemented in `scripts/annotate/api_frame_selection.py`, with offline guard tests.
This supersedes the pending independent-only `api_input_ablation.py` matrix.
Frozen inputs, Markdown responses, usage and cost logs are saved under
`outputs/frame_selection_v1`; its `REPORT.md` records actual execution status.

The initial execution stopped after R001_A completed ($0.044356 estimated generation cost).
R001_B's token preflight returned 133,226, exceeding the frozen 40,000-token guard;
no Gemini generation was sent. See `outputs/frame_selection_v1/RUN_NOTES.md` for
the cost accounting, feasibility finding and required input revision. The planned
comparison remains incomplete, with no annotation-quality conclusions.

Latest execution: v3 resumed successfully after the input and Markdown-parser fixes,
then stopped on a transport timeout at R003_E. Sixteen cells completed (all A-F for
R001/R002, A-D for R003). Known generation estimate is $0.519260; the timed-out
request has unknown charges and retains its $0.12 reservation. See
`outputs/frame_selection_v3/RESULTS.md` for cumulative allowances and partial results.

## Resume revision (2026-10-01)

The user authorized investigating and resuming where possible. The explicit Gemini
`MEDIA_RESOLUTION_LOW` setting was accepted by Robotics ER 2's token-count endpoint.
For the same R001_B input it reduced the count from 133,226 to 38,264 tokens:
9,080 text tokens plus 29,184 image tokens. A two-image probe changed image tokens
from 2,178 to 512. These are observed endpoint counts, not inferred from dimensions.

Run v2 uses `scripts/annotate/api_frame_selection_v2.py` and writes to
`outputs/frame_selection_v2`. It preserves all image bytes, frames, prompts,
telemetry, GPT settings and selection budgets. Both Gemini B and E use explicit
low media resolution. A versus B therefore compares the named model/configuration
combinations; it is not a comparison at equal internal visual detail. D versus F
still isolates selection at matched downstream GPT settings and image quantity.
No claim of unchanged Gemini quality follows from reduced token allocation.

The completed R001_A is reused only after checking identical payload/evidence hashes.
All 19 remaining static inputs are counted before any new generation. The four
dynamic F inputs are counted after validated selection. Count requests include
Gemini's generation configuration, preventing a resolution mismatch. Every count
is reused for its exact hashed generation payload; no duplicate preflight is sent.

Total reservations including the prior blocked preflight and all three diagnostics
are $4.45, within the original $4.48 total envelope. Existing R001_A reserves $0.22;
the remaining 15 GPT cells reserve $0.20 each; 8 Gemini cells reserve $0.12 each;
prior blocked preflight/diagnostics reserve $0.27. These are bookkeeping allowances,
not observed charges. Each generation is blocked if the counted input at maximum
input/cache-write prices plus maximum output and its preflight allowance would
exceed that call's reservation. Actual provider estimates and historical allowances
are accumulated without double-counting R001_A. Provider reservations for the matrix
exclude the separate historical/diagnostic allowance; the total includes both.

Sources: [media resolution](https://ai.google.dev/gemini-api/docs/media-resolution),
[countTokens schema](https://ai.google.dev/api/tokens),
[generation configuration](https://ai.google.dev/api/generate-content),
[Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing), and
[GPT-6.1 Sol pricing](https://developers.openai.com/api/docs/models/gpt-6.1-sol).

### Markdown parser correction

The v2 run then stopped at R001_E because the local parser only accepted `-`
bullets, although the prompt requested Markdown bullets without restricting the
marker. Gemini returned a valid `*` list with exactly K indices and all anchors.
The v3 runner accepts CommonMark `-`, `*`, and `+` list markers. It still rejects
extra prose, invalid indices, missing anchors, duplicates, or an incorrect count.
This corrects parsing rather than repairing a model selection. The original answer
is preserved byte-for-byte, and no generation is repeated. All saved v2 preflights
and completed cells are reused after payload-hash checks. Current output is
`outputs/frame_selection_v3`; runner: `scripts/annotate/api_frame_selection_v3.py`.

## Question and scope

Does task-aware frame selection by Gemini preserve useful visual evidence for GPT
better than uniform sampling at the same number of frames? Can the complete
Gemini-selection-plus-GPT-annotation pipeline cost less than direct GPT annotation
without an unacceptable loss in human-reviewed quality?

Those are separate questions. Improved quality at the same downstream frame count
does not by itself establish lower end-to-end cost. We are testing frame selection,
not whether Gemini can emit better semantic labels to guide GPT.

All model answers use Markdown. JSON remains an internal API transport and logging
format only. Gemini selection is a Markdown list of source-frame indices; downstream
annotations are human-readable segment descriptions.

## Responsibilities and prompts

1. **Local preparation:** extract synchronized camera pairs from the recordings.
   Fix resolution, JPEG settings, timestamps and observable telemetry before calls.
2. **Gemini selector:** use `scripts/annotate/prompts/select_frames.md`. Receive the
   candidate camera pairs, task and telemetry. Return exactly K frame indices with
   mandatory anchors. Do not output progress/failure labels or alter pixels.
3. **Local selection:** validate indices, budget, uniqueness and anchors. Copy the
   corresponding original images byte-for-byte in chronological order. Invalid
   selection stops the pipeline; do not repair it, fill it, or ask the model again.
4. **GPT annotator:** start a fresh request containing only the selected images,
   their original timestamps, task, and the fixed observable telemetry. Prepend
   `scripts/annotate/prompts/annotate_frame_subset.md` to the unchanged common
   `scripts/annotate/prompts/progress_failure.md`. Never forward the selector's
   Markdown, reasoning, descriptions, category guesses, or provider identity.

Direct GPT and direct Gemini annotation use the same common annotation prompt.
The two-stage pipeline has two additional role-specific prompts: one for selection
and one for independent annotation from potentially irregular samples. The latter
is also applied to the matched GPT controls below, preventing prompt differences
from being mistaken for selection gains.

Gemini does not resize or compress video. Do these transformations deterministically
in local code if testing them later. Keep them fixed here. Native-video selection
would change what Gemini actually observes and is a separate later experiment;
this first selector sees explicit candidate frames so every permissible selection
can be checked against the actual input.

## Frozen candidate pool and equal input budgets

Use R001 through R004 from the existing development pack. Tasks are tomato sauce,
butter, orange juice and milk into a basket. No outcome, prior annotation or
simulator reference is used for selection. This is development data, not a new
held-out benchmark.

For each episode, form candidate pool C from every fifth source frame plus the
last frame: both cameras, 256x256, JPEG quality 90, original 20 FPS timebase.
This is a 4 FPS candidate pool, not the entire 20 FPS recording. Both full-input
annotators and the selector see the same pool. No claim about preservation relative
to full-frame inference follows from this comparison.

Set K = ceil(len(C) / 4):

| Episode | Candidate pairs | Retained pairs K | Images sent to reduced-input GPT |
|---|---:|---:|---:|
| R001 | 57 | 15 | 30 |
| R002 | 31 | 8 | 16 |
| R003 | 57 | 15 | 30 |
| R004 | 57 | 15 | 30 |

For the uniform control, choose pool positions
`floor(i * (N - 1) / (K - 1) + 0.5)` for i from 0 through K-1, then map to
source-frame indices. These positions are distinct for these N and K.

Mandatory anchors are the uniform control's selections at indices
`0, floor((K-1)/3), floor(2*(K-1)/3), K-1`. This includes both episode endpoints
and two interior coverage anchors. Gemini must retain those same four anchors and
choose the remaining K-4 frames from the same pool. This constrains both methods
to preserve coarse episode coverage while leaving the selector adaptive choices.

Every retained timestamp carries both camera images; Gemini cannot secretly obtain
more views than the control. Images have identical pixel dimensions and encoding.
Use the same 4 FPS telemetry sequence for every annotator, independently of image
selection. The experiment therefore reduces visual input only. Metadata uses the
same template and includes only the actually supplied frame indices. No arm names
or claims about the quality of the selection are shown to GPT.

## Comparison matrix

Apply every condition to the same four episodes, one fresh call per cell:

| Condition | Annotator and input | Prompt | Calls |
|---|---|---|---:|
| A | GPT, all candidate pairs | Common annotation prompt | 4 |
| B | Gemini, all candidate pairs | Same common prompt | 4 |
| C | GPT, all candidate pairs | Subset-handling note + common prompt | 4 |
| D | GPT, uniform K pairs | Same prompt as C | 4 |
| E | Gemini selector, all candidate pairs | Frame-selection prompt | 4 |
| F | GPT, Gemini-selected K pairs | Same prompt as C and D | 4 |

E feeds only the locally selected images into F. All other semantic annotations are
independent; A-D are not inputs to E or F. No examples or conversation history.
Fix model IDs, image detail, reasoning settings, output budgets and request style.
No automatic retries. Invalid/truncated outputs remain failed attempts, not silently
improved answers. Freeze the selector's output and selected-image hashes before F.

Interpret comparisons narrowly:

- **A versus B:** direct model comparison with the same task and evidence.
- **A versus C:** checks the effect of the additional input-handling instructions.
- **C versus D:** effect of uniform visual reduction with the prompt held fixed.
- **D versus F (primary):** learned versus uniform selection at equal K, camera
  count, resolution, telemetry and downstream prompt/settings.
- **C versus E+F:** full versus selected pipeline quality and total cost.

D versus F controls downstream visual quantity, not total compute: E is additional
compute. Report that cost explicitly. After this small screen, a deterministic
motion/telemetry selector is a useful stronger baseline to test whether an LLM is
needed. Random selection and repeated calls can also be added in a later approved
study. Do not infer a general benefit from one run on four episodes.

## Human evaluation and cost

Create human references from the original 20 FPS recordings before revealing model
outputs where possible. Review annotations in shuffled order with model/arm names
hidden. Separate missing evidence from interpretation errors. Track missed and false
failure/progress intervals, category mistakes, boundary uncertainty, unsupported
claims, and human correction effort. Inspect whether omitted frames hide real events.
Do not use the richer-input model or an unverified simulator signal as ground truth.

Agree on acceptable degradation before inspecting comparative outputs. Four
episodes can identify obvious losses and promising methods; they cannot establish
statistical non-inferiority. Confirm the chosen method on fresh human-reviewed
episodes with repeats before claiming preserved quality.

Report per-episode input/output/thinking tokens, wall time, payload size and cost.
Pipeline cost = Gemini selection + GPT reduced-input annotation (including both
preflights and any billed failed requests). Report downstream token reduction and
end-to-end cost reduction separately. Selection is economically useful only if its
own cost is less than the GPT input cost it saves, allowing for output-cost changes.

## Authorized spending envelope

24 generation requests: 16 OpenAI and 8 Gemini. Retain the reviewed runner limits:
40,000 counted input tokens and 4,096 combined output/reasoning tokens per call.
At the previously reviewed prices and conservative per-attempt reservations:

- OpenAI: 16 x $0.22 = **$3.52** maximum reserved.
- Gemini: 8 x $0.12 = **$0.96** maximum reserved.
- Total: **$4.48**, below the proposed $5 ceiling.

Keep exclusive attempt reservations, no retries, persistent run lock, input hashes,
an approved manifest hash, and the pricing-expiry check. A selector failure blocks
its downstream request; no fallback selection is silently substituted. The user
approved execution after reviewing this design. Stop the entire run on a failed
attempt. Generation estimates use returned usage; token-count preflight allowances
are tracked separately and are not asserted to be observed charges.

Prepare with `python scripts/annotate/api_frame_selection.py prepare`, inspect the
frozen manifest, then run with `run --approve-manifest-sha256 <manifest SHA256>`.
The runner refuses repeat attempts. `report` rebuilds cost and review artifacts
without making API calls.
