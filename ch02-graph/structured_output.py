"""Section 2.6: Structured Output — Resume parser with YAML + validation + retries"""
from pocketflow import Node, Flow
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from call_llm import call_llm
import yaml

class ParseResume(Node):
    def prep(self, shared):
        return shared["resume_text"]

    def exec(self, resume_text):
        prompt = f"""Extract info from this resume as YAML:

{resume_text}

```yaml
name: full name
email: email address
skills:
  - skill 1
  - skill 2
```"""
        response = call_llm(prompt)
        yaml_str = response.split("```yaml")[1].split("```")[0].strip()
        result = yaml.safe_load(yaml_str)
        assert "name" in result
        assert "email" in result
        assert isinstance(result["skills"], list)
        return result

    def post(self, shared, prep_res, exec_res):
        shared["parsed"] = exec_res

resume = """John Smith, john@example.com
Senior Python developer with 5 years experience.
Skills: Python, FastAPI, PostgreSQL, Docker, AWS"""

shared = {"resume_text": resume}
ParseResume(max_retries=3).run(shared)
print(shared["parsed"])
