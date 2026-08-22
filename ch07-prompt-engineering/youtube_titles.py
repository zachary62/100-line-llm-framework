"""Section 7.2 — YouTube title prompt iteration. Shows how domain knowledge transforms output."""
import sys
sys.path.append("..")
from call_llm import call_llm

TRANSCRIPT_SUMMARY = """This video teaches viewers how to build AI applications
(chatbots, RAG, agents) from scratch using only 100 lines of Python instead of
heavyweight frameworks like LangChain. It shows that every AI product — ChatGPT,
Cursor, NotebookLM — is the same graph pattern underneath, and you can build them
yourself without any framework."""

# v1: What most people write
prompt_v1 = f"""Generate 5 YouTube title options for this video.
Return only the titles, one per line, no numbering or explanation.

{TRANSCRIPT_SUMMARY}"""

# v2: Add domain knowledge — what makes titles click
prompt_v2 = f"""Generate 5 YouTube title options for this video.
Return only the titles, one per line, no numbering or explanation.

A good title opens a curiosity gap — the viewer needs to click to close the loop.
Techniques that work:
- Specific numbers that seem unexpected ("7,292 miles")
- Contrast ("$1 vs $500,000 plane ticket")
- Counterintuitive claim ("Why studying LESS gives you an advantage")
- Insider framing ("What nobody tells you about...")
- Imply transformation ("I tried X for 30 days")

{TRANSCRIPT_SUMMARY}"""

# v3: Add constraints and anti-patterns from experience
prompt_v3 = f"""Generate 5 YouTube title options for this video.
Return only the titles, one per line, no numbering or explanation.

A good title opens a curiosity gap — the viewer needs to click to close the loop.
Techniques that work:
- Specific numbers that seem unexpected ("7,292 miles")
- Contrast ("$1 vs $500,000 plane ticket")
- Counterintuitive claim ("Why studying LESS gives you an advantage")
- Insider framing ("What nobody tells you about...")
- Imply transformation ("I tried X for 30 days")

Constraints:
- 40-60 characters (truncation on mobile)
- No clickbait — the title must be payoff-able by the actual content
- Use power words: "actually," "secret," "proven," not filler words like
  "interesting" or "comprehensive"
- Do NOT use generic words: "guide," "tutorial," "explained," "everything
  you need to know," "master," "ultimate"
- Do NOT use colons or "How to" — they signal low-effort content

{TRANSCRIPT_SUMMARY}"""

for label, prompt in [("v1: No domain knowledge", prompt_v1),
                      ("v2: + curiosity gap techniques", prompt_v2),
                      ("v3: + constraints and anti-patterns", prompt_v3)]:
    print(f"{'=' * 60}\n{label}\n{'=' * 60}")
    print(call_llm(prompt))
    print()
