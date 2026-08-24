# Chapter 6: Workflow Products

One folder per product, each in the standard PocketFlow project layout: `main.py` (entry point and shared store), `flow.py` (wiring), `nodes.py` (the nodes), `docs/design.md` (the high-level design), and a README recording the output from a real run.

| Folder | Section | Pattern |
|---|---|---|
| [`notebook-lm/`](notebook-lm/) | 6.1 NotebookLM | Three-node chain: Analyze → Script → Audio |
| [`text-to-sql/`](text-to-sql/) | 6.2 Text to SQL | Chain + self-healing loop (three repairs, then give up) |
| [`codebase-knowledge/`](codebase-knowledge/) | 6.3 Codebase knowledge | Chain + context-carrying loop |
| [`lead-gen/`](lead-gen/) | 6.4 Lead gen | Four-node chain, LLM touches only the last two |
| [`invoice-processing/`](invoice-processing/) | 6.5 Invoice processing | Extract → deterministic Validate |
| [`newsletter/`](newsletter/) | 6.6 AI newsletter | Curate → Filter → Summarize → Format |

Run any of them from inside its folder:

```bash
cd text-to-sql && python main.py
```
