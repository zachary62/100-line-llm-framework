"""Section 2.2: Flow — Chain, Branch, Loop, Nest"""
from pocketflow import Node, Flow

# --- Chain ---
class AddOne(Node):
    def prep(self, shared):
        return shared["number"]
    def exec(self, prep_res):
        return prep_res + 1
    def post(self, shared, prep_res, exec_res):
        shared["number"] = exec_res

class MultiplyByTwo(Node):
    def prep(self, shared):
        return shared["number"]
    def exec(self, prep_res):
        return prep_res * 2
    def post(self, shared, prep_res, exec_res):
        shared["number"] = exec_res

add = AddOne()
multiply = MultiplyByTwo()
add >> multiply

shared = {"number": 5}
Flow(start=add).run(shared)
print(f"Chain: 5 -> +1 -> *2 = {shared['number']}")  # 12

# --- Branch ---
class CheckSign(Node):
    def prep(self, shared):
        return shared["number"]
    def exec(self, prep_res):
        return "positive" if prep_res >= 0 else "negative"
    def post(self, shared, prep_res, exec_res):
        return exec_res

class DoubleIt(Node):
    def prep(self, shared):
        return shared["number"]
    def exec(self, prep_res):
        return prep_res * 2
    def post(self, shared, prep_res, exec_res):
        shared["number"] = exec_res

class NegateIt(Node):
    def prep(self, shared):
        return shared["number"]
    def exec(self, prep_res):
        return -prep_res
    def post(self, shared, prep_res, exec_res):
        shared["number"] = exec_res

check = CheckSign()
check - "positive" >> DoubleIt()
check - "negative" >> NegateIt()

shared = {"number": 3}
Flow(start=check).run(shared)
print(f"Branch (positive): 3 -> {shared['number']}")  # 6

shared = {"number": -3}
Flow(start=check).run(shared)
print(f"Branch (negative): -3 -> {shared['number']}")  # 3

# --- Loop ---
class DoubleUntilBig(Node):
    def prep(self, shared):
        return shared["number"]
    def exec(self, prep_res):
        return prep_res * 2
    def post(self, shared, prep_res, exec_res):
        shared["number"] = exec_res
        if exec_res <= 10:
            return "continue"

loop_node = DoubleUntilBig()
loop_node - "continue" >> loop_node

shared = {"number": 1}
Flow(start=loop_node).run(shared)
print(f"Loop: 1 -> double until >10 = {shared['number']}")  # 16

# --- Nest ---
add1 = AddOne()
add2 = AddOne()
add1 >> add2
inner_flow = Flow(start=add1)

multiply2 = MultiplyByTwo()
inner_flow >> multiply2
outer_flow = Flow(start=inner_flow)

shared = {"number": 5}
outer_flow.run(shared)
print(f"Nest: 5 -> (+1 -> +1) -> *2 = {shared['number']}")  # 14
