"""Profile module: combine hardware detection with model recommendation.

Usage:
    from budgetbench.profile import profile
    report = profile()  # returns dict with 'hardware' and 'recommendation'
"""

from .utils.hardware import detect_hardware
from .utils.recommendation import detect_best_model


def profile() -> dict:
    """Return combined hardware report and model recommendation.

    Returns:
        dict with keys 'hardware' (HardwareReport) and
        'recommendation' (RecommendationReport).
    """
    hardware = detect_hardware()
    recommendation = detect_best_model(hardware)
    return {"hardware": hardware, "recommendation": recommendation}
