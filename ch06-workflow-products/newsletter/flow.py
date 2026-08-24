from pocketflow import Flow
from nodes import CurateSources, FilterStories, SummarizeStories, FormatNewsletter

def create_newsletter_flow():
    curate = CurateSources()
    filter_node = FilterStories()
    summarize = SummarizeStories()
    format_node = FormatNewsletter()

    curate >> filter_node >> summarize >> format_node
    return Flow(start=curate)
