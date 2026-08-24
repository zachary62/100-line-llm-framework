import sys, os, yaml
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from pocketflow import Node
from call_llm import call_llm
from utils import text_to_speech

class AnalyzeDocs(Node):
    def prep(self, shared):
        return shared["documents"]

    def exec(self, docs):
        all_docs = "\n\n---\n\n".join(
            f"Document {i+1}:\n{doc}" for i, doc in enumerate(docs)
        )
        prompt = f"""Extract 2-3 surprising or interesting nuggets from EACH
document below. Focus on things that would make someone say 'wait, really?'

{all_docs}"""
        return call_llm(prompt)

    def post(self, shared, prep_res, exec_res):
        shared["nuggets"] = exec_res

VOICES = {"Alex": "Kore", "Jamie": "Puck"}

class WriteScript(Node):
    def prep(self, shared):
        return shared["nuggets"]

    def exec(self, nuggets):
        prompt = f"""Write a podcast script between two hosts: Alex and Jamie.

Source nuggets:
{nuggets}

Write a full conversation (about 6 exchanges / 12 lines).
Make it natural — interruptions, reactions, "wait, seriously?" moments.
Cover all the nuggets. Be conversational, not a lecture.

Output as YAML:
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
            assert item["name"] in VOICES
        return result["script"]

    def post(self, shared, prep_res, exec_res):
        shared["script"] = exec_res

class AudioStudio(Node):
    def prep(self, shared):
        return shared["script"]

    def exec(self, script):
        audio_parts = []
        for item in script:
            audio = text_to_speech(item["line"], VOICES[item["name"]])
            audio_parts.append(audio)
        return b"".join(audio_parts)

    def post(self, shared, prep_res, exec_res):
        shared["audio"] = exec_res
