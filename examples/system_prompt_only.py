"""Simplest possible integration — just the prompt."""
from anthropic import Anthropic
from humility import system_prompt

client = Anthropic()
resp = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    system=system_prompt(tier="tier2"),
    messages=[{"role": "user", "content": "Predict next quarter's stock price."}],
)
print(resp.content[0].text)
