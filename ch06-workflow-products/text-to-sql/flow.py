from pocketflow import Flow
from nodes import SchemaFetcher, SQLGenerator, SQLExecutor, SQLDebugger, AnswerFormatter

def create_sql_agent():
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

    return Flow(start=fetcher)
