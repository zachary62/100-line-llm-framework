"""Section 3.4: Self-Healing — generate mermaid, compile, fix errors, retry"""
import sys, os, shutil, subprocess, tempfile
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from pocketflow import Node, Flow
from call_llm import call_llm

# Use the installed CLI if there is one; otherwise npx fetches it on first run.
MMDC = ["mmdc"] if shutil.which("mmdc") else ["npx", "--yes", "@mermaid-js/mermaid-cli"]

class WriteChart(Node):
    def prep(self, shared):
        shared.setdefault("attempts", [])
        return {"task": shared["task"], "attempts": shared["attempts"]}
    def exec(self, inputs):
        history = "\n\n".join(
            f"Attempt {i+1}:\n```mermaid\n{a['code']}\n```\nError: {a['error']}"
            for i, a in enumerate(inputs["attempts"])
        )
        prompt = f"Write a Mermaid diagram for: {inputs['task']}\nOutput ONLY the mermaid code in ```mermaid``` block."
        if history:
            prompt += f"\n\nPrevious attempts:\n{history}\n\nFix the syntax errors."
        response = call_llm(prompt)
        return response.split("```mermaid")[1].split("```")[0].strip()
    def post(self, shared, prep_res, exec_res):
        shared["chart"] = exec_res
        print(f"\n--- Mermaid ---\n{exec_res}\n")

class CompileChart(Node):
    def prep(self, shared):
        return shared["chart"]
    def exec(self, code):
        with tempfile.NamedTemporaryFile(suffix=".mmd", mode="w", delete=False) as f:
            f.write(code)
            mmd_path = f.name
        svg_path = mmd_path.replace(".mmd", ".svg")
        result = subprocess.run(
            [*MMDC, "-i", mmd_path, "-o", svg_path],
            capture_output=True, text=True, timeout=180
        )
        os.unlink(mmd_path)
        if os.path.exists(svg_path):
            os.unlink(svg_path)
        if result.returncode != 0:
            error = result.stderr or result.stdout
            # Extract parse error, add hints for cryptic mermaid errors
            lines = error.split("\n")
            clean = []
            for l in lines:
                if "Parse error" in l or "Expecting" in l:
                    clean.append(l)
            clean_error = "\n".join(clean[:3]) if clean else error[:500]
            if "got 'PS'" in error:
                clean_error += "\nHint: Mermaid can't handle parentheses () inside node labels. Use quotes: node[\"label with (parens)\"]"
            return {"success": False, "error": clean_error}
        return {"success": True}
    def post(self, shared, prep_res, exec_res):
        if exec_res["success"]:
            print("Compiled successfully!")
            return "done"
        print(f"Error: {exec_res['error']}")
        shared["attempts"].append({"code": shared["chart"], "error": exec_res["error"]})
        if len(shared["attempts"]) >= 3:
            print("Max retries reached.")
            return "done"
        return "fix" if len(shared["attempts"]) < 3 else "done"

if not shutil.which("mmdc") and not shutil.which("npx"):
    print("This example needs the mermaid CLI, a Node package:")
    print("    npm install -g @mermaid-js/mermaid-cli")
    print("Everything else in this chapter runs without it.")
    sys.exit(0)

write = WriteChart()
compile = CompileChart()
write >> compile
compile - "fix" >> write

shared = {"task": "A flowchart for error handling: Request --> Parse JSON --> Validate(check required fields) --> Process. If Parse fails, route to Error[Return 400: 'Invalid JSON (parse error)']. If Validate fails, route to Error2[Return 422: 'Missing field(s): {details}']. Process --> DB[INSERT INTO orders(id, total)] --> Response[Return 201: {order_id}]. Use a subgraph 'Happy Path (v2)' around Validate, Process and DB."}
Flow(start=write).run(shared)
