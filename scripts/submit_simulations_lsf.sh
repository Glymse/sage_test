#!/bin/bash
#BSUB -J mulle-simulations
#BSUB -q gpuv100
#BSUB -gpu "num=1"
#BSUB -n 1
#BSUB -R "rusage[mem=16GB]"
#BSUB -W 24:00
#BSUB -o lsf_logs/%J.out
#BSUB -e lsf_logs/%J.err

set -euo pipefail

cd "${LS_SUBCWD:-$PWD}"
mkdir -p results lsf_logs

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
  --output-dir results
