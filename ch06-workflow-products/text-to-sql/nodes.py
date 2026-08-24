import sys, os, sqlite3
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from pocketflow import Node
from call_llm import call_llm

class SchemaFetcher(Node):
    def prep(self, shared):
        return shared["db_path"]

    def exec(self, db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
        rows = cursor.fetchall()
        schema = "\n\n".join([row[0] for row in rows if row[0]])
        conn.close()
        return schema

    def post(self, shared, prep_res, exec_res):
        shared["schema"] = exec_res

class SQLGenerator(Node):
    def prep(self, shared):
        return shared["question"], shared["schema"]

    def exec(self, inputs):
        question, schema = inputs
        prompt = f"""You are a SQL expert. Write a SQLite query.

Database Schema:
{schema}

Question: {question}

Return ONLY the SQL query. No markdown. No explanation."""
        return call_llm(prompt)

    def post(self, shared, prep_res, exec_res):
        shared["sql_query"] = exec_res.replace("```sql", "").replace("```", "").strip()

class SQLExecutor(Node):
    def prep(self, shared):
        return shared["db_path"], shared["sql_query"]

    def exec(self, inputs):
        db_path, sql = inputs

        if not sql.upper().startswith("SELECT"):
            return {"error": "Only SELECT queries are allowed."}

        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            cursor = conn.cursor()
            cursor.execute(sql)
            results = cursor.fetchall()
            conn.close()
            return {"success": True, "data": results}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def post(self, shared, prep_res, exec_res):
        if exec_res.get("success"):
            shared["results"] = exec_res["data"]
            return "success"
        shared["error_msg"] = exec_res["error"]
        shared["fix_attempts"] = shared.get("fix_attempts", 0) + 1
        return "error" if shared["fix_attempts"] <= 3 else "give_up"

class SQLDebugger(Node):
    def prep(self, shared):
        return {
            "question": shared["question"],
            "schema": shared["schema"],
            "bad_sql": shared["sql_query"],
            "error": shared["error_msg"]
        }

    def exec(self, ctx):
        prompt = f"""The previous SQL query failed. Fix it.

Schema:
{ctx['schema']}

Question: {ctx['question']}
Failed Query: {ctx['bad_sql']}
Error Message: {ctx['error']}

Return ONLY the fixed SQL."""
        return call_llm(prompt)

    def post(self, shared, prep_res, exec_res):
        shared["sql_query"] = exec_res.replace("```sql", "").replace("```", "").strip()
        return "retry"

class AnswerFormatter(Node):
    def prep(self, shared):
        return shared["question"], shared.get("results"), shared.get("error_msg", "")

    def exec(self, inputs):
        question, results, error = inputs
        if results is None:
            return f"I couldn't answer that one. The last query failed with: {error}"
        return call_llm(
            f"Question: {question}\nSQL result: {results}\n"
            f"Answer in one short sentence, no SQL."
        )

    def post(self, shared, prep_res, exec_res):
        shared["answer"] = exec_res
