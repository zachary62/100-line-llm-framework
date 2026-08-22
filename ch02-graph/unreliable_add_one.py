from pocketflow import Node
import random

class UnreliableAddOne(Node):
    def prep(self, shared):
        return shared["number"]

    def exec(self, prep_res):
        if random.random() < 0.5:
            print("  Failed! Retrying...")
            raise Exception("Random failure!")
        print("  Success!")
        return prep_res + 1

    def exec_fallback(self, prep_res, exc):
        print("  All retries failed, using fallback")
        return prep_res

    def post(self, shared, prep_res, exec_res):
        shared["number"] = exec_res

node = UnreliableAddOne(max_retries=3, wait=1)
shared = {"number": 5}
node.run(shared)
print(f"Result: {shared['number']}")
