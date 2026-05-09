"""
BudgetBench Results Aggregator
Reads summary.jsonl from one or more log dirs and produces an aggregated CSV.

Usage:
    python scripts/analyze_results.py --log-dirs logs/full_study/20260508_120000 --model qwen2.5:14b
"""
import argparse
import json
import os
from datetime import datetime
from typing import List

import pandas as pd


def load_summary_files(log_dirs: List[str]) -> pd.DataFrame:
    """Read summary.jsonl from each log_dir and concatenate into a single DataFrame."""
    rows = []
    for log_dir in log_dirs:
        summary_path = os.path.join(log_dir, "summary.jsonl")
        if not os.path.exists(summary_path):
            print(f"  [warn] No summary.jsonl in {log_dir} - skipping")
            continue
        with open(summary_path) as f:
            for line in f:
                try:
                    row = json.loads(line.strip())
                    row["_log_dir"] = log_dir
                    rows.append(row)
                except json.JSONDecodeError:
                    pass
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def compute_violation_rates(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each row, read the per-combination JSONL to compute violation_rate.
    Per-combination JSONL: {log_dir}/{task}_{strategy}_{budget}.jsonl
    violation_rate = fraction of turns where violation == True.
    """
    violation_rates = []
    for _, row in df.iterrows():
        log_dir = row.get("_log_dir", "")
        task = row.get("task", "")
        strategy = row.get("strategy", "")
        budget = row.get("budget", 0)
        combo_file = os.path.join(log_dir, f"{task}_{strategy}_{budget}.jsonl")
        if not os.path.exists(combo_file):
            violation_rates.append(None)
            continue
        total = 0
        violations = 0
        with open(combo_file) as f:
            for line in f:
                try:
                    turn = json.loads(line.strip())
                    total += 1
                    if turn.get("violation", False):
                        violations += 1
                except json.JSONDecodeError:
                    pass
        rate = violations / total if total > 0 else None
        violation_rates.append(rate)
    df = df.copy()
    df["violation_rate"] = violation_rates
    return df


def main():
    parser = argparse.ArgumentParser(description="Aggregate BudgetBench summary.jsonl files into CSV")
    parser.add_argument("--log-dirs", nargs="+", required=True, help="Log directories containing summary.jsonl")
    parser.add_argument("--model", type=str, required=True, help="Model name (e.g. qwen2.5:14b)")
    args = parser.parse_args()

    print(f"Loading summary files from: {args.log_dirs}")
    df = load_summary_files(args.log_dirs)
    if df.empty:
        print("No data found. Exiting.")
        return

    df = compute_violation_rates(df)

    out_cols = ["model", "task", "strategy", "budget", "accuracy", "violation_rate", "duration_sec"]
    for col in out_cols:
        if col not in df.columns:
            df[col] = None
    df_out = df[out_cols].copy()

    os.makedirs("results", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_slug = args.model.replace(":", "_").replace(".", "_")
    out_path = os.path.join("results", f"full_study_{model_slug}_{timestamp}.csv")
    df_out.to_csv(out_path, index=False)
    print(f"Results written to: {out_path}")


if __name__ == "__main__":
    main()
