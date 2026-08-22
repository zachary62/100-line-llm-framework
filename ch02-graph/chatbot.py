"""Section 2.4: A Chatbot in 30 Lines"""
from pocketflow import Node, Flow
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from call_llm import call_llm

class ChatNode(Node):
    def prep(self, shared):
        user_input = input("You: ")
        if user_input.lower() == "exit":
            return None
        shared.setdefault("messages", [])
        shared["messages"].append({"role": "user", "content": user_input})
        return shared["messages"]

    def exec(self, messages):
        if messages is None:
            return None
        prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
        return call_llm(prompt)

    def post(self, shared, prep_res, exec_res):
        if prep_res is None:
            return "exit"
        print(f"Bot: {exec_res}")
        shared["messages"].append({"role": "assistant", "content": exec_res})
        return "continue"

chat = ChatNode()
chat - "continue" >> chat
Flow(start=chat).run({})
