"""Section 3.5: Chain of Thought — step-by-step reasoning loop"""
import sys, os, re
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from pocketflow import Node, Flow
from call_llm import call_llm

MAX_STEPS = 8

class Thinker(Node):
    def prep(self, shared):
        shared.setdefault("thoughts", [])
        return {
            "question": shared["question"],
            "thoughts": "\n".join(f"Step {i+1}: {t}" for i, t in enumerate(shared["thoughts"]))
        }

    def exec(self, ctx):
        resp = call_llm(f"""Solve this step by step. Do ONE calculation per step.

If you need to think more, output:
ACTION: think
THOUGHT: <one sentence with actual numbers and calculation>

If you have the final answer, output:
ACTION: answer
RESULT: <number>

Do NOT repeat previous steps. Do NOT describe what you will do — actually do the math.

Problem: "{ctx['question']}"

{ctx['thoughts']}""")
        action_m = re.search(r"ACTION:\s*(think|answer)", resp, re.IGNORECASE)
        action = action_m.group(1).lower() if action_m else "think"
        if action == "answer":
            result_m = re.search(r"RESULT:\s*(.+)", resp)
            return {"action": "answer", "result": result_m.group(1).strip() if result_m else resp.strip()}
        thought_m = re.search(r"THOUGHT:\s*(.+)", resp)
        return {"action": "think", "thought": thought_m.group(1).strip() if thought_m else resp.split("\n")[0].strip()}

    def post(self, shared, prep_res, exec_res):
        if exec_res["action"] == "think":
            shared["thoughts"].append(exec_res["thought"])
            print(f"  Step {len(shared['thoughts'])}: {exec_res['thought']}")
            if len(shared["thoughts"]) >= MAX_STEPS:
                print("  (max steps reached, forcing answer)")
                return "answer"
            return "think"
        shared["result"] = exec_res["result"]
        print(f"  Answer: {exec_res['result']}")
        return "answer"

thinker = Thinker(max_retries=3)
thinker - "think" >> thinker

shared = {
    "question": "Your app has 2,000 users. Analytics shows: 1,200 use mobile, "
                "800 use web, 500 use API. 400 use both mobile and web, "
                "200 use both mobile and API, 150 use both web and API. "
                "100 use all three. How many users never engaged?"
}
Flow(start=thinker).run(shared)
print(f"\nFinal answer: {shared.get('result', 'unknown')}")
