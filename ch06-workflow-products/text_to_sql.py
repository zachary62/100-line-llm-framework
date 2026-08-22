"""Section 6.2: Text to SQL — schema, generate, execute, debug, answer.

Listings 6.5 through 6.9 in chapter 6, assembled into one runnable file.
The sample database is created on first run.
"""
import sys, os, sqlite3
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from pocketflow import Node, Flow
from call_llm import call_llm

DB_PATH = os.path.join(os.path.dirname(__file__), "shop.db")

def setup_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS customers;
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY, name TEXT, email TEXT, plan TEXT, signed_up DATE
        );
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY, customer_id INTEGER, product TEXT,
            amount REAL, status TEXT, ordered_at DATE,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        );
        INSERT INTO customers VALUES
            (1,'Alice','alice@example.com','pro','2024-01-15'),
            (2,'Bob','bob@example.com','free','2024-03-22'),
            (3,'Carol','carol@example.com','pro','2024-02-10'),
            (4,'Dave','dave@example.com','enterprise','2024-01-05'),
            (5,'Eve','eve@example.com','free','2024-04-18');
        INSERT INTO orders VALUES
            (1,1,'Widget',29.99,'completed','2024-02-01'),
            (2,1,'Gadget',49.99,'completed','2024-03-15'),
            (3,2,'Widget',29.99,'refunded','2024-04-01'),
            (4,3,'Gadget',49.99,'completed','2024-02-20'),
            (5,3,'Gizmo',99.99,'completed','2024-03-10'),
            (6,4,'Gizmo',99.99,'completed','2024-01-20'),
            (7,4,'Widget',29.99,'completed','2024-02-15'),
            (8,4,'Gadget',49.99,'pending','2024-04-25'),
            (9,5,'Widget',29.99,'completed','2024-05-01');
    """)
    conn.commit()
    conn.close()

import sqlite3
from pocketflow import Node

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

fetcher = SchemaFetcher()
generator = SQLGenerator()
executor = SQLExecutor()
debugger = SQLDebugger()
formatter = AnswerFormatter()

fetcher >> generator >> executor
executor - "success" >> formatter
executor - "error"   >> debugger
executor - "give_up" >> formatter
debugger - "retry"   >> executor

sql_agent = Flow(start=fetcher)


setup_db()

for question in [
    "How much revenue came from completed orders?",
    "Which customer spent the most?",
]:
    shared = {"db_path": DB_PATH, "question": question}
    sql_agent.run(shared)
    print(f"Q: {question}")
    print(f"A: {shared['answer']}\n")
