# Repository scope after cleanup

The maintained scope is teacher labeling, human review, vision-language student
distillation, and evaluation. New labeling/training/evaluation uses real OopsieData.

The cleanup removes the causal transformer representation learner, offline RL
and policy/reward baselines, simulation rollout recorders, simulator utilities,
collection schedules, simulator annotation benchmarks, and their research proposals
and guides. Removed local files were copied to a sibling backup outside the repo
before removal. Previously committed files remain available in Git history.

Retained material includes:

- OopsieData collection, versioned prompts/configurations, trace validation,
  Markdown review, SFT exports, Qwen recipes, job planning, and evaluation.
- Historical Gemma distillation and reusable recorded-dataset export helpers.
  The retired simulator-derived release package, its guide, and release-specific
  download/publication tools are archived locally rather than shared in this tree.
- Earlier prompt/labeling comparisons and native FLORA baseline evidence, including
  historical simulator integration outputs. These preserve provenance rather than
  authorize new simulator labeling or make the old corpus current.
- Human reference notes and frozen native evidence with original contents intact.

The historical release's recorded-video decoder now lives in
`../scripts/annotate/decode_recorded_episode.py`; the export no longer imports
simulator benchmark code. Frozen source fingerprints, archived release snapshots,
native evidence, and human notes are preserved. Git attributes preserve prompt,
configuration, and human-note bytes across clones as well.

`../scripts/check_offline.py` provides fixture-based CPU verification. The initial
cleanup checks passed 236 annotation tests, three additional decoder tests,
121 distillation tests under Linux/WSL, and 22 TACC tests. Six real Qwen
processor/model integration tests are excluded from this offline command.
Windows cannot run the full suite in the local environment because queue helpers
require Unix `fcntl` and Application Control blocks a PyTorch DLL. Linux/WSL
verification passed. No paid model calls, training jobs, GPU benchmarks, or cluster
submissions were made for this cleanup.

Source syntax, local documentation links, published code fingerprints, native
provenance bytes, and credential-pattern checks were also checked. Credentials,
raw recordings, generated videos, checkpoints, environments, and bulk run outputs
remain outside Git. Preserve ignored `outputs/` evidence when sharing source.
