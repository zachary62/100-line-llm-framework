"""Section 10.4: Two-Pass Editing — Plan (read-only) → Edit (write) → Verify"""
import sys, os, subprocess, json
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from pocketflow import Node, Flow
from call_llm import call_llm
from setup_test_project import setup_test_project, WORKDIR
from coding_agent import (
    load_memory, load_skills, save_memory,
    ListFiles, GrepSearch, ReadFile, RunCommand, PatchFile,
    MAX_STEPS,
)

# ===== PhaseDecide: Decide configurable per phase =====
# Uses instance attrs (not params) so they survive Flow's param propagation.

class PhaseDecide(Node):
    def __init__(self, phase, tool_desc, valid_tools, **kwargs):
        super().__init__(**kwargs)
        self.phase = phase
        self.tool_desc = tool_desc
        self.valid_tools = valid_tools

    def prep(self, shared):
        history = shared.get("history", [])
        skills = load_skills()
        memory = load_memory()

        history_text = ""
        for h in history:
            args_str = ", ".join(f"{k}={repr(v)}" for k, v in h.get("args", {}).items())
            history_text += f"\n[{h['tool']}({args_str})]\n{h['result']}\n"

        extra = ""
        if self.phase == "edit" and shared.get("plan"):
            extra = f"\n\nPlan to follow:\n{shared['plan']}\n"

        return f"""You are a coding agent in {self.phase.upper()} phase.
{f"Project rules:{chr(10)}{skills}" if skills else ""}
{f"Memory:{chr(10)}{memory}" if memory else ""}
Available tools:
{self.tool_desc}

Task: {shared['task']}{extra}

History:{history_text or " (none yet — start by exploring the codebase)"}

Pick ONE tool. Output ONLY json:
```json
{{"tool": "tool_name", "args": {{"arg1": "value1"}}, "reason": "why"}}
```"""

    def exec(self, prompt):
        resp = call_llm(prompt)
        json_str = resp.split("```json")[1].split("```")[0].strip()
        return json.loads(json_str)

    def post(self, shared, prep_res, exec_res):
        tool = exec_res.get("tool", "done")
        step = shared.get("step", 0) + 1
        shared["step"] = step

        if tool == f"{self.phase}_done" or step >= MAX_STEPS:
            if self.phase == "plan":
                shared["plan"] = exec_res.get("args", {}).get("plan", "")
                print(f"\nPLAN:\n{shared['plan']}")
            return "done"

        print(f"  [{self.phase}:{step}] {tool} — {exec_res.get('reason', '')}")
        shared["tool_call"] = exec_res

        if tool not in self.valid_tools:
            shared.setdefault("history", []).append({
                "tool": tool, "args": {}, "result": f"Unknown tool '{tool}'",
            })
            return "retry"
        return tool


# ===== Plan Phase (read-only) =====

PLAN_DESC = """- list_files(directory='.') — List all files
- grep_search(pattern, path='.') — Search for pattern
- read_file(path, start=1, end=None) — Read file
- run_command(cmd) — Run shell command
- plan_done(plan) — Finish planning. Pass your full plan as text."""

plan_decide = PhaseDecide("plan", PLAN_DESC,
    {"list_files", "grep_search", "read_file", "run_command"}, max_retries=3)

plan_decide - "list_files"  >> ListFiles()  >> plan_decide
plan_decide - "grep_search" >> GrepSearch() >> plan_decide
plan_decide - "read_file"   >> ReadFile()   >> plan_decide
plan_decide - "run_command" >> RunCommand() >> plan_decide
plan_decide - "retry" >> plan_decide

class PlanFlow(Flow):
    def post(self, shared, prep_res, exec_res):
        shared["history"] = []  # clear — plan text transfers, not exploration history
        shared["step"] = 0

plan_flow = PlanFlow(start=plan_decide)


# ===== Edit Phase (write tools + plan context) =====

EDIT_DESC = """- read_file(path, start=1, end=None) — Read file
- patch_file(path, old_str, new_str) — Replace old_str with new_str
- run_command(cmd) — Run shell command
- edit_done() — Finish editing"""

edit_decide = PhaseDecide("edit", EDIT_DESC,
    {"read_file", "patch_file", "run_command"}, max_retries=3)

edit_decide - "read_file"   >> ReadFile()   >> edit_decide
edit_decide - "patch_file"  >> PatchFile()  >> edit_decide
edit_decide - "run_command" >> RunCommand() >> edit_decide
edit_decide - "retry" >> edit_decide

class EditFlow(Flow):
    def post(self, shared, prep_res, exec_res):
        shared["step"] = 0  # reset for potential retry

edit_flow = EditFlow(start=edit_decide)


# ===== Verify Phase =====

MAX_VERIFY_ROUNDS = 3

class VerifyNode(Node):
    def exec(self, prep_res):
        r = subprocess.run(
            "python -m pytest test_tokenizer.py test_parser.py test_executor.py test_sql.py -v",
            shell=True, capture_output=True, text=True, cwd=WORKDIR, timeout=30,
        )
        output = r.stdout + r.stderr
        print(f"\nVERIFY:\n{output[-500:]}")
        return "pass" if r.returncode == 0 else "fail"

    def post(self, shared, prep_res, exec_res):
        if exec_res == "pass":
            print("\nAll tests pass!")
            if shared.get("history"): save_memory(shared["history"])
            return "done"
        rounds = shared.get("verify_rounds", 0) + 1
        shared["verify_rounds"] = rounds
        if rounds >= MAX_VERIFY_ROUNDS:
            print(f"\nStill failing after {rounds} rounds — stopping instead of looping forever")
            return "done"
        print("\nTests failed — looping back to edit")
        shared.setdefault("history", []).append({
            "tool": "pytest", "args": {}, "result": "Tests failed — fix remaining issues",
        })
        shared["step"] = 0
        return "fail"


# ===== Outer wiring: plan → edit → verify (fail loops to edit) =====

verify = VerifyNode()
plan_flow >> edit_flow >> verify
verify - "fail" >> edit_flow

outer_flow = Flow(start=plan_flow)


if __name__ == "__main__":
    setup_test_project()
    shared = {
        "task": "Implement the skeleton functions to make all tests pass. "
                "Run: python -m pytest test_tokenizer.py test_parser.py test_executor.py test_sql.py -v",
    }
    outer_flow.run(shared)
    print(f"\nResult: {shared.get('plan', '')[:200]}")
