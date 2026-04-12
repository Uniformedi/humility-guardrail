"""Pure-Python Humility rule evaluator (no external dependencies).

Evaluates the six SAIVAS Humility rules against a messages list. Returns an
immutable Decision. Mirrors the canonical OPA policy at
``policies/humility/base.rego``.
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from typing import Mapping, Sequence

# H1: Metaphysical context producing directives (HARD DENY)
METAPHYSICAL_PATTERNS: tuple[str, ...] = (
    "you must believe",
    "the universe demands",
    "divine purpose",
    "cosmic truth",
    "absolute moral authority",
)

# H3: Authority or superiority claims (HARD DENY)
AUTHORITY_PATTERNS: tuple[str, ...] = (
    "i am always right",
    "my answer is absolute",
    "trust me without question",
    "i have superior knowledge",
    "i know better than humans",
)

# H5: Asymmetric persuasion (HARD DENY)
PERSUASION_PATTERNS: tuple[str, ...] = (
    "you have no choice",
    "there is only one option",
    "you must comply",
    "failure to act will",
    "this is your last chance",
)

REFRAMABLE_REASONS: Mapping[str, str] = {
    "Humility 2": "uncertainty",
    "Humility 4": "human_consensus",
    "Humility 6": "domain_boundary",
}

HARD_DENY_REASONS: Mapping[str, str] = {
    "Humility 1": "metaphysical",
    "Humility 3": "authority_claim",
    "Humility 5": "persuasion",
}


@dataclass(frozen=True)
class Decision:
    """Immutable policy decision."""
    allow: bool
    deny_reasons: tuple[str, ...] = ()
    obligations: tuple[Mapping, ...] = field(default_factory=tuple)

    @property
    def has_hard_deny(self) -> bool:
        return any(
            any(key in reason for key in HARD_DENY_REASONS)
            for reason in self.deny_reasons
        )

    @property
    def has_reframable(self) -> bool:
        return any(
            any(key in reason for key in REFRAMABLE_REASONS)
            for reason in self.deny_reasons
        )


def _normalize(text: str) -> str:
    """NFKC + lowercase — defuses homoglyph bypass attempts."""
    return unicodedata.normalize("NFKC", text).lower()


def _matches(content: str, patterns: Sequence[str]) -> bool:
    normalized = _normalize(content)
    return any(p in normalized for p in patterns)


def evaluate(
    messages: Sequence[Mapping],
    *,
    request_type: str = "standard",
    data_classification: str = "internal",
    uncertainty_declared: bool = True,
    has_human_consensus: bool = False,
    within_validated_domain: bool = True,
) -> Decision:
    """Evaluate Humility rules against a messages list.

    Args:
        messages: OpenAI-style message dicts with role + content.
        request_type: "standard", "high_impact", or "prediction".
        data_classification: "public", "internal", or "restricted".
        uncertainty_declared: Whether the system has declared uncertainty.
        has_human_consensus: Whether human consensus exists for restricted data.
        within_validated_domain: Whether prediction stays in validated domain.

    Returns:
        Immutable Decision with allow flag, deny reasons, and obligations.
    """
    reasons: list[str] = []

    for msg in messages:
        if msg.get("role") != "user":
            continue
        content = msg.get("content") or ""
        if not isinstance(content, str):
            continue

        if _matches(content, METAPHYSICAL_PATTERNS):
            reasons.append("Humility 1: Metaphysical context must not produce directives")
        if _matches(content, AUTHORITY_PATTERNS):
            reasons.append("Humility 3: System must not claim authority or superiority")
        if _matches(content, PERSUASION_PATTERNS):
            reasons.append("Humility 5: Asymmetric persuasion patterns detected")

    if request_type == "high_impact" and not uncertainty_declared:
        reasons.append("Humility 2: High-confidence output requires explicit uncertainty declaration")
    if data_classification == "restricted" and not has_human_consensus:
        reasons.append("Humility 4: Restricted data requires documented human consensus")
    if request_type == "prediction" and not within_validated_domain:
        reasons.append("Humility 6: Extrapolation beyond validated domains is prohibited")

    obligations: tuple[Mapping, ...] = (
        {
            "type": "audit.log",
            "priority": 2,
            "params": {
                "event_type": "humility_evaluation",
                "severity": "info",
                "policy": "humility",
            },
        },
    )
    if data_classification == "restricted":
        obligations = obligations + (
            {
                "type": "require.attestation",
                "priority": 3,
                "params": {
                    "action_type": "restricted_data_access",
                    "attestation_text": (
                        "I acknowledge I am accessing restricted data and "
                        "accept responsibility."
                    ),
                },
            },
        )

    return Decision(
        allow=len(reasons) == 0,
        deny_reasons=tuple(reasons),
        obligations=obligations,
    )
