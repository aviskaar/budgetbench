import pytest
from unittest.mock import MagicMock
from budgetbench.evaluation.harness import run_evaluation_task
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
    
    # Check metrics logged
    metrics = logger.log_metrics.call_args[0][0]
    assert "quality" in metrics
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
