import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.export_swebench_predictions import export_predictions, iter_prediction_rows


def _write_logs(tmp_path):
    summary = {
        "timestamp": "20260618_000000",
        "model": "qwen2.5:1.5b",
        "task": "swe",
        "strategy": "truncation",
        "budget": 2048,
        "accuracy": 0.0,
        "total": 2,
        "success": 0,
        "duration_sec": 1.0,
    }
    (tmp_path / "summary.jsonl").write_text(json.dumps(summary) + "\n", encoding="utf-8")
    rows = [
        {
            "item_id": "repo__issue-1",
            "prediction": "diff --git a/x b/x\n--- a/x\n+++ b/x\n@@ -1,1 +1,1 @@\n-old\n+fix\n",
        },
        {"item_id": "repo__issue-2", "prediction": ""},
        {"item_id": "repo__issue-2", "quality": 0.0},
    ]
    (tmp_path / "swe_truncation_2048.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )
    return tmp_path


def test_iter_prediction_rows_exports_official_schema(tmp_path):
    log_dir = _write_logs(tmp_path)
    rows = list(
        iter_prediction_rows(
            log_dir=str(log_dir),
            strategy="truncation",
            budget=2048,
        )
    )
    assert rows == [
        {
            "instance_id": "repo__issue-1",
            "model_name_or_path": "qwen2.5:1.5b",
            "model_patch": "diff --git a/x b/x\n--- a/x\n+++ b/x\n@@ -1,1 +1,1 @@\n-old\n+fix\n",
        }
    ]


def test_export_predictions_writes_jsonl(tmp_path):
    log_dir = _write_logs(tmp_path)
    output = tmp_path / "predictions.jsonl"
    count = export_predictions(
        log_dir=str(log_dir),
        output_path=str(output),
        strategy="truncation",
        budget=2048,
    )
    assert count == 1
    exported = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert exported[0]["instance_id"] == "repo__issue-1"


def test_export_predictions_skips_invalid_patches(tmp_path):
    summary = {
        "timestamp": "20260618_000000",
        "model": "qwen2.5:1.5b",
        "task": "swe",
        "strategy": "truncation",
        "budget": 2048,
        "accuracy": 0.0,
        "total": 2,
        "success": 0,
        "duration_sec": 1.0,
    }
    (tmp_path / "summary.jsonl").write_text(json.dumps(summary) + "\n", encoding="utf-8")
    rows = [
        {
            "item_id": "repo__issue-1",
            "prediction": "diff --git a/src/foo.py b/src/foo.py\nindex 1..2 100644\n--- a/src.bad.py\n+++ b/src/foo.py\n@@ -1,1 +1,1 @@\n-a\n+b\n",
        },
        {
            "item_id": "repo__issue-2",
            "prediction": "diff --git a/src/foo.py b/src/foo.py\n--- a/src/foo.py\n+++ b/src/foo.py\n@@ -1,1 +1,1 @@\n-a\n+b\n",
        },
    ]
    (tmp_path / "swe_truncation_2048.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "predictions.jsonl"
    count = export_predictions(
        log_dir=str(tmp_path),
        output_path=str(output),
        strategy="truncation",
        budget=2048,
    )
    assert count == 1
    exported = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert exported[0]["instance_id"] == "repo__issue-2"
