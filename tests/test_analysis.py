import json
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.analyze_results import compute_violation_rates, load_summary_files


def _write_summary(tmp_path, rows):
    summary_file = tmp_path / "summary.jsonl"
    summary_file.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return str(tmp_path)


def test_load_summary_files(tmp_path):
    rows = [
        {
            "model": "qwen2.5:14b",
            "task": "swe",
            "strategy": "truncation",
            "budget": 2048,
            "accuracy": 0.1,
            "total": 20,
            "success": 2,
            "duration_sec": 100.0,
        },
        {
            "model": "qwen2.5:14b",
            "task": "long",
            "strategy": "rag",
            "budget": 8192,
            "accuracy": 0.4,
            "total": 50,
            "success": 20,
            "duration_sec": 200.0,
        },
    ]
    log_dir = _write_summary(tmp_path, rows)
    df = load_summary_files([log_dir])
    assert len(df) == 2
    assert "accuracy" in df.columns
    assert "task" in df.columns


def test_load_summary_files_missing_dir():
    df = load_summary_files(["nonexistent_dir/"])
    assert isinstance(df, pd.DataFrame)
    assert df.empty


def test_violation_rate_from_jsonl(tmp_path):
    summary_row = {
        "model": "qwen2.5:14b",
        "task": "swe",
        "strategy": "truncation",
        "budget": 2048,
        "accuracy": 0.0,
        "total": 3,
        "success": 0,
        "duration_sec": 10.0,
    }
    log_dir = _write_summary(tmp_path, [summary_row])

    combo_file = tmp_path / "swe_truncation_2048.jsonl"
    turns = [
        {"tokens_used": 2100, "budget": 2048, "violation": True},
        {"tokens_used": 1900, "budget": 2048, "violation": False},
        {"tokens_used": 2200, "budget": 2048, "violation": True},
        {"tokens_used": 1800, "budget": 2048, "violation": False},
    ]
    combo_file.write_text("\n".join(json.dumps(t) for t in turns) + "\n")

    df = compute_violation_rates(load_summary_files([log_dir]))
    assert "violation_rate" in df.columns
    assert df["violation_rate"].iloc[0] == pytest.approx(0.5)


def test_violation_rate_missing_combo_file(tmp_path):
    summary_row = {
        "model": "qwen2.5:14b",
        "task": "swe",
        "strategy": "mem0",
        "budget": 4096,
        "accuracy": 0.0,
        "total": 5,
        "success": 0,
        "duration_sec": 5.0,
    }
    log_dir = _write_summary(tmp_path, [summary_row])
    df = compute_violation_rates(load_summary_files([log_dir]))
    assert df["violation_rate"].iloc[0] is None or pd.isna(df["violation_rate"].iloc[0])
