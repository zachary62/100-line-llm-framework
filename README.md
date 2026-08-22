<div align="center">
  <img src="./img/title.png" alt="PocketFlow" width="600"/>
  <br>
  <strong style="font-size:2em">Code for <em>The 100-Line LLM Framework</em></strong>
  <br>
  <a href="./pocketflow/__init__.py"><img src="https://img.shields.io/badge/the%20whole%20framework-100%20lines-blue" alt="100 lines"/></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="MIT"/></a>
</div>

Every program the book builds is a file in this repo, organized by chapter and runnable in one command. Nothing here is pseudocode: the chatbot is a chatbot, the coding agent edits a real project and runs its tests, and each chapter folder has a README with the flow diagram and the output I got when I ran it. Chapters 8, 9, 11, 12, and 13 have no folder because they don't build new programs, they change the prompts, tools, context, and process around the ones you already ran.

The framework underneath all of it is [PocketFlow](https://github.com/The-Pocket/PocketFlow): 100 lines of Python, no dependencies, no vendor lock-in, no hidden control flow. You can read the whole thing before your coffee gets cold.

---

## Quickstart

```bash
git clone https://github.com/zachary62/100-line-llm-framework
cd 100-line-llm-framework
pip install -r requirements.txt

export GEMINI_API_KEY="your-key"     # any provider works, see below
python call_llm.py                   # sanity check: prints a hello from both model tiers

python ch02-graph/chatbot.py         # a working chatbot, 30 lines
python ch03-patterns/agent.py        # a ReAct agent that searches the web
python ch05-deep-research/deep_research.py
```

**Any provider works.** `call_llm.py` is the only file that knows about a model vendor for text, and it's about ten lines. The two exceptions are the chapter 6 examples that aren't text at all: `invoice_processing.py` reads a PDF and `notebook_lm.py` synthesizes two voices, and both call the provider's multimodal API directly. The examples were run on Gemini, and OpenAI, Anthropic, and local Ollama versions are sitting in the same file, commented out. Swap the block, keep everything else.

**Model IDs change; roles don't.** `call_llm.py` defines `FAST_MODEL` (drafting, classification), `SMART_MODEL` (judging, planning), `EMBED_MODEL`, and `TTS_MODEL`, and every example calls those names. When a provider retires a model, you edit one line here rather than hunting through thirteen chapters. Override without touching code:

```bash
export FAST_MODEL=gemini-3.6-flash
export SMART_MODEL=gemini-3.6-pro
```

---

## What's in each chapter folder

| Chapter | Folder | What you'll run |
|---|---|---|
| 2. The graph | [`ch02-graph/`](./ch02-graph) | The three-step node, the four flow operations, a 30-line chatbot, retries, YAML structured output, batch, and async parallel |
| 3. Workflow, agent, and more | [`ch03-patterns/`](./ch03-patterns) | Tweet workflow, ReAct agent, guardrail, judge, majority vote, debate, chain of thought, self-healing code, heartbeat monitor |
| 4. RAG | [`ch04-rag/`](./ch04-rag) | The whole pipeline twice, once on word overlap with no embedding API and once on real embeddings, plus cosine similarity from scratch and an agentic RAG loop |
| 5. Deep research | [`ch05-deep-research/`](./ch05-deep-research) | Planner → Researcher → Synthesizer, looping until the report is done |
| 6. Workflow products | [`ch06-workflow-products/`](./ch06-workflow-products) | A NotebookLM clone, text-to-SQL with a debug loop, lead generation, invoice extraction, an AI newsletter |
| 7. Prompt engineering | [`ch07-prompt-engineering/`](./ch07-prompt-engineering) | The same prompt in three versions, showing what domain knowledge does to the output |
| 10. Coding agent | [`ch10-coding-agent/`](./ch10-coding-agent) | Four versions of a coding agent, from the naive three-tool loop to one with edit-by-diff, two-pass reading, and safety rails, editing a real test project |

For the topics the book only mentions in passing (MCP, A2A, streaming, FastAPI and Gradio and Streamlit front ends, tracing, voice chat, text-to-speech), the [PocketFlow cookbook](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook) has a worked example of each.

---

## Checking the examples still run

Every example in this repo runs in CI against a stub model, so no key and no spend:

```bash
python scripts/smoke_test.py          # 33/33 examples, about a minute
python scripts/smoke_test.py ch03     # one chapter
```

The stub answers in whatever format each prompt asked for, which means YAML parsing,
JSON tool calls, branch routing, and loop termination all get exercised for real. What
it can't check is answer quality, which is what chapter 13's evals are for.

---

## Why 100 lines

Most LLM frameworks ship six figures of code, most of which is application wrappers and vendor bindings you didn't ask for. The table below is measured, not quoted: `scripts/framework_audit.py` clones each framework at the pinned release, counts non-blank, non-comment Python in the packages that ship on PyPI, and resolves the package count from each project's own lock file.

```bash
python scripts/framework_audit.py --clone     # git only, nothing is installed
```

| Framework | Pinned at | Framework code installed | Packages installed |
|---|---|---:|---:|
| LangChain | 1.2.14 (2026-03-31) | 131,014 | 33 |
| LangChain Classic | 1.0.3 | 53,839 | — |
| CrewAI | 1.12.2 (2026-03-25) | 81,963 | 136 |
| LangGraph | 1.1.4 (2026-03-31) | 33,826 | 31 |
| deepagents | 0.4.12 (2026-03-20) | 7,402 | 50 |
| AutoGen | 0.7.5 (2025-09-29) | 15,479 | 11 |
| smolagents | 1.24.0 (2026-01-16) | 9,896 | — |
| **PocketFlow** | — | **100** | **0** |

LangChain's number is the honest total for `pip install langchain`, which also installs `langchain-core`, four `langgraph` packages, and `langsmith`. That's more Python than all of Django. The script scores PocketFlow at 88 because it ignores blank and comment lines; the file itself is 100 lines.

---

## The three ideas

- **Node** — one unit of work, with three steps: `prep` reads from the shared store, `exec` does the work, `post` writes results back and returns an action string.
- **Flow** — how nodes connect: chain, branch, loop, nest. A Flow is itself a Node, which is why an entire agent can sit in one slot of a bigger graph.
- **Shared store** — a Python dict. Print it at any moment and you see your whole application's state.

<div align="center">
  <img src="./img/abstraction.png" width="700"/>
</div>

Every pattern in the book is those three ideas wired differently:

<div align="center">
  <img src="./img/design.png" width="700"/>
</div>

---

## License

MIT. Use the code in your own projects, commercial or not.
