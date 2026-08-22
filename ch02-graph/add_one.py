from pocketflow import Node

class AddOne(Node):
    def prep(self, shared):
        return shared["number"]

    def exec(self, prep_res):
        return prep_res + 1

    def post(self, shared, prep_res, exec_res):
        shared["number"] = exec_res

shared = {"number": 5}
AddOne().run(shared)
print(shared["number"])  # 6
