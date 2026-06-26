#!/usr/bin/env sage -python
"""Batch wrapper around the exact FACIT simulation code.

The algorithm and timing functions are loaded from
FACIT/notebooks/Simulations.ipynb. The WeakPopov baseline is imported from
FACIT/notebooks/Weakpopov.py through the FACIT notebook's own import line.

This file only adds CLI parsing, W&B logging, and JSON/CSV result saving.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import os
import platform
import socket
import sys
from datetime import UTC, datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FACIT_DIR = REPO_ROOT / "FACIT"
FACIT_NOTEBOOKS = FACIT_DIR / "notebooks"
FACIT_SIMULATIONS = FACIT_NOTEBOOKS / "Simulations.ipynb"


def parse_int_list(value):
    return tuple(int(part.strip()) for part in value.split(",") if part.strip())


def select_array_case(sizes, max_degrees, array_index):
    cases = [(n, d) for n in sizes for d in max_degrees]
    if array_index < 1 or array_index > len(cases):
        raise ValueError(f"array index {array_index} is outside 1..{len(cases)}")
    return cases[array_index - 1], len(cases)


def load_facit_namespace():
    sys.path.insert(0, str(FACIT_NOTEBOOKS))

    notebook = json.loads(FACIT_SIMULATIONS.read_text(encoding="utf-8"))
    namespace = {
        "__name__": "facit_simulations_runtime",
        "__file__": str(FACIT_SIMULATIONS),
    }

    for cell in notebook["cells"]:
        if cell.get("cell_type") != "code":
            continue

        source = "".join(cell.get("source", []))
        if not source.strip():
            continue

        tree = ast.parse(source, filename=str(FACIT_SIMULATIONS))
        kept_nodes = [
            node for node in tree.body
            if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef))
        ]

        if not kept_nodes:
            continue

        tree.body = kept_nodes
        ast.fix_missing_locations(tree)
        exec(compile(tree, str(FACIT_SIMULATIONS), "exec"), namespace)

    return namespace


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True, default=str)


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def maybe_init_wandb(args, config):
    if not args.wandb:
        return None

    try:
        import wandb
    except ImportError:
        print("wandb is not installed; continuing with local result files only.", file=sys.stderr, flush=True)
        return None

    return wandb.init(
        project=args.wandb_project,
        name=args.run_name,
        config=config,
        mode=args.wandb_mode,
        job_type="simulation",
    )


def log_results_to_wandb(wandb_run, results):
    if wandb_run is None:
        return

    for row in results:
        wandb_run.log({f"result/{key}": value for key, value in row.items()})


def main():
    parser = argparse.ArgumentParser(description="Run exact FACIT simulations with saved results.")
    parser.add_argument("--sizes", default="5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100,105,110,115,120,125,130")
    parser.add_argument("--max-degrees", default="10,20,30,40,50,60,70,80,90,100,110,120,130,140,150,160,170,180,190,200,210,220,230,240,250,260,270,280,290,300,310,320,330,340,350,360,370,380,390,400,410,420,430,440,450,460,470,480,490,500,510")
    parser.add_argument("--field-size", type=int, default=7)
    parser.add_argument("--density", type=float, default=0.9)
    parser.add_argument("--trials", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", default="results")
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--wandb", action="store_true", help="Log returned FACIT result rows to W&B.")
    parser.add_argument("--wandb-project", default=os.environ.get("WANDB_PROJECT", "mulle"))
    parser.add_argument("--wandb-mode", default=os.environ.get("WANDB_MODE", "online"))
    parser.add_argument("--smoke-test", action="store_true", help="Run a tiny FACIT-code smoke check.")
    parser.add_argument("--array-index", type=int, default=None, help="Run one 1-based grid case, for LSF arrays.")
    args = parser.parse_args()

    if args.smoke_test:
        args.sizes = "2,3"
        args.max_degrees = "2,3"
        args.trials = 1
        args.wandb = False
        args.run_name = args.run_name or "smoke-test"

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    args.run_name = args.run_name or f"simulations-{timestamp}"

    sizes = parse_int_list(args.sizes)
    max_degrees = parse_int_list(args.max_degrees)
    array_index = args.array_index

    if array_index is None and os.environ.get("LSB_JOBINDEX"):
        array_index = int(os.environ["LSB_JOBINDEX"])

    array_total = None
    selected_case = None
    if array_index is not None:
        selected_case, array_total = select_array_case(sizes, max_degrees, array_index)
        sizes = (selected_case[0],)
        max_degrees = (selected_case[1],)

    config = {
        "sizes": sizes,
        "max_degrees": max_degrees,
        "field_size": args.field_size,
        "density": args.density,
        "trials": args.trials,
        "seed": args.seed,
        "run_name": args.run_name,
        "host": socket.gethostname(),
        "python": sys.version,
        "platform": platform.platform(),
        "lsb_jobid": os.environ.get("LSB_JOBID"),
        "lsb_queue": os.environ.get("LSB_QUEUE"),
        "lsb_jobindex": os.environ.get("LSB_JOBINDEX"),
        "array_index": array_index,
        "array_total": array_total,
        "selected_case": selected_case,
        "facit_simulations": str(FACIT_SIMULATIONS),
    }

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = output_dir / args.run_name
    if array_index is not None:
        prefix = output_dir / f"{args.run_name}-part-{array_index:03d}"

    facit = load_facit_namespace()
    wandb_run = maybe_init_wandb(args, config)

    try:
        results = facit["run_simulations"](
            sizes=config["sizes"],
            max_degrees=config["max_degrees"],
            field_size=config["field_size"],
            density=config["density"],
            trials=config["trials"],
            seed=config["seed"],
        )

        normalized_results = facit["add_normalized_times"](results)
        fits = {}
        if len(results) >= 3:
            fits = {
                "WeakPopov": facit["fit_power_law_two_variables"](results, "WeakPopov"),
                "Alekhnovich": facit["fit_power_law_two_variables"](results, "Alekhnovich"),
            }

        summary = {
            "config": config,
            "result_count": len(results),
            "fits": fits,
            "results": results,
            "normalized_results": normalized_results,
        }

        json_path = prefix.with_suffix(".json")
        csv_path = prefix.with_suffix(".csv")
        write_json(json_path, summary)
        write_csv(csv_path, results)

        print(f"Saved JSON results to {json_path}", flush=True)
        print(f"Saved CSV results to {csv_path}", flush=True)

        log_results_to_wandb(wandb_run, results)
        if wandb_run is not None:
            wandb_run.summary["result_count"] = len(results)
            wandb_run.summary["json_result_path"] = str(json_path)
            wandb_run.summary["csv_result_path"] = str(csv_path)
            wandb_run.save(str(json_path))
            wandb_run.save(str(csv_path))

    finally:
        if wandb_run is not None:
            wandb_run.finish()


if __name__ == "__main__":
    main()
