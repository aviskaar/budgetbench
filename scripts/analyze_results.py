"""
BudgetBench Results Aggregator
Reads summary.jsonl from one or more log dirs and produces an aggregated CSV.

Usage:
    python scripts/analyze_results.py --log-dirs logs/full_study/20260508_120000 --model qwen2.5:14b
"""
import argparse
import json
import os
import random
import re
from datetime import datetime
from typing import List, Optional, Sequence, Tuple

import pandas as pd


def _model_slug(model: str) -> str:
    """Return a filesystem-safe flat slug for local and provider model IDs."""
    return re.sub(r"[^A-Za-z0-9_-]+", "_", model).strip("_")


def _collect_non_null(values: pd.Series) -> List[str]:
    return [value for value in values if pd.notna(value)]


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
    For each row, read the per-combination JSONL to compute budget metrics.
    Per-combination JSONL: {log_dir}/{task}_{strategy}_{budget}.jsonl
    violation_rate = mean violation rate across metric rows.
    """
    violation_rates = []
    mean_used_budgets = []
    peak_budgets = []
    for _, row in df.iterrows():
        log_dir = row.get("_log_dir", "")
        task = row.get("task", "")
        strategy = row.get("strategy", "")
        budget = row.get("budget", 0)
        recorded_combo_file = row.get("combo_log_file")
        if isinstance(recorded_combo_file, str) and recorded_combo_file:
            combo_file = recorded_combo_file
        else:
            combo_file = os.path.join(log_dir, f"{task}_{strategy}_{budget}.jsonl")
        if not os.path.exists(combo_file):
            violation_rates.append(None)
            mean_used_budgets.append(None)
            peak_budgets.append(None)
            continue

        bool_total = 0
        bool_violations = 0
        rate_values = []
        used_values = []
        peak_values = []
        with open(combo_file) as f:
            for line in f:
                try:
                    turn = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue

                # Older logs used a boolean violation field.  Current runner logs
                # per-item violation_rate after retries, so support both formats.
                if "violation" in turn:
                    bool_total += 1
                    if turn.get("violation", False):
                        bool_violations += 1
                if "violation_rate" in turn:
                    rate_values.append(float(turn["violation_rate"]))
                if "used_budget" in turn and turn["used_budget"] is not None:
                    used_values.append(float(turn["used_budget"]))
                if "peak_budget" in turn and turn["peak_budget"] is not None:
                    peak_values.append(float(turn["peak_budget"]))

        if rate_values:
            rate = sum(rate_values) / len(rate_values)
        elif bool_total > 0:
            rate = bool_violations / bool_total
        else:
            rate = None
        violation_rates.append(rate)
        mean_used_budgets.append(sum(used_values) / len(used_values) if used_values else None)
        peak_budgets.append(max(peak_values) if peak_values else None)

    df = df.copy()
    df["violation_rate"] = violation_rates
    df["mean_used_budget"] = mean_used_budgets
    df["max_peak_budget"] = peak_budgets
    return df


def _combo_file_for_row(row: pd.Series) -> str:
    if row.get("combo_log_file"):
        return str(row.get("combo_log_file"))
    log_dir = row.get("_log_dir", "")
    task = row.get("task", "")
    strategy = row.get("strategy", "")
    budget = row.get("budget", 0)
    return os.path.join(log_dir, f"{task}_{strategy}_{budget}.jsonl")


def _combo_files_for_row(row: pd.Series) -> List[str]:
    combo_files = row.get("combo_log_files")
    if isinstance(combo_files, list):
        return [str(path) for path in combo_files if path]
    combo_file = _combo_file_for_row(row)
    return [combo_file] if combo_file else []


def _quality_rows_from_combo(combo_file: str) -> List[dict]:
    rows: List[dict] = []
    if not os.path.exists(combo_file):
        return rows

    with open(combo_file) as f:
        for line in f:
            try:
                turn = json.loads(line.strip())
            except json.JSONDecodeError:
                continue
            if "quality" not in turn or turn["quality"] is None:
                continue
            try:
                quality = float(turn["quality"])
            except (TypeError, ValueError):
                continue
            rows.append(
                {
                    "item_id": (
                        turn.get("item_id")
                        if turn.get("item_id") != "unknown"
                        else None
                    ) or turn.get("longmem_question_id"),
                    "quality": quality,
                    "natural_prompt_tokens": turn.get("natural_prompt_tokens"),
                    "memory_category": turn.get("memory_category"),
                }
            )
    return rows


def _quality_values_from_combo(combo_file: str) -> List[float]:
    return [row["quality"] for row in _quality_rows_from_combo(combo_file)]


def _quality_rows_from_row(row: pd.Series) -> List[dict]:
    combo_files = _combo_files_for_row(row)
    if len(combo_files) <= 1:
        combo_file = combo_files[0] if combo_files else ""
        return _quality_rows_from_combo(combo_file)

    grouped_rows = {}
    for combo_file in combo_files:
        for quality_row in _quality_rows_from_combo(combo_file):
            item_id = quality_row.get("item_id")
            if item_id is None:
                continue
            existing = grouped_rows.setdefault(
                item_id,
                {
                    "item_id": item_id,
                    "qualities": [],
                    "natural_prompt_tokens": quality_row.get("natural_prompt_tokens"),
                    "memory_category": quality_row.get("memory_category"),
                },
            )
            existing["qualities"].append(float(quality_row["quality"]))
            if existing.get("natural_prompt_tokens") is None:
                existing["natural_prompt_tokens"] = quality_row.get("natural_prompt_tokens")
            if existing.get("memory_category") is None:
                existing["memory_category"] = quality_row.get("memory_category")

    aggregated_rows = []
    for item_id, values in grouped_rows.items():
        qualities = values.pop("qualities", [])
        if not qualities:
            continue
        aggregated_rows.append(
            {
                "item_id": item_id,
                "quality": sum(qualities) / len(qualities),
                "natural_prompt_tokens": values.get("natural_prompt_tokens"),
                "memory_category": values.get("memory_category"),
            }
        )
    return aggregated_rows


def _bootstrap_mean_interval(
    values: Sequence[float],
    confidence: float = 0.95,
    n_bootstrap: int = 2000,
    seed: int = 0,
) -> Tuple[Optional[float], Optional[float]]:
    if not values:
        return None, None
    if len(values) == 1 or n_bootstrap <= 0:
        mean_value = sum(values) / len(values)
        return mean_value, mean_value
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1")

    rng = random.Random(seed)
    sample_size = len(values)
    means = []
    for _ in range(n_bootstrap):
        sample_total = sum(values[rng.randrange(sample_size)] for _ in range(sample_size))
        means.append(sample_total / sample_size)
    means.sort()

    alpha = 1.0 - confidence
    low_index = max(0, min(n_bootstrap - 1, int((alpha / 2.0) * n_bootstrap)))
    high_index = max(0, min(n_bootstrap - 1, int((1.0 - alpha / 2.0) * n_bootstrap) - 1))
    return means[low_index], means[high_index]


def compute_quality_intervals(
    df: pd.DataFrame,
    confidence: float = 0.95,
    n_bootstrap: int = 2000,
    seed: int = 0,
) -> pd.DataFrame:
    """Add bootstrap intervals from item-level quality rows when logs exist."""
    lows = []
    highs = []
    counts = []

    for idx, (_, row) in enumerate(df.iterrows()):
        values = [quality_row["quality"] for quality_row in _quality_rows_from_row(row)]
        low, high = _bootstrap_mean_interval(
            values,
            confidence=confidence,
            n_bootstrap=n_bootstrap,
            seed=seed + idx,
        )
        lows.append(low)
        highs.append(high)
        counts.append(len(values))

    df = df.copy()
    df["quality_ci_low"] = lows
    df["quality_ci_high"] = highs
    df["quality_n"] = counts
    return df


def _quality_map_from_combo(combo_file: str) -> dict:
    quality_map = {}
    for row in _quality_rows_from_combo(combo_file):
        item_id = row.get("item_id")
        if item_id is None:
            continue
        quality_map[item_id] = row["quality"]
    return quality_map


def _quality_map_from_row(row: pd.Series) -> dict:
    quality_map = {}
    for quality_row in _quality_rows_from_row(row):
        item_id = quality_row.get("item_id")
        if item_id is None:
            continue
        quality_map[item_id] = quality_row["quality"]
    return quality_map


def compute_paired_deltas(
    df: pd.DataFrame,
    baseline_strategy: str,
    baseline_budget: int,
    confidence: float = 0.95,
    n_bootstrap: int = 2000,
    seed: int = 0,
) -> pd.DataFrame:
    """
    Compute item-level paired quality deltas versus a baseline cell.

    Deltas are candidate quality minus baseline quality over the intersection
    of item IDs present in both raw JSONL logs.
    """
    rows = []
    if df.empty:
        return pd.DataFrame(rows)

    grouped = df.groupby(["_log_dir", "task"], dropna=False)
    for (log_dir, task), group in grouped:
        baseline_rows = group[
            (group["strategy"] == baseline_strategy)
            & (group["budget"].astype(int) == int(baseline_budget))
        ]
        if baseline_rows.empty:
            continue
        baseline_row = baseline_rows.iloc[0]
        baseline_map = _quality_map_from_row(baseline_row)
        if not baseline_map:
            continue

        for idx, candidate_row in group.iterrows():
            candidate_map = _quality_map_from_row(candidate_row)
            paired_ids = sorted(set(candidate_map) & set(baseline_map))
            if not paired_ids:
                continue

            deltas = [candidate_map[item_id] - baseline_map[item_id] for item_id in paired_ids]
            mean_delta = sum(deltas) / len(deltas)
            low, high = _bootstrap_mean_interval(
                deltas,
                confidence=confidence,
                n_bootstrap=n_bootstrap,
                seed=seed + int(idx),
            )

            candidate_accuracy = sum(candidate_map[item_id] for item_id in paired_ids) / len(paired_ids)
            baseline_accuracy = sum(baseline_map[item_id] for item_id in paired_ids) / len(paired_ids)
            rows.append(
                {
                    "model": candidate_row.get("model"),
                    "task": task,
                    "strategy": candidate_row.get("strategy"),
                    "budget": candidate_row.get("budget"),
                    "baseline_strategy": baseline_strategy,
                    "baseline_budget": baseline_budget,
                    "paired_n": len(paired_ids),
                    "candidate_accuracy": candidate_accuracy,
                    "baseline_accuracy": baseline_accuracy,
                    "mean_delta": mean_delta,
                    "delta_ci_low": low,
                    "delta_ci_high": high,
                    "candidate_duration_sec": candidate_row.get("duration_sec"),
                    "baseline_duration_sec": baseline_row.get("duration_sec"),
                    "candidate_violation_rate": candidate_row.get("violation_rate"),
                    "baseline_violation_rate": baseline_row.get("violation_rate"),
                    "_log_dir": log_dir,
                }
            )

    return pd.DataFrame(rows)


def compute_grouped_quality(
    df: pd.DataFrame,
    group_column: str,
    confidence: float = 0.95,
    n_bootstrap: int = 2000,
    seed: int = 0,
) -> pd.DataFrame:
    """Compute quality intervals by a per-item metric metadata column."""
    rows = []
    if df.empty:
        return pd.DataFrame(rows)

    for idx, (_, row) in enumerate(df.iterrows()):
        grouped_values = {}
        for quality_row in _quality_rows_from_row(row):
            group_value = quality_row.get(group_column)
            if group_value is None:
                continue
            grouped_values.setdefault(group_value, []).append(quality_row["quality"])

        for offset, (group_value, values) in enumerate(sorted(grouped_values.items())):
            low, high = _bootstrap_mean_interval(
                values,
                confidence=confidence,
                n_bootstrap=n_bootstrap,
                seed=seed + int(idx) + offset,
            )
            rows.append(
                {
                    "model": row.get("model"),
                    "task": row.get("task"),
                    "strategy": row.get("strategy"),
                    "budget": row.get("budget"),
                    group_column: group_value,
                    "accuracy": sum(values) / len(values),
                    "quality_ci_low": low,
                    "quality_ci_high": high,
                    "quality_n": len(values),
                    "_log_dir": row.get("_log_dir"),
                }
            )

    return pd.DataFrame(rows)


def summarize_repeats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate repeated cell runs into one row per model/task/strategy/budget.

    Accuracy and duration are summarized across repeat executions, while
    confidence intervals and budget-use metrics are averaged over the repeated
    rows already computed from item-level logs.
    """
    if df.empty:
        return df.copy()

    group_cols = ["_log_dir", "model", "task", "strategy", "budget"]
    agg_map = {
        "accuracy": ["mean", "std", "count"],
        "duration_sec": ["mean", "std"],
        "violation_rate": "mean",
        "mean_used_budget": "mean",
        "max_peak_budget": "mean",
        "quality_ci_low": "mean",
        "quality_ci_high": "mean",
        "quality_n": "max",
        "combo_log_file": _collect_non_null,
    }

    grouped = df.groupby(group_cols, dropna=False).agg(agg_map)
    grouped.columns = [
        "_".join(str(part) for part in col if part).rstrip("_")
        for col in grouped.columns.to_flat_index()
    ]
    grouped = grouped.reset_index()

    rename_map = {
        "accuracy_mean": "accuracy",
        "accuracy_std": "accuracy_std",
        "accuracy_count": "repeat_count",
        "duration_sec_mean": "duration_sec",
        "duration_sec_std": "duration_sec_std",
        "violation_rate_mean": "violation_rate",
        "mean_used_budget_mean": "mean_used_budget",
        "max_peak_budget_mean": "max_peak_budget",
        "quality_ci_low_mean": "quality_ci_low",
        "quality_ci_high_mean": "quality_ci_high",
        "quality_n_max": "quality_n",
        "combo_log_file__collect_non_null": "combo_log_files",
    }
    grouped = grouped.rename(columns=rename_map)
    return grouped


