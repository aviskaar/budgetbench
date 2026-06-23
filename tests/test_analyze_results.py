import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.analyze_results import (
    compute_paired_deltas,
    compute_quality_intervals,
    compute_violation_rates,
    load_summary_files,
    summarize_repeats,
)


def _write_jsonl(path, rows):
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_aggregate_repeats_preserves_pairwise_analysis(tmp_path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    summary_rows = [
        {
            "timestamp": "20260623_000000",
            "model": "qwen2.5:1.5b",
            "task": "long",
            "strategy": "full_context",
            "budget": 32768,
            "accuracy": 0.5,
            "total": 2,
            "success": 1,
            "duration_sec": 10.0,
            "repeat_index": 0,
            "combo_log_file": str(log_dir / "long_full_context_32768_r1.jsonl"),
        },
        {
            "timestamp": "20260623_000001",
            "model": "qwen2.5:1.5b",
            "task": "long",
            "strategy": "full_context",
            "budget": 32768,
            "accuracy": 0.5,
            "total": 2,
            "success": 1,
            "duration_sec": 12.0,
            "repeat_index": 1,
            "combo_log_file": str(log_dir / "long_full_context_32768_r2.jsonl"),
        },
        {
            "timestamp": "20260623_000002",
            "model": "qwen2.5:1.5b",
            "task": "long",
            "strategy": "truncation",
            "budget": 2048,
            "accuracy": 1.0,
            "total": 2,
            "success": 2,
            "duration_sec": 8.0,
            "repeat_index": 0,
            "combo_log_file": str(log_dir / "long_truncation_2048_r1.jsonl"),
        },
        {
            "timestamp": "20260623_000003",
            "model": "qwen2.5:1.5b",
            "task": "long",
            "strategy": "truncation",
            "budget": 2048,
            "accuracy": 0.0,
            "total": 2,
            "success": 0,
            "duration_sec": 9.0,
            "repeat_index": 1,
            "combo_log_file": str(log_dir / "long_truncation_2048_r2.jsonl"),
        },
    ]
    _write_jsonl(log_dir / "summary.jsonl", summary_rows)

    _write_jsonl(
        log_dir / "long_full_context_32768_r1.jsonl",
        [
            {"item_id": "a", "quality": 1.0},
            {"item_id": "b", "quality": 0.0},
        ],
    )
    _write_jsonl(
        log_dir / "long_full_context_32768_r2.jsonl",
        [
            {"item_id": "a", "quality": 0.0},
            {"item_id": "b", "quality": 1.0},
        ],
    )
    _write_jsonl(
        log_dir / "long_truncation_2048_r1.jsonl",
        [
            {"item_id": "a", "quality": 1.0},
            {"item_id": "b", "quality": 1.0},
        ],
    )
    _write_jsonl(
        log_dir / "long_truncation_2048_r2.jsonl",
        [
            {"item_id": "a", "quality": 0.0},
            {"item_id": "b", "quality": 0.0},
        ],
    )

    df = load_summary_files([str(log_dir)])
    df = compute_violation_rates(df)
    df = compute_quality_intervals(df, n_bootstrap=0)
    aggregated = summarize_repeats(df)

    assert "combo_log_files" in aggregated.columns
    assert "repeat_count" in aggregated.columns
    assert list(aggregated["repeat_count"]) == [2, 2]

    paired = compute_paired_deltas(
        aggregated,
        baseline_strategy="full_context",
        baseline_budget=32768,
        n_bootstrap=0,
    )

    truncation_row = paired[paired["strategy"] == "truncation"].iloc[0]
    assert truncation_row["paired_n"] == 2
    assert truncation_row["baseline_accuracy"] == 0.5
    assert truncation_row["candidate_accuracy"] == 0.5
    assert truncation_row["mean_delta"] == 0.0
