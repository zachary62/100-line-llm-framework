"""Section 3.2: Agent — the ReAct loop (reason, act, observe, repeat).
Listings 3.5-3.7 in chapter 3, assembled into one runnable file."""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from pocketflow import Node, Flow
from call_llm import call_llm
import yaml

class DecideNode(Node):
    def prep(self, shared):
        return {
            "question": shared["question"],
            "observations": shared.get("observations", "")
        }

    def exec(self, context):
        response = call_llm(f"""You are a research assistant.

You have one tool: search_web(query).

Output ONLY valid YAML:

If you need to search:
```yaml
action: search
query: <search query>
```

If you can answer:
```yaml
action: answer
content: <your answer>
```

Question: "{context['question']}"

Previous search results:
{context['observations']}""")
        yaml_str = response.split("```yaml")[1].split("```")[0].strip()
        return yaml.safe_load(yaml_str)

    def post(self, shared, prep_res, exec_res):
        shared["decision"] = exec_res
        return exec_res["action"]

def search_web(query):
    """Search DuckDuckGo — pip install ddgs"""
    from ddgs import DDGS
    results = DDGS().text(query, max_results=2)
    return "\n\n".join(
        f"Title: {r['title']}\nSnippet: {r['body']}" for r in results
    ) if results else "No results found."

class SearchNode(Node):
    def prep(self, shared):
        return shared["decision"]["query"]
    def exec(self, query):
        return search_web(query)
    def post(self, shared, prep_res, exec_res):
        shared["observations"] = exec_res

decide = DecideNode()
search = SearchNode()
decide - "search" >> search
search >> decide

shared = {"question": "Who is the CEO of the company that makes the iPhone?"}
Flow(start=decide).run(shared)
print(shared["decision"]["content"])
