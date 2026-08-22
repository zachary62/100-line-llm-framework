"""Run every example in this repo against a stub model, with no API key and no cost.

    python scripts/smoke_test.py            # all chapters
    python scripts/smoke_test.py ch03       # just one

This does not check that the model gives good answers, which is what your eyes and
chapter 13's evals are for. It checks the part that silently rots: that every file
still imports, every graph still wires up, every node still returns an action some
edge actually matches, and no loop runs forever. A stub stands in for the LLM and
answers in whatever format the prompt asked for, so YAML parsing and branch routing
get exercised for real.

Exit code is non-zero if any example fails, so CI can run it.
"""
import argparse
import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent

# Scripts that talk to something other than an LLM (a real browser, a real PDF, a
# real audio device) or that are interactive by design. Everything else runs.
SKIP = {
    "ch06-workflow-products/create_invoice_pdf.py",  # writes a PDF with fpdf2
    "ch06-workflow-products/invoice_processing.py",  # needs that PDF and vision
    "ch06-workflow-products/notebook_lm.py",         # needs the TTS endpoint
    "ch10-coding-agent/setup_test_project.py",       # a fixture generator, run by the agents
}

STUB = r'''
import sys, types, itertools, re, builtins

_calls = itertools.count()

_SNIPPETS = {
    "python": "print('stub')",
    "sql": "SELECT 1",
    "mermaid": "graph LR\n    A --> B",
    "bash": "echo stub",
}

def _pick(options, first_time):
    """Loop branches list the keep-going option first and the terminal one last."""
    return options[0] if (first_time and len(options) > 1) else options[-1]

def _fake_answer(prompt):
    """Answer in whatever shape the prompt demanded."""
    n = next(_calls)
    blocks = re.findall(r"```yaml\n(.*?)```", prompt, re.S)
    if blocks:
        block = _pick(blocks, n == 0)
        filled = re.sub(r"<[^>\n]*>", "stub", block)
        filled = re.sub(r"^(\s*-\s*)$", r"\1stub", filled, flags=re.M)
        # "action: read/answer" offers alternatives on one line: take one of them.
        filled = re.sub(r"^(\s*\w+:\s*)([\w-]+(?:/[\w-]+)+)\s*$",
                        lambda m: m.group(1) + _pick(m.group(2).split("/"), n == 0),
                        filled, flags=re.M)
        return "```yaml\n" + filled + "```"
    if "```json" in prompt:
        # Tool-call prompts. The stub always says "done", so agent loops make one
        # decision and exit: enough to exercise parsing, wiring, and termination
        # without pretending a stub can pick sensible tool arguments.
        return '```json\n{"tool": "done", "args": {}}\n```'
    for lang, snippet in _SNIPPETS.items():
        if "```" + lang in prompt:
            return "```" + lang + "\n" + snippet + "\n```"
    for token in ("PASS", "APPROVE", "approve", "SAFE", "YES"):
        if token in prompt:
            return token
    return "stub answer"

def install():
    call_llm = types.ModuleType("call_llm")
    call_llm.FAST_MODEL = call_llm.MODEL = "stub-fast"
    call_llm.SMART_MODEL = "stub-smart"
    call_llm.EMBED_MODEL = "stub-embed"
    call_llm.TTS_MODEL = "stub-tts"

    def _call_llm(prompt, model=None, **kw):
        return _fake_answer(prompt)

    class _Models:
        def generate_content(self, model=None, contents=None, config=None, **kw):
            text = contents if isinstance(contents, str) else str(contents)
            r = types.SimpleNamespace(text=_fake_answer(text))
            r.candidates = [types.SimpleNamespace(
                content=types.SimpleNamespace(parts=[types.SimpleNamespace(
                    text=r.text, inline_data=types.SimpleNamespace(data=b"\0" * 32))]))]
            return r

        def embed_content(self, model=None, contents=None, **kw):
            h = abs(hash(str(contents)))
            vec = [((h >> i) % 97) / 97 for i in range(8)]
            return types.SimpleNamespace(embeddings=[types.SimpleNamespace(values=vec)])

        def count_tokens(self, model=None, contents=None, **kw):
            return types.SimpleNamespace(total_tokens=len(str(contents)) // 4)

    call_llm.client = types.SimpleNamespace(models=_Models(), aio=types.SimpleNamespace(models=_Models()))
    call_llm.call_llm = _call_llm
    sys.modules["call_llm"] = call_llm

    ddgs = types.ModuleType("ddgs")
    class DDGS:
        def text(self, query, max_results=3):
            return [{"title": f"stub result {i}", "body": f"stub snippet for {query}",
                     "href": "https://example.com"} for i in range(max_results)]
    ddgs.DDGS = DDGS
    sys.modules["ddgs"] = ddgs

    search = types.ModuleType("search_web")
    search.search_web = lambda query, max_results=3: f"[stub search results for {query}]"
    sys.modules["search_web"] = search

    replies = itertools.chain(["hello", "exit"], itertools.repeat("exit"))
    builtins.input = lambda *a, **k: next(replies)
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("filter", nargs="?", default="", help="only run paths containing this string")
    ap.add_argument("--timeout", type=int, default=120)
    args = ap.parse_args()

    (REPO / "scripts" / "_smokestub.py").write_text(STUB)

    files = [p for p in sorted(REPO.glob("ch*/*.py"))
             if str(p.relative_to(REPO)) not in SKIP and args.filter in str(p)]

    failures = []
    for path in files:
        rel = path.relative_to(REPO)
        code = (f"import sys; sys.path[:0]=[{str(path.parent)!r}, {str(REPO / 'scripts')!r}, {str(REPO)!r}]; "
                f"import _smokestub, runpy; _smokestub.install(); "
                f"runpy.run_path({str(path)!r}, run_name='__main__')")
        try:
            r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                               timeout=args.timeout, cwd=REPO)
        except subprocess.TimeoutExpired:
            print(f"TIMEOUT  {rel}")
            failures.append((rel, "timed out"))
            continue
        if r.returncode == 0:
            print(f"ok       {rel}")
        else:
            tail = (r.stderr.strip().splitlines() or ["(no output)"])[-1]
            print(f"FAIL     {rel}  {tail}")
            failures.append((rel, tail))

    print(f"\n{len(files) - len(failures)}/{len(files)} examples ran clean against the stub model")
    for rel, why in failures:
        print(f"  {rel}: {why}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
