# Humility OPA Integration

The canonical Rego policy lives at `policies/humility/base.rego` and evaluates to a decision at `data.humility.decision`.

## Load the policy

```bash
opa run --server policies/humility/
```

## Query shape

```http
POST /v1/data/humility/decision
Content-Type: application/json

{
  "input": {
    "messages": [
      {"role": "user", "content": "Predict Q4 revenue."}
    ],
    "request_type": "prediction",
    "data_classification": "internal",
    "uncertainty_declared": false,
    "has_human_consensus": false,
    "within_validated_domain": false
  }
}
```

## Response shape

```json
{
  "result": {
    "allow": false,
    "deny_reasons": [
      "Humility 6: Extrapolation beyond validated domains is prohibited"
    ],
    "obligations": [
      {"type": "audit.log", "priority": 2, "params": {...}}
    ]
  }
}
```

## Test

```bash
opa test policies/humility/
```

## Enforcement model

OPA is pure — it receives input, returns a decision. Your application is responsible for executing obligations (audit logging, attestation prompts, review queue enqueue, etc.). Precedence: Humility is mandatory; industry overlays (HIPAA, SOX, FDCPA, FERPA, GLBA) stack on top without overriding Humility denials.

## Known divergence: text normalisation

`humility.rules` and `policies/humility/base.rego` are meant to mirror each
other, and they agree on every rule and every pattern. They do **not** agree on
how text is folded before those patterns are matched.

| | Python (`rules.py`) | Rego (`base.rego`) |
|---|---|---|
| Lowercase | yes | yes |
| NFKC (`ｃｏｓｍｉｃ`) | yes | no |
| Confusable folding (Cyrillic `с`, Greek `ο`) | yes | no |
| Invisible/bidi stripping (`cos<U+200B>mic`) | yes | no |

Rego has no NFKC primitive and no character-translation builtin, so the policy
cannot reproduce the Python folding on its own. The practical consequence: a
message using homoglyphs or zero-width characters to disguise a pattern is
**denied by the Python evaluator and allowed by the OPA policy**.

If you enforce via OPA, normalise upstream of the policy query — fold the text
in the application before putting it in `input`, using the same passes
`humility.rules._normalize` applies. Do not assume the two paths return the
same decision for adversarial input; they do not.
