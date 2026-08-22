"""Section 2.7: Batch — Same Node, 1000 Inputs"""
from pocketflow import BatchNode, Flow
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from call_llm import call_llm

class SummarizeReviews(BatchNode):
    def prep(self, shared):
        return shared["reviews"]

    def exec(self, review):
        return call_llm(f"Summarize this review in one sentence: {review}")

    def post(self, shared, prep_res, exec_res):
        shared["summaries"] = exec_res

reviews = [
    "The food was amazing but the service was slow. We waited 30 minutes for our appetizers.",
    "Best pizza in town! Crispy crust, fresh ingredients. Will definitely come back.",
    "Overpriced for what you get. The pasta was bland and the portions were tiny.",
]

shared = {"reviews": reviews}
SummarizeReviews(max_retries=3).run(shared)
for i, s in enumerate(shared["summaries"]):
    print(f"Review {i+1}: {s}")
