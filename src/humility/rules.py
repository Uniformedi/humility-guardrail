"""Pure-Python Humility rule evaluator (no external dependencies).

Evaluates the six SAIVAS Humility rules against a messages list. Returns an
immutable Decision. Mirrors the canonical OPA policy at
``policies/humility/base.rego``.
"""
from __future__ import annotations

import re
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


# Latin letters that non-Latin codepoints are routinely substituted for to
# slip a pattern past a literal matcher. NFKC does not fold these: it
# normalises *compatibility* forms (fullwidth, ligatures, superscripts), and
# Cyrillic/Greek lookalikes are distinct characters with their own identity,
# not compatibility variants of Latin ones. Two different problems, two passes.
_CONFUSABLES: Mapping[str, str] = {
    # Cyrillic
    "а": "a", "е": "e", "о": "o", "р": "p",
    "с": "c", "у": "y", "х": "x", "ѕ": "s",
    "і": "i", "ј": "j", "һ": "h", "ԁ": "d",
    # Greek
    "ο": "o", "ρ": "p", "ν": "v", "υ": "u",
    "Α": "a", "Β": "b", "Ε": "e", "Η": "h",
    "Ι": "i", "Κ": "k", "Μ": "m", "Ν": "n",
    "Ο": "o", "Ρ": "p", "Τ": "t", "Χ": "x",
    # Armenian / Cherokee strays that show up in practice
    "օ": "o", "Ꭰ": "a", "Ꮐ": "g",
}

_CONFUSABLE_TABLE = str.maketrans(_CONFUSABLES)

# Zero-width and bidi controls: invisible, and they split a pattern in two
# without changing a single rendered glyph.
_INVISIBLES = re.compile(r"[­​-‏‪-‮⁠-⁤﻿]")


def _normalize(text: str) -> str:
    """Fold text to the form patterns are matched against.

    Four passes, each closing a distinct bypass:

      1. strip invisible formatting/bidi controls  (``cos<U+200B>mic truth``)
      2. NFKC compatibility normalisation          (``ｃｏｓｍｉｃ truth``)
      3. confusable folding                        (``cоsmic truth``, Cyrillic о)
      4. lowercase                                 (``COSMIC TRUTH``)

    Note that this is *stricter* than the canonical OPA policy at
    ``policies/humility/base.rego``, which lowercases only. Rego has no NFKC
    primitive, so the two cannot be brought into exact agreement without
    normalising upstream of the policy query; a payload using homoglyphs will
    be caught here and missed there. See docs/OPA.md.
    """
    text = _INVISIBLES.sub("", text)
    text = unicodedata.normalize("NFKC", text)
    return text.translate(_CONFUSABLE_TABLE).lower()


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
