"""Section 3.4: LLM as Judge — evaluator-optimizer loop"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from pocketflow import Node, Flow
from call_llm import call_llm, FAST_MODEL, SMART_MODEL

class Generator(Node):
    def prep(self, shared):
        return {"task": shared["task"], "feedback": shared.get("feedback", "")}
    def exec(self, inputs):
        prompt = f"Write a product description for: {inputs['task']}"
        if inputs["feedback"]:
            prompt += f"\n\nPrevious attempt was rejected: {inputs['feedback']}"
        return call_llm(prompt, model=FAST_MODEL)
    def post(self, shared, prep_res, exec_res):
        shared["draft"] = exec_res
        print(f"\n--- Draft ---\n{exec_res}\n")

class Judge(Node):
    def prep(self, shared):
        return shared["draft"]
    def exec(self, draft):
        return call_llm(
            f'Rate this product description 1-10 for clarity and persuasiveness.\n'
            f'If score >= 7, output "PASS". Otherwise output "FAIL: <specific feedback>".\n\n'
            f'Description: {draft}',
            model=SMART_MODEL,
        )
    def post(self, shared, prep_res, exec_res):
        print(f"Judge: {exec_res}\n")
        if "PASS" in exec_res.upper():
            return "pass"
        shared["feedback"] = exec_res
        shared["attempts"] = shared.get("attempts", 0) + 1
        if shared["attempts"] >= 3:
            return "pass"
        return "fail"

generator = Generator()
judge = Judge()
generator >> judge
judge - "fail" >> generator

shared = {"task": "noise-canceling headphones"}
Flow(start=generator).run(shared)
print(f"Final:\n{shared['draft']}")
