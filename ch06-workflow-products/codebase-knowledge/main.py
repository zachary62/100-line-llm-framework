"""Section 6.3: Codebase knowledge — a loop that carries context forward.

Points at this repo's own pocketflow/ package by default, so it has something
real to read without any setup. Override with REPO_PATH=/path/to/repo.
"""
import os
from flow import create_tutorial_flow

REPO = os.path.join(os.path.dirname(__file__), "..", "..", "pocketflow")
shared = {"repo_path": os.environ.get("REPO_PATH", REPO)}

create_tutorial_flow().run(shared)

out = os.path.join(os.path.dirname(__file__), "output", "tutorial.md")
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w") as f:
    f.write("\n\n---\n\n".join(shared["written"]))
print(f"Full tutorial saved to {out}")

for i, chapter in enumerate(shared["chapters"]):
    print(f"\n===== Chapter {i+1}: {chapter['title']} =====")
    print(shared["written"][i][:400], "...")
