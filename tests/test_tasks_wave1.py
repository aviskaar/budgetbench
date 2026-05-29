import pytest
import json
from unittest.mock import MagicMock, patch
from budgetbench.tasks.long import LongBenchV2Task
from budgetbench.tasks.swe import SWEBenchTask

@pytest.fixture
def mock_datasets():
    with patch("datasets.load_dataset") as mock:
        yield mock

def test_longbench_wrapper(mock_datasets):
    # Mock dataset
    mock_item = {
        "context": "The capital of France is Paris.",
        "question": "What is the capital of France?",
        "choice_A": "London",
        "choice_B": "Paris",
        "choice_C": "Berlin",
        "choice_D": "Rome",
        "answer": "B"
    }
    # datasets.load_dataset returns a dataset object that is iterable
    mock_ds = MagicMock()
    mock_ds.__iter__.return_value = [mock_item]
    mock_ds.__len__.return_value = 1
    mock_datasets.return_value = mock_ds
    
    task = LongBenchV2Task()
    items = task.get_dataset()
    assert len(items) == 1
    assert items[0]["answer"] == "B"
    
    # Mock LLM and Strategy
    strategy = MagicMock(side_effect=lambda msgs, budget: msgs)
    llm_client = MagicMock(return_value="The answer is B.")
    tokenizer_fn = MagicMock(return_value=10)
    logger = MagicMock()
    
    prediction = task.run(
        item=items[0],
        strategy=strategy,
        llm_client=llm_client,
        tokenizer_fn=tokenizer_fn,
        max_tokens=1000,
        logger=logger
    )
    
    assert task.grade(prediction, items[0]["answer"]) is True
    assert task.grade("A", "B") is False
    assert task.grade("B.", "B") is True
    assert task.grade("Selected answer: C", "C") is True

GOLD_PATCH = """\
diff --git a/src/foo.py b/src/foo.py
--- a/src/foo.py
+++ b/src/foo.py
@@ -10,7 +10,7 @@
-    return x + 1
+    return x + 2
"""

def test_swe_run_extracts_patch(mock_datasets):
    mock_item = {
        "instance_id": "test_id",
        "problem_statement": "Fix the off-by-one error in foo.py",
        "hints_text": "",
        "patch": GOLD_PATCH,
    }
    mock_ds = MagicMock()
    mock_ds.__iter__.return_value = [mock_item]
    mock_ds.__len__.return_value = 1
    mock_datasets.return_value = mock_ds

    task = SWEBenchTask()
    items = task.get_dataset()

    # Model returns the patch inline
    llm_client = MagicMock(return_value=GOLD_PATCH)
    strategy = MagicMock(side_effect=lambda msgs, budget: msgs)
    tokenizer_fn = MagicMock(return_value=10)
    logger = MagicMock()

    result = task.run(
        item=items[0],
        strategy=strategy,
        llm_client=llm_client,
        tokenizer_fn=tokenizer_fn,
        max_tokens=2000,
        logger=logger,
    )

    assert "diff --git" in result
    assert llm_client.call_count == 1  # single-turn, not multi-turn


def test_swe_grade_exact_match():
    task = SWEBenchTask()
    item = {"patch": GOLD_PATCH}
    assert task.grade(GOLD_PATCH, item) == 1.0


def test_swe_grade_wrong_file():
    task = SWEBenchTask()
    wrong = GOLD_PATCH.replace("src/foo.py", "src/bar.py")
    item = {"patch": GOLD_PATCH}
    assert task.grade(wrong, item) == 0.0


def test_swe_grade_right_file_wrong_lines():
    task = SWEBenchTask()
    wrong_lines = """\
diff --git a/src/foo.py b/src/foo.py
--- a/src/foo.py
+++ b/src/foo.py
@@ -10,7 +10,7 @@
-    return x + 1
+    return x + 99
"""
    item = {"patch": GOLD_PATCH}
    score = task.grade(wrong_lines, item)
    # File matched, removal line shared, only addition differs → 1/2 lines match
    # 0.4 * file_recall(1.0) + 0.6 * line_score(0.5) = 0.7
    assert score == pytest.approx(0.7)


def test_swe_grade_empty_patch():
    task = SWEBenchTask()
    assert task.grade("", {"patch": GOLD_PATCH}) == 0.0


def test_swe_grade_no_gold():
    task = SWEBenchTask()
    assert task.grade(GOLD_PATCH, {"patch": ""}) == 0.0


def test_longbench_chunking():
    """Verify format_message() chunks large context into multiple user messages."""
    task = LongBenchV2Task()
    large_item = {
        "context": "X" * 10000,
        "question": "What is X?",
        "choice_A": "One",
        "choice_B": "Two",
        "choice_C": "Three",
        "choice_D": "Four",
        "answer": "A",
    }
    messages = task.format_message(large_item, budget=2048)
    assert messages[0]["role"] == "system"
    assert messages[-1]["content"].startswith("Question:")
    context_msgs = messages[1:-1]
    assert len(context_msgs) == 5
    assert all(m["role"] == "user" for m in context_msgs)
    assert "Context part 1:" in context_msgs[0]["content"]

    small_item = {**large_item, "context": "Short context."}
    small_msgs = task.format_message(small_item, budget=8192)
    assert len(small_msgs) == 3
    assert "Context:\n" in small_msgs[1]["content"]
