"""Section 10.1-10.5: Coding Agent — one node per tool, patch_file as subflow"""
import sys, os, subprocess, re, json, difflib
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from pocketflow import Node, Flow
from call_llm import call_llm
from setup_test_project import setup_test_project, WORKDIR

MEMORY_FILE = os.path.join(WORKDIR, ".memory.md")
MAX_STEPS = 50
COMPACT_AFTER = 30

# ===== Utilities =====

def _path(p): return os.path.join(WORKDIR, p)

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE) as f: return f.read()
    return ""

def save_memory(history):
    summary = call_llm(
        "Summarize key learnings from this coding session in 2-3 bullets:\n"
        + "\n".join(f"- {h['tool']}: {h['result']}" for h in history[-5:])
    )
    with open(MEMORY_FILE, "w") as f: f.write(summary)

def load_skills():
    p = os.path.join(WORKDIR, "AGENTS.md")
    if os.path.exists(p):
        with open(p) as f: return f.read()
    return ""

TOOL_DESC = """- list_files(directory='.') — List all files
- grep_search(pattern, path='.') — Search for pattern in .py files
- read_file(path, start=1, end=None) — Read file with line numbers
- patch_file(path, old_str, new_str) — Replace old_str with new_str. Must be unique; include surrounding lines.
- run_command(cmd) — Run shell command
- done(result) — Task complete"""

VALID_TOOLS = {"list_files", "grep_search", "read_file", "patch_file", "run_command"}

# ===== Agent Nodes =====

