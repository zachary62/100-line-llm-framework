"""TTS utility — swap for OpenAI or ElevenLabs by editing this one function."""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from call_llm import client, TTS_MODEL
from google.genai import types

def text_to_speech(text, voice):
    resp = client.models.generate_content(
        model=TTS_MODEL,
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                )
            ),
        ),
    )
    return resp.candidates[0].content.parts[0].inline_data.data  # raw 24kHz 16-bit PCM

if __name__ == "__main__":
    print(f"{len(text_to_speech('Hello from PocketFlow.', 'Kore'))} bytes of audio")
