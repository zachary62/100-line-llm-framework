"""Section 3.3: Guardrail — a gate node between the worker and the action.
Listings 3.8 through 3.11 in chapter 3, assembled into one runnable file."""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from pocketflow import Node, Flow
from call_llm import call_llm

class DraftEmail(Node):
    def prep(self, shared):
        return {
            "topic": shared["topic"],
            "feedback": shared.get("feedback", ""),
        }
    def exec(self, inputs):
        topic, feedback = inputs["topic"], inputs["feedback"]
        prompt = f"Draft a professional email about: {topic}."
        if feedback:
            prompt += f"\n\nPrevious draft rejected: {feedback}"
        return call_llm(prompt)
    def post(self, shared, prep_res, exec_res):
        shared["draft"] = exec_res

class Supervisor(Node):
    def prep(self, shared):
        return shared["draft"]
    def exec(self, draft):
        return call_llm(f"""Review this email draft:
"{draft}"

Is it polite and professional?
Output ONLY "APPROVE" or "REJECT: <reason>".""")
    def post(self, shared, prep_res, exec_res):
        shared["rounds"] = shared.get("rounds", 0) + 1
        if exec_res.strip().upper().startswith("APPROVE") or shared["rounds"] >= 3:
            return "approve"
        shared["feedback"] = exec_res
        return "reject"

class SendEmail(Node):
    def exec(self, prep_res):
        print("Email sent!")

drafter = DraftEmail()
supervisor = Supervisor()
sender = SendEmail()

drafter >> supervisor
supervisor - "reject" >> drafter
supervisor - "approve" >> sender

Flow(start=drafter).run({"topic": "Demanding a refund immediately"})


# Human in the loop: same graph, one node swapped.
class HumanSupervisor(Node):
    def prep(self, shared):
        return shared["draft"]
    def exec(self, draft):
        print(f"\n--- REVIEW ---\n{draft}\n--------------")
        if input("Approve? (y/n): ").lower() == "y":
            return "APPROVE"
        return f"REJECT: {input('What needs fixing? ')}"
    def post(self, shared, prep_res, exec_res):
        if exec_res.strip().upper().startswith("APPROVE"):
            return "approve"
        shared["feedback"] = exec_res
        return "reject"

if __name__ == "__main__" and os.getenv("HUMAN_REVIEW"):
    drafter, supervisor, sender = DraftEmail(), HumanSupervisor(), SendEmail()
    drafter >> supervisor
    supervisor - "reject" >> drafter
    supervisor - "approve" >> sender
    Flow(start=drafter).run({"topic": "Demanding a refund immediately"})
