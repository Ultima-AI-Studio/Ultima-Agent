import pytest

from scripts.gorch.smoke_probe import normalize_smoke


def test_normalize_smoke_strips_whitespace_and_lowercases():
    assert normalize_smoke("  Smoke  ") == "smoke"


def test_normalize_smoke_lowercases_uppercase_string():
    assert normalize_smoke("SMOKE") == "smoke"


def test_normalize_smoke_returns_none_for_none():
    assert normalize_smoke(None) is None


def test_normalize_smoke_raises_type_error_for_other_types():
    with pytest.raises(TypeError):
        normalize_smoke(42)
