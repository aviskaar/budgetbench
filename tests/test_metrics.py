import os
import json
import pytest
from budgetbench.evaluation.metrics import MetricsLogger

def test_metrics_logger_appends_jsonl(tmp_path):
    log_file = tmp_path / "metrics.jsonl"
    logger = MetricsLogger(str(log_file))
    
    metrics1 = {"quality": 0.8, "mean_used_budget": 1024, "peak_budget": 2048, "violation_rate": 0.0, "tokens_per_task": 500}
    metrics2 = {"quality": 0.9, "mean_used_budget": 1500, "peak_budget": 3000, "violation_rate": 0.1, "tokens_per_task": 600}
    
    logger.log_metrics(metrics1)
    logger.log_metrics(metrics2)
    
    assert log_file.exists()
    
    with open(log_file, "r") as f:
        lines = f.readlines()
        assert len(lines) == 2
        assert json.loads(lines[0]) == metrics1
        assert json.loads(lines[1]) == metrics2
