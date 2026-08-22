"""Section 3.5: Self-Healing — run code, get error, fix, retry"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from pocketflow import Node, Flow
from call_llm import call_llm

class WriteCode(Node):
    def prep(self, shared):
        return {"task": shared["task"], "error": shared.get("error", "")}
    def exec(self, inputs):
        prompt = f"Write a Python function to: {inputs['task']}\nOutput ONLY the code in ```python``` block."
        if inputs["error"]:
            prompt += f"\n\nPrevious code failed with:\n{inputs['error']}\nFix the bug."
        response = call_llm(prompt)
        return response.split("```python")[1].split("```")[0].strip()
    def post(self, shared, prep_res, exec_res):
        shared["code"] = exec_res
        print(f"\n--- Code ---\n{exec_res}\n")

class RunCode(Node):
    def prep(self, shared):
        return shared["code"]
    def exec(self, code):
        try:
            exec_globals = {}
            exec(code, exec_globals)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    def post(self, shared, prep_res, exec_res):
        if exec_res["success"]:
            print("Success!")
            return "done"
        print(f"Error: {exec_res['error']}")
        shared["error"] = exec_res["error"]
        shared["attempts"] = shared.get("attempts", 0) + 1
        if shared["attempts"] >= 3:
            print("Max retries reached.")
            return "done"
        return "fix"

write = WriteCode()
run = RunCode()
write >> run
run - "fix" >> write

shared = {"task": "print the first 10 fibonacci numbers"}
Flow(start=write).run(shared)
