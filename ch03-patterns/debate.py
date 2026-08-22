"""Section 3.5: Debate — two advocates argue three rounds, a third model judges.
Listings 3.21 and 3.22 in chapter 3, assembled into one runnable file."""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from pocketflow import Node, Flow
from call_llm import call_llm

class AdvocateFor(Node):
    def prep(self, shared):
        shared.setdefault("history", [])
        return {"claim": shared["claim"], "history": shared["history"]}
    def exec(self, inputs):
        history = "\n\n".join(f"[{h['side']}]: {h['argument']}" for h in inputs["history"])
        return call_llm(f"""Argue FOR this claim. Be specific, use evidence:
"{inputs['claim']}"

Debate so far:
{history or '(opening round)'}

Present your next argument. Rebut any opposing points.""")
    def post(self, shared, prep_res, exec_res):
        shared["history"].append({"side": "FOR", "argument": exec_res})

class AdvocateAgainst(Node):
    def prep(self, shared):
        return {"claim": shared["claim"], "history": shared["history"]}
    def exec(self, inputs):
        history = "\n\n".join(f"[{h['side']}]: {h['argument']}" for h in inputs["history"])
        return call_llm(f"""Argue AGAINST this claim:
"{inputs['claim']}"

Debate so far:
{history}

Present your next argument. Rebut any opposing points.""")
    def post(self, shared, prep_res, exec_res):
        shared["history"].append({"side": "AGAINST", "argument": exec_res})
        shared["round"] = shared.get("round", 0) + 1
        return "done" if shared["round"] >= 3 else "continue"

class JudgeDebate(Node):
    def prep(self, shared):
        return shared
    def exec(self, s):
        history = "\n\n".join(f"[{h['side']}]: {h['argument']}" for h in s["history"])
        return call_llm(f"""Two experts debated: "{s['claim']}"

Full debate:
{history}

Which argument is stronger? Give your verdict and explain why.""")
    def post(self, shared, prep_res, exec_res):
        shared["verdict"] = exec_res

advocate_for = AdvocateFor()
advocate_against = AdvocateAgainst()
judge = JudgeDebate()

advocate_for >> advocate_against
advocate_against - "continue" >> advocate_for
advocate_against - "done" >> judge

if __name__ == "__main__":
    shared = {"claim": "We should rewrite our Python backend in Rust"}
    Flow(start=advocate_for).run(shared)
    for h in shared["history"]:
        print(f"[{h['side']}]\n{h['argument'][:300]}\n")
    print(f"VERDICT:\n{shared['verdict']}")
