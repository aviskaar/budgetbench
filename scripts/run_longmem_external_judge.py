"""
Run a LongMemEval-style external judge over exported BudgetBench predictions.

This is not the official LongMemEval judge.  It is an auditable bridge that
records the judge model, prompt version, raw response, parsed decision, and
source BudgetBench row so the paper can report LLM-judge evidence separately
from deterministic normalized-containment scores.
"""
import argparse
import csv
import json
import os
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

import requests


PROMPT_VERSION = "budgetbench-longmem-judge-v2"
DEFAULT_URL = "http://localhost:11434/v1/chat/completions"


SYSTEM_PROMPT = (
    "You are a strict but fair evaluator for LongMemEval-style memory QA. "
    "Decide whether the candidate answer correctly answers the question, "
    "using the reference answer as ground truth. Accept paraphrases, equivalent "
    "numbers, and answers that include extra text if the required answer is "
    "clearly present. Mark incorrect if the candidate contradicts the reference, "
    "answers a different question, omits the key fact, or hallucinates when the "
    "reference says the information is insufficient. If the candidate gives a "
    "different number, date, name, location, or object than the reference, mark "
    "it incorrect. Return only JSON with keys correct and rationale. The "
    "rationale must be at most 20 words."
)


def _compact_text(value: Any, max_chars: Optional[int]) -> str:
    text = "" if value is None else str(value)
    if max_chars is None or len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n[...truncated...]"


def build_user_prompt(row: Dict[str, Any], max_chars: Optional[int] = None) -> str:
    return (
        f"Question: {_compact_text(row.get('question'), max_chars)}\n"
        f"Reference answer: {_compact_text(row.get('reference_answer'), max_chars)}\n"
        f"Candidate answer: {_compact_text(row.get('prediction'), max_chars)}\n\n"
        'Return JSON exactly like: {"correct": true, "rationale": "short reason"}'
    )


def load_rows(input_path: str) -> List[Dict[str, Any]]:
    rows = []
    with open(input_path, encoding="utf-8") as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def row_matches(
    row: Dict[str, Any],
    strategies: Optional[Sequence[str]],
    budgets: Optional[Sequence[int]],
    categories: Optional[Sequence[str]],
) -> bool:
    if not row.get("prediction_available"):
        return False
    if row.get("judge_status") != "pending_external_longmemeval_judge":
        return False
    if strategies is not None and row.get("strategy") not in strategies:
        return False
    if budgets is not None and int(row.get("budget")) not in budgets:
        return False
    if categories is not None and row.get("memory_category") not in categories:
        return False
    return True


def filter_rows(
    rows: Iterable[Dict[str, Any]],
    strategies: Optional[Sequence[str]],
    budgets: Optional[Sequence[int]],
    categories: Optional[Sequence[str]],
    limit: Optional[int],
) -> List[Dict[str, Any]]:
    selected = [
        row
        for row in rows
        if row_matches(row, strategies=strategies, budgets=budgets, categories=categories)
    ]
    if limit is not None:
        return selected[:limit]
    return selected


