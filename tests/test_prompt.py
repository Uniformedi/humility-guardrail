import pytest

from humility import system_prompt


def test_tier1_strictest():
    assert "mandatory" in system_prompt("tier1").lower()


def test_tier3_minimal():
    assert len(system_prompt("tier3")) < len(system_prompt("tier1"))


def test_unknown_tier_raises():
    with pytest.raises(ValueError):
        system_prompt("tier99")


def test_default_is_tier3():
    assert system_prompt() == system_prompt("tier3")
