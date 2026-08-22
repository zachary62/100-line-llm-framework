"""Section 3.4: Debate — adversarial reasoning with two advocates and a judge"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from pocketflow import Node, Flow
from call_llm import call_llm

class AdvocateFor(Node):
    def prep(self, shared):
        return shared["claim"]
    def exec(self, claim):
        return call_llm(
            f'Argue FOR this claim. Be specific, use evidence:\n'
            f'"{claim}"\n'
            f'Present your strongest case in 3-4 sentences.'
        )
    def post(self, shared, prep_res, exec_res):
        shared["case_for"] = exec_res
        print(f"\n--- FOR ---\n{exec_res}\n")

class AdvocateAgainst(Node):
    def prep(self, shared):
        return {"claim": shared["claim"], "opposing": shared["case_for"]}
    def exec(self, inputs):
        return call_llm(
            f'Argue AGAINST this claim:\n'
            f'"{inputs["claim"]}"\n\n'
            f'Your opponent argued: {inputs["opposing"]}\n\n'
            f'Rebut their points and present your strongest counterarguments in 3-4 sentences.'
        )
    def post(self, shared, prep_res, exec_res):
        shared["case_against"] = exec_res
        print(f"--- AGAINST ---\n{exec_res}\n")

class JudgeDebate(Node):
    def prep(self, shared):
        return shared
    def exec(self, s):
        return call_llm(
            f'Two experts debated: "{s["claim"]}"\n\n'
            f'FOR:\n{s["case_for"]}\n\n'
            f'AGAINST:\n{s["case_against"]}\n\n'
            f'Which argument is stronger? Give your verdict and one-sentence explanation.'
        )
    def post(self, shared, prep_res, exec_res):
        shared["verdict"] = exec_res
        print(f"--- VERDICT ---\n{exec_res}")

advocate_for = AdvocateFor()
advocate_against = AdvocateAgainst()
judge = JudgeDebate()
advocate_for >> advocate_against >> judge

shared = {"claim": "We should rewrite our Python backend in Rust"}
Flow(start=advocate_for).run(shared)
