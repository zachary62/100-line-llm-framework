from pocketflow import Flow
from nodes import PlannerNode, ResearcherNode, SynthesizerNode

def create_deep_research_flow():
    planner = PlannerNode()
    researcher = ResearcherNode()
    synthesizer = SynthesizerNode()

    planner >> researcher >> synthesizer
    synthesizer - "research" >> planner

    return Flow(start=planner)
