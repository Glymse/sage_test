#!/usr/bin/env python3
"""Merge LSF array outputs from scripts/run_simulations.py."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


def loglog(d):
    return math.log(max(math.log(d), 1.000001))


def weakpopov_complexity_term(row):
    n = row["n"]
    d = row["max_degree"]
    r = row.get("r", 1)

    return n**2 * r * d**2


def alekhnovich_complexity_term(row):
    n = row["n"]
    d = row["max_degree"]

    if d <= 1:
        return n**2 * d

    return n**3 * d * (math.log(d)**2) * loglog(d) + n**2 * d


def add_normalized_times(results):
    normalized = []

    for row in results:
        weak_term = weakpopov_complexity_term(row)
        alek_term = alekhnovich_complexity_term(row)

        new_row = dict(row)
        new_row["WeakPopov_normalized"] = row["WeakPopov_median"] / weak_term
        new_row["Alekhnovich_normalized"] = row["Alekhnovich_median"] / alek_term

        normalized.append(new_row)

    return normalized


def solve_3x3(A, b):
    M = [list(row) + [rhs] for row, rhs in zip(A, b)]

    for col in range(3):
        pivot = max(range(col, 3), key=lambda row: abs(M[row][col]))
        if M[pivot][col] == 0:
            raise ZeroDivisionError("singular normal-equation matrix")

        M[col], M[pivot] = M[pivot], M[col]
        scale = M[col][col]
        M[col] = [value / scale for value in M[col]]

        for row in range(3):
            if row == col:
                continue
            factor = M[row][col]
            M[row] = [a - factor * c for a, c in zip(M[row], M[col])]

    return [M[row][3] for row in range(3)]


def fit_power_law_two_variables(results, algorithm):
    time_key = algorithm + "_median"

    rows = [
        row for row in results
        if row[time_key] > 0 and row["n"] > 0 and row["max_degree"] > 0
    ]

    if len(rows) < 3:
        return None

    X = []
    y = []

    for row in rows:
        X.append([
            1.0,
            math.log(float(row["n"])),
            math.log(float(row["max_degree"])),
        ])
        y.append(math.log(float(row[time_key])))

    normal = [[sum(x[i] * x[j] for x in X) for j in range(3)] for i in range(3)]
    rhs = [sum(x[i] * yi for x, yi in zip(X, y)) for i in range(3)]
    log_C, alpha, beta = solve_3x3(normal, rhs)
    C = math.exp(log_C)

    return {
        "algorithm": algorithm,
        "C": C,
        "n_exponent": alpha,
        "degree_exponent": beta,
        "model": f"T ~= {C:.3e} * n^{alpha:.3f} * d^{beta:.3f}",
    }


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

    for path in sorted(parts_dir.glob("*.json")):
        with path.open("r", encoding="utf-8") as f:
            summary = json.load(f)

        summaries.append({
            "path": str(path),
            "config": summary.get("config", {}),
            "result_count": summary.get("result_count", 0),
        })
        results.extend(summary.get("results", []))

    results.sort(key=lambda row: (row["n"], row["max_degree"]))
    normalized_results = add_normalized_times(results)

    expected_total = None
    seen_indices = set()
    for summary in summaries:
        config = summary["config"]
        if config.get("array_total") is not None:
            expected_total = config["array_total"]
        if config.get("array_index") is not None:
            seen_indices.add(config["array_index"])

    missing_indices = []
    if expected_total is not None:
        missing_indices = [idx for idx in range(1, expected_total + 1) if idx not in seen_indices]

    fits = {
        "WeakPopov": fit_power_law_two_variables(results, "WeakPopov"),
        "Alekhnovich": fit_power_law_two_variables(results, "Alekhnovich"),
    }

    merged = {
        "part_count": len(summaries),
        "result_count": len(results),
        "expected_part_count": expected_total,
        "missing_part_count": len(missing_indices),
        "missing_part_indices": missing_indices,
        "fits": fits,
        "parts": summaries,
        "results": results,
        "normalized_results": normalized_results,
    }

    write_json(output_prefix.with_suffix(".json"), merged)
    write_csv(output_prefix.with_suffix(".csv"), normalized_results)
    write_csv(output_prefix.with_suffix(".raw.csv"), results)

    print(f"Merged {len(summaries)} parts with {len(results)} result rows")
    if missing_indices:
        print(f"Missing {len(missing_indices)} array parts")
    print(f"Saved {output_prefix.with_suffix('.json')}")
    print(f"Saved {output_prefix.with_suffix('.csv')}")
    print(f"Saved {output_prefix.with_suffix('.raw.csv')}")


if __name__ == "__main__":
    main()
