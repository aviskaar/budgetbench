"""Recommendation engine for the BudgetBench profiler.

Matches detected hardware to the optimal Qwen model + context budget tier
based on VRAM vs model weights + KV-cache footprint.
"""

from typing import Optional

from .hardware import HardwareReport
from .types import BUDGET_TIERS


class RecommendationReport(dict):
    """Structured recommendation for the user's hardware."""
    pass


# Model registry: VRAM estimates for Qwen Coder models.
# kv_per_1k_gb: approximate KV-cache overhead per 1K tokens at the target tier.
# Actual KV cache = kv_per_1k_gb * (tier_tokens / 1024)
MODEL_REGISTRY: dict[str, dict] = {
    "Qwen2.5-Coder-1.5B": {
        "params_b": 1.5,
        "weights_gb": 3.0,
        "kv_per_1k_gb": 0.02,
        "moe": False,
    },
    "Qwen2.5-Coder-3B": {
        "params_b": 3.0,
        "weights_gb": 6.0,
        "kv_per_1k_gb": 0.06,
        "moe": False,
    },
    "Qwen2.5-Coder-7B": {
        "params_b": 7.0,
        "weights_gb": 14.0,
        "kv_per_1k_gb": 0.14,
        "moe": False,
    },
    "Qwen2.5-Coder-14B": {
        "params_b": 14.0,
        "weights_gb": 28.0,
        "kv_per_1k_gb": 0.28,
        "moe": False,
    },
    "Qwen2.5-Coder-32B": {
        "params_b": 32.0,
        "weights_gb": 64.0,
        "kv_per_1k_gb": 0.64,
        "moe": False,
    },
    "Qwen3-Coder-30B-A3B": {
        "params_b": 30.0,
        "weights_gb": 3.0,   # MoE: only 3B active params in float16
        "kv_per_1k_gb": 0.04,
        "moe": True,
    },
}


def _total_vram(model: dict, tier_tokens: int) -> float:
    """Calculate total VRAM needed for a model at a given budget tier.

    VRAM = weights (float16) + KV-cache (float16, tier-dependent).
    """
    kv_gb = model["kv_per_1k_gb"] * (tier_tokens / 1024)
    return model["weights_gb"] + kv_gb


def detect_best_model(report: HardwareReport) -> RecommendationReport:
    """Recommend the best Qwen model + budget tier for detected hardware.

    Uses a greedy largest-first approach: sorts models by parameter size,
    then picks the first model+tier where total VRAM (weights + KV-cache)
    fits within available VRAM with 10% headroom.

    Args:
        report: HardwareReport from detect_hardware().

    Returns:
        RecommendationReport with model, tier, VRAM usage, and notes.
    """
    vram_gb = report.get("vram_gb") or 0
    cpu_only = report.get("cpu_only", True)
    ram_gb = report.get("ram_gb", 0)
    cpu_cores = report.get("cpu_cores", 1)

    recommendation = RecommendationReport()

    # CPU-only or very low VRAM: recommend CPU inference
    if cpu_only or vram_gb < 4:
        recommendation["model_name"] = "Qwen2.5-Coder-1.5B"
        recommendation["budget_tier"] = BUDGET_TIERS[0]   # 2K
        recommendation["vram_needed_gb"] = 3.0
        recommendation["vram_available_gb"] = vram_gb if vram_gb else ram_gb
        recommendation["vram_limited"] = True
        recommendation["cpu_only_rec"] = True
        recommendation["notes"] = (
            "No GPU detected or VRAM < 4 GB. "
            "Recommending smallest model for CPU inference via llama.cpp or mlx-lm. "
            "Performance will be significantly slower than GPU inference."
        )
        return recommendation

    # 10% headroom for OS/GPU overhead
    available = vram_gb * 0.9

    # Sort models by size descending, pick largest that fits
    sorted_models = sorted(
        MODEL_REGISTRY.items(),
        key=lambda item: item[1]["params_b"],
        reverse=True,
    )

    for model_name, model in sorted_models:
        # Check each tier from largest to smallest
        for tier in reversed(BUDGET_TIERS):
            needed = _total_vram(model, tier)
            if needed <= available:
                recommendation["model_name"] = model_name
                recommendation["budget_tier"] = tier
                recommendation["vram_needed_gb"] = round(needed, 1)
                recommendation["vram_available_gb"] = vram_gb
                recommendation["vram_limited"] = needed > available * 0.7
                recommendation["cpu_only_rec"] = False
                moe_tag = " (MoE)" if model.get("moe") else ""
                recommendation["notes"] = (
                    f"Recommended{moe_tag} model fits within VRAM with "
                    f"{round(vram_gb - needed, 1)} GB headroom."
                )
                return recommendation

    # Fallback: no model fits even at 2K
    recommendation["model_name"] = "Qwen2.5-Coder-1.5B"
    recommendation["budget_tier"] = BUDGET_TIERS[0]
    recommendation["vram_needed_gb"] = _total_vram(MODEL_REGISTRY["Qwen2.5-Coder-1.5B"], BUDGET_TIERS[0])
    recommendation["vram_available_gb"] = vram_gb
    recommendation["vram_limited"] = True
    recommendation["cpu_only_rec"] = False
    recommendation["notes"] = (
        "No model fits within available VRAM. "
        "Recommending smallest model at lowest tier; consider CPU inference or upgrading GPU."
    )
    return recommendation
