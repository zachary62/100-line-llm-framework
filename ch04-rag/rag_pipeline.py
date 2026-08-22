"""Section 4.3: RAG with word overlap, no embeddings needed.

Listings 4.2 through 4.7 in chapter 4.
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import json
from pocketflow import Node, Flow
from call_llm import call_llm

def word_overlap(text_a, text_b):
    words_a = set(text_a.lower().split())
    words_b = set(text_b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)

class Chunk(Node):
    def prep(self, shared):
        return shared["docs"]
    def exec(self, docs):
        chunks = []
        for doc in docs:
            words = doc.split()
            for i in range(0, len(words), 200):
                chunks.append(" ".join(words[i:i+250]))
        return chunks
    def post(self, shared, prep_res, exec_res):
        shared["chunks"] = exec_res

class Store(Node):
    def prep(self, shared):
        return shared["chunks"], shared["index_file"]
    def exec(self, inputs):
        chunks, path = inputs
        with open(path, "w") as f:
            json.dump(chunks, f)
        return len(chunks)
    def post(self, shared, prep_res, exec_res):
        print(f"Indexed {exec_res} chunks")

chunk = Chunk()
store = Store()
chunk >> store
offline_flow = Flow(start=chunk)

class Retrieve(Node):
    def prep(self, shared):
        if "chunks" not in shared:
            with open(shared["index_file"]) as f:
                shared["chunks"] = json.load(f)
        return shared["question"], shared["chunks"]
    def exec(self, inputs):
        question, chunks = inputs
        return sorted(chunks, key=lambda c: word_overlap(question, c), reverse=True)[:3]
    def post(self, shared, prep_res, exec_res):
        shared["context"] = exec_res

class Generate(Node):
    def prep(self, shared):
        return shared["question"], shared["context"]
    def exec(self, inputs):
        question, context = inputs
        context_str = "\n---\n".join(context)
        return call_llm(
            f"Answer based ONLY on this context. If not found, say 'I don't know'.\n\n"
            f"Context:\n{context_str}\n\nQuestion: {question}"
        )
    def post(self, shared, prep_res, exec_res):
        shared["answer"] = exec_res

retrieve = Retrieve()
generate = Generate()
retrieve >> generate
online_flow = Flow(start=retrieve)

docs = [
    "PocketFlow is a 100-line minimalist LLM framework. It has zero dependencies "
    "and zero vendor lock-in. The core abstraction is a Graph with Nodes and Flows.",
    "Nodes have three steps: prep reads from shared store, exec does the work like "
    "calling an LLM, and post writes results back. Only exec is retried when a Node "
    "must handle a failure.",
    "A Flow connects nodes with chains, branches, and loops. The >> operator chains "
    "nodes. Action strings from post determine which branch to take.",
    "BatchNode processes multiple items. prep returns a list, exec handles one item, "
    "post gets all results. AsyncParallelBatchNode runs items concurrently.",
    "RAG stands for Retrieval Augmented Generation. It has two flows: offline indexing "
    "(chunk, embed, store) and online query (embed question, retrieve, generate).",
]

shared = {"docs": docs, "index_file": os.path.join(os.path.dirname(__file__), "index.json")}
offline_flow.run(shared)

shared["question"] = "How does a Node handle failures?"
online_flow.run(shared)
print(f"Q: {shared['question']}")
print(f"A: {shared['answer']}")
