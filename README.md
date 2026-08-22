<div align="center">
  <img src="./img/title.png" alt="PocketFlow" width="600"/>
  <br>
  <strong style="font-size:2em">Code for <em>The 100-Line LLM Framework</em></strong>
  <br>
  <a href="./pocketflow/__init__.py"><img src="https://img.shields.io/badge/the%20whole%20framework-100%20lines-blue" alt="100 lines"/></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="MIT"/></a>
</div>

Clone this and you can run every program in the book. There is one folder per chapter.

None of it is pseudocode. The chatbot holds a real conversation, and the coding agent opens a real project, edits the files, and runs the tests. Each chapter folder has a README with the flow diagram and the output I got when I ran it.

All of it runs on [PocketFlow](https://github.com/The-Pocket/PocketFlow), which is 100 lines of Python with no dependencies. You can read the whole file in an afternoon, and when you need it to behave differently you copy it into your own repo and edit it. There is no layer underneath to outgrow.

---

## Quickstart

```bash
git clone https://github.com/zachary62/100-line-llm-framework
cd 100-line-llm-framework
pip install -r requirements.txt

export GEMINI_API_KEY="your-key"
python call_llm.py                   # sanity check

python ch02-graph/chatbot.py         # a working chatbot, 30 lines
python ch03-patterns/agent.py        # a ReAct agent that searches the web
python ch05-deep-research/deep_research.py
```

**Any provider works.** `call_llm.py` is the only file with vendor code, about ten lines of it. Gemini is active; OpenAI, Anthropic, and local Ollama sit in the same file, commented out. (Two chapter 6 examples call the provider's PDF and speech APIs directly, since they aren't text.)

**Models are named by role, not version.** Override any of them without touching code:

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

Chapters 8, 9, 11, 12, and 13 have no folder. They don't build new programs; they change the prompts, tools, context, and process around the ones you already ran.

For what the book only mentions in passing (MCP, A2A, streaming, web front ends, tracing, voice chat), the [PocketFlow cookbook](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook) has a worked example of each.

---

## The three ideas

- **Node** — one unit of work, with three steps: `prep` reads from the shared store, `exec` does the work, `post` writes results back and returns an action string.
- **Flow** — how nodes connect: chain, branch, loop, nest. A Flow is itself a Node, which is why an entire agent can sit in one slot of a bigger graph.
- **Shared store** — a Python dict. Print it at any moment and you see your whole application's state.

<div align="center">
  <img src="./img/abstraction.png" width="700"/>
</div>

Every pattern in the book is those three ideas wired differently: a chatbot is a loop, RAG is a chain, and an agent is a loop with a branch.

<div align="center">
  <img src="./img/design.png" width="700"/>
</div>

---

## Scripts

```bash
python scripts/smoke_test.py         # all 33 examples against a stub model, no key, no spend
python scripts/framework_audit.py    # re-derives chapter 1's framework line counts
```

The smoke test runs in CI on every push. The stub replies in whatever format each prompt asked for, so YAML parsing, tool calls, branch routing, and loop termination all get exercised for real. It can't judge answer quality; that's what chapter 13's evals are for.

---

## License

MIT. Use the code in your own projects, commercial or not.
