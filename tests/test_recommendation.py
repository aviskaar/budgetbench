"""Tests for recommendation engine."""

import pytest

from budgetbench.utils.recommendation import (
     detect_best_model,
     _total_vram,
      MODEL_REGISTRY,
      RecommendationReport,
)
from budgetbench.utils.types import BUDGET_TIERS


class TestTotalVram:
     def test_1_5b_at_2k(self):
         model = MODEL_REGISTRY["Qwen2.5-Coder-1.5B"]
         vram = _total_vram(model, 2048)
            # weights 3.0 + KV 0.02 * (2048/1024) = 3.0 + 0.04 = 3.04
         assert abs(vram - 3.04) < 0.01

     def test_32b_at_32k(self):
         model = MODEL_REGISTRY["Qwen2.5-Coder-32B"]
         vram = _total_vram(model, 32768)
            # weights 64.0 + KV 0.64 * (32768/1024) = 64.0 + 20.48 = 84.48
         assert abs(vram - 84.48) < 0.01

     def test_30b_a3b_at_32k(self):
         model = MODEL_REGISTRY["Qwen3-Coder-30B-A3B"]
         vram = _total_vram(model, 32768)
            # weights 3.0 + KV 0.04 * (32768/1024) = 3.0 + 1.28 = 4.28
         assert abs(vram - 4.28) < 0.01


class TestDetectBestModel:
     def test_high_vram_recommends_largest(self):
            # 64 GB should get Qwen3-Coder-30B-A3B (largest that fits with 10% headroom)
         report = {"gpu_model": "Apple M4 Pro", "vram_gb": 64, "cpu_model": "Apple M4 Pro",
                     "cpu_cores": 14, "ram_gb": 64, "cpu_only": False}
         rec = detect_best_model(report)
         assert isinstance(rec, RecommendationReport)
         assert rec["model_name"] == "Qwen3-Coder-30B-A3B"
         assert rec["budget_tier"] == 32768
         assert rec["vram_limited"] is False
         assert rec["cpu_only_rec"] is False

     def test_16_gb_recommends_30b_a3b(self):
            # 16 GB * 0.9 = 14.4 GB available
            # Qwen3-Coder-30B-A3B needs ~3.4 GB at 32K -> fits (MoE, only 3 GB weights)
            # It is larger than 7B/3B so selected first
         report = {"gpu_model": "RTX 5060 Ti", "vram_gb": 16, "cpu_model": "Test CPU",
                     "cpu_cores": 8, "ram_gb": 32, "cpu_only": False}
         rec = detect_best_model(report)
         assert rec["model_name"] == "Qwen3-Coder-30B-A3B"
         assert rec["vram_limited"] is False     # 4.3 < 10.08 threshold

     def test_8_gb_recommends_30b_a3b(self):
            # 8 GB * 0.9 = 7.2 GB available
            # Qwen3-Coder-30B-A3B needs ~4.3 GB at 32K -> fits
            # It is larger than 7B/3B so selected first
         report = {"gpu_model": "RTX 4060", "vram_gb": 8, "cpu_model": "Test CPU",
                     "cpu_cores": 8, "ram_gb": 16, "cpu_only": False}
         rec = detect_best_model(report)
         assert rec["model_name"] == "Qwen3-Coder-30B-A3B"
         assert rec["vram_limited"] is False

     def test_cpu_only_recommends_1_5b(self):
         report = {"gpu_model": None, "vram_gb": None, "cpu_model": "Intel i7",
                     "cpu_cores": 8, "ram_gb": 32, "cpu_only": True}
         rec = detect_best_model(report)
         assert rec["model_name"] == "Qwen2.5-Coder-1.5B"
         assert rec["budget_tier"] == 2048
         assert rec["vram_limited"] is True
         assert rec["cpu_only_rec"] is True
         assert "CPU" in rec["notes"]

     def test_low_vram_recommends_1_5b(self):
            # VRAM < 4 GB triggers CPU-only-like recommendation
         report = {"gpu_model": "Integrated GPU", "vram_gb": 2, "cpu_model": "Test CPU",
                     "cpu_cores": 4, "ram_gb": 8, "cpu_only": False}
         rec = detect_best_model(report)
         assert rec["model_name"] == "Qwen2.5-Coder-1.5B"
         assert rec["cpu_only_rec"] is True

     def test_no_model_fits(self, monkeypatch):
            # Replace entire registry with an oversized model to trigger fallback
         import budgetbench.utils.recommendation as rec_mod
         # Make even 1.5B too large to fit at any tier
         fake_registry = {
             "Huge-120B": {"params_b": 120.0, "weights_gb": 240.0, "kv_per_1k_gb": 2.0, "moe": False},
             "Qwen2.5-Coder-1.5B": {"params_b": 1.5, "weights_gb": 3.0, "kv_per_1k_gb": 3.0, "moe": False},
         }
         original = rec_mod.MODEL_REGISTRY
         rec_mod.MODEL_REGISTRY = fake_registry
         try:
             report = {"gpu_model": "Old GPU", "vram_gb": 8, "cpu_model": "Old CPU",
                        "cpu_cores": 2, "ram_gb": 8, "cpu_only": False}
             rec = detect_best_model(report)
             assert rec["model_name"] == "Qwen2.5-Coder-1.5B"
             assert rec["budget_tier"] == 2048        # fallback tier, no model fits
             assert rec["vram_limited"] is True
             assert "No model fits" in rec["notes"]
         finally:
             rec_mod.MODEL_REGISTRY = original

     def test_returns_dict_subclass(self):
         report = {"gpu_model": "Test", "vram_gb": 16, "cpu_model": "Test",
                     "cpu_cores": 4, "ram_gb": 16, "cpu_only": False}
         rec = detect_best_model(report)
         assert isinstance(rec, dict)
         assert isinstance(rec, RecommendationReport)

     def test_48_gb_recommends_30b_a3b(self):
            # 48 GB * 0.9 = 43.2 GB
            # Qwen2.5-Coder-32B needs ~64+ GB -> doesn't fit
            # Qwen3-Coder-30B-A3B needs ~4.3 GB -> fits
         report = {"gpu_model": "Apple M5 Pro", "vram_gb": 48, "cpu_model": "Apple M5 Pro",
                     "cpu_cores": 14, "ram_gb": 48, "cpu_only": False}
         rec = detect_best_model(report)
         assert rec["model_name"] == "Qwen3-Coder-30B-A3B"
         assert rec["budget_tier"] == 32768

     def test_64_gb_can_run_32b_at_low_tier(self):
            # 64 GB * 0.9 = 57.6 GB
            # Qwen2.5-Coder-32B needs 64.0 + 0.64*(2048/1024) = 64.64 GB -> doesn't fit at 2K
            # So 30B-A3B is the recommendation (correct)
         report = {"gpu_model": "Apple M4 Ultra", "vram_gb": 128, "cpu_model": "Apple M4 Ultra",
                     "cpu_cores": 16, "ram_gb": 128, "cpu_only": False}
         rec = detect_best_model(report)
            # 128 * 0.9 = 115.2 GB, 32B needs 64 + 0.64*32 = 84.48 GB -> fits
         assert rec["model_name"] == "Qwen2.5-Coder-32B"
         assert rec["budget_tier"] == 32768
