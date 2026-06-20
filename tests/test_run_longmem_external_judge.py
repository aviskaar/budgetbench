import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.run_longmem_external_judge import (
    aggregate_judge_results,
    build_user_prompt,
    filter_rows,
    parse_judge_response,
)


def test_parse_judge_response_accepts_plain_json():
    parsed = parse_judge_response('{"correct": true, "rationale": "matches"}')
    assert parsed["judge_correct"] is True
    assert parsed["judge_rationale"] == "matches"
    assert parsed["judge_parse_error"] is None


def test_parse_judge_response_extracts_embedded_json():
    parsed = parse_judge_response('Here: {"correct": "false", "rationale": "wrong number"}')
    assert parsed["judge_correct"] is False
    assert parsed["judge_rationale"] == "wrong number"
    assert parsed["judge_parse_error"] is None


def test_parse_judge_response_reports_bad_json():
    parsed = parse_judge_response("not json")
    assert parsed["judge_correct"] is None
    assert parsed["judge_parse_error"] == "could_not_parse_json"


def test_build_user_prompt_can_compact_long_fields():
    prompt = build_user_prompt(
        {
            "question": "q" * 80,
            "reference_answer": "r" * 80,
            "prediction": "p" * 80,
        },
        max_chars=20,
    )

    assert prompt.count("[...truncated...]") == 3
    assert "q" * 21 not in prompt


def test_filter_rows_requires_prediction_and_pending_status():
    rows = [
        {
            "question_id": "a",
            "prediction_available": True,
            "judge_status": "pending_external_longmemeval_judge",
            "strategy": "lean_retrieval",
            "budget": 2048,
            "memory_category": "knowledge_update",
        },
        {
            "question_id": "b",
            "prediction_available": False,
            "judge_status": "not_judgeable_budget_violation",
            "strategy": "lean_retrieval",
            "budget": 2048,
            "memory_category": "knowledge_update",
        },
        {
            "question_id": "c",
            "prediction_available": True,
            "judge_status": "pending_external_longmemeval_judge",
            "strategy": "rag",
            "budget": 2048,
            "memory_category": "knowledge_update",
        },
    ]

    selected = filter_rows(
        rows,
        strategies=["lean_retrieval"],
        budgets=[2048],
        categories=["knowledge_update"],
        limit=None,
    )

    assert [row["question_id"] for row in selected] == ["a"]


def test_aggregate_judge_results(tmp_path):
    rows = [
        {
            "candidate_model": "qwen2.5:1.5b",
            "judge_model": "qwen3.5:2b",
            "strategy": "lean_retrieval",
            "budget": 2048,
            "judge_correct": True,
            "budgetbench_normalized_contains": 1.0,
            "judge_duration_sec": 0.1,
        },
        {
            "candidate_model": "qwen2.5:1.5b",
            "judge_model": "qwen3.5:2b",
            "strategy": "lean_retrieval",
            "budget": 2048,
            "judge_correct": False,
            "budgetbench_normalized_contains": 0.0,
            "judge_duration_sec": 0.3,
        },
    ]
    input_path = tmp_path / "judge.jsonl"
    output_path = tmp_path / "aggregate.csv"
    input_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )

    count = aggregate_judge_results(str(input_path), str(output_path))

    assert count == 2
    text = output_path.read_text(encoding="utf-8")
    assert "lean_retrieval" in text
    assert "0.5" in text
