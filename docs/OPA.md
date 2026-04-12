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
