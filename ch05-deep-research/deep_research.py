"""Section 5.1-5.4: Deep Research — recursive map-reduce with search API"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from pocketflow import Node, BatchNode, Flow
from call_llm import call_llm
from search_web import search_web
import yaml

class PlannerNode(Node):
    def prep(self, shared):
        return shared["topic"], shared.get("feedback", "")

    def exec(self, inputs):
        topic, feedback = inputs
        if not feedback:
            instruction = f"Generate 3 diverse search queries to research: '{topic}'."
        else:
            instruction = (
                f"We are researching '{topic}'.\n"
                f"Gaps to fill: {feedback}\n\n"
                f"Generate 3 search queries to fill these gaps."
            )
        prompt = f"""{instruction}

Output ONLY yaml:
```yaml
queries:
  - "query 1"
  - "query 2"
  - "query 3"
```"""
        resp = call_llm(prompt)
        yaml_str = resp.split("```yaml")[1].split("```")[0].strip()
        return yaml.safe_load(yaml_str)["queries"]

    def post(self, shared, prep_res, exec_res):
        shared["current_queries"] = exec_res
        print(f"  Planner: {exec_res}")

class ResearcherNode(BatchNode):
    def prep(self, shared):
        return shared["current_queries"]

    def exec(self, query):
        raw = search_web(query)
        extracted = call_llm(
            f"Extract key facts relevant to this query. Be brief.\n\n"
            f"Query: {query}\nSearch result:\n{raw}"
        )
        return f"Q: {query}\nFacts: {extracted}"

    def post(self, shared, prep_res, exec_res):
        if "notes" not in shared:
            shared["notes"] = []
        shared["notes"].extend(exec_res)

class SynthesizerNode(Node):
    def prep(self, shared):
        return shared["topic"], shared.get("notes", []), shared.get("loop_count", 0)

    def exec(self, inputs):
        topic, notes, loops = inputs
        if loops >= 2:
            notes_text = "\n---\n".join(notes)
            report = call_llm(
                f"Write a concise research report on '{topic}' "
                f"using these notes:\n{notes_text}"
            )
            return {"action": "finalize", "content": report}

        notes_text = "\n---\n".join(notes)
        prompt = f"""We are researching: "{topic}"

Notes collected:
{notes_text}

Is the information sufficient for a comprehensive report?
Output ONLY yaml:
```yaml
action: research
feedback: "what's missing"
```
OR
```yaml
action: finalize
content: "the final report in markdown"
```"""
        resp = call_llm(prompt)
        yaml_str = resp.split("```yaml")[1].split("```")[0].strip()
        return yaml.safe_load(yaml_str)

    def post(self, shared, prep_res, exec_res):
        if exec_res["action"] == "research":
            shared["loop_count"] = shared.get("loop_count", 0) + 1
            shared["feedback"] = exec_res.get("feedback", "")
            print(f"  Synthesizer: gaps found — {shared['feedback']}")
            return "research"
        shared["report"] = exec_res["content"]
        print("  Synthesizer: done")
        return "finalize"

planner = PlannerNode()
researcher = ResearcherNode()
synthesizer = SynthesizerNode()

planner >> researcher >> synthesizer
synthesizer - "research" >> planner

shared = {"topic": "PocketFlow, the 100-line minimalist LLM framework"}
print(f"Researching: {shared['topic']}\n")
Flow(start=planner).run(shared)
print(f"\n--- Report ---\n{shared['report']}")
