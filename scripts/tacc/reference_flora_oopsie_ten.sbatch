#!/bin/bash
# Separate ten-episode run; preserves the existing three-episode job.
# Whole H100 node at 6 SU/hour; eight-hour upper bound 48 SU.
#SBATCH --job-name=flora-oopsie-ten
#SBATCH --account=IRI26045
#SBATCH --partition=gpu-h100
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --time=08:00:00
#SBATCH --output=flora-oopsie-ten-%j.out
#SBATCH --error=flora-oopsie-ten-%j.err
set -euo pipefail
export FLORA_INPUTS_RELATIVE=outputs/oopsiedata_ten_reference_v1
export FLORA_AUDIT_RELATIVE=outputs/flora_oopsie_ten_audit_v1
export FLORA_RESULT_TAG=flora_oopsie_ten_reference
cd "${FLORA_REPO:-$SLURM_SUBMIT_DIR}"
bash scripts/tacc/reference_flora_oopsie.sbatch
