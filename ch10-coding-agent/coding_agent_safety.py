"""Section 10.3: Safety Gate — graph enforces approval for dangerous tools"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from pocketflow import Node, Flow
from setup_test_project import setup_test_project, WORKDIR
from coding_agent import (
    CompactHistory, Decide,
    ListFiles, GrepSearch, ReadFile, RunCommand, PatchFile,
)

# ===== SafetyGate Node =====
# With one-node-per-tool, the graph itself decides which tools need approval.
# No SAFE_TOOLS set. No conditional checking. The wiring IS the policy.

class SafetyGate(Node):
    def prep(self, shared):
        return shared["tool_call"]
    def exec(self, tool_call):
        args_str = ", ".join(f"{k}={repr(v)}" for k, v in tool_call.get("args", {}).items())
        print(f"\n⚠ DANGEROUS: {tool_call['tool']}({args_str})")
        return "allow" if input("Allow? (y/n): ").strip().lower() == "y" else "block"
    def post(self, shared, prep_res, exec_res):
        if exec_res == "block":
            shared.setdefault("history", []).append({
                "tool": shared["tool_call"]["tool"],
                "args": shared["tool_call"].get("args", {}),
                "result": "BLOCKED by safety gate",
            })
            print("  → BLOCKED")
            return "blocked"
        return "allow"


# ===== Wiring: safe tools direct, dangerous tools through gate =====

compact = CompactHistory()
decide = Decide(max_retries=3)
decide - "retry" >> compact

# Safe tools — straight through
decide - "list_files"  >> ListFiles()  >> compact
decide - "grep_search" >> GrepSearch() >> compact
decide - "read_file"   >> ReadFile()   >> compact

# Dangerous tools — gate first
gate_patch = SafetyGate()
gate_cmd = SafetyGate()

decide - "patch_file" >> gate_patch
gate_patch - "allow"   >> PatchFile()   >> compact
gate_patch - "blocked" >> compact

decide - "run_command" >> gate_cmd
gate_cmd - "allow"   >> RunCommand() >> compact
gate_cmd - "blocked" >> compact

compact >> decide
flow = Flow(start=compact)


if __name__ == "__main__":
    setup_test_project()
    shared = {
        "task": "Implement the skeleton functions to make all tests pass. "
                "Run: python -m pytest test_tokenizer.py test_parser.py test_executor.py test_sql.py -v",
    }
    flow.run(shared)
    print(f"\nResult: {shared.get('result', '')}")
