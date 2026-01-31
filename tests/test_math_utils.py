import math

from services.utils.math_utils import safe_divide, sanitize_number


def test_safe_divide_handles_zero_and_invalid():
    assert safe_divide(10, 0) == 0
    assert safe_divide(10, 0, default=5) == 5
    assert safe_divide(None, 5) == 0
    assert safe_divide(10, None) == 0
    assert safe_divide(10, float("nan")) == 0


def test_sanitize_number_handles_nan():
    assert sanitize_number(float("nan")) == 0
    assert sanitize_number(float("inf")) == 0
    assert sanitize_number(-5) == -5
    assert sanitize_number("3.5") == 3.5
