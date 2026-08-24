from pocketflow import Flow
from nodes import FetchFiles, PlanChapters, WriteChapter

def create_tutorial_flow():
    fetch = FetchFiles()
    plan = PlanChapters()
    write = WriteChapter()

    fetch >> plan >> write
    write - "next" >> write

    return Flow(start=fetch)
