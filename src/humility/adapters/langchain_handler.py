"""LangChain callback handler — enforces Humility on LLM inputs."""
from __future__ import annotations

from typing import Any

try:
    from langchain_core.callbacks.base import BaseCallbackHandler
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "LangChain is required for the LangChain adapter. "
        "Install with: pip install humility-guardrail[langchain]"
    ) from exc

from humility.prompt import system_prompt
from humility.responses import compassionate_response
from humility.rules import evaluate


class HumilityDenied(Exception):
    """Raised when a request is blocked by Humility."""


class HumilityCallbackHandler(BaseCallbackHandler):
    """Add before any LLM invocation in your chain.

    Usage::

        from langchain_openai import ChatOpenAI
        from humility.adapters.langchain_handler import HumilityCallbackHandler

        llm = ChatOpenAI(callbacks=[HumilityCallbackHandler(tier="tier2")])
    """

    def __init__(self, tier: str = "tier3") -> None:
        super().__init__()
        self._system_prompt = system_prompt(tier)

    def on_llm_start(self, serialized: dict, prompts: list[str], **kwargs: Any) -> None:
        messages = [{"role": "user", "content": p} for p in prompts]
        decision = evaluate(messages)
        if not decision.allow and decision.has_hard_deny:
            raise HumilityDenied(compassionate_response(decision.deny_reasons))

    @property
    def canonical_system_prompt(self) -> str:
        return self._system_prompt
