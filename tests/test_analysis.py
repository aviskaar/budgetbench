import json
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.analyze_results import (
    compute_grouped_quality,
    compute_paired_deltas,
    compute_quality_intervals,
    compute_violation_rates,
    load_summary_files,
)


def _write_summary(tmp_path, rows):
    summary_file = tmp_path / "summary.jsonl"
    summary_file.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return str(tmp_path)


def test_load_summary_files(tmp_path):
    rows = [
        {"model": "qwen2.5:14b", "task": "swe", "strategy": "truncation", "budget": 2048, "accuracy": 0.1, "total": 20, "success": 2, "duration_sec": 100.0},
        {"model": "qwen2.5:14b", "task": "long", "strategy": "rag", "budget": 8192, "accuracy": 0.4, "total": 50, "success": 20, "duration_sec": 200.0},
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
    summary_row = {"model": "qwen2.5:14b", "task": "swe", "strategy": "truncation", "budget": 2048, "accuracy": 0.0, "total": 3, "success": 0, "duration_sec": 10.0}
    log_dir = _write_summary(tmp_path, [summary_row])

    combo_file = tmp_path / "swe_truncation_2048.jsonl"
    turns = [
        {"tokens_used": 2100, "budget": 2048, "violation": True},
        {"tokens_used": 1900, "budget": 2048, "violation": False},
        {"tokens_used": 2200, "budget": 2048, "violation": True},
        {"tokens_used": 1800, "budget": 2048, "violation": False},
    ]
    combo_file.write_text("\n".join(json.dumps(t) for t in turns) + "\n")

    df = load_summary_files([log_dir])
    df = compute_violation_rates(df)
    assert "violation_rate" in df.columns
    assert df["violation_rate"].iloc[0] == pytest.approx(0.5)


def test_violation_rate_missing_combo_file(tmp_path):
    summary_row = {"model": "qwen2.5:14b", "task": "swe", "strategy": "mem0", "budget": 4096, "accuracy": 0.0, "total": 5, "success": 0, "duration_sec": 5.0}
    log_dir = _write_summary(tmp_path, [summary_row])
    df = load_summary_files([log_dir])
    df = compute_violation_rates(df)
    assert df["violation_rate"].iloc[0] is None or pd.isna(df["violation_rate"].iloc[0])


def test_quality_intervals_from_item_logs(tmp_path):
    summary_row = {"model": "qwen2.5:14b", "task": "long", "strategy": "rag", "budget": 2048, "accuracy": 0.5, "total": 4, "success": 2, "duration_sec": 10.0}
    log_dir = _write_summary(tmp_path, [summary_row])

    combo_file = tmp_path / "long_rag_2048.jsonl"
    turns = [
        {"item_id": "a", "quality": 1.0},
        {"used_budget": 1000},
        {"item_id": "b", "quality": 0.0},
        {"item_id": "c", "quality": 1.0},
        {"item_id": "d", "quality": 0.0},
    ]
    combo_file.write_text("\n".join(json.dumps(t) for t in turns) + "\n")

    df = load_summary_files([log_dir])
    df = compute_quality_intervals(df, n_bootstrap=200, seed=123)

    assert df["quality_n"].iloc[0] == 4
    assert 0.0 <= df["quality_ci_low"].iloc[0] <= 0.5
    assert 0.5 <= df["quality_ci_high"].iloc[0] <= 1.0


def test_quality_intervals_missing_item_logs(tmp_path):
    summary_row = {"model": "qwen2.5:14b", "task": "long", "strategy": "rag", "budget": 8192, "accuracy": 0.0, "total": 0, "success": 0, "duration_sec": 1.0}
    log_dir = _write_summary(tmp_path, [summary_row])

    df = load_summary_files([log_dir])
    df = compute_quality_intervals(df)

    assert df["quality_n"].iloc[0] == 0
    assert df["quality_ci_low"].iloc[0] is None or pd.isna(df["quality_ci_low"].iloc[0])


def test_compute_grouped_quality_from_item_metadata(tmp_path):
    summary_row = {"model": "qwen2.5:1.5b", "task": "memory", "strategy": "lean_retrieval", "budget": 1024, "accuracy": 0.75, "total": 4, "success": 3, "duration_sec": 10.0}
    log_dir = _write_summary(tmp_path, [summary_row])

    combo_file = tmp_path / "memory_lean_retrieval_1024.jsonl"
    turns = [
        {"item_id": "a", "memory_category": "knowledge_update", "quality": 1.0},
        {"item_id": "b", "memory_category": "knowledge_update", "quality": 0.0},
        {"item_id": "c", "memory_category": "abstention", "quality": 1.0},
        {"item_id": "d", "memory_category": "abstention", "quality": 1.0},
    ]
    combo_file.write_text("\n".join(json.dumps(t) for t in turns) + "\n")

    df = load_summary_files([log_dir])
    grouped = compute_grouped_quality(
        df,
        group_column="memory_category",
        n_bootstrap=100,
        seed=123,
    )

    by_category = {
        row["memory_category"]: row
        for _, row in grouped.iterrows()
    }
    assert by_category["knowledge_update"]["accuracy"] == pytest.approx(0.5)
    assert by_category["knowledge_update"]["quality_n"] == 2
    assert by_category["abstention"]["accuracy"] == pytest.approx(1.0)


def test_compute_paired_deltas_against_baseline(tmp_path):
    rows = [
        {"model": "qwen2.5:1.5b", "task": "long", "strategy": "rag", "budget": 8192, "accuracy": 0.75, "total": 4, "success": 3, "duration_sec": 20.0},
        {"model": "qwen2.5:1.5b", "task": "long", "strategy": "full_context", "budget": 32768, "accuracy": 0.5, "total": 4, "success": 2, "duration_sec": 40.0},
    ]
    log_dir = _write_summary(tmp_path, rows)

    (tmp_path / "long_rag_8192.jsonl").write_text(
        "\n".join(
            json.dumps(row)
            for row in [
                {"item_id": "a", "quality": 1.0},
                {"item_id": "b", "quality": 1.0},
                {"item_id": "c", "quality": 1.0},
                {"item_id": "d", "quality": 0.0},
            ]
        )
        + "\n"
    )
    (tmp_path / "long_full_context_32768.jsonl").write_text(
        "\n".join(
            json.dumps(row)
            for row in [
                {"item_id": "a", "quality": 1.0},
                {"item_id": "b", "quality": 0.0},
                {"item_id": "c", "quality": 1.0},
                {"item_id": "d", "quality": 0.0},
            ]
        )
        + "\n"
    )

    df = load_summary_files([log_dir])
    paired = compute_paired_deltas(
        df,
        baseline_strategy="full_context",
        baseline_budget=32768,
        n_bootstrap=200,
        seed=123,
    )

    rag_row = paired[
        (paired["strategy"] == "rag") & (paired["budget"] == 8192)
    ].iloc[0]
    assert rag_row["paired_n"] == 4
    assert rag_row["candidate_accuracy"] == pytest.approx(0.75)
    assert rag_row["baseline_accuracy"] == pytest.approx(0.5)
    assert rag_row["mean_delta"] == pytest.approx(0.25)
    assert rag_row["delta_ci_low"] <= rag_row["mean_delta"] <= rag_row["delta_ci_high"]


def test_compute_paired_deltas_uses_item_intersection(tmp_path):
    rows = [
        {"model": "qwen2.5:1.5b", "task": "long", "strategy": "truncation", "budget": 2048, "accuracy": 1.0, "total": 2, "success": 2, "duration_sec": 10.0},
        {"model": "qwen2.5:1.5b", "task": "long", "strategy": "full_context", "budget": 32768, "accuracy": 0.0, "total": 2, "success": 0, "duration_sec": 10.0},
    ]
    log_dir = _write_summary(tmp_path, rows)
    (tmp_path / "long_truncation_2048.jsonl").write_text(
        json.dumps({"item_id": "shared", "quality": 1.0}) + "\n"
        + json.dumps({"item_id": "candidate-only", "quality": 1.0}) + "\n"
    )
    (tmp_path / "long_full_context_32768.jsonl").write_text(
        json.dumps({"item_id": "shared", "quality": 0.0}) + "\n"
        + json.dumps({"item_id": "baseline-only", "quality": 0.0}) + "\n"
    )

    df = load_summary_files([log_dir])
    paired = compute_paired_deltas(
        df,
        baseline_strategy="full_context",
        baseline_budget=32768,
        n_bootstrap=100,
    )
    row = paired[
        (paired["strategy"] == "truncation") & (paired["budget"] == 2048)
    ].iloc[0]
    assert row["paired_n"] == 1
    assert row["mean_delta"] == pytest.approx(1.0)


def test_compute_paired_deltas_recovers_longmem_question_id(tmp_path):
    rows = [
        {"model": "qwen2.5:1.5b", "task": "longmem", "strategy": "lean_retrieval", "budget": 2048, "accuracy": 1.0, "total": 1, "success": 1, "duration_sec": 10.0},
        {"model": "qwen2.5:1.5b", "task": "longmem", "strategy": "full_context", "budget": 8192, "accuracy": 0.0, "total": 1, "success": 0, "duration_sec": 10.0},
    ]
    log_dir = _write_summary(tmp_path, rows)
    (tmp_path / "longmem_lean_retrieval_2048.jsonl").write_text(
        json.dumps({"item_id": "unknown", "longmem_question_id": "q-1", "quality": 1.0}) + "\n"
    )
    (tmp_path / "longmem_full_context_8192.jsonl").write_text(
        json.dumps({"item_id": "unknown", "longmem_question_id": "q-1", "quality": 0.0}) + "\n"
    )

    df = load_summary_files([log_dir])
    paired = compute_paired_deltas(
        df,
        baseline_strategy="full_context",
        baseline_budget=8192,
        n_bootstrap=100,
    )
    row = paired[
        (paired["strategy"] == "lean_retrieval") & (paired["budget"] == 2048)
    ].iloc[0]
    assert row["paired_n"] == 1
    assert row["mean_delta"] == pytest.approx(1.0)
