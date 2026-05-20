"""Tests for profile module and CLI."""

import json
import sys
from io import StringIO
from unittest.mock import patch

import pytest

from budgetbench.profile import profile as _profile
from budgetbench.cli import _format_report


class TestProfile:
     def test_profile_returns_dict(self):
         data = _profile()
         assert isinstance(data, dict)
         assert "hardware" in data
         assert "recommendation" in data

     def test_profile_hardware_keys(self):
         data = _profile()
         hw = data["hardware"]
         for key in ("gpu_model", "vram_gb", "cpu_model", "cpu_cores", "ram_gb", "cpu_only"):
             assert key in hw, f"Missing hardware key: {key}"

     def test_profile_recommendation_keys(self):
         data = _profile()
         rec = data["recommendation"]
         for key in ("model_name", "budget_tier", "vram_needed_gb", "vram_available_gb",
                      "vram_limited", "cpu_only_rec", "notes"):
             assert key in rec, f"Missing recommendation key: {key}"

     def test_profile_json_serializable(self):
         data = _profile()
         # Should not raise
         json_str = json.dumps(data, indent=2, default=str)
         assert len(json_str) > 0
         # Round-trip
         parsed = json.loads(json_str)
         assert "hardware" in parsed
         assert "recommendation" in parsed

     def test_importable(self):
         import budgetbench
         assert hasattr(budgetbench, "profile")
         data = budgetbench.profile()
         assert isinstance(data, dict)


class TestFormatReport:
     def test_format_report_contains_model(self):
         data = {
             "hardware": {
                 "gpu_model": "Apple M4 Pro",
                 "vram_gb": 64,
                 "cpu_model": "Apple M4 Pro",
                 "cpu_cores": 14,
                 "ram_gb": 64,
                 "cpu_only": False,
             },
             "recommendation": {
                 "model_name": "Qwen3-Coder-30B-A3B",
                 "budget_tier": 32768,
                 "vram_needed_gb": 4.3,
                 "vram_available_gb": 64,
                 "vram_limited": False,
                 "cpu_only_rec": False,
                 "notes": "Recommended model fits.",
             },
         }
         output = _format_report(data)
         assert "BudgetBench Hardware Profile" in output
         assert "Apple M4 Pro" in output
         assert "Qwen3-Coder-30B-A3B" in output
         assert "32768" in output

     def test_format_report_cpu_only(self):
         data = {
             "hardware": {
                 "gpu_model": None,
                 "vram_gb": None,
                 "cpu_model": "Intel i7",
                 "cpu_cores": 8,
                 "ram_gb": 32,
                 "cpu_only": True,
             },
             "recommendation": {
                 "model_name": "Qwen2.5-Coder-1.5B",
                 "budget_tier": 2048,
                 "vram_needed_gb": 3.0,
                 "vram_available_gb": 32,
                 "vram_limited": True,
                 "cpu_only_rec": True,
                 "notes": "No GPU detected.",
             },
         }
         output = _format_report(data)
         assert "CPU-only" in output
         assert "No GPU detected" in output

     def test_format_report_no_notes(self):
         data = {
             "hardware": {
                 "gpu_model": "Test",
                 "vram_gb": 8,
                 "cpu_model": "Test",
                 "cpu_cores": 4,
                 "ram_gb": 8,
                 "cpu_only": False,
             },
             "recommendation": {
                 "model_name": "X",
                 "budget_tier": 2048,
                 "vram_needed_gb": 1.0,
                 "vram_available_gb": 8,
                 "vram_limited": False,
                 "cpu_only_rec": False,
                 "notes": None,
             },
         }
         output = _format_report(data)
         assert "BudgetBench Hardware Profile" in output
         assert "Note:" not in output
