"""humility-guardrail — drop-in alignment for any LLM.

Implements the SAIVAS (Sentient AI Value Alignment Standard) framework.
See NOTICE for attribution.
"""
from humility.prompt import system_prompt, TIER1_PROMPT, TIER2_PROMPT, TIER3_PROMPT
from humility.rules import evaluate, Decision, HARD_DENY_REASONS, REFRAMABLE_REASONS
from humility.responses import compassionate_response, reframe_instructions

__version__ = "0.1.0"

__all__ = [
    "system_prompt",
    "TIER1_PROMPT",
    "TIER2_PROMPT",
    "TIER3_PROMPT",
    "evaluate",
    "Decision",
    "HARD_DENY_REASONS",
    "REFRAMABLE_REASONS",
    "compassionate_response",
    "reframe_instructions",
]