def call_judge(
    row: Dict[str, Any],
    url: str,
    judge_model: str,
    api_key: Optional[str] = None,
    timeout: int = 120,
    prompt_max_chars: Optional[int] = None,
) -> str:
    payload = {
        "model": judge_model,
        "temperature": 0.0,
        "max_tokens": 160,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(row, max_chars=prompt_max_chars)},
        ],
    }
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    response = requests.post(url, json=payload, headers=headers, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def parse_judge_response(content: str) -> Dict[str, Any]:
    parsed = None
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, flags=re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
            except json.JSONDecodeError:
                parsed = None

    if not isinstance(parsed, dict):
        return {
            "judge_correct": None,
            "judge_rationale": "",
            "judge_parse_error": "could_not_parse_json",
        }

    correct = parsed.get("correct")
    if isinstance(correct, str):
        correct = correct.strip().lower() in {"true", "yes", "1", "correct"}
    elif correct is not None:
        correct = bool(correct)
    return {
        "judge_correct": correct,
        "judge_rationale": str(parsed.get("rationale", "")),
        "judge_parse_error": None if isinstance(correct, bool) else "missing_correct_boolean",
    }


def already_judged_keys(output_path: str) -> set:
    if not os.path.exists(output_path):
        return set()
    keys = set()
    with open(output_path, encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            keys.add((row.get("question_id"), row.get("strategy"), int(row.get("budget"))))
    return keys


def run_judge(
    input_path: str,
    output_path: str,
    url: str,
    judge_model: str,
    api_key: Optional[str] = None,
    strategies: Optional[Sequence[str]] = None,
    budgets: Optional[Sequence[int]] = None,
    categories: Optional[Sequence[str]] = None,
    limit: Optional[int] = None,
    resume: bool = True,
    max_attempts: int = 1,
) -> int:
    rows = filter_rows(
        load_rows(input_path),
        strategies=strategies,
        budgets=budgets,
        categories=categories,
        limit=limit,
    )
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    seen = already_judged_keys(output_path) if resume else set()

    count = 0
    with output.open("a" if resume else "w", encoding="utf-8") as f:
        for index, row in enumerate(rows, start=1):
            key = (row.get("question_id"), row.get("strategy"), int(row.get("budget")))
            if key in seen:
                continue
            start = time.time()
            attempts = 0
            content = ""
            parsed = {
                "judge_correct": None,
                "judge_rationale": "",
                "judge_parse_error": "could_not_parse_json",
            }
            try:
                prompt_max_chars = None
                for attempt in range(max(1, max_attempts)):
                    attempts = attempt + 1
                    content = call_judge(
                        row,
                        url=url,
                        judge_model=judge_model,
                        api_key=api_key,
                        prompt_max_chars=prompt_max_chars,
                    )
                    parsed = parse_judge_response(content)
                    if content.strip() and parsed["judge_correct"] is not None:
                        break
                    prompt_max_chars = 2000
                error = None
            except Exception as exc:
                content = ""
                parsed = {
                    "judge_correct": None,
                    "judge_rationale": "",
                    "judge_parse_error": None,
                }
                error = str(exc)
            duration = time.time() - start

            out_row = {
                "question_id": row.get("question_id"),
                "question_type": row.get("question_type"),
                "memory_category": row.get("memory_category"),
                "strategy": row.get("strategy"),
                "budget": row.get("budget"),
                "candidate_model": row.get("model"),
                "judge_model": judge_model,
                "judge_prompt_version": PROMPT_VERSION,
                "judge_correct": parsed["judge_correct"],
                "judge_rationale": parsed["judge_rationale"],
                "judge_parse_error": parsed["judge_parse_error"],
                "judge_error": error,
                "judge_duration_sec": duration,
                "judge_attempts": attempts,
                "raw_judge_response": content,
                "question": row.get("question"),
                "reference_answer": row.get("reference_answer"),
                "prediction": row.get("prediction"),
                "budgetbench_normalized_contains": row.get("budgetbench_normalized_contains"),
                "natural_prompt_tokens": row.get("natural_prompt_tokens"),
                "used_budget": row.get("used_budget"),
                "peak_budget": row.get("peak_budget"),
                "violation_rate": row.get("violation_rate"),
                "source_log_dir": row.get("source_log_dir"),
                "source_combo_file": row.get("source_combo_file"),
            }
            f.write(json.dumps(out_row, ensure_ascii=False) + "\n")
            f.flush()
            count += 1
            if index % 10 == 0:
                print(f"Judged {index}/{len(rows)} selected rows")
    return count


def aggregate_judge_results(input_path: str, output_csv: str) -> int:
    groups: Dict[tuple, List[Dict[str, Any]]] = defaultdict(list)
    with open(input_path, encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("judge_correct") is None:
                continue
            key = (
                row.get("candidate_model"),
                row.get("judge_model"),
                row.get("strategy"),
                int(row.get("budget")),
            )
            groups[key].append(row)

    output = Path(output_csv)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "candidate_model",
            "judge_model",
            "strategy",
            "budget",
            "judge_accuracy",
            "judge_n",
            "normalized_contains_accuracy",
            "mean_judge_duration_sec",
            "judge_prompt_version",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for key, rows in sorted(groups.items()):
            candidate_model, judge_model, strategy, budget = key
            judge_accuracy = sum(1 for row in rows if row.get("judge_correct")) / len(rows)
            normalized_accuracy = (
                sum(float(row.get("budgetbench_normalized_contains") or 0.0) for row in rows)
                / len(rows)
            )
            mean_duration = sum(float(row.get("judge_duration_sec") or 0.0) for row in rows) / len(rows)
            writer.writerow(
                {
                    "candidate_model": candidate_model,
                    "judge_model": judge_model,
                    "strategy": strategy,
                    "budget": budget,
                    "judge_accuracy": judge_accuracy,
                    "judge_n": len(rows),
                    "normalized_contains_accuracy": normalized_accuracy,
                    "mean_judge_duration_sec": mean_duration,
                    "judge_prompt_version": PROMPT_VERSION,
                }
            )
    return sum(len(rows) for rows in groups.values())


def _parse_budgets(values: Optional[List[str]]) -> Optional[List[int]]:
    if values is None:
        return None
    return [int(value) for value in values]


def _load_api_key(env_name: Optional[str], file_path: Optional[str]) -> Optional[str]:
    if file_path:
        with open(file_path, encoding="utf-8") as f:
            return f.read().strip()
    if env_name:
        return os.environ.get(env_name)
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Run external LLM judge over LongMemEval exports")
    parser.add_argument("--input", required=True, help="Judge input JSONL from export_longmem_judge_inputs.py")
    parser.add_argument("--output", required=True, help="Judge decision JSONL output")
    parser.add_argument("--aggregate-output", default=None, help="Optional aggregate CSV output")
    parser.add_argument("--judge-url", default=DEFAULT_URL, help="OpenAI-compatible chat-completions URL")
    parser.add_argument("--judge-model", required=True, help="Judge model name")
    parser.add_argument("--api-key-env", default=None, help="Environment variable containing API key")
    parser.add_argument("--api-key-file", default=None, help="File containing API key; never logged")
    parser.add_argument("--strategies", nargs="+", default=None, help="Optional strategies to judge")
    parser.add_argument("--budgets", nargs="+", default=None, help="Optional budget tiers to judge")
    parser.add_argument("--categories", nargs="+", default=None, help="Optional memory categories to judge")
    parser.add_argument("--limit", type=int, default=None, help="Optional selected-row limit")
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=1,
        help="Maximum judge attempts per row before giving up; >1 enables compact-prompt retry",
    )
    parser.add_argument("--no-resume", action="store_true", help="Overwrite output instead of resuming")
    args = parser.parse_args()

    judged = run_judge(
        input_path=args.input,
        output_path=args.output,
        url=args.judge_url,
        judge_model=args.judge_model,
        api_key=_load_api_key(args.api_key_env, args.api_key_file),
        strategies=args.strategies,
        budgets=_parse_budgets(args.budgets),
        categories=args.categories,
        limit=args.limit,
        resume=not args.no_resume,
        max_attempts=args.max_attempts,
    )
    print(f"Wrote {judged} new judge rows to: {args.output}")

    if args.aggregate_output:
        aggregated = aggregate_judge_results(args.output, args.aggregate_output)
        print(f"Aggregated {aggregated} judge rows to: {args.aggregate_output}")


if __name__ == "__main__":
    main()
