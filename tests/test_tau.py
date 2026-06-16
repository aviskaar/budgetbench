"""
Tests for TauBenchTask with correct ImportError behavior and tau2 task loading.

These tests cover:
- test_tau_raises_importerror_when_tau2_absent: run() and get_dataset() raise ImportError
- test_tau_dataset_calls_registry_when_available: get_dataset() calls tau2 task loaders when mocked
- test_tau_dataset_limit: get_dataset(limit=1) returns at most 1 item
- test_tau_run_calls_harness_when_available: run() calls run_evaluation_task (not mock success)
"""
import pytest
from unittest.mock import MagicMock, patch


def test_tau_raises_importerror_when_tau2_absent():
    """When tau2-bench is not installed, run() and get_dataset() raise ImportError."""
    with patch("budgetbench.tasks.tau.TAU2_AVAILABLE", False):
        from budgetbench.tasks.tau import TauBenchTask
        task = TauBenchTask()
        with pytest.raises(ImportError, match="tau2-bench"):
            task.get_dataset()
        with pytest.raises(ImportError, match="tau2-bench"):
            task.run(
                item={"goal": "test", "id": "1"},
                strategy=MagicMock(),
                llm_client=MagicMock(),
                tokenizer_fn=lambda s: len(s.split()),
                max_tokens=100,
                logger=MagicMock(),
            )


def test_tau_dataset_calls_env_when_available():
    """When tau2 is mocked as available, get_dataset() calls task loaders."""
    task_one = MagicMock(id="retail-1")
    task_two = MagicMock(id="airline-1")
    mock_registry = MagicMock()
    mock_registry.registry.get_tasks_loader.side_effect = [
        lambda: [task_one],
        lambda: [task_two],
    ]
    with patch("budgetbench.tasks.tau.TAU2_AVAILABLE", True), \
         patch("budgetbench.tasks.tau._tau2_registry", mock_registry):
        import budgetbench.tasks.tau as tau_mod
        task = tau_mod.TauBenchTask()
        items = task.get_dataset()
        assert len(items) == 2
        assert items[0]["id"] == "retail:retail-1"
        assert items[1]["id"] == "airline:airline-1"


def test_tau_dataset_limit():
    """get_dataset(limit=1) returns at most 1 item."""
    mock_registry = MagicMock()
    mock_registry.registry.get_tasks_loader.side_effect = [
        lambda: [MagicMock(id="1"), MagicMock(id="2")],
        lambda: [MagicMock(id="3")],
    ]
    with patch("budgetbench.tasks.tau.TAU2_AVAILABLE", True), \
         patch("budgetbench.tasks.tau._tau2_registry", mock_registry):
        import budgetbench.tasks.tau as tau_mod
        task = tau_mod.TauBenchTask()
        items = task.get_dataset(limit=1)
        assert len(items) == 1


def test_tau_run_calls_harness_when_available(tokenizer_fn):
    """When tau2 is mocked, run() calls run_evaluation_task (not mock success)."""
    mock_llm = MagicMock(
        return_value={"choices": [{"message": {"content": "action"}}]}
    )
    mock_strategy = MagicMock(side_effect=lambda msgs, budget: msgs)
    mock_logger = MagicMock()

    with patch("budgetbench.tasks.tau.TAU2_AVAILABLE", True), \
         patch(
             "budgetbench.tasks.tau.run_evaluation_task",
             return_value={"choices": [{"message": {"content": "action"}}]},
         ) as mock_harness:
        import budgetbench.tasks.tau as tau_mod
        task = tau_mod.TauBenchTask()
        result = task.run(
            item={"scenario": "Test goal", "id": "t1", "domain": "retail"},
            strategy=mock_strategy,
            llm_client=mock_llm,
            tokenizer_fn=tokenizer_fn,
            max_tokens=200,
            logger=mock_logger,
        )
        assert mock_harness.called, (
            "run_evaluation_task must be called — harness must not be bypassed"
        )
        assert "success" in result
