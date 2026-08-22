"""Section 6.1: NotebookLM — upload docs, get a podcast"""
import sys, os, wave, yaml, base64
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from pocketflow import Node, Flow
from call_llm import call_llm, client, TTS_MODEL
from google.genai import types

DOCS = [
    """PocketFlow is a 100-line minimalist LLM framework. Zero dependencies, zero vendor lock-in.
The core abstraction is a nested directed graph. Nodes do the work, Flows connect them.
Compared to LangChain (405K lines), CrewAI (18K lines), or LangGraph (37K lines),
PocketFlow proves you only need 100 lines to capture every LLM design pattern.""",

    """Nodes have three phases: prep reads from shared store, exec does the work (LLM calls,
tool use), post writes results back. Only exec retries on failure. This separation means
your data logic and compute logic never tangle. BatchNode processes lists — prep returns
an iterable, exec runs per item, post gets all results.""",

    """A Flow connects nodes with >> for chaining and action strings for branching.
post() returns a string that picks the next branch. Flows are also Nodes, so they nest:
a payment flow inside an order flow inside a checkout flow. This composability means
you build complex systems from simple, tested pieces.""",

    """The key design patterns: Workflow (chain of nodes), Agent (decide-act loop),
RAG (retrieve then generate), Map-Reduce (fan out, combine), and Reflection
(generate, evaluate, retry). Every AI product — NotebookLM, Cursor, Devin —
is built from these same five patterns.""",
]

class AnalyzeDocs(Node):
    def prep(self, shared):
        return shared["docs"]
    def exec(self, docs):
        all_docs = "\n\n---\n\n".join(f"Document {i+1}:\n{doc}" for i, doc in enumerate(docs))
        return call_llm(
            f"Extract 2-3 surprising or interesting nuggets from EACH document below. "
            f"Focus on things that would make someone say 'wait, really?'\n\n{all_docs}"
        )
    def post(self, shared, prep_res, exec_res):
        shared["nuggets"] = exec_res
        print(f"  Extracted nuggets from {len(shared['docs'])} docs")

class WriteScript(Node):
    def prep(self, shared):
        return shared["nuggets"]

    def exec(self, nuggets):
        prompt = f"""You are writing a podcast script between two hosts: Alex and Jamie.
They are discussing a tech framework.

Source nuggets:
{nuggets}

Write a full podcast conversation (about 6 exchanges / 12 lines).
Make it natural — interruptions, reactions, "wait, seriously?" moments.
Cover all the nuggets. Be conversational, not a lecture.

Output as YAML (IMPORTANT: quote all line values with double quotes, escape inner quotes):
```yaml
script:
  - name: Alex
    line: "what Alex says"
  - name: Jamie
    line: "what Jamie says"
```"""
        response = call_llm(prompt)
        result = yaml.safe_load(response.split("```yaml")[1].split("```")[0])
        assert isinstance(result["script"], list)
        for item in result["script"]:
            assert "name" in item and "line" in item
            assert item["name"] in VOICES, f"Unknown speaker: {item['name']}"
        return result["script"]

    def post(self, shared, prep_res, exec_res):
        shared["script"] = exec_res

VOICES = {"Alex": "Kore", "Jamie": "Puck"}

class AudioStudio(Node):
    def prep(self, shared):
        return shared["script"]

    def exec(self, script):
        audio_parts = []
        for item in script:
            voice = VOICES[item["name"]]
            resp = client.models.generate_content(
                model=TTS_MODEL,
                contents=item["line"],
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                        )
                    ),
                ),
            )
            raw = resp.candidates[0].content.parts[0].inline_data.data
            audio_parts.append(base64.b64decode(raw))
        return b"".join(audio_parts)

    def post(self, shared, prep_res, exec_res):
        out = os.path.join(os.path.dirname(__file__), "podcast.wav")
        with wave.open(out, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(exec_res)
        shared["audio_file"] = out
        print(f"  Audio saved to {out}")

analyze = AnalyzeDocs()
write = WriteScript(max_retries=3)   # the asserts only retry if the node is allowed to
tts = AudioStudio()

analyze >> write >> tts

flow = Flow(start=analyze)

shared = {"docs": DOCS}
flow.run(shared)
print("--- Podcast Script ---")
for item in shared["script"]:
    print(f"{item['name']}: {item['line']}")
