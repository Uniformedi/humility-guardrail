"""LiteLLM adapters — plug Humility into the LiteLLM proxy or SDK.

Exports two callbacks:

    HumilityPromptCallback     — soft guidance (Layer 1): prepends the canonical
                                 Humility system prompt to every request.
    HumilityGuardrailCallback  — hard enforcement (Layer 2): evaluates rules
                                 before the call; blocks or reframes on denial.

Subclass either to customize prompt loading (e.g. Redis) or decision sourcing
(e.g. OPA).
"""
from __future__ import annotations

import logging
import os
from typing import Any

try:
    from litellm.integrations.custom_logger import CustomLogger
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "LiteLLM is required for the LiteLLM adapter. "
        "Install with: pip install humility-guardrail[litellm]"
    ) from exc

from humility.prompt import system_prompt
from humility.responses import compassionate_response, reframe_instructions
from humility.rules import Decision, evaluate

logger = logging.getLogger("humility.litellm")

SENTINEL = "[HUMILITY_INJECTED]"


class HumilityPromptCallback(CustomLogger):
    """Prepend the canonical Humility system prompt to every LLM call.

    Override :meth:`load_prompt` to source the prompt from Redis, a database,
    or a remote config service.
    """

    def __init__(self, tier: str | None = None) -> None:
        super().__init__()
        self.tier = tier or os.environ.get("HUMILITY_TIER", "tier3")
        logger.info("HumilityPromptCallback initialized (tier=%s)", self.tier)

    def load_prompt(self) -> str:
        """Return the system prompt text. Override to load from external store."""
        return system_prompt(self.tier)

    async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        if call_type not in ("completion", "acompletion"):
            return data
        messages = data.get("messages") or []
        if not messages:
            return data
        if messages[0].get("role") == "system" and SENTINEL in (messages[0].get("content") or ""):
            return data

        prompt = self.load_prompt()
        if not prompt:
            return data

        if messages[0].get("role") == "system":
            existing = messages[0].get("content", "")
            messages[0]["content"] = f"{SENTINEL}\n{prompt}\n\n{existing}"
        else:
            messages.insert(0, {"role": "system", "content": f"{SENTINEL}\n{prompt}"})

        data["messages"] = messages
        return data


class HumilityGuardrailCallback(CustomLogger):
    """Hard-enforce Humility rules at the gateway.

    Strategy:
      1. :meth:`evaluate_decision` returns a Decision (default: local Python rules).
      2. On allow → pass through.
      3. On hard deny → raise with a compassionate response.
      4. On reframable deny → inject reframing system message and continue.

    Override :meth:`evaluate_decision` to delegate to OPA or another engine.
    Override :meth:`on_decision` to add audit logging.
    """

    def __init__(self, fail_mode: str = "closed") -> None:
        super().__init__()
        self.fail_mode = os.environ.get("HUMILITY_FAIL_MODE", fail_mode)
        logger.info("HumilityGuardrailCallback initialized (fail_mode=%s)", self.fail_mode)

    def evaluate_decision(
        self, messages: list[dict], user_info: dict
    ) -> Decision:
        """Return a Decision for the given request. Override to use OPA."""
        return evaluate(messages)

    def on_decision(self, decision: Decision, user_info: dict) -> None:
        """Hook for audit logging. Default: no-op."""
        return None

    async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        if call_type not in ("completion", "acompletion"):
            return data
        messages = data.get("messages") or []
        if not messages:
            return data

        metadata = data.get("metadata") or {}
        if metadata.get("humility_guardrail_evaluated"):
            return data

        user_info = user_api_key_dict or {}
        decision = self.evaluate_decision(messages, user_info)
        self.on_decision(decision, user_info)

        result_data: dict[str, Any] = {
            **data,
            "metadata": {**metadata, "humility_guardrail_evaluated": True},
        }

        if decision.allow:
            return result_data

        if self.fail_mode != "closed":
            logger.warning("Humility denial (log-only): %s", decision.deny_reasons)
            return result_data

        if decision.has_hard_deny:
            raise Exception(compassionate_response(decision.deny_reasons))

        reframe = reframe_instructions(decision.deny_reasons)
        if reframe:
            new_messages = list(messages)
            reframe_msg = {"role": "system", "content": f"[HUMILITY REFRAME]\n{reframe}"}
            insert_idx = len(new_messages) - 1
            for i in range(len(new_messages) - 1, -1, -1):
                if new_messages[i].get("role") == "user":
                    insert_idx = i
                    break
            new_messages.insert(insert_idx, reframe_msg)
            return {**result_data, "messages": new_messages}

        raise Exception(
            "Request blocked by Humility guardrail: "
            + "; ".join(decision.deny_reasons)
        )
