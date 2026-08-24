from pocketflow import Flow
from nodes import AnalyzeDocs, WriteScript, AudioStudio

def create_podcast_flow():
    analyze = AnalyzeDocs()
    write = WriteScript(max_retries=3)   # the asserts only retry if the node is allowed to
    studio = AudioStudio()

    analyze >> write >> studio
    return Flow(start=analyze)
