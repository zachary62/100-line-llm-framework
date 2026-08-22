"""Section 3.6: Heartbeat — wait node loops with nested email flow"""
import sys, os, time, warnings
warnings.filterwarnings("ignore")
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from pocketflow import Node, Flow
from call_llm import call_llm

# Simulated inbox — some cycles have mail, some don't
INBOX = [
    [],
    [{"from": "boss@work.com", "subject": "Q3 report", "body": "Need the Q3 numbers by Friday. Please confirm."}],
    [],
    [{"from": "client@acme.com", "subject": "Invoice #1042", "body": "Invoice #1042 seems wrong. Amount should be $4,500 not $5,400."}],
]
check_count = 0

def check_email():
    global check_count
    emails = INBOX[check_count % len(INBOX)]
    check_count += 1
    return emails

class WaitNode(Node):
    def prep(self, shared):
        shared["cycle"] = shared.get("cycle", 0) + 1
        print(f"\n--- Heartbeat {shared['cycle']} ---")
    def exec(self, _):
        print("Sleeping 2s...")
        time.sleep(2)
    def post(self, shared, prep_res, exec_res):
        if shared["cycle"] > 4:
            return "done"

class CheckEmail(Node):
    def exec(self, _):
        return check_email()
    def post(self, shared, prep_res, exec_res):
        if not exec_res:
            print("No new emails.")
            return None
        shared["emails"] = exec_res
        print(f"{len(exec_res)} new email(s)!")
        return "new_email"

class ProcessEmail(Node):
    def prep(self, shared):
        return shared["emails"]
    def exec(self, emails):
        summaries = []
        for e in emails:
            summary = call_llm(
                f"Summarize this email in one sentence and suggest a one-line reply action.\n"
                f"From: {e['from']}\nSubject: {e['subject']}\nBody: {e['body']}")
            summaries.append(summary)
        return summaries
    def post(self, shared, prep_res, exec_res):
        for s in exec_res:
            print(f"-> {s}")
        shared.setdefault("processed", []).extend(exec_res)

# Inner flow: check → process
check = CheckEmail()
process = ProcessEmail()
check - "new_email" >> process
email_flow = Flow(start=check)

# Outer flow: wait → email_flow → wait (loop)
wait = WaitNode()
wait >> email_flow
email_flow >> wait

Flow(start=wait).run({})
