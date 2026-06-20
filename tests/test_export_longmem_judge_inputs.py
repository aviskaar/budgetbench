import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.export_longmem_judge_inputs import export_judge_inputs, iter_export_rows, load_longmem_dataset


def _write_dataset(tmp_path):
    data = [
        {
            "question_id": "q-1",
            "question_type": "knowledge-update",
            "question": "What is my current preferred cafe?",
            "answer": "Blue Cup",
            "question_date": "2024/01/03",
            "answer_session_ids": ["s1"],
        },
        {
            "question_id": "q-2",
            "question_type": "temporal-reasoning",
            "question": "Which cafe did I visit first?",
            "answer": "Red Mug",
            "question_date": "2024/01/04",
            "answer_session_ids": ["s2"],
        },
    ]
    path = tmp_path / "longmemeval_oracle.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _write_logs(tmp_path):
    summary = {
        "timestamp": "20260618_000000",
        "model": "qwen2.5:1.5b",
        "task": "longmem",
        "strategy": "lean_retrieval",
        "budget": 2048,
        "accuracy": 1.0,
        "total": 1,
        "success": 1,
        "duration_sec": 1.0,
    }
    (tmp_path / "summary.jsonl").write_text(json.dumps(summary) + "\n", encoding="utf-8")
    rows = [
        {
            "item_id": "q-1",
            "longmem_question_id": "q-1",
            "memory_category": "knowledge_update",
            "longmem_grader": "normalized_contains",
            "natural_prompt_tokens": 4000,
            "used_budget": 1800,
            "peak_budget": 2048,
            "violation_rate": 0.0,
        },
        {
            "item_id": "q-1",
            "longmem_question_id": "q-1",
            "memory_category": "knowledge_update",
            "longmem_grader": "normalized_contains",
            "quality": 1.0,
            "task_success": 1.0,
            "prediction": "Blue Cup",
        },
        {
            "item_id": "q-2",
            "longmem_question_id": "q-2",
            "quality": 0.0,
        },
    ]
    (tmp_path / "longmem_lean_retrieval_2048.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )
    return tmp_path


def test_export_longmem_judge_inputs_joins_dataset_and_prediction(tmp_path):
    data_path = _write_dataset(tmp_path)
    log_dir = _write_logs(tmp_path)
    output_path = tmp_path / "judge_inputs.jsonl"

    count = export_judge_inputs(
        log_dir=str(log_dir),
        data_path=str(data_path),
        output_path=str(output_path),
        strategies=["lean_retrieval"],
        budgets=[2048],
    )

    assert count == 2
    exported = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    assert exported[0]["question_id"] == "q-1"
    assert exported[0]["question"] == "What is my current preferred cafe?"
    assert exported[0]["reference_answer"] == "Blue Cup"
    assert exported[0]["prediction"] == "Blue Cup"
    assert exported[0]["budgetbench_normalized_contains"] == 1.0
    assert exported[0]["prediction_available"] is True
    assert exported[0]["judge_status"] == "pending_external_longmemeval_judge"
    assert exported[0]["used_budget"] == 1800
    assert "external_judge_prompt_v1" in exported[0]
    assert exported[1]["question_id"] == "q-2"
    assert exported[1]["prediction_available"] is False
    assert exported[1]["judge_status"] == "not_judgeable_no_prediction"
    assert "external_judge_prompt_v1" not in exported[1]


def test_iter_export_rows_can_omit_judge_prompt(tmp_path):
    data_path = _write_dataset(tmp_path)
    log_dir = _write_logs(tmp_path)
    dataset = load_longmem_dataset(str(data_path))

    rows = list(
        iter_export_rows(
            log_dir=str(log_dir),
            dataset_by_id=dataset,
            include_judge_prompt=False,
        )
    )

    assert len(rows) == 2
    assert "external_judge_prompt_v1" not in rows[0]


def test_export_longmem_judge_inputs_can_filter_prediction_only(tmp_path):
    data_path = _write_dataset(tmp_path)
    log_dir = _write_logs(tmp_path)
    output_path = tmp_path / "judge_inputs_predictions_only.jsonl"

    count = export_judge_inputs(
        log_dir=str(log_dir),
        data_path=str(data_path),
        output_path=str(output_path),
        prediction_only=True,
    )

    exported = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    assert count == 1
    assert exported[0]["question_id"] == "q-1"
