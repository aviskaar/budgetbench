import pytest
import json
import sys
import types
from unittest.mock import MagicMock, patch
from budgetbench.tasks.long import LongBenchV2Task
from budgetbench.tasks.swe import SWEBenchTask

@pytest.fixture
def mock_datasets():
    fake_module = types.ModuleType("datasets")
    fake_module.load_dataset = MagicMock()
    original = sys.modules.get("datasets")
    sys.modules["datasets"] = fake_module
    try:
        yield fake_module.load_dataset
    finally:
        if original is None:
            sys.modules.pop("datasets", None)
        else:
            sys.modules["datasets"] = original

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
    assert items[0]["_budgetbench_item_id"] == "THUDM/LongBench-v2:train:0"
    
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


def test_swe_run_trims_user_prompt_instead_of_dropping_it(mock_datasets):
    mock_item = {
        "instance_id": "test_id",
        "problem_statement": "very long bug report " * 200,
        "hints_text": "long hints " * 200,
        "patch": GOLD_PATCH,
    }
    mock_ds = MagicMock()
    mock_ds.__iter__.return_value = [mock_item]
    mock_ds.__len__.return_value = 1
    mock_datasets.return_value = mock_ds

    task = SWEBenchTask()
    items = task.get_dataset()

    captured = {}

    def llm_client(messages):
        captured["messages"] = messages
        return GOLD_PATCH

    strategy = MagicMock(side_effect=lambda msgs, budget: msgs)

    def tokenizer(text: str) -> int:
        return len(text.split())

    logger = MagicMock()
    task.run(
        item=items[0],
        strategy=strategy,
        llm_client=llm_client,
        tokenizer_fn=tokenizer,
        max_tokens=120,
        logger=logger,
    )

    assert len(captured["messages"]) == 2
    assert captured["messages"][1]["role"] == "user"
    assert captured["messages"][1]["content"].startswith("Bug report:\n")
    assert "very long bug report" in captured["messages"][1]["content"]


def test_swe_extract_patch_discards_trailing_markdown_and_invalid_tail():
    task = SWEBenchTask()
    content = """diff --git a/src/foo.py b/src/foo.py
index 123..456 100644
--- a/src/foo.py
+++ b/src/foo.py
@@ -10,7 +10,7 @@
-    return x + 1
+    return x + 2
```"""
    patch = task._extract_patch(content)
    assert patch.endswith("\n")
    assert "```" not in patch
    assert patch.startswith("diff --git")


def test_swe_extract_patch_returns_empty_for_header_only_diff():
    task = SWEBenchTask()
    content = """diff --git a/src/foo.py b/src/foo.py
index 123..456 100644
--- a/src/foo.py
+++ b/src/foo.py
"""
    assert task._extract_patch(content) == ""


def test_swe_extract_patch_rejects_mismatched_header_paths():
    task = SWEBenchTask()
    content = """diff --git a/src/foo.py b/src/foo.py
index 123..456 100644
--- a/src.bar.py
+++ b/src/foo.py
@@ -1,1 +1,1 @@
-x = 1
+x = 2
"""
    assert task._extract_patch(content) == ""


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


def test_longbench_chunking_respects_override():
    task = LongBenchV2Task(context_chunk_tokens=100, context_char_per_token=1)
    item = {
        "context": "X" * 250,
        "question": "What is X?",
        "choice_A": "One",
        "choice_B": "Two",
        "choice_C": "Three",
        "choice_D": "Four",
        "answer": "A",
    }
    messages = task.format_message(item, budget=2048)
    assert len(messages[1:-1]) == 3


def test_longbench_natural_prompt_token_count():
    task = LongBenchV2Task()
    item = {
        "context": "alpha beta gamma",
        "question": "Which word appears?",
        "choice_A": "alpha",
        "choice_B": "delta",
        "choice_C": "epsilon",
        "choice_D": "zeta",
        "answer": "A",
    }

    token_count = task.natural_prompt_token_count(
        item,
        tokenizer_fn=lambda text: len(text.split()),
    )

    assert token_count > 0
