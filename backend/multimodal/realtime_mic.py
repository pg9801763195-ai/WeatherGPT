"""
Real-Time Voice Detection and Microphone Capture Engine.
Uses sounddevice, soundfile, and speech_recognition to access hardware microphone,
perform Voice Activity Detection (VAD) with energy thresholding, and transcribe speech in real-time.
"""
import os
import io
import time
import math
import wave
import tempfile
import threading
import numpy as np
from typing import Optional, Dict, Any, Callable, Tuple

try:
    import sounddevice as sd
    import soundfile as sf
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

from config import AgentConfig


class RealtimeVoiceDetector:
    """
    Accesses device hardware microphone, monitors real-time audio streams,
    detects voice presence (VAD), and transcribes speech into text.
    """

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        sample_rate: int = 16000,
        channels: int = 1,
        silence_duration: float = 1.3,
        energy_threshold: float = 0.015
    ):
        self.config = config or AgentConfig()
        self.sample_rate = sample_rate
        self.channels = channels
        self.silence_duration = silence_duration
        self.energy_threshold = energy_threshold
        self.is_listening = False
        self.audio_output_dir = os.path.join(os.path.dirname(__file__), "audio_outputs")
        os.makedirs(self.audio_output_dir, exist_ok=True)

    @staticmethod
    def list_audio_devices() -> list[Dict[str, Any]]:
        """List all available hardware audio input devices (microphones)."""
        if not SOUNDDEVICE_AVAILABLE:
            return []
        
        devices = []
        try:
            device_list = sd.query_devices()
            default_input = sd.default.device[0]
            for idx, dev in enumerate(device_list):
                if dev.get("max_input_channels", 0) > 0:
                    devices.append({
                        "index": idx,
                        "name": dev.get("name", f"Microphone {idx}"),
                        "channels": dev.get("max_input_channels"),
                        "default_samplerate": dev.get("default_samplerate"),
                        "is_default": idx == default_input
                    })
        except Exception as e:
            print(f"[RealtimeVoiceDetector] Error listing devices: {e}")
        return devices

    def record_until_silence(
        self,
        max_duration: float = 12.0,
        device_index: Optional[int] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Optional[str]:
        """
        Open device microphone and record audio in real-time.
        Starts recording when speech is detected (VAD), and automatically stops
        after a continuous period of silence.
        
        Returns path to the saved WAV file.
        """
        if not SOUNDDEVICE_AVAILABLE:
            print("[RealtimeVoiceDetector] sounddevice library not installed.")
            return None

        # Calibrate / dynamic silence threshold
        chunk_duration = 0.1  # 100ms chunks
        chunk_samples = int(self.sample_rate * chunk_duration)
        
        audio_buffer = []
        speech_started = False
        silence_start_time = None
        start_time = time.time()
        
        if progress_callback:
            progress_callback(0.0, "Listening for voice...")

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
                device=device_index,
                blocksize=chunk_samples
            ) as stream:
                
                while True:
                    data, overflowed = stream.read(chunk_samples)
                    if overflowed:
                        pass
                    
                    audio_chunk = data.flatten()
                    rms_energy = float(np.sqrt(np.mean(audio_chunk ** 2)))
                    audio_buffer.append(audio_chunk)

                    # Dynamic VAD Check
                    is_voice = rms_energy > self.energy_threshold

                    if is_voice:
                        if not speech_started:
                            speech_started = True
                            if progress_callback:
                                progress_callback(rms_energy, "Speech detected, recording...")
                        silence_start_time = None
                    else:
                        if speech_started:
                            if silence_start_time is None:
                                silence_start_time = time.time()
                            elif (time.time() - silence_start_time) >= self.silence_duration:
                                # Silence period elapsed after speaking -> finalize
                                if progress_callback:
                                    progress_callback(0.0, "Silence detected, processing voice...")
                                break

                    # Timeout check
                    elapsed = time.time() - start_time
                    if elapsed >= max_duration:
                        if progress_callback:
                            progress_callback(0.0, "Max duration reached, processing...")
                        break

                    # If no speech at all after 5 seconds, exit
                    if not speech_started and elapsed >= 5.0:
                        if progress_callback:
                            progress_callback(0.0, "No speech detected.")
                        break

            if not audio_buffer or not speech_started:
                return None

            # Concatenate and save to WAV
            full_audio = np.concatenate(audio_buffer, axis=0)
            
            # Normalize audio
            max_val = np.max(np.abs(full_audio))
            if max_val > 0:
                full_audio = full_audio / max_val * 0.9

            out_wav = os.path.join(self.audio_output_dir, f"mic_capture_{int(time.time())}.wav")
            sf.write(out_wav, full_audio, self.sample_rate, subtype="PCM_16")
            return out_wav

        except Exception as e:
            print(f"[RealtimeVoiceDetector] Microphone error: {e}")
            return None

    def transcribe_audio_file(self, audio_file_path: str, language: str = "hi-IN") -> str:
        """
        Transcribe recorded audio file into text using speech_recognition or Gemini Multimodal.
        """
        if not os.path.exists(audio_file_path):
            return ""

        # 1. Try SpeechRecognition (Google Free Speech-to-Text API)
        if SPEECH_RECOGNITION_AVAILABLE:
            recognizer = sr.Recognizer()
            try:
                with sr.AudioFile(audio_file_path) as source:
                    audio_data = recognizer.record(source)
                
                # Try preferred language first (e.g. Hindi, Odia, English)
                languages_to_try = [language, "hi-IN", "en-IN", "or-IN", "bn-IN"]
                for lang in languages_to_try:
                    try:
                        text = recognizer.recognize_google(audio_data, language=lang)
                        if text and text.strip():
                            return text.strip()
                    except (sr.UnknownValueError, sr.RequestError):
                        continue
            except Exception as e:
                print(f"[RealtimeVoiceDetector] speech_recognition error: {e}")

        # 2. Try Gemini API multimodal audio if key available
        if self.config.gemini_api_key:
            try:
                import requests
                import base64
                with open(audio_file_path, "rb") as af:
                    b64 = base64.b64encode(af.read()).decode("utf-8")
                
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.config.gemini_api_key}"
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": "Accurately transcribe this audio voice recording. Return only the exact transcribed query text."},
                            {"inlineData": {"mimeType": "audio/wav", "data": b64}}
                        ]
                    }]
                }
                resp = requests.post(url, json=payload, timeout=8)
                if resp.status_code == 200:
                    cand = resp.json().get("candidates", [])
                    if cand and "content" in cand[0]:
                        parts = cand[0]["content"].get("parts", [])
                        if parts and "text" in parts[0]:
                            return parts[0]["text"].strip()
            except Exception as e:
                print(f"[RealtimeVoiceDetector] Gemini STT error: {e}")

        return ""

    def listen_and_transcribe(
        self,
        language: str = "hi-IN",
        max_duration: float = 10.0,
        device_index: Optional[int] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Tuple[str, Optional[str]]:
        """
        One-stop method: Listens to device microphone until user finishes speaking,
        saves audio, and returns (transcribed_text, audio_filepath).
        """
        wav_path = self.record_until_silence(
            max_duration=max_duration,
            device_index=device_index,
            progress_callback=progress_callback
        )
        if not wav_path:
            return "", None

        text = self.transcribe_audio_file(wav_path, language=language)
        return text, wav_path
