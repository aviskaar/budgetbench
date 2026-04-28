import pytest
from unittest.mock import MagicMock
from budgetbench.tasks import get_task, TauBenchTask, LongBenchV2Task, SWEBenchTask
from budgetbench.tasks.base import BaseTask
from budgetbench.evaluation.runner import TaskRunner
from budgetbench.core.strategy import MemoryStrategy
from budgetbench.evaluation.metrics import MetricsLogger

def test_tau_wrapper(tokenizer_fn, llm_client):
    task = get_task("tau")
    assert isinstance(task, TauBenchTask)
    
    # Mocking strategy and logger
    strategy = MagicMock(spec=MemoryStrategy)
    strategy.side_effect = lambda msgs, budget: msgs # Identity strategy
    logger = MagicMock(spec=MetricsLogger)
    
    # Mock item
    item = {"goal": "Test goal", "id": "test-1"}
    
    # Run
    # Since we mocked env to be None or if it's missing, it returns a mock success
    result = task.run(
        item=item,
        strategy=strategy,
        llm_client=llm_client,
        tokenizer_fn=tokenizer_fn,
        max_tokens=100,
        logger=logger
    )
    
    assert "success" in result
    assert task.grade(result, item) is True

def test_task_registry():
    long_task = get_task("long")
    assert isinstance(long_task, LongBenchV2Task)
    assert isinstance(long_task, BaseTask)
    
    swe_task = get_task("swe")
    assert isinstance(swe_task, SWEBenchTask)
    assert isinstance(swe_task, BaseTask)
    
    tau_task = get_task("tau")
    assert isinstance(tau_task, TauBenchTask)
    assert isinstance(tau_task, BaseTask)
    
    with pytest.raises(ValueError):
        get_task("nonexistent")

def test_runner(tokenizer_fn, llm_client):
    task = get_task("tau")
    strategy = MagicMock(spec=MemoryStrategy)
    strategy.side_effect = lambda msgs, budget: msgs
    logger = MagicMock(spec=MetricsLogger)
    
    runner = TaskRunner(
        task=task,
        strategy=strategy,
        llm_client=llm_client,
        tokenizer_fn=tokenizer_fn,
        logger=logger
    )
    
    results = runner.run_evaluation(max_tokens=100, limit=1)
    assert len(results) == 1
    assert results[0]["is_correct"] is True
