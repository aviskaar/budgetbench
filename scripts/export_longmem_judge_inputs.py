"""
Export BudgetBench LongMemEval prediction logs for external LLM judging.

The cleaned LongMemEval dataset card provides oracle data splits but no public
judge runner schema.  This script creates a conservative JSONL bundle that
preserves the fields an external or official judge would need: question ID,
question, reference answer, candidate prediction, strategy/budget metadata,
BudgetBench deterministic score, and log provenance.
"""
import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


DEFAULT_LONGMEM_PATH = "data/longmemeval_oracle.json"


def load_longmem_dataset(data_path: str = DEFAULT_LONGMEM_PATH) -> Dict[str, Dict[str, Any]]:
    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("LongMemEval data must be a JSON list")
    indexed = {}
    for item in data:
        question_id = item.get("question_id")
        if question_id is None:
            continue
        indexed[str(question_id)] = item
    return indexed


def load_summary_rows(log_dir: str) -> List[Dict[str, Any]]:
    summary_path = os.path.join(log_dir, "summary.jsonl")
    rows = []
    with open(summary_path, encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("task") == "longmem" and "error" not in row:
                rows.append(row)
    return rows


def _item_key(row: Dict[str, Any]) -> Optional[str]:
    item_id = row.get("item_id")
    if item_id == "unknown":
        item_id = None
    return row.get("longmem_question_id") or item_id


def _merged_item_rows(combo_file: str) -> Dict[str, Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    with open(combo_file, encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = _item_key(row)
            if key is None:
                continue
            merged.setdefault(str(key), {}).update(row)
    return merged


def _judge_prompt(question: str, reference_answer: Any, prediction: Any) -> str:
    return (
        "You are judging a LongMemEval memory question.\n"
        "Return JSON with keys correct (true/false) and rationale (short string).\n\n"
        f"Question: {question}\n"
        f"Reference answer: {reference_answer}\n"
        f"Candidate answer: {prediction}\n"
    )


def _matches_filter(value: Any, allowed: Optional[Sequence[Any]]) -> bool:
    if allowed is None:
        return True
    return value in allowed


def iter_export_rows(
    log_dir: str,
    dataset_by_id: Dict[str, Dict[str, Any]],
    strategies: Optional[Sequence[str]] = None,
    budgets: Optional[Sequence[int]] = None,
    include_judge_prompt: bool = True,
    prediction_only: bool = False,
) -> Iterable[Dict[str, Any]]:
    for summary in load_summary_rows(log_dir):
        strategy = summary.get("strategy")
        budget = int(summary.get("budget"))
        if not _matches_filter(strategy, strategies):
            continue
        if not _matches_filter(budget, budgets):
            continue

        combo_file = os.path.join(log_dir, f"longmem_{strategy}_{budget}.jsonl")
        if not os.path.exists(combo_file):
            continue

        for question_id, metric_row in sorted(_merged_item_rows(combo_file).items()):
            prediction_available = "prediction" in metric_row
            if prediction_only and not prediction_available:
                continue
            if "quality" not in metric_row and not prediction_available:
                continue
            dataset_item = dataset_by_id.get(question_id)
            if dataset_item is None:
                continue

            question = dataset_item.get("question")
            reference_answer = dataset_item.get("answer")
            prediction = metric_row.get("prediction")
            judge_status = "pending_external_longmemeval_judge"
            if not prediction_available:
                judge_status = "not_judgeable_no_prediction"
                if metric_row.get("violation_rate") == 1.0 or metric_row.get("status") == "failed":
                    judge_status = "not_judgeable_budget_violation"
            export_row = {
                "question_id": question_id,
                "question_type": dataset_item.get("question_type"),
                "memory_category": metric_row.get("memory_category"),
                "question": question,
                "reference_answer": reference_answer,
                "prediction": prediction,
                "prediction_available": prediction_available,
                "strategy": strategy,
                "budget": budget,
                "model": summary.get("model"),
                "budgetbench_normalized_contains": metric_row.get("quality"),
                "budgetbench_grader": metric_row.get("longmem_grader"),
                "judge_status": judge_status,
                "source_dataset": "xiaowu0162/longmemeval-cleaned/longmemeval_oracle.json",
                "source_log_dir": log_dir,
                "source_combo_file": combo_file,
                "natural_prompt_tokens": metric_row.get("natural_prompt_tokens"),
                "used_budget": metric_row.get("used_budget"),
                "peak_budget": metric_row.get("peak_budget"),
                "violation_rate": metric_row.get("violation_rate"),
                "question_date": dataset_item.get("question_date"),
                "answer_session_ids": dataset_item.get("answer_session_ids"),
            }
            if include_judge_prompt and prediction_available:
                export_row["external_judge_prompt_v1"] = _judge_prompt(
                    question=str(question or ""),
                    reference_answer=reference_answer,
                    prediction=prediction,
                )
            yield export_row


def export_judge_inputs(
    log_dir: str,
    data_path: str,
    output_path: str,
    strategies: Optional[Sequence[str]] = None,
    budgets: Optional[Sequence[int]] = None,
    include_judge_prompt: bool = True,
    prediction_only: bool = False,
) -> int:
    dataset_by_id = load_longmem_dataset(data_path)
    rows = list(
        iter_export_rows(
            log_dir=log_dir,
            dataset_by_id=dataset_by_id,
            strategies=strategies,
            budgets=budgets,
            include_judge_prompt=include_judge_prompt,
            prediction_only=prediction_only,
        )
    )
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
        description="Export BudgetBench LongMemEval prediction logs for external judging"
    )
    parser.add_argument("--log-dir", required=True, help="BudgetBench LongMemEval log directory")
    parser.add_argument("--data-path", default=DEFAULT_LONGMEM_PATH, help="LongMemEval oracle JSON path")
    parser.add_argument("--output", required=True, help="Output JSONL path")
    parser.add_argument("--strategies", nargs="+", default=None, help="Optional strategies to export")
    parser.add_argument("--budgets", nargs="+", default=None, help="Optional budget tiers to export")
    parser.add_argument(
        "--no-judge-prompt",
        action="store_true",
        help="Omit the generic external judge prompt from each row",
    )
    parser.add_argument(
        "--prediction-only",
        action="store_true",
        help="Only export rows with model predictions; omit budget-violation rows",
    )
    args = parser.parse_args()

    count = export_judge_inputs(
        log_dir=args.log_dir,
        data_path=args.data_path,
        output_path=args.output,
        strategies=args.strategies,
        budgets=_parse_budgets(args.budgets),
        include_judge_prompt=not args.no_judge_prompt,
        prediction_only=args.prediction_only,
    )
    print(f"Exported {count} LongMemEval judge rows to: {args.output}")


if __name__ == "__main__":
    main()
