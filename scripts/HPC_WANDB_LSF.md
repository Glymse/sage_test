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

## 3. Submit the CPU LSF array job

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

## 4. Monitor jobs

```bash
bjobs
```

## 5. Merge outputs

Each array task saves one part locally:

```text
results/parts/<run-name>-part-<index>.json
results/parts/<run-name>-part-<index>.csv
```

After all jobs finish, merge them:

```bash
python3 scripts/merge_simulation_parts.py --parts-dir results/parts --output-prefix results/merged
```

LSF logs are written to:

```text
lsf_logs/<job-id>_<array-index>.out
lsf_logs/<job-id>_<array-index>.err
```

If W&B is online and authenticated, the same run is logged to the `mulle` project.
