"""Shared LLM wrapper — every example in this book imports this file.

Model IDs churn every few months. Name the *role* (fast vs. smart), not the
version, so a new release is a one-line edit here instead of a find-and-replace
across every chapter. Override either one without touching code:

    export FAST_MODEL=gemini-2.5-flash-lite

The examples in this repo were run and their outputs recorded with the Gemini
models below. Any provider works: swap the six lines under "-- Gemini --" for
one of the commented blocks and every example keeps running, because the whole
contract is call_llm(prompt) -> str.

temperature is the one knob the examples use (chapter 3's majority vote turns it
up so five calls disagree). Its range is provider-specific: OpenAI and Gemini
accept up to 2.0, Anthropic caps at 1.0.
"""
import os

# Role, not version. Swap the value, not the call sites.
FAST_MODEL = os.getenv("FAST_MODEL", "gemini-2.5-flash")        # drafting, classification, extraction
SMART_MODEL = os.getenv("SMART_MODEL", "gemini-2.5-pro")        # judging, planning, hard reasoning
EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-001")  # RAG (chapter 4)
TTS_MODEL = os.getenv("TTS_MODEL", "gemini-2.5-flash-preview-tts")  # NotebookLM clone (chapter 6)

## -- Gemini (what this repo was tested on) --
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def call_llm(prompt, model=FAST_MODEL, temperature=1.0):
    r = client.models.generate_content(
        model=model, contents=prompt, config={"temperature": temperature}
    )
    return r.text

## -- OpenAI --
# from openai import OpenAI
# client = OpenAI()  # reads OPENAI_API_KEY
#
# def call_llm(prompt, model=FAST_MODEL, temperature=1.0):
#     r = client.chat.completions.create(
#         model=model, messages=[{"role": "user", "content": prompt}],
#         temperature=temperature
#     )
#     return r.choices[0].message.content

## -- Anthropic (Claude) --
# from anthropic import Anthropic
# client = Anthropic()  # reads ANTHROPIC_API_KEY
#
# def call_llm(prompt, model=FAST_MODEL, temperature=1.0):
#     r = client.messages.create(
#         model=model, max_tokens=4096,
#         messages=[{"role": "user", "content": prompt}],
#         temperature=min(temperature, 1.0)   # Anthropic's ceiling is 1.0
#     )
#     return r.content[0].text

## -- Local models via Ollama (speaks the OpenAI protocol) --
# from openai import OpenAI
# client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
#
# def call_llm(prompt, model=FAST_MODEL, temperature=1.0):
#     r = client.chat.completions.create(
#         model=model, messages=[{"role": "user", "content": prompt}],
#         temperature=temperature
#     )
#     return r.choices[0].message.content

if __name__ == "__main__":
    print(f"fast : {FAST_MODEL} -> {call_llm('Say hello in one word')}")
    print(f"smart: {SMART_MODEL} -> {call_llm('Say hello in one word', model=SMART_MODEL)}")
