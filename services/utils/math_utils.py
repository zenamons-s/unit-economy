"""
Utility helpers for safe numeric operations.
"""

from __future__ import annotations

import math
from typing import Optional


def sanitize_number(value: Optional[float], default: float = 0.0) -> float:
    """Return a finite float or a default if the value is invalid."""
    try:
        if value is None:
            return default
        if isinstance(value, (int, float)):
            if not math.isfinite(value):
                return default
            return float(value)
        return float(value)
    except Exception:
        return default


def safe_divide(numerator: Optional[float], denominator: Optional[float], default: float = 0.0) -> float:
    """Safely divide two numbers with protection against zero/invalid values."""
    numerator_value = sanitize_number(numerator, default)
    denominator_value = sanitize_number(denominator, None)
    if denominator_value in (None, 0):
        return default
    return numerator_value / denominator_value
