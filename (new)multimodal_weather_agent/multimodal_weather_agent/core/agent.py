"""
Unified Multimodal Weather & NWP AI Agent ('MausamVani').
Coordinates Live Weather (OpenWeather API), NWP Models, IMD Alerts, Agro-Advisory,
Agentic RAG (Qdrant), Indian Multilingual support, Google Gemini Reasoning & TTS, and Whisper Audio.
"""
import os
import re
import requests
from typing import Optional, Dict, Any, List

from config import AgentConfig
from schemas.weather_schemas import (
    MultimodalInput, AgentResponse, GeoLocation, CurrentWeather,
    DailyForecastItem, NWPForecast, CAPAlert, AgroAdvisory, ClimateTrendAnalysis
)
from tools.realtime_weather import RealtimeWeatherTool
from tools.nwp_engine import NWPEngine
from tools.alerts_engine import AlertsEngine
from tools.advisory_engine import AdvisoryEngine
from tools.historical_climate import HistoricalClimateAnalyzer
from rag.agentic_rag import AgenticRAGPipeline
from multimodal.multilingual import MultilingualEngine
from multimodal.audio_engine import AudioEngine
from multimodal.vision_engine import VisionEngine
from core.prompts import WEATHER_AGENT_SYSTEM_PROMPT, AGENT_SYNTHESIS_PROMPT
from utils.gpu_manager import GPUManager


