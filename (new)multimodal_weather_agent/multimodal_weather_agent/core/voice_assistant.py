"""
Interactive Voice Assistant Engine for MausamVani.
Enables full-duplex voice interactions (Voice Query In -> Gemini Reasoning & Agentic RAG -> Gemini TTS Audio Out).
"""
import os
import sys
import time
from typing import Optional, Dict, Any

from config import AgentConfig
from schemas.weather_schemas import MultimodalInput, AgentResponse
from core.agent import MultimodalWeatherAgent


class MausamVaniVoiceAssistant:
    """Full-duplex conversational voice assistant for farmers and rural communities."""

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        self.agent = MultimodalWeatherAgent(config=self.config)
        self.active_voice = self.config.gemini_voice or "Puck"
        self.language = "hi"  # Default Hindi for rural accessibility

    def set_voice_persona(self, voice_name: str):
        """Set Gemini prebuilt voice persona (Puck, Charon, Kore, Fenrir, Aoede)."""
        self.active_voice = voice_name
        self.config.gemini_voice = voice_name

    def set_language(self, lang_code: str):
        """Set user interaction language ('hi', 'te', 'ta', 'mr', 'en', etc.)."""
        self.language = lang_code

    def speak_and_respond(
        self,
        voice_query_text: Optional[str] = None,
        audio_input_path: Optional[str] = None,
        language: Optional[str] = None,
        crop: Optional[str] = None,
        location: Optional[str] = None
    ) -> AgentResponse:
        """
        Process a voice or text query and generate synchronized spoken audio output.
        """
        target_lang = language or self.language
        
        input_data = MultimodalInput(
            text_query=voice_query_text,
            audio_path=audio_input_path,
            language_code=target_lang,
            location=location,
            crop=crop
        )

        # Process through full multimodal weather pipeline
        response = self.agent.process_query(input_data)

        # Determine speech text (translated regional or original)
        speech_text = response.translated_response or response.response_text
        
        # Synthesize audio with Gemini TTS
        audio_file = self.agent.audio_engine.synthesize_speech_gemini(
            text=speech_text,
            voice_name=self.active_voice,
            output_path=os.path.join(
                self.agent.audio_engine.audio_output_dir,
                f"assistant_voice_{target_lang}_{int(time.time())}.wav"
            )
        )
        if audio_file:
            response.audio_output_file = audio_file

        return response
