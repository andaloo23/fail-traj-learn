# fail-traj-learn

Pipelines for labeling real robot videos and distilling failure annotations into
vision-language students. New labeling, distillation, and evaluation use **real
OopsieData**. Teacher annotations are proposals for human review, not ground truth.

Start with the [OopsieData pipeline](docs/oopsie_distillation.md). The
[documentation index](docs/README.md) separates versioned labeling protocols,
distillation recipes and evaluation.

| Task | Guide |
| --- | --- |
| Prepare, collect, review, and export OopsieData labels | [OopsieData pipeline](docs/oopsie_distillation.md) |
| Review the prepared Corral Astra pilot | [Rich failure V8.2](docs/corral_astra_rich_failure_v8_2.md) |
| Reproduce the Sol V8.1 collection | [500-episode collection](docs/oopsie_rich_failure_v8_1_500_batch.md) |
| Review binary segmentation protocols | [V9.1 twelve-episode pilot](docs/oopsie_binary_v9_1_twelve.md) |
| Inspect student recipes and evaluation | [Recipe study](docs/oopsie_distillation_recipe_study_v1.md), [local execution](docs/oopsie_distillation_local_sequential_v1.md), [TACC copies](docs/oopsie_distillation_tacc_replicates_v2.md) |
| Run the FLORA labeling/evaluation baseline | [FLORA runbook](docs/flora_tacc.md) |
| Review historical prompt comparisons | [Atomic annotation guide](scripts/annotate/README.md), [review pack](REVIEW.md) |

Existing run documents are dated records. Their statements about queued jobs,
approvals, and costs describe those runs, not a fresh authorization or current
service state. Review the concrete recipe/job plan with the user before starting
new training or submitting jobs. Repository cleanup does not start any jobs or
teacher calls.

Record the actual generating model from frozen requests and responses. Keep
model identity, prompt versions, and source hashes with each dataset. A display
name or video title does not change teacher provenance. Model agreement does not
make outputs from two different teachers interchangeable.

| Location | Contents |
| --- | --- |
| `scripts/distill/` | Teacher collection, trace validation, review, export, Qwen/Gemma SFT, scoring, and recipe orchestration |
| `scripts/annotate/` | Labeling prompts, prompt experiments, human review, annotation comparison, and historical V8 release tools |
| `scripts/analysis/` | Student/teacher evaluation, provenance audits, and annotated-video exports |
| `scripts/tacc/` | OopsieData staging, FLORA baseline, and distillation job templates |
| `configs/` | Versioned labeling and distillation recipes |
| `annotations/` | Markdown human reference notes |
| `docs/` | Workflow guides and preserved labeling/evaluation evidence |
| `outputs/` | Ignored local frozen runs, reviews, reports, media, and checkpoints |

Source, configurations, prompts, small provenance records, and human notes are
committed. Credentials, environments, recordings, generated videos, model weights,
and bulk run artifacts stay outside Git. A fresh clone needs the datasets and
frozen runs named by its chosen guide; links into `outputs/` refer to local evidence.
Retired release files and existing generated runs are preserved locally.

Create a Python environment and install dependencies for the workflow you need:

```bash
python -m venv .venv
# Activate .venv using your platform's activation command.
python -m pip install -r scripts/annotate/requirements-current-annotation.txt
python -m unittest discover -s scripts/annotate -p 'test_batch_trajectories.py'
```

For Qwen/GPU dependencies use the [OopsieData setup](docs/oopsie_distillation.md)
and `scripts/distill/requirements-oopsie.txt` or `requirements-recipes.txt`.
For CPU-only source checks and the Linux/WSL offline suite, see the
[script index](scripts/README.md). Tests use temporary fixtures; paid collection,
training, and cluster submission are separate commands.
