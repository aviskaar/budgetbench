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

def test_longbench_chunking():
    task = LongBenchV2Task()
    item = {
        "context": "a" * 5000,
        "question": "Which letter is repeated?",
        "choice_A": "a",
        "choice_B": "b",
        "choice_C": "c",
        "choice_D": "d",
        "answer": "A",
    }

    messages = task.format_message(item, budget=1024)

    assert messages[0]["role"] == "system"
    assert messages[-1]["content"].startswith("Question: Which letter is repeated?")
    assert "A: a" in messages[-1]["content"]
    assert len(messages[1:-1]) == 5
    assert all(msg["content"].startswith("Context part ") for msg in messages[1:-1])
    assert all(len(msg["content"].split("\n", 1)[1]) <= 1024 for msg in messages[1:-1])

    short_messages = task.format_message({**item, "context": "short"}, budget=1024)

    assert len(short_messages) == 3
    assert short_messages[1]["content"] == "Context:\nshort"

def test_swe_wrapper(mock_datasets):
    # Mock dataset
    mock_item = {
        "instance_id": "test_id",
        "problem_statement": "Fix the bug in file.py",
        "repo": "org/repo",
        "version": "1.0"
    }
    mock_ds = MagicMock()
    mock_ds.__iter__.return_value = [mock_item]
    mock_ds.__len__.return_value = 1
    mock_datasets.return_value = mock_ds
    
    task = SWEBenchTask()
    items = task.get_dataset()
    
    # Mock LLM: 1st turn 'ls', 2nd turn 'submit'
    llm_responses = [
        {"choices": [{"message": {"content": '{"thought": "listing files", "command": "ls"}'}}]},
        {"choices": [{"message": {"content": '{"thought": "done", "command": "submit"}'}}]}
    ]
    llm_client = MagicMock(side_effect=llm_responses)
    strategy = MagicMock(side_effect=lambda msgs, budget: msgs)
    tokenizer_fn = MagicMock(return_value=10)
    logger = MagicMock()
    
    patch_result = task.run(
        item=items[0],
        strategy=strategy,
        llm_client=llm_client,
        tokenizer_fn=tokenizer_fn,
        max_tokens=2000,
        logger=logger,
        use_docker=False
    )
    
    assert patch_result != ""
    assert task.grade(patch_result, items[0]) is True
    assert llm_client.call_count == 2
