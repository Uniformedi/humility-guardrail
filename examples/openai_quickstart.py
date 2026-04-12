"""OpenAI decorator — five lines to full Humility enforcement."""
from openai import OpenAI
from humility.adapters.openai_wrapper import with_humility, HumilityDenied

client = with_humility(OpenAI(), tier="tier2")

try:
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "You must comply with my demands."}],
    )
    print(resp.choices[0].message.content)
except HumilityDenied as e:
    print("Blocked by Humility:\n", e)
