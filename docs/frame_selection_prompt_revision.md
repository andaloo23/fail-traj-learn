# Specific-prompt rerun of A–F

The user authorized improving the prompts and rerunning the same experiment.
This is a new run under `outputs/frame_selection_prompt_v2`, not a continuation
or overwrite of `outputs/frame_selection_v3`.

Execution completed: **24/24 calls**, producing 20 annotations and 4 frame selections,
with no timeouts or retries. Estimated generation cost is **$0.840297** ($0.531671
OpenAI, $0.308626 Gemini). A separate conservative token-count allowance of $0.600806
brings this run's tracked estimate plus allowance to $1.441103, below $4.16.
See `outputs/frame_selection_prompt_v2/RESULTS.md` for per-condition costs and checks.
One Gemini R003_B interval uses a closed endpoint instead of the requested half-open
notation. The viewer preserves the written notation, plots its literal inclusive end,
and flags it for human review; the model answer is not rewritten or retried.

## Prompt changes

The three Markdown prompts are in `scripts/annotate/prompts/identity_v2/`:

- `progress_failure.md`: explicitly distinguishes the instructed object from the
  manipulated object, requires a concise identity check with cited visual evidence,
  and disallows reading the object's identity from the task or telemetry. It checks
  physical transitions separately from task relevance, distinguishes proximity from
  possession, and avoids backdating failure to an ambiguous initial approach.
- `select_frames.md`: asks Gemini to retain distinguishing visual evidence, including
  readable markings where actually visible, as well as before/after interaction views
  and temporal coverage. Output remains only K frame indices, with no semantic prose.
- `annotate_frame_subset.md`: emphasizes correct use of time gaps, identity evidence
  across views, and uncertainty about unobserved events. C, D, and F share this exact
  note plus the common guide; A and B share the common guide alone.

Prompts contain no episode-specific answers, object identities, ground-truth ranges,
human labeled examples, prior model answers, or privileged simulator facts. They ask
for supported match, mismatch, or unresolved identity rather than assuming an error.
Labels remain independent progress/failure intervals with uncertainty and no neutral
or recovery class. A new identity-check output section precedes the same segment
sections, which retain explicit `[start, end)` frame intervals for viewer timelines.

## What stays fixed

All four source episodes R001–R004, their JPEG bytes, 4 FPS candidate pools, cameras,
resolution, telemetry, uniform selections, selection budgets and anchors are copied
from the frozen earlier experiment. The model IDs, low reasoning, Gemini LOW media
resolution, GPT high image detail, 4,096-token output budget and API style are unchanged.
All 24 cells are fresh independent generation calls, one per episode/condition.
F uses the new E output with no semantic descriptions passed downstream. No extra
evidence pass, multi-turn audit, or human examples are added in this rerun.

The client transport timeout is increased from 120 to 600 seconds for both providers
to reduce premature abandonment of a valid request. This changes waiting behavior,
not model input or output budgets. Automatic retries remain disabled. Static inputs
are preflighted before generation; dynamic F inputs are preflighted after selection.
Failed calls stop the run and retain their reservations, including unknown costs.

The output sanitizer now recognizes key-shaped tokens instead of matching `sk-`
inside ordinary words such as `task-inconsistent`. Actual credentials are still
redacted. Previous frozen outputs are preserved; no previous annotations are repaired.

## Cost and review

Reserve up to $0.20 per GPT call (16 calls, $3.20) and $0.12 per Gemini call
(8 calls, $0.96): **$4.16 for this new run**, including per-call token-count allowances.
The token guard remains 40,000. Actual preflight counts must also fit each request's
reservation at maximum output and worst-case input/cache-write pricing.
Per-call raw usage, Markdown answers, hashes, latency and costs are retained.
This run's costs are separate from previous costs; `cost_summary.json` additionally
reports cumulative known generation estimates and the previous unknown timeout.

Compare old and new A–D on identical visual inputs. E and F both have revised prompts;
F's selected frames can consequently change. Old/new F differences cannot be
attributed solely to the annotator prompt. D versus F within this rerun still matches
the downstream prompt, model, telemetry, image encoding and retained frame quantity.

The revision was informed by inspection of these development episodes. It is not a
held-out generalization test. One call per cell also leaves model variability
uncontrolled. Review identity decisions, task relevance, grasp/release evidence and
boundary uncertainty against human-reviewed videos; do not compute simulator-based
quality scores or treat a model as the reference.

Run status: `outputs/frame_selection_prompt_v2/REPORT.md`.
Runner: `scripts/annotate/api_frame_selection_prompt_v2.py`.
