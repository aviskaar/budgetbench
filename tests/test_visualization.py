import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.plot_tradeoffs import plot_tradeoff_curves


def _make_df(model="test_model"):
    return pd.DataFrame([
        {"model": model, "task": "swe", "strategy": "truncation", "budget": 2048, "accuracy": 0.1, "violation_rate": 0.0, "duration_sec": 10.0},
        {"model": model, "task": "long", "strategy": "truncation", "budget": 2048, "accuracy": 0.2, "violation_rate": 0.05, "duration_sec": 5.0},
        {"model": model, "task": "swe", "strategy": "truncation", "budget": 8192, "accuracy": 0.3, "violation_rate": 0.0, "duration_sec": 10.0},
        {"model": model, "task": "long", "strategy": "truncation", "budget": 8192, "accuracy": 0.4, "violation_rate": 0.0, "duration_sec": 5.0},
    ])


def test_plot_tradeoff_curves_no_crash(tmp_path):
    df = _make_df()
    out_path = str(tmp_path / "tradeoff.png")
    plot_tradeoff_curves(df, model="test_model", out_path=out_path)
    assert os.path.exists(out_path), "PNG file should be created"


def test_plot_tradeoff_curves_empty_data(tmp_path):
    df = _make_df(model="other_model")
    out_path = str(tmp_path / "empty_tradeoff.png")
    plot_tradeoff_curves(df, model="unknown", out_path=out_path)
    assert os.path.exists(out_path), "PNG should be created even with empty data"
