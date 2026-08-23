"""Section 6.3: Codebase knowledge — a loop that carries context forward.

Listings 6.10 through 6.13 in chapter 6, assembled into one runnable file.
Points at this repo's own pocketflow/ package by default, so it has something
real to read without any setup.
"""
import sys, os, yaml
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from pocketflow import Node, Flow
from call_llm import call_llm

class FetchFiles(Node):
    def prep(self, shared):
        return shared["repo_path"]

    def exec(self, repo_path):
        files = []
        for root, dirs, filenames in os.walk(repo_path):
            for f in filenames:
                if f.endswith((".py", ".js", ".ts")):
                    path = os.path.join(root, f)
                    with open(path) as fh:
                        files.append(f"--- {path} ---\n{fh.read()}")
        return "\n\n".join(files)

    def post(self, shared, prep_res, exec_res):
        shared["files_text"] = exec_res

class PlanChapters(Node):
    def prep(self, shared):
        return shared["files_text"]

    def exec(self, files_text):
        prompt = f"""Analyze this codebase. Identify the 10 most important
abstractions (classes, patterns, modules). Order them so a beginner
can learn each one building on the previous.

Files:
{files_text}

Output YAML:
```yaml
chapters:
  - title: <chapter title>
    description: <one sentence>
```"""
        return call_llm(prompt)

    def post(self, shared, prep_res, exec_res):
        shared["chapters"] = yaml.safe_load(
            exec_res.split("```yaml")[1].split("```")[0]
        )["chapters"]
        shared["written"] = []
        shared["current_idx"] = 0

class WriteChapter(Node):
    def prep(self, shared):
        idx = shared["current_idx"]
        chapter = shared["chapters"][idx]
        prev = "\n\n".join(
            f"Chapter {i+1}: {shared['chapters'][i]['title']}\n{w[:500]}"
            for i, w in enumerate(shared["written"])
        )
        return chapter, shared["files_text"], prev  #A

    def exec(self, inputs):
        chapter, files_text, prev = inputs
        prompt = f"""Write a beginner-friendly tutorial chapter.

Chapter: {chapter['title']}
Description: {chapter['description']}

Source files:
{files_text}

Previous chapters covered:
{prev or '(This is the first chapter)'}

Write a clear explanation with code snippets from the source files.
Explain what the code does and why it's designed this way.
End with a one-paragraph summary."""
        return call_llm(prompt)

    def post(self, shared, prep_res, exec_res):
        shared["written"].append(exec_res)
        shared["current_idx"] += 1
        if shared["current_idx"] >= len(shared["chapters"]):
            return None
        return "next"

fetch = FetchFiles()
plan = PlanChapters()
write = WriteChapter()

fetch >> plan >> write
write - "next" >> write

flow = Flow(start=fetch)
REPO = os.path.join(os.path.dirname(__file__), "..", "pocketflow")
shared = {"repo_path": os.environ.get("REPO_PATH", REPO)}
flow.run(shared)

for i, chapter in enumerate(shared["chapters"]):
    print(f"\n===== Chapter {i+1}: {chapter['title']} =====")
    print(shared["written"][i][:400], "...")

