# Running the simulations on DTU HPC

## 1. Save W&B variables globally

Open:

```bash
https://wandb.ai/authorize
```

Then copy the API key and keep it secret. On the DTU login node, run:

```bash
cat >> ~/.bashrc <<'EOF'
export WANDB_API_KEY="paste_your_key_here"
export WANDB_PROJECT="mulle"
export WANDB_MODE="offline"
EOF
source ~/.bashrc
```

Check it is available:

```bash
echo "$WANDB_PROJECT"
test -n "$WANDB_API_KEY" && echo "WANDB_API_KEY is set"
```

W&B creates the `mulle` project automatically the first time a run is logged.

## 2. Provide Sage on HPC

The Dockerfile is for the local dev container. The LSF job does not build Docker on HPC.

If `sage` is already available:

```bash
which sage
```

If not, create an Apptainer/Singularity image once from the repo root:

```bash
module avail apptainer singularity
module load apptainer 2>/dev/null || module load singularity
apptainer pull sage.sif docker://sagemath/sagemath:latest
```

If your cluster uses `singularity` instead of `apptainer`, use:

```bash
singularity pull sage.sif docker://sagemath/sagemath:latest
```

The job script automatically uses `./sage.sif` if it exists. You can also point to a Sage executable manually:

```bash
export SAGE_CMD=/path/to/sage
```

Install W&B once for that Sage Python before submitting the array:

```bash
$SAGE_CMD -pip install --user wandb
$SAGE_CMD -python -c "import wandb; print(wandb.__version__)"
```

Do not install W&B inside each array task; many parallel `pip install` processes can fail on the shared home filesystem.

## 3. Smoke test before HPC

Run the same script in tiny mode:

```bash
apptainer exec sage.sif sage -python scripts/run_simulations.py --smoke-test --output-dir results/smoke
```

If plain `sage` exists instead, use:

```bash
sage -python scripts/run_simulations.py --smoke-test --output-dir results/smoke
```

If your cluster uses `singularity`, use:

```bash
singularity exec sage.sif sage -python scripts/run_simulations.py --smoke-test --output-dir results/smoke
```

It should create:

```text
results/smoke/smoke-test.json
results/smoke/smoke-test.csv
```

## 4. Submit the CPU LSF array job

From the repository root on DTU HPC:

```bash
bsub < scripts/submit_simulations_lsf.sh
```

The job runs one `(size, max_degree)` case per array task:

```bash
#BSUB -J "mulle-sim[1-400]"
#BSUB -q hpc
#BSUB -n 1
```

## 5. Monitor jobs

```bash
bjobs
```

## 6. Merge outputs

Each array task saves one part locally:

```text
results/parts/<run-name>-part-<index>.json
results/parts/<run-name>-part-<index>.csv
```

After all jobs finish, merge them:

```bash
python3 scripts/merge_simulation_parts.py --parts-dir results/parts --output-prefix results/merged
```

This creates the final files:

```text
results/merged.csv        normalized notebook-style table with complexity columns
results/merged.raw.csv    raw FACIT result rows
results/merged.json       raw rows, normalized rows, global fits, and missing part indices
```

LSF logs are written to:

```text
lsf_logs/<job-id>_<array-index>.out
lsf_logs/<job-id>_<array-index>.err
```

If W&B is online and authenticated, the same run is logged to the `mulle` project.
By default the LSF array uses `WANDB_MODE=offline` to avoid rate limits from 400 parallel tasks. Sync later with:

```bash
wandb sync results/wandb/wandb/*
```
