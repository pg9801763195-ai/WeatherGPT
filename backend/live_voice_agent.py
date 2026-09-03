"""
Real-Time Interactive Voice Agent CLI (MausamVani Live Voice).
Listens to your device microphone in real-time, detects voice activity, transcribes speech,
processes weather intelligence, and speaks responses directly out of your system speakers.

Usage:
    python live_voice_agent.py
"""
import os
import sys
import time

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import AgentConfig
from core.agent import MultimodalWeatherAgent
from schemas.weather_schemas import MultimodalInput
from multimodal.realtime_mic import RealtimeVoiceDetector

try:
    import sounddevice as sd
    import soundfile as sf
except ImportError:
    pass


def print_banner():
    print("=" * 65)
    print("   🎙️  MausamVani AI - Real-Time Voice Assistant (Device Mic)")
    print("=" * 65)
    print("  • Automatic Voice Activity Detection (VAD)")
    print("  • Supports English, Hindi (हिन्दी), Odia (ଓଡ଼ିଆ), Hinglish, etc.")
    print("  • Speak your question into your microphone!")
    print("=" * 65 + "\n")


def play_audio(audio_path: str):
    """Play audio file through default system speakers."""
    if not os.path.exists(audio_path):
        return
    try:
        data, fs = sf.read(audio_path, dtype="float32")
        sd.play(data, fs)
        sd.wait()
    except Exception:
        # Fallback to system default player on Windows
        try:
            import winsound
            winsound.PlaySound(audio_path, winsound.SND_FILENAME)
        except Exception:
            pass


def main():
    print_banner()

    config = AgentConfig()
    agent = MultimodalWeatherAgent(config)
    detector = RealtimeVoiceDetector(config=config, energy_threshold=0.018, silence_duration=1.2)

    devices = detector.list_audio_devices()
    print(f"📡 Found {len(devices)} Audio Input Device(s):")
    for d in devices:
        def_tag = " [DEFAULT]" if d.get("is_default") else ""
        print(f"   • [{d['index']}] {d['name']}{def_tag}")
    print()

    current_location = "Jatani"
    print(f"📍 Active Location Context: {current_location}")
    print("🟢 Ready! Speak into your microphone (or press Ctrl+C to quit).\n")

    try:
        while True:
            print("-" * 55)
            print("👂 Listening... (Start speaking now)")

            def on_progress(energy, msg):
                bar = "█" * int(min(energy * 250, 25))
                if energy > 0:
                    print(f"\r   🎙️ [{bar:<25}] {msg}", end="", flush=True)

            text, audio_path = detector.listen_and_transcribe(
                language="hi-IN",
                max_duration=12.0,
                progress_callback=on_progress
            )
            print()

            if not text:
                print("⚠️  No clear speech detected. Listening again...")
                time.sleep(1)
                continue

            print(f"\n🗣️  You said: \"{text}\"")
            print("⏳ Analyzing weather data & synthesizing response...")

            input_data = MultimodalInput(
                text_query=text,
                location_name=current_location,
                language_code="auto"
            )
            response = agent.process_query(input_data)
            
            main_text = response.translated_response or response.response_text
            print("\n🤖 MausamVani:")
            print(main_text)

            # Generate and play speech audio response
            audio_file = agent.audio_engine.text_to_speech(
                text=main_text,
                language_code=response.detected_language or "hi",
                filename=f"live_reply_{int(time.time())}.wav"
            )
            if audio_file and os.path.exists(audio_file):
                print("\n🔊 Playing audio response...")
                play_audio(audio_file)

            print("\n")
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n👋 Stopped live voice assistant. Goodbye!")


if __name__ == "__main__":
    main()