class CompactHistory(Node):
    def prep(self, shared):
        return shared.get("history", []), shared["task"]

    def exec(self, inputs):
        history, task = inputs
        if len(history) <= COMPACT_AFTER: return history
        old = history[:len(history) - COMPACT_AFTER // 2]
        recent = history[len(history) - COMPACT_AFTER // 2:]
        old_text = "\n".join(f"- {h['tool']}: {h['result']}" for h in old)
        summary = call_llm(f"Summarize these past actions briefly:\n{old_text}")
        print(f"  [Compacted {len(old)} old steps into summary]")
        return [{"tool": "summary", "args": {}, "result": summary}] + recent

    def post(self, shared, prep_res, exec_res):
        shared["history"] = exec_res

class Decide(Node):
    def prep(self, shared):
        history = shared.get("history", [])
        skills = load_skills()
        memory = load_memory()

        history_text = ""
        for h in history:
            args_str = ", ".join(f"{k}={repr(v)}" for k, v in h.get("args", {}).items())
            history_text += f"\n[{h['tool']}({args_str})]\n{h['result']}\n"

        return f"""You are a coding agent. Your job: fix failing tests.
{f"Project rules:{chr(10)}{skills}" if skills else ""}
{f"Memory from past sessions:{chr(10)}{memory}" if memory else ""}
Available tools:
{TOOL_DESC}

Task: {shared['task']}

History:{history_text or " (none yet — start by running the tests)"}

Pick ONE tool. Output ONLY json:
```json
{{"tool": "tool_name", "args": {{"arg1": "value1"}}, "reason": "why"}}
```"""

    def exec(self, prompt):
        resp = call_llm(prompt)
        json_str = resp.split("```json")[1].split("```")[0].strip()
        parsed = json.loads(json_str)
        assert "tool" in parsed
        return parsed

    def post(self, shared, prep_res, exec_res):
        tool = exec_res.get("tool", "done")
        step = shared.get("step", 0) + 1
        shared["step"] = step

        if tool == "done" or step >= MAX_STEPS:
            shared["result"] = exec_res.get("result", exec_res.get("args", {}).get("result", ""))
            if shared.get("history"): save_memory(shared["history"])
            return "done"

        print(f"  [{step}] {tool} — {exec_res.get('reason', '')}")
        shared["tool_call"] = exec_res

        if tool not in VALID_TOOLS:
            shared.setdefault("history", []).append({
                "tool": tool, "args": {}, "result": f"Unknown tool '{tool}'. Use: {', '.join(VALID_TOOLS)}"
            })
            return "retry"

        return tool  # action = tool name → graph routes to the right node


# ===== Tool Nodes (one per tool) =====

class ToolNode(Node):
    """Base: reads args from shared["tool_call"], appends result to history."""
    def prep(self, shared):
        return shared["tool_call"].get("args", {})
    def post(self, shared, prep_res, exec_res):
        shared.setdefault("history", []).append({
            "tool": shared["tool_call"]["tool"],
            "args": shared["tool_call"].get("args", {}),
            "result": str(exec_res),
        })
        print(f"  → {str(exec_res)[:200]}")

class ListFiles(ToolNode):
    def exec(self, args):
        result = []
        for root, _, files in os.walk(_path(args.get("directory", "."))):
            for f in files:
                if not f.startswith("."): result.append(os.path.relpath(os.path.join(root, f), WORKDIR))
        return "\n".join(result)

class GrepSearch(ToolNode):
    def exec(self, args):
        pattern, path = args.get("pattern", ""), args.get("path", ".")
        results = []
        for root, _, files in os.walk(_path(path)):
            for fname in files:
                if not fname.endswith(".py"): continue
                fpath = os.path.join(root, fname)
                with open(fpath) as f:
                    for i, line in enumerate(f, 1):
                        if re.search(pattern, line):
                            results.append(f"{os.path.relpath(fpath, WORKDIR)}:{i}: {line.rstrip()}")
        return "\n".join(results) or "No matches"

class ReadFile(ToolNode):
    def exec(self, args):
        with open(_path(args["path"])) as f: lines = f.readlines()
        end = args.get("end") or len(lines)
        start = args.get("start", 1)
        return "".join(f"{i}: {l}" for i, l in enumerate(lines[start-1:end], start))

class RunCommand(ToolNode):
    def exec(self, args):
        r = subprocess.run(args["cmd"], shell=True, capture_output=True, text=True, cwd=WORKDIR, timeout=10)
        return (r.stdout + r.stderr) or "(no output)"


# ===== patch_file as Subflow (tool-as-chain) =====
# Three nodes: Read → Validate → Apply. Flow IS Node, so it wires like any tool.

class PatchRead(Node):
    def prep(self, shared):
        return shared["tool_call"]["args"]["path"]
    def exec(self, path):
        with open(_path(path)) as f: return f.read()
    def post(self, shared, prep_res, exec_res):
        shared["_patch_content"] = exec_res

class PatchValidate(Node):
    def prep(self, shared):
        args = shared["tool_call"]["args"]
        return shared["_patch_content"], args["old_str"], args["path"]
    def exec(self, inputs):
        content, old_str, path = inputs
        if old_str not in content:
            lines = content.split('\n')
            n = old_str.count('\n') + 1
            chunks = ['\n'.join(lines[i:i+n]) for i in range(len(lines))]
            best = difflib.get_close_matches(old_str, chunks, n=1, cutoff=0.4)
            if best: return f"ERROR: old_str not found in {path}. Did you mean:\n{best[0]}"
            return f"ERROR: old_str not found in {path}"
        if content.count(old_str) > 1:
            return f"ERROR: old_str appears {content.count(old_str)} times. Include more context."
        return "ok"
    def post(self, shared, prep_res, exec_res):
        if exec_res != "ok":
            shared["_patch_result"] = exec_res
            return "error"  # no successor for "error" → flow ends

class PatchApply(Node):
    def prep(self, shared):
        args = shared["tool_call"]["args"]
        return shared["_patch_content"], args["old_str"], args["new_str"], args["path"]
    def exec(self, inputs):
        content, old_str, new_str, path = inputs
        with open(_path(path), "w") as f: f.write(content.replace(old_str, new_str, 1))
        return f"Patched {path}"
    def post(self, shared, prep_res, exec_res):
        shared["_patch_result"] = exec_res

# Wire patch subflow: read → validate → apply
_pr, _pv, _pa = PatchRead(), PatchValidate(), PatchApply()
_pr >> _pv >> _pa

class PatchFile(Flow):
    """Flow IS Node. To the outer graph, this is just another tool node."""
    def __init__(self): super().__init__(start=_pr)
    def post(self, shared, prep_res, exec_res):
        result = shared.pop("_patch_result", "ERROR: validation failed")
        shared.setdefault("history", []).append({
            "tool": "patch_file",
            "args": shared["tool_call"].get("args", {}),
            "result": result,
        })
        print(f"  → {result[:200]}")


# ===== Wiring: one node per tool =====

compact = CompactHistory()
decide = Decide(max_retries=3)

decide - "retry" >> compact  # unknown tool → loop back

decide - "list_files"   >> ListFiles()   >> compact
decide - "grep_search"  >> GrepSearch()  >> compact
decide - "read_file"    >> ReadFile()    >> compact
decide - "patch_file"   >> PatchFile()   >> compact  # subflow wired as a node
decide - "run_command"  >> RunCommand()  >> compact

compact >> decide
flow = Flow(start=compact)


# ===== Run =====

if __name__ == "__main__":
    setup_test_project()
    shared = {
        "task": "Implement the skeleton functions to make all tests pass. "
                "Run: python -m pytest test_tokenizer.py test_parser.py test_executor.py test_sql.py -v",
    }
    flow.run(shared)
    print(f"\nResult: {shared.get('result', '')}")
