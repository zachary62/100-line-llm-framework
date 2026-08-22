"""Section 4.2: Embeddings — turning text into numbers that capture meaning"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from call_llm import client, EMBED_MODEL
import numpy as np

def get_embedding(text):
    r = client.models.embed_content(model=EMBED_MODEL, contents=text)
    return r.embeddings[0].values

def cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# Demo: similar vs unrelated texts
pairs = [
    ("The dog barked loudly", "The puppy made noise"),
    ("The dog barked loudly", "The cat meowed softly"),
    ("The dog barked loudly", "Stock market crashed today"),
]

for a, b in pairs:
    sim = cosine_similarity(get_embedding(a), get_embedding(b))
    print(f"  {sim:.3f}  |  '{a}'  vs  '{b}'")
