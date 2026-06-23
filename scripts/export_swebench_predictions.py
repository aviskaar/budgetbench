"""
Export BudgetBench SWE prediction logs into the official SWE-bench JSONL format.

The official SWE-bench harness expects one JSON object per instance with:
  - instance_id
  - model_name_or_path
  - model_patch

BudgetBench stores predictions inside per-cell JSONL logs, so this exporter
extracts one task/strategy/budget bucket into the official schema.
"""
import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from budgetbench.tasks.swe import SWEBenchTask


def load_summary_rows(log_dir: str) -> List[Dict[str, Any]]:
    summary_path = os.path.join(log_dir, "summary.jsonl")
    rows = []
    with open(summary_path, encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("task") == "swe" and "error" not in row:
                rows.append(row)
    return rows


def _combo_file(summary_row: Dict[str, Any], log_dir: str) -> str:
    combo_file = summary_row.get("combo_log_file")
    if combo_file:
        return str(combo_file)
    strategy = summary_row["strategy"]
    budget = int(summary_row["budget"])
    repeat_index = int(summary_row.get("repeat_index", 0))
    suffix = f"_r{repeat_index + 1}" if repeat_index else ""
    return os.path.join(log_dir, f"swe_{strategy}_{budget}{suffix}.jsonl")


def iter_prediction_rows(
    log_dir: str,
    strategy: str,
    budget: int,
    repeat_index: int = 0,
) -> Iterable[Dict[str, Any]]:
    target_summary = None
    for row in load_summary_rows(log_dir):
        if (
            row.get("strategy") == strategy
            and int(row.get("budget")) == int(budget)
            and int(row.get("repeat_index", 0)) == int(repeat_index)
        ):
            target_summary = row
            break
    if target_summary is None:
        raise FileNotFoundError(
            f"No SWE summary row found for strategy={strategy}, budget={budget}, repeat_index={repeat_index}"
        )

    combo_file = _combo_file(target_summary, log_dir)
    if not os.path.exists(combo_file):
        raise FileNotFoundError(f"Missing combo log file: {combo_file}")

    merged: Dict[str, Dict[str, Any]] = {}
    with open(combo_file, encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            item_id = row.get("item_id")
            if not item_id or item_id == "unknown":
                continue
            merged.setdefault(str(item_id), {}).update(row)

    model_name = target_summary.get("model") or "unknown"
    swe_task = SWEBenchTask()
    for instance_id, row in sorted(merged.items()):
        patch = row.get("prediction")
        if not patch:
            continue
        patch = swe_task._sanitize_patch(str(patch))
        if not patch:
            continue
        yield {
            "instance_id": instance_id,
            "model_name_or_path": model_name,
            "model_patch": patch,
        }


def export_predictions(
    log_dir: str,
    output_path: str,
    strategy: str,
    budget: int,
    repeat_index: int = 0,
) -> int:
    rows = list(
        iter_prediction_rows(
            log_dir=log_dir,
            strategy=strategy,
            budget=budget,
            repeat_index=repeat_index,
        )
    )
    if not rows:
        raise ValueError(
            "No prediction-bearing SWE rows were found. "
            "Older pilot logs did not persist predictions; rerun the desired SWE bucket with the current runner first."
        )
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export BudgetBench SWE predictions into official SWE-bench JSONL format"
    )
    parser.add_argument("--log-dir", required=True, help="BudgetBench run directory containing summary.jsonl")
    parser.add_argument("--output", required=True, help="Output JSONL path for official SWE-bench evaluation")
    parser.add_argument("--strategy", required=True, help="BudgetBench strategy name")
    parser.add_argument("--budget", required=True, type=int, help="Active budget tier to export")
    parser.add_argument("--repeat-index", default=0, type=int, help="Repeat index to export (0-based)")
    args = parser.parse_args()

    count = export_predictions(
        log_dir=args.log_dir,
        output_path=args.output,
        strategy=args.strategy,
        budget=args.budget,
        repeat_index=args.repeat_index,
    )
    print(f"Exported {count} SWE predictions to: {args.output}")


if __name__ == "__main__":
    main()
