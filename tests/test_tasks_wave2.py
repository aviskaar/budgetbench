import pytest
from unittest.mock import MagicMock, patch
from budgetbench.tasks import get_task, TauBenchTask, LongBenchV2Task, SWEBenchTask
from budgetbench.tasks.longmem import LongMemEvalTask
from budgetbench.tasks.memory import MemoryUpdateTask
from budgetbench.tasks.base import BaseTask
from budgetbench.evaluation.runner import TaskRunner
from budgetbench.core.strategy import MemoryStrategy
from budgetbench.evaluation.metrics import MetricsLogger

def test_tau_wrapper(tokenizer_fn, llm_client):
    task = get_task("tau")
    assert isinstance(task, TauBenchTask)

    # Mocking strategy and logger
    strategy = MagicMock(spec=MemoryStrategy)
    strategy.side_effect = lambda msgs, budget: msgs  # Identity strategy
    logger = MagicMock(spec=MetricsLogger)

    # Mock item
    item = {"goal": "Test goal", "id": "test-1"}

    # When tau2-bench is absent, run() must raise ImportError (not return mock success)
    with patch("budgetbench.tasks.tau.TAU2_AVAILABLE", False), \
         pytest.raises(ImportError, match="tau2-bench"):
        task.run(
            item=item,
            strategy=strategy,
            llm_client=llm_client,
            tokenizer_fn=tokenizer_fn,
            max_tokens=100,
            logger=logger,
        )

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

    memory_task = get_task("memory")
    assert isinstance(memory_task, MemoryUpdateTask)
    assert isinstance(memory_task, BaseTask)

    longmem_task = get_task("longmem")
    assert isinstance(longmem_task, LongMemEvalTask)
    assert isinstance(longmem_task, BaseTask)
    
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
        logger=logger,
    )

    # When tau2-bench is absent, get_dataset() raises ImportError
    with patch("budgetbench.tasks.tau.TAU2_AVAILABLE", False), \
         pytest.raises(ImportError, match="tau2-bench"):
        runner.run_evaluation(max_tokens=100, limit=1)
