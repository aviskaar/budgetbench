"""
Export BudgetBench LongMemEval predictions into the official LongMemEval
evaluation format: one JSONL row per question with fields
  - question_id
  - hypothesis
"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from scripts.export_longmem_judge_inputs import (  # type: ignore
        DEFAULT_LONGMEM_PATH,
        iter_export_rows,
        load_longmem_dataset,
    )
else:
    from scripts.export_longmem_judge_inputs import (
        DEFAULT_LONGMEM_PATH,
        iter_export_rows,
        load_longmem_dataset,
    )


def iter_hypotheses(
    log_dir: str,
    data_path: str,
    strategies: Optional[Sequence[str]] = None,
    budgets: Optional[Sequence[int]] = None,
) -> Iterable[Dict[str, str]]:
    dataset_by_id = load_longmem_dataset(data_path)
    for row in iter_export_rows(
        log_dir=log_dir,
        dataset_by_id=dataset_by_id,
        strategies=strategies,
        budgets=budgets,
        include_judge_prompt=False,
        prediction_only=True,
    ):
        yield {
            "question_id": row["question_id"],
            "hypothesis": row["prediction"],
        }


def export_hypotheses(
    log_dir: str,
    data_path: str,
    output_path: str,
    strategies: Optional[Sequence[str]] = None,
    budgets: Optional[Sequence[int]] = None,
) -> int:
    rows = list(iter_hypotheses(log_dir, data_path, strategies=strategies, budgets=budgets))
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return len(rows)


def _parse_budgets(values: Optional[List[str]]) -> Optional[List[int]]:
    if values is None:
        return None
    return [int(value) for value in values]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export BudgetBench LongMemEval predictions into official hypothesis JSONL format"
    )
    parser.add_argument("--log-dir", required=True, help="BudgetBench LongMemEval log directory")
    parser.add_argument("--data-path", default=DEFAULT_LONGMEM_PATH, help="LongMemEval JSON path")
    parser.add_argument("--output", required=True, help="Output JSONL path")
    parser.add_argument("--strategies", nargs="+", default=None, help="Optional strategies to export")
    parser.add_argument("--budgets", nargs="+", default=None, help="Optional budget tiers to export")
    args = parser.parse_args()

    count = export_hypotheses(
        log_dir=args.log_dir,
        data_path=args.data_path,
        output_path=args.output,
        strategies=args.strategies,
        budgets=_parse_budgets(args.budgets),
    )
    print(f"Exported {count} LongMemEval hypotheses to: {args.output}")


if __name__ == "__main__":
    main()
