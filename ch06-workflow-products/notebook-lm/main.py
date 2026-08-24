"""Section 6.1: NotebookLM — upload docs, get a podcast."""
import os, wave
from flow import create_podcast_flow

shared = {"documents": [
    "Doc A: Q3 revenue increased 20% due to AI adoption...",
    "Doc B: Risk report indicates high churn in enterprise...",
    "Doc C: New employee benefits include unlimited coffee."
]}

create_podcast_flow().run(shared)

out = os.path.join(os.path.dirname(__file__), "podcast.wav")
with wave.open(out, "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(24000)
    wf.writeframes(shared["audio"])
print(f"Audio saved to {out}")

print("--- Podcast Script ---")
for item in shared["script"]:
    print(f"{item['name']}: {item['line']}")
