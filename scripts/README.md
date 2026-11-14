# Labeling and distillation entry points

Run from the repository root. Use the dependency file and environment described
by each workflow guide. New work uses real OopsieData.

| Task | Entry point |
| --- | --- |
| Prepare/collect/review teacher traces | `distill/oopsie_pipeline.py`, `distill/oopsie.ps1` |
| Rich V8.1 collection | `distill/oopsie_bulk_v8_1.py`, `distill/oopsie_bulk_batch.py` |
| Fresh Corral Astra V8.2 pilot | `distill/corral_astra_v8_2.py` |
| Binary failure collection and review | `distill/binary_segments_v9.py` |
| Serve original-video review | `distill/review_oopsie_video.py`, `distill/serve_oopsie_review.py` |
| Train/evaluate Qwen students | `distill/qwen_oopsie_sft.py`, `distill/qwen_recipe_runner.py`, `distill/score_recipe_suite.py` |
| Prepare recipe/job plans | `distill/recipe_job_plan.py`, `distill/oopsie_full_jobs.py` |
| Historical Gemma distillation | `distill/data.py`, `distill/model.py`, `distill/train.py`, `distill/eval.py` |
| Evaluate and render student/teacher comparisons | `analysis/audit_completed_distillation_v1.py`, `analysis/export_qwen_development_review.py`, `analysis/export_teacher_joint_side_by_side.py` |
| Stage OopsieData/run FLORA | `tacc/prepare_oopsiedata.py`, `tacc/run_flora.py`, `tacc/*.sbatch` |
| Atomic annotation and human review | [Annotation tools](annotate/README.md), `annotate/human_annotator.py` |
| Recorded-dataset export helpers | `annotate/prepare_distillation_v8.py`, `annotate/export_distillation_v8.py` |

The historical V8 exporter retains recorded-video decoding in
`annotate/decode_recorded_episode.py` and original sampling corrections in
`analysis/exclusions.json`. These support release reproduction. New OopsieData
work uses `distill/oopsie_common.py`.

Use Linux/WSL with the recipe environment (including CPU PyTorch, NumPy,
Pillow, and PyAV) for the full offline suite. Some annotation evaluation tests
also need their optional runtime dependencies. Windows supports the annotation
and TACC scopes; Linux queue tests require Unix file locking (`fcntl`). No GPU benchmark, training, paid generation, publication,
or cluster job is launched by these commands:

```bash
python -m compileall -q scripts
python scripts/check_offline.py
```

Job templates and recovery helpers are explicit entry points. Confirm the concrete
recipe/job plan before starting new training or submitting jobs. Preserve native
requests, answers, and notes; new prompts and format changes use new run versions.

`scripts/check_offline.py` excludes the real Qwen processor/model integration
tests, disables model downloads and GPU visibility, and isolates each test scope
in a fresh interpreter. The legacy Gemma integration check is explicit-only in
`distill/check_legacy_eval_cpu.py`; use a scratch output tree for that check.
