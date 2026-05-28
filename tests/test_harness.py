import pytest
from unittest.mock import MagicMock, call
from budgetbench.evaluation.harness import run_evaluation_task
from budgetbench.evaluation.runner import TaskRunner
from budgetbench.core.exceptions import BudgetExceededError

def test_run_evaluation_task_success():
    messages = [{"role": "user", "content": "hello"}]
    strategy = MagicMock(side_effect=lambda msgs, budget: msgs)
    llm_client = MagicMock(return_value="mock response")
    tokenizer_fn = MagicMock(return_value=10) # 10 tokens per message
    logger = MagicMock()
    
    result = run_evaluation_task(
        messages=messages,
        strategy=strategy,
        llm_client=llm_client,
        tokenizer_fn=tokenizer_fn,
        max_tokens=100,
        logger=logger
    )
    
    assert result == "mock response"
    strategy.assert_called_once()
    llm_client.assert_called_once()
    logger.log_metrics.assert_called_once()
    
    # Check metrics logged — quality must NOT be here (runner logs it after grading)
    metrics = logger.log_metrics.call_args[0][0]
    assert "quality" not in metrics, "harness must not log quality; grading happens in runner"
    assert "used_budget" in metrics
    assert metrics["used_budget"] == 10
    assert metrics["violation_rate"] == 0.0

def test_run_evaluation_task_retry_success():
    messages = [{"role": "user", "content": "hello"}]
    
    # First call fails budget, second call passes
    def strategy_mock(msgs, budget):
        if strategy_mock.call_count == 0:
            strategy_mock.call_count += 1
            return [{"role": "user", "content": "very long message"}]
        return msgs
    strategy_mock.call_count = 0
    
    strategy = MagicMock(side_effect=strategy_mock)
    
    llm_client = MagicMock(return_value="mock response")
    
    def tokenizer_fn(text):
        if text == "very long message":
            return 200
        return 10
    
    logger = MagicMock()
    
    result = run_evaluation_task(
        messages=messages,
        strategy=strategy,
        llm_client=llm_client,
        tokenizer_fn=tokenizer_fn,
        max_tokens=100,
        logger=logger
    )
    
    assert result == "mock response"
    assert strategy.call_count == 2
    assert logger.log_metrics.call_args[0][0]["violation_rate"] > 0

def test_run_evaluation_task_max_retries_exceeded():
    messages = [{"role": "user", "content": "hello"}]
    
    # Always fails budget
    strategy = MagicMock(side_effect=lambda msgs, budget: [{"role": "user", "content": "too long"}])
    llm_client = MagicMock()
    tokenizer_fn = MagicMock(return_value=200)
    logger = MagicMock()
    
    with pytest.raises(BudgetExceededError):
        run_evaluation_task(
            messages=messages,
            strategy=strategy,
            llm_client=llm_client,
            tokenizer_fn=tokenizer_fn,
            max_tokens=100,
            logger=logger,
            max_retries=2
        )

    assert strategy.call_count == 2


def test_runner_logs_actual_quality():
    """quality logged by runner must equal the grade, not a hardcoded 1.0."""
    item = {"id": "x", "content": "q"}
    grade_score = 0.42

    task = MagicMock()
    task.get_dataset.return_value = [item]
    task.run.return_value = {"response": "some answer"}
    task.grade.return_value = grade_score

    strategy = MagicMock(side_effect=lambda msgs, budget: msgs)
    llm_client = MagicMock(return_value="some answer")
    tokenizer_fn = MagicMock(return_value=5)
    logger = MagicMock()

    runner = TaskRunner(
        task=task,
        strategy=strategy,
        llm_client=llm_client,
        tokenizer_fn=tokenizer_fn,
        logger=logger,
    )
    results = runner.run_evaluation(max_tokens=1000, limit=1)

    assert len(results) == 1
    assert results[0]["is_correct"] == grade_score

    # Find the log_metrics call that contains "quality"
    quality_calls = [
        c for c in logger.log_metrics.call_args_list
        if "quality" in c[0][0]
    ]
    assert quality_calls, "runner must log a 'quality' metric"
    logged_quality = quality_calls[-1][0][0]["quality"]
    assert logged_quality == grade_score, (
        f"expected quality={grade_score}, got {logged_quality} — "
        "quality must not be hardcoded to 1.0"
    )
