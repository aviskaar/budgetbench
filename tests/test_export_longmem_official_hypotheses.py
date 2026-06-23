import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.export_longmem_official_hypotheses import export_hypotheses, iter_hypotheses


def _write_dataset(tmp_path):
    data = [
        {
            "question_id": "q-1",
            "question_type": "knowledge-update",
            "question": "What is my current preferred cafe?",
            "answer": "Blue Cup",
        },
        {
            "question_id": "q-2",
            "question_type": "temporal-reasoning",
            "question": "Which cafe did I visit first?",
            "answer": "Red Mug",
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
        {"item_id": "q-1", "longmem_question_id": "q-1", "quality": 1.0, "prediction": "Blue Cup"},
        {"item_id": "q-2", "longmem_question_id": "q-2", "quality": 0.0},
    ]
    (tmp_path / "longmem_lean_retrieval_2048.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )
    return tmp_path


def test_iter_hypotheses_exports_official_schema(tmp_path):
    data_path = _write_dataset(tmp_path)
    log_dir = _write_logs(tmp_path)
    rows = list(
        iter_hypotheses(
            log_dir=str(log_dir),
            data_path=str(data_path),
            strategies=["lean_retrieval"],
            budgets=[2048],
        )
    )
    assert rows == [{"question_id": "q-1", "hypothesis": "Blue Cup"}]


def test_export_hypotheses_writes_jsonl(tmp_path):
    data_path = _write_dataset(tmp_path)
    log_dir = _write_logs(tmp_path)
    output = tmp_path / "hypotheses.jsonl"
    count = export_hypotheses(
        log_dir=str(log_dir),
        data_path=str(data_path),
        output_path=str(output),
    )
    assert count == 1
    exported = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert exported[0]["question_id"] == "q-1"
