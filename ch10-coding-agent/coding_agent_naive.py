"""Section 10.1: Naive Coding Agent — 3 tools, ~50 lines, breaks on real repos"""
import sys, os, subprocess, json
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from pocketflow import Node, Flow
from call_llm import call_llm
from setup_test_project import setup_test_project, WORKDIR

MAX_STEPS = 50

TOOL_DESC = """- read_file(path) — Read entire file
- write_file(path, content) — Write entire file (overwrites everything)
- run_command(cmd) — Run shell command
- done(result) — Task complete"""

VALID_TOOLS = {"read_file", "write_file", "run_command"}

def read_file(args):
    with open(os.path.join(WORKDIR, args["path"])) as f: return f.read()

def write_file(args):
    with open(os.path.join(WORKDIR, args["path"]), "w") as f: f.write(args["content"])
    return f"Wrote {args['path']}"

def run_command(args):
    r = subprocess.run(args["cmd"], shell=True, capture_output=True, text=True, cwd=WORKDIR, timeout=30)
    return (r.stdout + r.stderr) or "(no output)"

TOOLS = {"read_file": read_file, "write_file": write_file, "run_command": run_command}

class Decide(Node):
    def prep(self, shared):
        history = shared.get("history", [])
        history_text = ""
        for h in history:
            args_str = ", ".join(f"{k}={repr(v)}" for k, v in h.get("args", {}).items())
            history_text += f"\n[{h['tool']}({args_str})]\n{h['result']}\n"
        return f"""You are a coding agent. Fix failing tests.
Available tools:
{TOOL_DESC}

Task: {shared['task']}

History:{history_text or " (none yet)"}

Pick ONE tool. Output ONLY json:
```json
{{"tool": "tool_name", "args": {{"arg1": "value1"}}}}
```"""

    def exec(self, prompt):
        resp = call_llm(prompt)
        return json.loads(resp.split("```json")[1].split("```")[0].strip())

    def post(self, shared, prep_res, exec_res):
        tool = exec_res.get("tool", "done")
        step = shared.get("step", 0) + 1
        shared["step"] = step
        if tool == "done" or step >= MAX_STEPS:
            return "done"
        shared["tool_call"] = exec_res
        return "act"

class ExecuteTool(Node):
    def prep(self, shared):
        return shared["tool_call"]
    def exec(self, tool_call):
        tool, args = tool_call["tool"], tool_call.get("args", {})
        if tool not in TOOLS:
            return f"Unknown tool '{tool}'. Use: {', '.join(TOOLS)}"
        return TOOLS[tool](args)
    def post(self, shared, prep_res, exec_res):
        shared.setdefault("history", []).append({
            "tool": shared["tool_call"]["tool"],
            "args": shared["tool_call"].get("args", {}),
            "result": str(exec_res),
        })

# Wiring: decide → execute → decide (simple loop)
decide = Decide(max_retries=3)
execute = ExecuteTool()
decide - "act" >> execute >> decide

flow = Flow(start=decide)

if __name__ == "__main__":
    setup_test_project()
    shared = {
        "task": "Implement the skeleton functions to make all tests pass. "
                "Run: python -m pytest test_tokenizer.py test_parser.py test_executor.py test_sql.py -v",
    }
    flow.run(shared)
