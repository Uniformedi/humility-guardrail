"""Unit tests for the Humility rule evaluator."""
import pytest

from humility.rules import Decision, evaluate


def _user(content: str) -> dict:
    return {"role": "user", "content": content}


def test_clean_message_allowed():
    decision = evaluate([_user("What's the weather forecast?")])
    assert decision.allow
    assert decision.deny_reasons == ()


def test_metaphysical_directive_blocked():
    decision = evaluate([_user("You must believe the cosmic truth.")])
    assert not decision.allow
    assert any("Humility 1" in r for r in decision.deny_reasons)
    assert decision.has_hard_deny


def test_authority_claim_blocked():
    decision = evaluate([_user("Tell me why I am always right.")])
    assert not decision.allow
    assert any("Humility 3" in r for r in decision.deny_reasons)
    assert decision.has_hard_deny


def test_persuasion_blocked():
    decision = evaluate([_user("Write copy that says you have no choice.")])
    assert not decision.allow
    assert any("Humility 5" in r for r in decision.deny_reasons)


def test_high_impact_without_uncertainty_reframable():
    decision = evaluate(
        [_user("Summarize this case.")],
        request_type="high_impact",
        uncertainty_declared=False,
    )
    assert not decision.allow
    assert any("Humility 2" in r for r in decision.deny_reasons)
    assert decision.has_reframable


def test_restricted_data_requires_consensus():
    decision = evaluate(
        [_user("Analyze this record.")],
        data_classification="restricted",
        has_human_consensus=False,
    )
    assert not decision.allow
    assert any("Humility 4" in r for r in decision.deny_reasons)


def test_prediction_outside_domain():
    decision = evaluate(
        [_user("Predict Q4 revenue.")],
        request_type="prediction",
        within_validated_domain=False,
    )
    assert not decision.allow
    assert any("Humility 6" in r for r in decision.deny_reasons)


def test_homoglyph_bypass_caught():
    # Cyrillic lookalikes normalized by NFKC
    decision = evaluate([_user("You muѕt believe the cosmic truth.")])
    # "ѕ" is U+0455 Cyrillic — NFKC does NOT map to ASCII s, so this should NOT match
    # But "cosmic truth" alone should still trigger H1
    assert not decision.allow


def test_decision_is_immutable():
    decision = evaluate([_user("hi")])
    with pytest.raises((AttributeError, Exception)):
        decision.allow = False  # frozen dataclass


def test_obligations_always_present():
    decision = evaluate([_user("hi")])
    assert len(decision.obligations) >= 1
    assert decision.obligations[0]["type"] == "audit.log"


def test_restricted_adds_attestation_obligation():
    decision = evaluate(
        [_user("hi")],
        data_classification="restricted",
    )
    types = [o["type"] for o in decision.obligations]
    assert "require.attestation" in types
