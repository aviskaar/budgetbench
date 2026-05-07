"""
Tests for TauBenchTask with correct ImportError behavior when tau2-bench is absent.

These tests cover:
- test_tau_raises_importerror_when_tau2_absent: run() and get_dataset() raise ImportError
- test_tau_dataset_calls_env_when_available: get_dataset() calls env.get_dataset() when mocked
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
    """When tau2 is mocked as available, get_dataset() calls env.get_dataset()."""
    mock_env = MagicMock()
    mock_env.get_dataset.return_value = [
        {"goal": "Find a laptop under $1000", "id": "retail-1"},
        {"goal": "Cancel my flight to Paris", "id": "airline-1"},
    ]
    with patch("budgetbench.tasks.tau.TAU2_AVAILABLE", True), \
         patch("budgetbench.tasks.tau._tau2_get_env", return_value=mock_env):
        import budgetbench.tasks.tau as tau_mod
        task = tau_mod.TauBenchTask()
        items = task.get_dataset()
        assert len(items) == 2
        assert all("goal" in item and "id" in item for item in items)


def test_tau_dataset_limit():
    """get_dataset(limit=1) returns at most 1 item."""
    mock_env = MagicMock()
    mock_env.get_dataset.return_value = [
        {"goal": "goal 1", "id": "1"},
        {"goal": "goal 2", "id": "2"},
    ]
    with patch("budgetbench.tasks.tau.TAU2_AVAILABLE", True), \
         patch("budgetbench.tasks.tau._tau2_get_env", return_value=mock_env):
        import budgetbench.tasks.tau as tau_mod
        task = tau_mod.TauBenchTask()
        items = task.get_dataset(limit=1)
        assert len(items) == 1


def test_tau_run_calls_harness_when_available(tokenizer_fn):
    """When tau2 is mocked, run() calls run_evaluation_task (not mock success)."""
    mock_env = MagicMock()
    mock_env.reset.return_value = ("Initial obs", {"tools": []})
    mock_env.step.return_value = ("Next obs", 1.0, True, False, {"success": True})

    mock_llm = MagicMock(
        return_value={"choices": [{"message": {"content": "action"}}]}
    )
    mock_strategy = MagicMock(side_effect=lambda msgs, budget: msgs)
    mock_logger = MagicMock()

    with patch("budgetbench.tasks.tau.TAU2_AVAILABLE", True), \
         patch("budgetbench.tasks.tau._tau2_get_env", return_value=mock_env), \
         patch(
             "budgetbench.tasks.tau.run_evaluation_task",
             return_value={"choices": [{"message": {"content": "action"}}]},
         ) as mock_harness:
        import budgetbench.tasks.tau as tau_mod
        task = tau_mod.TauBenchTask()
        task.env = mock_env
        result = task.run(
            item={"goal": "Test goal", "id": "t1"},
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
