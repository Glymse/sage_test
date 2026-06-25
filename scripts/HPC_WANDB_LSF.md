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
EOF
source ~/.bashrc
```

Check it is available:

```bash
echo "$WANDB_PROJECT"
test -n "$WANDB_API_KEY" && echo "WANDB_API_KEY is set"
```

W&B creates the `mulle` project automatically the first time a run is logged.

## 2. Smoke test before HPC

Run the same script in tiny mode:

```bash
sage -python scripts/run_simulations.py --smoke-test --output-dir results/smoke
```

It should create:

```text
results/smoke/smoke-test.json
results/smoke/smoke-test.csv
```

## 3. Submit the V100 LSF job

From the repository root on DTU HPC:

```bash
bsub < scripts/submit_simulations_lsf.sh
```

The job requests:

```bash
#BSUB -q gpuv100
#BSUB -gpu "num=1:mode=exclusive_process"
```

## 4. Outputs

The script always saves results locally:

```text
results/<run-name>.json
results/<run-name>.csv
```

LSF logs are written to:

```text
lsf_logs/<job-id>.out
lsf_logs/<job-id>.err
```

If W&B is online and authenticated, the same run is logged to the `mulle` project.