def main():
    parser = argparse.ArgumentParser(description="Aggregate BudgetBench summary.jsonl files into CSV")
    parser.add_argument("--log-dirs", nargs="+", required=True, help="Log directories containing summary.jsonl")
    parser.add_argument("--model", type=str, required=True, help="Model name (e.g. qwen2.5:14b)")
    parser.add_argument("--bootstrap-samples", type=int, default=2000, help="Bootstrap resamples for quality confidence intervals")
    parser.add_argument("--confidence", type=float, default=0.95, help="Confidence level for quality intervals")
    parser.add_argument("--paired-baseline-strategy", type=str, default=None, help="Strategy to use as the paired-comparison baseline")
    parser.add_argument("--paired-baseline-budget", type=int, default=None, help="Budget to use as the paired-comparison baseline")
    parser.add_argument(
        "--group-by",
        action="append",
        default=[],
        help="Per-item metric metadata column to stratify quality by, e.g. memory_category",
    )
    parser.add_argument(
        "--aggregate-repeats",
        action="store_true",
        help="Aggregate repeated cell runs into one row per model/task/strategy/budget",
    )
    args = parser.parse_args()

    print(f"Loading summary files from: {args.log_dirs}")
    df = load_summary_files(args.log_dirs)
    if df.empty:
        print("No data found. Exiting.")
        return

    df = compute_violation_rates(df)
    df = compute_quality_intervals(
        df,
        confidence=args.confidence,
        n_bootstrap=args.bootstrap_samples,
    )
    if args.aggregate_repeats:
        df = summarize_repeats(df)

    out_cols = [
        "model",
        "task",
        "strategy",
        "budget",
        "accuracy",
        "violation_rate",
        "mean_used_budget",
        "max_peak_budget",
        "quality_ci_low",
        "quality_ci_high",
        "quality_n",
        "duration_sec",
        "duration_sec_std",
        "accuracy_std",
        "repeat_count",
    ]
    for col in out_cols:
        if col not in df.columns:
            df[col] = None
    df_out = df[out_cols].copy()

    os.makedirs("results", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_slug = _model_slug(args.model)
    out_path = os.path.join("results", f"full_study_{model_slug}_{timestamp}.csv")
    df_out.to_csv(out_path, index=False)
    print(f"Results written to: {out_path}")

    if args.paired_baseline_strategy and args.paired_baseline_budget is not None:
        paired_df = compute_paired_deltas(
            df,
            baseline_strategy=args.paired_baseline_strategy,
            baseline_budget=args.paired_baseline_budget,
            confidence=args.confidence,
            n_bootstrap=args.bootstrap_samples,
        )
        paired_path = os.path.join("results", f"paired_deltas_{model_slug}_{timestamp}.csv")
        paired_df.to_csv(paired_path, index=False)
        print(f"Paired deltas written to: {paired_path}")

    for group_column in args.group_by:
        grouped_df = compute_grouped_quality(
            df,
            group_column=group_column,
            confidence=args.confidence,
            n_bootstrap=args.bootstrap_samples,
        )
        if grouped_df.empty:
            print(f"No grouped quality rows found for: {group_column}")
            continue
        grouped_path = os.path.join(
            "results",
            f"grouped_{group_column}_{model_slug}_{timestamp}.csv",
        )
        grouped_df.to_csv(grouped_path, index=False)
        print(f"Grouped quality written to: {grouped_path}")


if __name__ == "__main__":
    main()
