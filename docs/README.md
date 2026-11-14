# Documentation index

This repository covers labeling, distillation, and evaluation. See the
[cleanup scope and verification](repository_scope.md) for what was retained. New work uses
real OopsieData. The historical Sol V8 release and earlier prompt experiments
remain for provenance and reproduction. Dated run reports describe their original
state; local artifacts linked under `../outputs/` are absent from a fresh clone.

| Workflow | Documents |
| --- | --- |
| OopsieData teacher/student pipeline | [Setup and commands](oopsie_distillation.md) |
| Teacher identity and presentation labels | [Sol/Astra attribution audit](teacher_provenance_audit.md) |
| Latest prepared rich pilot | [Corral Astra V8.2](corral_astra_rich_failure_v8_2.md) |
| Rich failure prompt lineage | [V8.1](oopsie_rich_failure_v8_1.md), [500-episode batch](oopsie_rich_failure_v8_1_500_batch.md), [additional batch](oopsie_rich_failure_v8_1_additional_500_batch_v2.md) |
| Binary failure labeling | [Sol V8/V9 comparison](oopsie_sol_v8_v9_twelve.md), [V9.1 pilot](oopsie_binary_v9_1_twelve.md), [distillation experiment plan](oopsie_binary_distillation_experiments.md) |
| Distillation recipes | [Study](oopsie_distillation_recipe_study_v1.md), [local sequential run](oopsie_distillation_local_sequential_v1.md), [TACC replicates](oopsie_distillation_tacc_replicates_v2.md) |
| FLORA baseline | [TACC setup](flora_tacc.md), [dated results](flora_results.md), [preserved native evidence](experiments/flora/2026-10-26/README.md) |
| Historical simulator-derived distillation release | [Sol V8 download, masks, and reproduction](sol_v8_distillation_500.md) |
| Atomic annotation and human review | [V8 runbook](annotation_runbook_v8.md), [annotation guide](../scripts/annotate/README.md), [review pack](../REVIEW.md) |
| Offline annotation evaluation | [Metrics and references](annotation_evaluation.md), [H pipeline comparison](h_pipeline_evaluation_v1.md) |

Earlier labeling experiments preserve the development of the prompts. Their
schemas and datasets differ from the current rich/binary OopsieData protocols.
They are historical comparisons, not the default recipe for new work.

| Experiment | Documents |
| --- | --- |
| Input/prompt pilots | [API label pilot](api_label_pilot.md), [input ablation](api_input_ablation.md) |
| Frame selection | [Initial experiment](frame_selection_experiment.md), [prompt revision](frame_selection_prompt_revision.md), [full coverage](frame_selection_full_coverage.md), [semantic coverage](frame_selection_semantic_v2.md), [points/windows](frame_selection_windows_v1.md) |
| Historical four-state scheme | [Annotation scheme](annotation_scheme.md) |
| Taxonomy V1-V3 | [V1](taxonomy_pilot_v1.md), [V2](taxonomy_pilot_v2.md), [V3](taxonomy_pilot_v3.md) |
| Identity/progress rules V4-V7 | [Identity](taxonomy_identity_v4.md), [explicit instructions](taxonomy_explicit_v5.md), [progress](taxonomy_progress_v6.md), [approach](taxonomy_approach_v7.md) |
| Teacher comparisons and input budget | [Sol/Luna](taxonomy_luna_v8.md), [Sol/Astra](taxonomy_astra_v9.md), [Sol frame budget](sol_frame_budget_v10.md) |

Keep frozen requests, native answers, human notes, and source hashes. Readable
conversions of old answers are derived artifacts. Similarity and agreement scores
measure consistency, not independently established annotation accuracy.
