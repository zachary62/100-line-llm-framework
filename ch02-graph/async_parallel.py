"""Section 2.8: Async and Parallel — From 100 Seconds to 10"""
from pocketflow import AsyncParallelBatchNode, AsyncFlow
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from call_llm import client, FAST_MODEL
import asyncio, time

class ParallelSummarize(AsyncParallelBatchNode):
    async def prep_async(self, shared):
        return shared["reviews"]

    async def exec_async(self, review):
        r = await asyncio.to_thread(
            client.models.generate_content,
            model=FAST_MODEL,
            contents=f"Summarize in one sentence: {review}"
        )
        return r.text

    async def post_async(self, shared, prep_res, exec_res):
        shared["summaries"] = exec_res

reviews = [
    "The food was amazing but the service was slow. We waited 30 minutes for our appetizers.",
    "Best pizza in town! Crispy crust, fresh ingredients. Will definitely come back.",
    "Overpriced for what you get. The pasta was bland and the portions were tiny.",
]

shared = {"reviews": reviews}
start = time.time()
asyncio.run(AsyncFlow(start=ParallelSummarize(max_retries=3)).run_async(shared))
print(f"Parallel took {time.time() - start:.1f}s")
for i, s in enumerate(shared["summaries"]):
    print(f"Review {i+1}: {s}")
