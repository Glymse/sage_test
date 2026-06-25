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

if [[ -z "${SAGE_CMD:-}" && -f "$PWD/sage.sif" ]]; then
  export SAGE_SIF="$PWD/sage.sif"
fi

if [[ -n "${SAGE_SIF:-}" ]]; then
  if command -v apptainer >/dev/null 2>&1; then
    run_sage() { apptainer exec "$SAGE_SIF" sage "$@"; }
  elif command -v singularity >/dev/null 2>&1; then
    run_sage() { singularity exec "$SAGE_SIF" sage "$@"; }
  else
    echo "SAGE_SIF is set, but neither apptainer nor singularity is available." >&2
    exit 127
  fi
elif [[ -n "${SAGE_CMD:-}" ]]; then
  run_sage() { "$SAGE_CMD" "$@"; }
elif command -v sage >/dev/null 2>&1; then
  run_sage() { sage "$@"; }
else
  echo "Could not find Sage." >&2
  echo "Either install/provide Sage and set SAGE_CMD=/path/to/sage, or create sage.sif with:" >&2
  echo "  apptainer pull sage.sif docker://sagemath/sagemath:latest" >&2
  exit 127
fi

run_sage -python -c "import wandb" || {
  echo "wandb is not installed for this Sage Python." >&2
  echo "Install it once on the login node with:" >&2
  echo "  \$SAGE_CMD -pip install --user wandb" >&2
  echo "or run without --wandb." >&2
  exit 1
}

run_sage -python scripts/run_simulations.py \
  --wandb \
  --wandb-project "$WANDB_PROJECT" \
  --run-name "mulle-${LSB_JOBID}" \
  --output-dir results/parts
