# Annotation evaluation: correctness, timing, and description similarity

The current implementation evaluates the semantic-v2 API outputs and the matched-
budget U/P/W experiment. No simulator labels, withdrawn event scores, or original R
model annotations are treated as ground truth. No paid API calls are made.

## Two distinct modes

- `agreement`: compare model outputs, explicitly reporting agreement, not accuracy.
  Models can agree on an incorrect object or hallucinated event. Provisional model
  labels remain provisional; their review-required fraction is reported.
- `score`: compare against independently reviewed, explicitly approved human
  references. Draft, mismatched-source, malformed or unresolved references are not
  scored. The evaluator cannot authenticate who performed a review: approval must
  reflect an actual human review, not just an edited status field.

`annotations/human_reference_v1/R001.md` through R004 are blank draft templates,
not prefilled model predictions. Review the full original video and use the current
Markdown annotation scheme. Fill Status, Reviewer and Reviewed at only after
completing and resolving the annotation. Source camera hashes bind the references
to the episodes. If an interval cannot be adjudicated, leave that episode pending;
this initial evaluator does not score partially verified human references.

## Metrics

1. **Frame-duration label correctness/agreement:** separate progress and failure
   precision, recall, F1 and IoU, plus joint four-state accuracy/agreement and a
   confusion matrix. A frame counts once per independent binary axis. The two labels
   are not forced into mutually exclusive progress versus failure classes.
2. **Failure reason classification:** per-type, frame-duration precision/recall/F1
   for missed_target, lost_control, wrong_action, collision, timeout and other.
   This measures reason coverage separately from prose similarity.
3. **Boundary matching:** one-to-one matching at 0.10, 0.25 and 0.50 seconds, maximizing
   matched count then minimizing timing error. Report precision/recall/F1, matched
   absolute timing error and unmatched counts. Episode endpoints do not count as
   detected transitions. Matched timing error alone would hide missed boundaries.
4. **Two temporal resolutions:** raw phase boundaries retain acquisition/transport/
   placement splits even if their binary labels match. Binary-state boundaries and
   segment IoU scores merge adjacent identical binary states, avoiding a penalty for
   legitimate semantic detail. One-to-one, label-consistent segment matching uses
   temporal IoU thresholds 0.25/0.50/0.75. This is a new reference-based implementation,
   not a revival of withdrawn simulator scores. Standard segmental overlap metrics
   motivate this distinction; see [Lea et al., CVPR 2017](https://openaccess.thecvf.com/content_cvpr_2017/papers/Lea_Temporal_Convolutional_Networks_CVPR_2017_paper.pdf).
5. **Description similarity:** local `sentence-transformers/all-MiniLM-L6-v2`
   embeddings, cosine similarity, weighted by the duration of each temporal
   intersection. A split/merge can map to several intersections; every covered frame
   is weighted once. Text consists of phase, description and failure reason, excluding
   generic instructions/confidence/frame lists. Also report text coverage and cosine
   conditional on matching binary states, with that subset's coverage. There is no
   global nearest-sentence search that could match the wrong time in the episode.
   This uses the [Sentence Transformers similarity approach](https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html)
   through [FastEmbed's local ONNX inference](https://qdrant.github.io/fastembed/Getting%20Started/).

Undefined metrics (e.g. failure F1 when neither annotation contains a failure) are
N/A, not zero or perfect. Counts are retained. Missing/structurally invalid API
outputs are listed as unavailable rather than silently repaired. Always report
successful-output coverage alongside scores; model failures must not disappear
from comparison denominators. Pairwise available episode sets can differ, so this
version reports per-episode rows and does not rank conditions with different samples.

## Semantic similarity is not correctness

Cosine similarity is not a calibrated probability or factuality score. Descriptions
can remain similar despite negation, wrong-object identity, different consequences,
or a missed brief failure. Do not average it into a single quality score. Human review
must separately check target identity, unsupported physical claims and missed failures.
Before setting acceptance thresholds, compare two human annotations and adjudicate
their disagreements; use that to establish reasonable boundary tolerances.

Four repeatedly inspected development episodes cannot establish generalization or
non-inferiority. Freeze the scheme and test additional held-out human-reviewed episodes
before concluding that Gemini+GPT preserves annotation quality. Compare quality with
selector-plus-annotator cost and request reliability. The JSON inventory contains
per-condition pipeline generation estimates; conservative allowances and unknown
charges remain in each original run's cost ledger.

## Run

The separate `.venv-eval` environment contains FastEmbed. Initial setup downloads
model weights; annotation text is embedded locally and not sent to a service.

```powershell
# Does not overwrite existing reference files.
.\.venv-eval\Scripts\python.exe scripts\annotate\evaluate_annotations.py prepare

# Available now: model agreement, including local semantic similarity.
.\.venv-eval\Scripts\python.exe scripts\annotate\evaluate_annotations.py agreement --embeddings

# After human references are genuinely reviewed and approved:
.\.venv-eval\Scripts\python.exe scripts\annotate\evaluate_annotations.py score --embeddings
```

Outputs: `outputs/annotation_evaluation_v1/agreement.md`, `.csv`, `.json`, and the
separate `score.*` artifacts. JSON includes full confusion matrices, per-type metrics,
boundary match counts, temporal text matches, unavailable cells and provenance.
`embedding_manifest.json` records package versions, weight/tokenizer hashes, the
token limit and chunking policy. Overlength descriptions are split by exact token
count, embedded, and combined by word-count-weighted mean with L2 normalization.
No long description is silently truncated. `requirements-annotation-eval.txt` records
the working environment. Core metrics run without embedding dependencies.
