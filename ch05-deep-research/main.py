"""Sections 5.1-5.4: Deep Research — recursive map-reduce with a search API."""
from flow import create_deep_research_flow

shared = {"topic": "PocketFlow, the 100-line minimalist LLM framework"}
print(f"Researching: {shared['topic']}\n")
create_deep_research_flow().run(shared)
print(f"\n--- Report ---\n{shared['report']}")
