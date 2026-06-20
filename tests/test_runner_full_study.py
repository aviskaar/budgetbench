import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.run_pilot import (
    BUDGET_TIERS,
    DEFAULT_TASKS_CONFIG,
    FULL_STUDY_BUDGET_TIERS,
    build_strategies,
    get_tokenizer_fn,
    load_completed_combinations,
    resolve_budget_tiers,
)


def test_full_study_budget_tiers():
    """Full study uses all 5 standard budget tiers."""
    assert FULL_STUDY_BUDGET_TIERS == [2048, 4096, 8192, 16384, 32768]
    assert len(FULL_STUDY_BUDGET_TIERS) == 5


def test_resolve_budget_tiers_defaults():
    assert resolve_budget_tiers() == BUDGET_TIERS
    assert resolve_budget_tiers(full_study=True) == FULL_STUDY_BUDGET_TIERS


def test_resolve_budget_tiers_custom_values():
    assert resolve_budget_tiers(selected_budgets=[2048, 8192, 32768]) == [
        2048,
        8192,
        32768,
    ]


def test_resolve_budget_tiers_limit_applies_to_custom_values():
    assert resolve_budget_tiers(
        selected_budgets=[2048, 8192, 32768],
        limit_budgets=2,
    ) == [2048, 8192]


def test_resolve_budget_tiers_rejects_nonpositive_values():
    with pytest.raises(ValueError):
        resolve_budget_tiers(selected_budgets=[2048, 0])


def test_default_tokenizer_counts_special_marker_as_text():
    tokenizer = get_tokenizer_fn()
    assert tokenizer("literal <|endoftext|> marker") > 0


def test_full_study_default_tasks_cover_requirements():
    """Full study includes the required task families."""
    task_limits = {
        cfg["name"]: cfg["default_limit"]
        for cfg in DEFAULT_TASKS_CONFIG
        if cfg.get("enabled_by_default", True)
    }
    assert task_limits == {"swe": 100, "long": 100, "memory": 30, "tau": 200}
    assert any(
        cfg["name"] == "longmem"
        and cfg["default_limit"] == 20
        and cfg.get("enabled_by_default") is False
        for cfg in DEFAULT_TASKS_CONFIG
    )


def test_resume_skip(tmp_path):
    """load_completed_combinations returns the correct set of finished combos."""
    summary_file = tmp_path / "summary.jsonl"
    rows = [
        {"task": "swe", "strategy": "truncation", "budget": 2048, "accuracy": 0.0, "total": 3, "success": 0, "duration_sec": 10.0},
        {"task": "long", "strategy": "rag", "budget": 8192, "accuracy": 0.5, "total": 10, "success": 5, "duration_sec": 30.0},
    ]
    summary_file.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    completed = load_completed_combinations(str(summary_file))
    assert ("swe", "truncation", 2048) in completed
    assert ("long", "rag", 8192) in completed
    assert ("swe", "rag", 4096) not in completed


def test_resume_malformed_line(tmp_path):
    """Malformed lines in summary.jsonl are silently skipped."""
    summary_file = tmp_path / "summary.jsonl"
    valid_row = {"task": "swe", "strategy": "summary", "budget": 4096, "accuracy": 0.0, "total": 5, "success": 0, "duration_sec": 5.0}
    summary_file.write_text(json.dumps(valid_row) + "\nnot-valid-json\n")

    completed = load_completed_combinations(str(summary_file))
    assert ("swe", "summary", 4096) in completed


def test_resume_missing_file(tmp_path):
    """load_completed_combinations returns empty set when file does not exist."""
    completed = load_completed_combinations(str(tmp_path / "nonexistent.jsonl"))
    assert completed == set()


def test_summary_schema():
    """Summary rows written by the runner include the 'model' field."""
    required_keys = {
        "timestamp", "model", "task", "strategy", "budget",
        "accuracy", "total", "success", "duration_sec",
    }
    summary = {
        "timestamp": "20260508_120000",
        "model": "qwen2.5:14b",
        "task": "swe",
        "strategy": "truncation",
        "budget": 2048,
        "accuracy": 0.0,
        "total": 20,
        "success": 0,
        "duration_sec": 120.0,
    }
    assert required_keys.issubset(summary.keys()), (
        f"Missing keys: {required_keys - summary.keys()}"
    )


def test_build_strategies_exposes_full_context():
    strategies = build_strategies(llm_client=lambda messages: "ok", selected_names=["full_context"])
    assert list(strategies) == ["full_context"]


def test_build_strategies_exposes_lean_retrieval(monkeypatch):
    class DummyLeanRetrievalStrategy:
        pass

    monkeypatch.setattr(
        "scripts.run_pilot.LeanRetrievalStrategy",
        DummyLeanRetrievalStrategy,
    )
    strategies = build_strategies(
        llm_client=lambda messages: "ok",
        selected_names=["lean_retrieval"],
    )
    assert list(strategies) == ["lean_retrieval"]
    assert isinstance(strategies["lean_retrieval"], DummyLeanRetrievalStrategy)