class MultimodalWeatherAgent:
    """The central agent orchestrator coordinating all 8 weather, NWP, Agentic RAG, and multimodal capabilities."""

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        
        # Initialize Core Engines
        self.weather_tool = RealtimeWeatherTool(config=self.config)
        self.nwp_engine = NWPEngine(config=self.config)
        self.alerts_engine = AlertsEngine()
        self.advisory_engine = AdvisoryEngine()
        self.climate_analyzer = HistoricalClimateAnalyzer(config=self.config)
        self.agentic_rag = AgenticRAGPipeline(config=self.config)
        self.multilingual = MultilingualEngine(config=self.config)
        self.audio_engine = AudioEngine(config=self.config)
        self.vision_engine = VisionEngine(config=self.config)

    def _extract_location_and_crop(self, query: str) -> tuple[str, str]:
        """Extract target city and crop entities from user query."""
        loc = self.config.default_location_name
        crop = "Cotton"
        q_lower = query.lower()

        cities = [
            "delhi", "new delhi", "mumbai", "nagpur", "pune", "bengaluru",
            "hyderabad", "chennai", "coimbatore", "kolkata", "patna",
            "varanasi", "lucknow", "chandigarh", "ludhiana", "jaipur",
            "ahmedabad", "bhopal", "indore", "guwahati", "bhubaneswar"
        ]
        for c in cities:
            if c in q_lower:
                loc = c.title()
                break

        crops = ["cotton", "paddy", "rice", "wheat", "soybean", "mustard", "sugarcane", "maize"]
        for cr in crops:
            if cr in q_lower:
                crop = cr.capitalize()
                break

        return loc, crop

    def _call_gemini_llm(self, prompt: str) -> Optional[str]:
        """Call Google Gemini 3.6 Flash / 2.5 Flash API for high-speed cloud reasoning."""
        if not self.config.gemini_api_key:
            return None

        # Try gemini-3.6-flash then gemini-2.5-flash
        for model in ["gemini-3.6-flash", "gemini-2.5-flash"]:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.config.gemini_api_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "systemInstruction": {"parts": [{"text": WEATHER_AGENT_SYSTEM_PROMPT}]},
                    "generationConfig": {
                        "temperature": getattr(self.config, "gemini_temperature", 0.5),
                        "maxOutputTokens": self.config.max_tokens
                    }
                }
                resp = requests.post(url, json=payload, timeout=12)
                if resp.status_code == 200:
                    text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if text:
                        return text
            except Exception:
                continue
        return None

    def _call_ollama_llm(self, prompt: str) -> Optional[str]:
        """Call local Ollama LLM endpoint with GPU-accelerated layer offloading."""
        endpoint = f"{self.config.ollama_host}/api/generate"
        gpu_opts = GPUManager.get_ollama_gpu_options() if self.config.use_gpu else {"num_gpu": 0}
        
        options = {
            "temperature": self.config.temperature,
            "num_predict": self.config.max_tokens,
            **gpu_opts
        }
        
        payload = {
            "model": self.config.llm_model,
            "prompt": prompt,
            "system": WEATHER_AGENT_SYSTEM_PROMPT,
            "stream": False,
            "options": options
        }
        try:
            resp = requests.post(endpoint, json=payload, timeout=20)
            if resp.status_code == 200:
                return resp.json().get("response", "").strip()
        except Exception:
            pass
        return None

    def _call_llm(self, prompt: str) -> Optional[str]:
        """Dispatch LLM reasoning to Google Gemini (primary) or local Ollama."""
        # 1. Primary: Google Gemini API
        if self.config.gemini_api_key:
            gemini_res = self._call_gemini_llm(prompt)
            if gemini_res:
                return gemini_res

        # 2. Local Ollama LLM
        return self._call_ollama_llm(prompt)

    def process_query(self, input_data: MultimodalInput) -> AgentResponse:
        """
        End-to-end multimodal pipeline processing queries across text, audio, and visual inputs.
        Fulfills all 8 core requirements.
        """
        # Step 1: Voice Input Handling (Case 8: Voice-enabled interaction)
        query_text = input_data.text_query or ""
        is_voice_query = False
        if input_data.audio_path:
            is_voice_query = True
            transcribed = self.audio_engine.speech_to_text(input_data.audio_path, language=input_data.language_code)
            if transcribed:
                query_text = transcribed

        if not query_text and not input_data.image_path:
            query_text = "What is the current weather forecast and farming advisory?"

        # Step 2: Multilingual Language Detection (Case 6: Indian languages)
        user_lang = input_data.language_code
        if not user_lang or user_lang == "en":
            detected = self.multilingual.detect_language(query_text)
            if detected != "en":
                user_lang = detected

        # Step 3: Entity Extraction & Location Resolution (Case 5)
        extracted_loc, extracted_crop = self._extract_location_and_crop(query_text)
        target_location = input_data.location or extracted_loc
        target_crop = input_data.crop or extracted_crop

        # Step 4: Real-time Weather Information Retrieval (Case 1: OpenWeather + Open-Meteo)
        current_weather, forecasts = self.weather_tool.get_current_weather(target_location)
        geo = current_weather.location

        # Step 5: Numerical Weather Prediction (NWP) Diagnostics (Case 3: GFS/WRF)
        nwp_data = self.nwp_engine.get_nwp_diagnostics(geo)

        # Step 6: Extreme Weather Early Warnings (Case 4: IMD/NDMA CAP Standard)
        active_alerts = self.alerts_engine.evaluate_severe_weather_risks(
            geo=geo,
            current=current_weather,
            forecasts=forecasts,
            nwp=nwp_data
        )

        # Step 7: Location-based Agro-Advisories (Case 5: Spray window & ET0)
        agro_advisory = self.advisory_engine.generate_crop_advisory(
            current=current_weather,
            forecasts=forecasts,
            crop_name=target_crop,
            growth_stage="Vegetative / Flowering"
        )

        # Step 8: Multi-Decadal Historical Climate Trends (Case 7: Kaggle Dataset)
        climate_trends = None
        if any(w in query_text.lower() for w in ["climate", "history", "historical", "trend", "monsoon", "past", "decade"]):
            climate_trends = self.climate_analyzer.analyze_climate_trends(geo)

        # Step 9: Agentic RAG Knowledge Retrieval (Case 9: Qdrant Vector DB & IPCC AR6)
        rag_results = self.agentic_rag.execute_agentic_retrieval(query_text)
        rag_context = rag_results["synthesized_context"]
        sources = rag_results["sources"]

        # Step 10: Format Synthesis Prompt for LLM Reasoning (Case 2)
        alerts_desc = "\n".join([f"- [{a.severity}] {a.headline}: {a.instruction}" for a in active_alerts]) if active_alerts else "No active severe alerts (Normal conditions)."
        
        fc_lines = []
        for fc in forecasts[:3]:
            fc_lines.append(f"- {fc.date}: {fc.temp_min_c:.1f}°C to {fc.temp_max_c:.1f}°C, Rain: {fc.precipitation_sum_mm:.1f}mm ({fc.precipitation_probability_pct}%), Condition: {fc.weather_description}")
        fc_text = "\n".join(fc_lines) if fc_lines else "Forecast data available."

        aqi_str = f"AQI {current_weather.aqi} ({current_weather.aqi_category})" if current_weather.aqi else "Moderate"

        synthesis_prompt = AGENT_SYNTHESIS_PROMPT.format(
            location=f"{geo.name}, {geo.state or geo.country}",
            temperature=f"{current_weather.temperature_c:.1f}",
            apparent_temp=f"{current_weather.apparent_temperature_c:.1f}",
            humidity=f"{current_weather.relative_humidity_pct:.0f}",
            pressure=f"{current_weather.surface_pressure_hpa:.1f}",
            wind_speed=f"{current_weather.wind_speed_kmh:.1f}",
            wind_dir=f"{current_weather.wind_direction_deg:.0f}",
            wind_gusts=f"{current_weather.wind_gusts_kmh:.1f}",
            condition=current_weather.weather_description,
            wmo_code=current_weather.weather_code,
            aqi_info=aqi_str,
            nwp_model=nwp_data.model_name,
            cape=f"{nwp_data.cape_j_kg:.0f}",
            cin=f"{nwp_data.cin_j_kg:.0f}",
            geo_500=f"{nwp_data.geopotential_height_500hpa:.0f}",
            alerts_text=alerts_desc,
            crop_name=agro_advisory.crop_name,
            growth_stage=agro_advisory.growth_stage,
            spray_rec=agro_advisory.spray_recommendation,
            irrigation_rec=agro_advisory.irrigation_advice,
            pest_rec=agro_advisory.pest_disease_risk,
            forecast_summary=fc_text,
            rag_context=rag_context or "Standard IMD and ICAR agricultural guidelines apply.",
            user_query=query_text
        )

        llm_response = self._call_llm(synthesis_prompt)
        if not llm_response:
            # Deterministic fallback response synthesis
            llm_response = (
                f"### 🌤️ Weather & Agro-Meteorological Report for **{geo.name}**\n\n"
                f"**Current Conditions:** {current_weather.weather_description}, **{current_weather.temperature_c:.1f}°C** "
                f"(Feels like {current_weather.apparent_temperature_c:.1f}°C), Humidity: {current_weather.relative_humidity_pct:.0f}%, "
                f"Wind: {current_weather.wind_speed_kmh:.1f} km/h.\n\n"
                f"**🌀 NWP Diagnostics (GFS / WRF):** Convective Available Potential Energy (CAPE) is **{nwp_data.cape_j_kg:.0f} J/kg**. "
                f"{'Stable atmospheric column.' if nwp_data.cape_j_kg < 1000 else 'Moderate convective instability.'}\n\n"
                f"**⚠️ Severe Weather Warnings:** {alerts_desc}\n\n"
                f"**🌾 Agricultural Advisory ({agro_advisory.crop_name}):**\n"
                f"- **Pesticide Spray Window:** {agro_advisory.spray_recommendation}\n"
                f"- **Irrigation:** {agro_advisory.irrigation_advice}\n"
                f"- **Pest & Disease Advisory:** {agro_advisory.pest_disease_risk}\n"
            )

        # Step 11: Indic Regional Multilingual Translation (Case 6)
        translated_text = None
        if user_lang and user_lang != "en":
            translated_text = self.multilingual.translate_advisory(llm_response, user_lang)

        # Step 12: Speech Audio Synthesis (Case 8: Gemini TTS)
        audio_output_path = None
        if is_voice_query or input_data.audio_path:
            speech_source = translated_text if translated_text else llm_response
            # Strip markdown headers for audio
            clean_speech = re.sub(r"[#\*\_`]", "", speech_source)
            audio_output_path = self.audio_engine.synthesize_speech(
                text=clean_speech,
                language=user_lang or "en",
                output_filename=f"voice_response_{geo.name.lower()}_{user_lang}.wav"
            )

        return AgentResponse(
            response_text=llm_response,
            current_weather=current_weather,
            forecasts=forecasts,
            nwp_data=nwp_data,
            active_alerts=active_alerts,
            agro_advisory=agro_advisory,
            climate_trends=climate_trends,
            translated_response=translated_text,
            audio_output_file=audio_output_path,
            retrieval_sources=sources
        )
