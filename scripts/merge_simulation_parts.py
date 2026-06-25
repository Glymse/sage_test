#!/usr/bin/env python3
"""Merge LSF array outputs from scripts/run_simulations.py."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


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


def main():
    parser = argparse.ArgumentParser(description="Merge simulation part JSON files.")
    parser.add_argument("--parts-dir", default="results/parts")
    parser.add_argument("--output-prefix", default="results/merged")
    args = parser.parse_args()

    parts_dir = Path(args.parts_dir)
    output_prefix = Path(args.output_prefix)

    summaries = []
    results = []
    normalized_results = []

    for path in sorted(parts_dir.glob("*.json")):
        with path.open("r", encoding="utf-8") as f:
            summary = json.load(f)

        summaries.append({
            "path": str(path),
            "config": summary.get("config", {}),
            "result_count": summary.get("result_count", 0),
        })
        results.extend(summary.get("results", []))
        normalized_results.extend(summary.get("normalized_results", []))

    merged = {
        "part_count": len(summaries),
        "result_count": len(results),
        "parts": summaries,
        "results": results,
        "normalized_results": normalized_results,
    }

    write_json(output_prefix.with_suffix(".json"), merged)
    write_csv(output_prefix.with_suffix(".csv"), results)

    print(f"Merged {len(summaries)} parts with {len(results)} result rows")
    print(f"Saved {output_prefix.with_suffix('.json')}")
    print(f"Saved {output_prefix.with_suffix('.csv')}")


if __name__ == "__main__":
    main()
