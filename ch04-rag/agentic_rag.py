"""Section 4.5: Agentic RAG — agent reads summaries, decides what to dive into"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import yaml
from pocketflow import Node, Flow
from call_llm import call_llm

DOCS = {
    "overview": "PocketFlow is a 100-line LLM framework. Core abstraction: Graph with Nodes and Flows. Zero dependencies.",
    "nodes": "Nodes have prep/exec/post. prep reads shared store, exec does work (LLM calls), post writes back. Only exec retries on failure. BatchNode handles lists.",
    "flows": "Flows connect nodes: >> chains, action strings branch, self-loops loop. Flow is also a Node, so flows nest inside flows.",
    "rag": "RAG = Retrieval Augmented Generation. Offline: chunk, embed, store. Online: embed query, retrieve top-K, generate answer with context.",
    "agents": "An agent is an LLM + tools + loop. DecideNode picks an action, tool nodes execute, loop back. ReAct pattern: Reason, Act, Observe, Repeat.",
}

def read_doc(name):
    return DOCS.get(name, "Document not found.")

def list_docs():
    return list(DOCS.keys())

class DecideAction(Node):
    def prep(self, shared):
        return shared["question"], shared.get("context", ""), list_docs()

    def exec(self, inputs):
        question, context, available = inputs
        prompt = f"""Question: {question}
Available docs: {available}
Already read: {context if context else 'nothing yet'}

If you have enough info to answer, set action to 'answer'.
Otherwise pick a doc to read. Output ONLY yaml:
```yaml
action: read/answer
doc: document name if reading
```"""
        resp = call_llm(prompt)
        yaml_str = resp.split("```yaml")[1].split("```")[0].strip()
        return yaml.safe_load(yaml_str)

    def post(self, shared, prep_res, exec_res):
        if exec_res["action"] == "read":
            shared["doc_to_read"] = exec_res.get("doc", "")
            print(f"  Agent: reading '{shared['doc_to_read']}'")
        return exec_res["action"]

class ReadDoc(Node):
    def prep(self, shared):
        return shared["doc_to_read"]
    def exec(self, doc_name):
        return read_doc(doc_name)
    def post(self, shared, prep_res, exec_res):
        shared["context"] = shared.get("context", "") + f"\n[{prep_res}]: {exec_res}"
        return "decide"

class Answer(Node):
    def prep(self, shared):
        return shared["question"], shared.get("context", "")
    def exec(self, inputs):
        question, context = inputs
        return call_llm(f"Based on this context:\n{context}\n\nAnswer: {question}")
    def post(self, shared, prep_res, exec_res):
        shared["answer"] = exec_res

decide = DecideAction()
read = ReadDoc()
answer = Answer()

decide - "read" >> read
decide - "answer" >> answer
read - "decide" >> decide

shared = {"question": "How does PocketFlow handle retries in nodes?"}
Flow(start=decide).run(shared)
print(f"\nQ: {shared['question']}")
print(f"A: {shared['answer']}")
