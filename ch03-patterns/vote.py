"""Section 3.4: Majority Vote — run 5 times, pick consensus"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from pocketflow import BatchNode, Node, Flow
from call_llm import call_llm
from collections import Counter
import yaml

class ClassifyMultiple(BatchNode):
    def prep(self, shared):
        return [shared["review"]] * 5

    def exec(self, review):
        response = call_llm(
            f"Is this restaurant review positive or negative?\n\n{review}\n\n"
            f"```yaml\nsentiment: positive or negative\nreason: one sentence why\n```",
            temperature=1.5
        )
        yaml_str = response.split("```yaml")[1].split("```")[0].strip()
        return yaml.safe_load(yaml_str)

    def post(self, shared, prep_res, exec_res):
        shared["votes"] = exec_res

class PickConsensus(Node):
    def prep(self, shared):
        return shared["votes"]
    def exec(self, votes):
        counts = Counter(v["sentiment"] for v in votes)
        return counts.most_common(1)[0][0]
    def post(self, shared, prep_res, exec_res):
        shared["result"] = exec_res

classify = ClassifyMultiple(max_retries=3)
pick = PickConsensus()
classify >> pick

shared = {"review": "The sushi here is the real deal — fresh fish, skilled chef, beautiful presentation. But we waited 20 min for water, they forgot our appetizer, and the bill was wrong. Hard to say how I feel about this place."}
Flow(start=classify).run(shared)
for i, v in enumerate(shared["votes"]):
    print(f"  Vote {i+1}: {v['sentiment']} — {v['reason']}")
print(f"Consensus: {shared['result']}")
