"""Section 4.4: the same RAG pipeline with real embeddings.

Listings 4.8 and 4.9 in chapter 4: one new node, one changed line.
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from pocketflow import Node, Flow
from call_llm import call_llm, client, EMBED_MODEL
import json
import numpy as np


def get_embedding(text):
    r = client.models.embed_content(model=EMBED_MODEL, contents=text)
    return r.embeddings[0].values

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

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

class Embed(Node):
    def prep(self, shared):
        return shared["chunks"]
    def exec(self, chunks):
        return [{"chunk": c, "embedding": get_embedding(c)} for c in chunks]
    def post(self, shared, prep_res, exec_res):
        shared["embedded_chunks"] = exec_res

class Store(Node):
    def prep(self, shared):
        return shared["embedded_chunks"], shared["index_file"]
    def exec(self, inputs):
        index, path = inputs
        with open(path, "w") as f:
            json.dump(index, f)
        return len(index)
    def post(self, shared, prep_res, exec_res):
        print(f"Indexed {exec_res} chunks")

class Retrieve(Node):
    def prep(self, shared):
        if "index" not in shared:
            with open(shared["index_file"]) as f:
                shared["index"] = json.load(f)
        return shared["question"], shared["index"]
    def exec(self, inputs):
        question, index = inputs
        query_emb = get_embedding(question)
        top = sorted(index, key=lambda item: cosine_similarity(query_emb, item["embedding"]), reverse=True)[:3]
        return [item["chunk"] for item in top]
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

chunk = Chunk()
embed = Embed()
store = Store()
chunk >> embed >> store
offline_flow = Flow(start=chunk)

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
