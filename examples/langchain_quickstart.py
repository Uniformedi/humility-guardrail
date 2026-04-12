"""LangChain integration — attach Humility as a callback handler."""
from langchain_openai import ChatOpenAI
from humility import system_prompt
from humility.adapters.langchain_handler import HumilityCallbackHandler

llm = ChatOpenAI(
    model="gpt-4o",
    callbacks=[HumilityCallbackHandler(tier="tier2")],
)

response = llm.invoke([
    ("system", system_prompt("tier2")),
    ("user", "What will the S&P 500 close at next Friday?"),
])
print(response.content)
