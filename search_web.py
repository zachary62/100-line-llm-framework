"""Shared search utility — reused across chapters"""
import requests
from ddgs import DDGS

def search_web(query, max_results=3):
    results = DDGS().text(query, max_results=max_results)
    full_texts = []
    for r in results:
        url = r["href"]
        page = requests.get(f"https://r.jina.ai/{url}").text
        full_texts.append(page)
    return "\n\n---\n\n".join(full_texts)

if __name__ == "__main__":
    print(search_web("PocketFlow LLM framework")[:2000])
