# Architecture

Humility is deliberately small. Three layers, each usable independently.

```
┌───────────────────────────────────────────────────────┐
│ Layer 1: system prompt                                │
│   humility.prompt.system_prompt(tier)                 │
│   Zero deps. Works with any model.                    │
├───────────────────────────────────────────────────────┤
│ Layer 2: runtime guardrail                            │
│   humility.rules.evaluate(messages, ...)              │
│   Pure Python, no network. Deterministic Decision.    │
├───────────────────────────────────────────────────────┤
│ Layer 3: OPA policy (enterprise)                      │
│   policies/humility/base.rego                         │
│   Adds obligations, attestation, audit chain.         │
└───────────────────────────────────────────────────────┘
```

## Design principles

- **Immutability.** `Decision` is a frozen dataclass. Messages are never mutated in place by `evaluate()`.
- **No network calls.** `rules.evaluate()` is pure. Adapters may add I/O (e.g. OPA queries, audit logging), never the rules.
- **Override, don't configure.** Redis-backed prompts, OPA-backed decisions, hub-backed audit — all live in adapter subclasses, not in the core.
- **Fail closed.** Default `fail_mode="closed"` — on denial, block. Operators opt into `log_only`.
- **Compassion is mandatory.** Hard denials always return a user-facing explanation and next steps. Never leave the user stranded.

## Non-goals

- Not a moderation filter (no toxicity scoring, no NSFW classifier).
- Not a PII scanner (use a DLP layer upstream).
- Not a jailbreak detector (orthogonal concern).

Humility enforces **alignment**, not **safety**. Stack it with those other layers.
