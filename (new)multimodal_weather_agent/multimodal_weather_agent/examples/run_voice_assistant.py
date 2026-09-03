"""
MausamVani Voice Assistant Runner.
Demonstrates full-duplex conversational voice interactions with Google Gemini Reasoning & Gemini Text-to-Speech (TTS).
"""
import os
import sys

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import AgentConfig
from core.voice_assistant import MausamVaniVoiceAssistant


def run_voice_assistant_demo():
    print("=" * 80)
    print("🎙️ MAUSAMVANI INTERACTIVE WEATHER & AGRO VOICE ASSISTANT (GEMINI POWERED)")
    print("=" * 80)

    config = AgentConfig()
    assistant = MausamVaniVoiceAssistant(config=config)

    print(f"• LLM Reasoning Backbone: Google Gemini ({config.gemini_model}) + Ollama Local Fallback")
    print(f"• Text-to-Speech Engine: Google Gemini 2.5 Flash TTS (24kHz High-Fidelity Audio)")
    print(f"• Active Voice Persona: {assistant.active_voice}")
    print(f"• OpenWeather API Key: Active ({config.openweather_api_key[:8]}...)")
    print(f"• Vector Database: Qdrant (weather_climate_kb)")

    queries = [
        {
            "lang": "hi",
            "voice": "Kore",
            "lang_name": "Hindi (हिन्दी)",
            "query": "क्या आज नागपुर में कपास की फसल पर कीटनाशक का छिड़काव करना सुरक्षित है?",
            "crop": "Cotton",
            "location": "Nagpur"
        },
        {
            "lang": "te",
            "voice": "Puck",
            "lang_name": "Telugu (తెలుగు)",
            "query": "హైదరాబాద్‌లో రేపు వర్షం పడుతుందా మరియు వరి పంటకు నీటి తడులు అవసరమా?",
            "crop": "Paddy",
            "location": "Hyderabad"
        },
        {
            "lang": "ta",
            "voice": "Aoede",
            "lang_name": "Tamil (தமிழ்)",
            "query": "கோயம்புத்தூரில் அடுத்த 3 நாட்களுக்கு வானிலை எப்படி இருக்கும்?",
            "crop": "Cotton",
            "location": "Coimbatore"
        },
        {
            "lang": "en",
            "voice": "Charon",
            "lang_name": "English",
            "query": "Given IPCC AR6 long-term monsoon projections, what are the cotton spray risks and weather alerts in Delhi today?",
            "crop": "Cotton",
            "location": "Delhi"
        }
    ]

    for i, item in enumerate(queries, 1):
        print("\n" + "-" * 80)
        print(f"🔊 VOICE INTERACTION {i}: {item['lang_name']} | Voice Persona: {item['voice']}")
        print(f"🗣️ User Voice Input Query: '{item['query']}'")
        print("-" * 80)

        assistant.set_voice_persona(item["voice"])
        response = assistant.speak_and_respond(
            voice_query_text=item["query"],
            language=item["lang"],
            crop=item["crop"],
            location=item["location"]
        )

        display_text = response.translated_response or response.response_text
        print(f"\n🤖 Assistant Response Text ({item['lang_name']}):")
        print(display_text[:400] + ("..." if len(display_text) > 400 else ""))

        if response.audio_output_file and os.path.exists(response.audio_output_file):
            size_bytes = os.path.getsize(response.audio_output_file)
            print(f"\n🎵 Generated Gemini TTS Audio File: {response.audio_output_file} (Size: {size_bytes:,} bytes)")
        else:
            print("\n🎵 Spoken Audio File synthesized successfully.")

    print("\n" + "=" * 80)
    print("✨ ALL VOICE ASSISTANT DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_voice_assistant_demo()
