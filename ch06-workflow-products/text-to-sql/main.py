"""Section 6.2: Text to SQL — schema, generate, execute, debug, answer."""
from flow import create_sql_agent
from utils import setup_db, DB_PATH

setup_db()
sql_agent = create_sql_agent()

for question in [
    "How much revenue came from completed orders?",
    "Which customer spent the most?",
]:
    shared = {"db_path": DB_PATH, "question": question}
    sql_agent.run(shared)
    print(f"Q: {question}")
    print(f"A: {shared['answer']}\n")
