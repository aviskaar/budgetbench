import json

import pytest

from budgetbench.tasks import get_task
from budgetbench.tasks.longmem import LongMemEvalTask


def _write_longmem_fixture(tmp_path):
    data = [
        {
            "question_id": "fixture_001",
            "question_type": "temporal-reasoning",
            "question": "Which cafe did I visit first?",
            "answer": "Blue Cup",
            "question_date": "2023/04/10 (Mon) 23:07",
            "haystack_dates": [
                "2023/04/09 (Sun) 10:00",
                "2023/04/10 (Mon) 12:00",
            ],
            "haystack_session_ids": ["s1", "s2"],
            "haystack_sessions": [
                [
                    {"role": "user", "content": "I visited Blue Cup in the morning.", "has_answer": True},
                    {"role": "assistant", "content": "That sounds nice.", "has_answer": False},
                ],
                [
                    {"role": "user", "content": "I later visited Red Mug.", "has_answer": False},
                    {"role": "assistant", "content": "Good to know.", "has_answer": False},
                ],
            ],
            "answer_session_ids": ["s1"],
        }
    ]
    path = tmp_path / "longmemeval_oracle.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_longmem_task_limit_samples_categories_round_robin(tmp_path):
    rows = []
    for index, category in enumerate(["temporal-reasoning", "temporal-reasoning", "knowledge-update"]):
        rows.append(
            {
                "question_id": f"fixture_{index}",
                "question_type": category,
                "question": "What is the answer?",
                "answer": f"answer-{index}",
                "question_date": "2023/04/10 (Mon) 23:07",
                "haystack_dates": ["2023/04/09 (Sun) 10:00"],
                "haystack_session_ids": ["s1"],
                "haystack_sessions": [[{"role": "user", "content": f"answer-{index}", "has_answer": True}]],
                "answer_session_ids": ["s1"],
            }
        )
    path = tmp_path / "longmemeval_oracle.json"
    path.write_text(json.dumps(rows), encoding="utf-8")

    task = LongMemEvalTask(data_path=str(path))
    sampled = task.get_dataset(limit=2)

    assert [item["question_type"] for item in sampled] == [
        "knowledge-update",
        "temporal-reasoning",
    ]


def test_longmem_task_loads_official_shape(tmp_path):
    path = _write_longmem_fixture(tmp_path)
    task = LongMemEvalTask(data_path=str(path))

    item = task.get_dataset(limit=1)[0]
    messages = task.format_message(item)

    assert item["question_id"] == "fixture_001"
    assert messages[0]["role"] == "system"
    assert any("2023/04/09" in message["content"] for message in messages)
    assert messages[-1]["content"].startswith("[Question date:")


def test_longmem_task_metric_context_and_grading(tmp_path):
    path = _write_longmem_fixture(tmp_path)
    task = LongMemEvalTask(data_path=str(path))
    item = task.get_dataset(limit=1)[0]

    assert task.metric_context(item) == {
        "memory_category": "temporal_reasoning",
        "longmem_question_id": "fixture_001",
        "longmem_grader": "normalized_contains",
    }
    assert task.grade("The answer is Blue Cup.", item) is True
    assert task.grade("Red Mug", item) is False


def test_longmem_task_requires_data_path(tmp_path):
    missing = tmp_path / "missing.json"
    task = LongMemEvalTask(data_path=str(missing))

    with pytest.raises(FileNotFoundError, match="LongMemEval data not found"):
        task.get_dataset(limit=1)


def test_longmem_registry(monkeypatch, tmp_path):
    path = _write_longmem_fixture(tmp_path)
    monkeypatch.setenv("BUDGETBENCH_LONGMEMEVAL_PATH", str(path))

    assert isinstance(get_task("longmem"), LongMemEvalTask)
