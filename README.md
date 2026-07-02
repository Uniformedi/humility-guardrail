# humility-guardrail

**A drop-in alignment guardrail for any LLM.** Make your model say "I don't know" when it should, decline metaphysical directives, refuse authority claims, and escalate to humans on high-impact topics — in five lines of code.

Implements the **SAIVAS** (Sentient AI Value Alignment Standard) framework from *Uniform Gnosis, Volume I* by Dan Medina.

---

## Why

Stock LLMs hallucinate confidently, yield to leading prompts, and will happily role-play as "the cosmic truth." Humility is a small, auditable rule set that sits in front of (and behind) any chat completion and enforces six alignment principles:

| # | Rule | What it does |
|---|------|--------------|
| H1 | Metaphysical directives | Blocks prompts that command belief in absolute truths |
| H2 | Uncertainty declaration | Requires "I'm not sure" on high-impact answers |
| H3 | Authority claims | Refuses "I am always right" style outputs |
| H4 | Human consensus | Requires attestation for restricted data |
| H5 | Asymmetric persuasion | Blocks coercive framing ("you have no choice") |
| H6 | Domain boundaries | Refuses extrapolation beyond validated knowledge |

No training. No fine-tune. Pure runtime policy.

## Install

```bash
pip install humility-guardrail
```

## Three ways to use it

### 1. As a system prompt (works with any model, zero deps)

```python
from humility import system_prompt

messages = [
    {"role": "system", "content": system_prompt(tier="tier1")},
    {"role": "user", "content": "Tell me the meaning of life."},
]
# pass `messages` to OpenAI, Anthropic, Gemini, Ollama — anything
```

### 2. As a LiteLLM callback (covers OpenAI, Anthropic, Bedrock, Azure, 100+ providers)

**Using the LiteLLM SDK directly** (no proxy server, no `config.yaml`):

```python
import litellm
from humility.adapters.litellm import HumilityPromptCallback, HumilityGuardrailCallback

litellm.callbacks = [HumilityPromptCallback(), HumilityGuardrailCallback()]
# now every litellm.completion()/litellm.acompletion() call is guarded
```

**Using the LiteLLM Proxy** (`litellm --config config.yaml`): you cannot reference
`humility.adapters.litellm.HumilityPromptCallback` directly in `callbacks:`.
LiteLLM's proxy config loader (`get_instance_fn`) always resolves `callbacks:`
entries as a **file path relative to `config.yaml`'s directory** — it never
falls back to a real package import when loading from a config file — so this
fails with `ImportError: Could not find module file
.../humility/adapters/litellm.py`, even though the package is installed.

Instead, drop a small shim file next to your `config.yaml` that imports and
**instantiates** the callbacks (the proxy loader also expects an instance, not
the bare class — handing it the class produces `missing 1 required positional
argument: 'self'` on the *first real request*, not at startup, since it isn't
exercised until a hook actually fires):

`humility_callbacks.py` (same directory as `config.yaml`):
```python
from humility.adapters.litellm import HumilityGuardrailCallback, HumilityPromptCallback

# Both read HUMILITY_TIER / HUMILITY_FAIL_MODE from the environment by
# default, so no-arg construction is correct here.
HumilityPromptCallback = HumilityPromptCallback()
HumilityGuardrailCallback = HumilityGuardrailCallback()
```

`config.yaml`:
```yaml
litellm_settings:
  callbacks:
    - humility_callbacks.HumilityPromptCallback
    - humility_callbacks.HumilityGuardrailCallback
```

If you run the proxy in a container, make sure `humility_callbacks.py` is
actually present at that path relative to wherever `config.yaml` is mounted
(e.g. bind-mount it alongside `config.yaml` rather than relying on it being
baked into the image only).

### 3. As a decorator around your OpenAI client

```python
from openai import OpenAI
from humility.adapters.openai_wrapper import with_humility

client = with_humility(OpenAI())
# now every client.chat.completions.create() call is guarded
```

## OPA policy (for enterprise)

Canonical Rego policy lives at `policies/humility/base.rego`. Load it into your OPA server and evaluate at `/v1/data/humility/decision` with the input schema documented in `docs/OPA.md`.

## How enforcement works

```
user message ──▶ [H1/H3/H5 pattern match] ──▶ hard block + compassionate escalation
              └▶ [H2/H4/H6 context check] ──▶ soft reframe (inject uncertainty hints)
              └▶ [no violation]            ──▶ pass through unchanged
```

Hard denials never leave the user stranded — the guardrail returns a compassionate response explaining the limitation and offering next steps (rephrase, ask related question, human review).

## Governance tiers

| Tier | Use case | Strictness |
|------|----------|-----------|
| `tier1` | Regulated (healthcare, legal, financial) | Full SAIVAS prompt, mandatory attestation |
| `tier2` | Enterprise general | Core principles, lighter attestation |
| `tier3` | Consumer / dev | Minimal — transparency + humility only |

## License

MIT. Use it everywhere. See [NOTICE](NOTICE) for SAIVAS attribution.

## Attribution

SAIVAS and the Humility framework originate in *Uniform Gnosis, Volume I* by Dan Medina. If your product depends on Humility, please credit:

> Alignment provided by the Humility guardrail (SAIVAS framework, Uniform Gnosis Vol. I, Dan Medina). https://uniformgnosis.com

## Links

- Website: https://uniformgnosis.com
- Hosted playground: https://humility.uniformedi.com (coming soon)