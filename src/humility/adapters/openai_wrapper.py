"""OpenAI SDK wrapper — guards ``client.chat.completions.create`` with Humility.

Usage::

    from openai import OpenAI
    from humility.adapters.openai_wrapper import with_humility

    client = with_humility(OpenAI(), tier="tier2")
    resp = client.chat.completions.create(model="gpt-4o", messages=[...])
"""
from __future__ import annotations

from typing import Any

from humility.prompt import system_prompt
from humility.responses import compassionate_response, reframe_instructions
from humility.rules import evaluate


class HumilityDenied(Exception):
    """Raised when a request is blocked by Humility (hard deny)."""


def with_humility(client: Any, *, tier: str = "tier3", fail_mode: str = "closed") -> Any:
    """Wrap an OpenAI (or compatible) client so every chat completion is guarded.

    The wrapper:
      - Prepends the canonical Humility system prompt.
      - Evaluates rules; hard-blocks with HumilityDenied, reframes softly.

    Returns the same client with a patched ``chat.completions.create`` method.
    Fully compatible with OpenAI, Azure OpenAI, and any SDK that mirrors the
    same surface (e.g. openai-python against Ollama, LMStudio).
    """
    original_create = client.chat.completions.create
    prompt = system_prompt(tier)

    def create(*args, **kwargs):
        messages = list(kwargs.get("messages") or [])
        if not messages or messages[0].get("role") != "system":
            messages.insert(0, {"role": "system", "content": prompt})
        else:
            messages[0] = {
                "role": "system",
                "content": f"{prompt}\n\n{messages[0].get('content', '')}",
            }

        decision = evaluate(messages)
        if not decision.allow:
            if fail_mode == "closed" and decision.has_hard_deny:
                raise HumilityDenied(compassionate_response(decision.deny_reasons))
            reframe = reframe_instructions(decision.deny_reasons)
            if reframe:
                insert_idx = next(
                    (i for i in range(len(messages) - 1, -1, -1)
                     if messages[i].get("role") == "user"),
                    len(messages) - 1,
                )
                messages.insert(insert_idx, {
                    "role": "system",
                    "content": f"[HUMILITY REFRAME]\n{reframe}",
                })

        kwargs["messages"] = messages
        return original_create(*args, **kwargs)

    client.chat.completions.create = create
    return client
