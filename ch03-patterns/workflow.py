"""Section 3.1: Workflow — Task Decomposition (chain beats mega-prompt)"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from pocketflow import Node, Flow
from call_llm import call_llm

class ExtractFacts(Node):
    def prep(self, shared):
        return shared["article"]
    def exec(self, article):
        return call_llm(f"Extract the 3 most interesting facts from this article:\n{article}")
    def post(self, shared, prep_res, exec_res):
        shared["facts"] = exec_res

class FindHook(Node):
    def prep(self, shared):
        return shared["facts"]
    def exec(self, facts):
        return call_llm(f"Pick the most surprising fact and turn it into a hook:\n{facts}")
    def post(self, shared, prep_res, exec_res):
        shared["hook"] = exec_res

class WriteTweet(Node):
    def prep(self, shared):
        return shared["hook"]
    def exec(self, hook):
        return call_llm(f"Write a viral tweet (under 280 chars) using this hook:\n{hook}")
    def post(self, shared, prep_res, exec_res):
        shared["tweet"] = exec_res

extract = ExtractFacts()
hook = FindHook()
tweet = WriteTweet()
extract >> hook >> tweet

shared = {"article": """
A new study found that octopuses can solve puzzles faster than most primates.
Researchers at MIT tested 12 species and found octopuses completed mazes in
under 30 seconds, while chimpanzees averaged 2 minutes. The study suggests
that distributed neural networks (octopuses have neurons in their arms) may
be more efficient for certain spatial tasks.
"""}

Flow(start=extract).run(shared)
print("Facts:", shared["facts"])
print("\nHook:", shared["hook"])
print("\nTweet:", shared["tweet"])
