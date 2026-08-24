"""Section 6.6: AI Newsletter — curate, filter, summarize, format."""
from flow import create_newsletter_flow

TOPICS = [
    "AI agents framework news this week",
    "LLM benchmark results 2025 2026",
    "AI startup funding rounds this month",
]

shared = {"topics": TOPICS}
create_newsletter_flow().run(shared)
print(shared["newsletter"])
