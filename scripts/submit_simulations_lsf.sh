#!/bin/bash
#BSUB -J "mulle-sim[1-400]"
#BSUB -q hpc
#BSUB -n 1
#BSUB -R "rusage[mem=8GB]"
#BSUB -W 04:00
#BSUB -o lsf_logs/%J_%I.out
#BSUB -e lsf_logs/%J_%I.err

set -euo pipefail

cd "${LS_SUBCWD:-$PWD}"
mkdir -p results/parts lsf_logs

: "${WANDB_API_KEY:?WANDB_API_KEY is not set. Add it to ~/.bashrc or export it before bsub.}"

export WANDB_PROJECT="${WANDB_PROJECT:-mulle}"
export WANDB_MODE="${WANDB_MODE:-online}"
export WANDB_DIR="$PWD/results/wandb"
mkdir -p "$WANDB_DIR"

module load sage

sage -python -c "import wandb" 2>/dev/null || sage -pip install --user wandb
sage -python scripts/run_simulations.py \
  --wandb \
  --wandb-project "$WANDB_PROJECT" \
  --run-name "mulle-${LSB_JOBID}" \
  --output-dir results/parts
