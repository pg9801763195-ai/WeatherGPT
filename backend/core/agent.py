"""
Core Multimodal Weather AI Agent Orchestrator ("MausamVani").
Integrates the LLM-based Query Understanding Layer, multi-turn Conversation Memory,
Dynamic Location Resolution, NWP model engine (GFS/WRF), extreme hazard alerts, agro-advisories,
historical climate reanalysis, Agentic RAG, remote sensing vision, and neural Indic voice synthesis.
"""
import os
import re
import time
import concurrent.futures
from typing import Optional, Dict, Any, List, Tuple
import requests

from config import AgentConfig
from schemas.weather_schemas import (
    GeoLocation,
    CurrentWeather,
    DailyForecastItem,
    NWPModelForecast,
    ExtremeWeatherAlert,
    AgroAdvisory,
    HistoricalClimateTrend,
    MultimodalInput,
    AgentResponse,
    AlertSeverity,
    CanonicalIntent,
    ResolvedQuery
)
from core.query_understanding import (
    QueryUnderstandingEngine,
    StructuredQuery,
    QueryIntent,
    ConversationMemory
)
from tools.location_resolver import LocationResolver
from tools.realtime_weather import RealtimeWeatherTool
from tools.nwp_engine import NWPEngineTool
from tools.alerts_engine import ExtremeAlertsEngineTool
from tools.advisory_engine import AgroAdvisoryTool
from tools.historical_climate import HistoricalClimateTool
from rag.agentic_rag import AgenticRAGPipeline, AgenticRAGResult
from multimodal.vision_engine import WeatherVisionEngine
from multimodal.audio_engine import VoiceInteractionEngine
from multimodal.multilingual import IndicLanguageEngine
from core.prompts import WEATHER_AGENT_SYSTEM_PROMPT, AGENT_SYNTHESIS_PROMPT
from utils.gpu_manager import GPUManager


class MultimodalWeatherAgent:
    """The central agent orchestrator coordinating Query Understanding, tools, and response synthesis."""

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        
        # Initialize Sub-Engines & Tools
        self.query_engine = QueryUnderstandingEngine(self.config)
        self.location_resolver = LocationResolver(self.config)
        self.weather_tool = RealtimeWeatherTool(self.config)
        self.nwp_tool = NWPEngineTool(self.config)
        self.alerts_tool = ExtremeAlertsEngineTool(self.config)
        self.advisory_tool = AgroAdvisoryTool(self.config)
        self.climate_tool = HistoricalClimateTool(self.config)
        self.agentic_rag = AgenticRAGPipeline(self.config)
        self.vision_engine = WeatherVisionEngine(self.config)
        self.audio_engine = VoiceInteractionEngine(self.config)
        self.indic_engine = IndicLanguageEngine(self.config)

        # High-Performance Caches (300s TTL) keyed strictly by canonical location name
        self._weather_cache: Dict[str, Tuple[float, CurrentWeather, List[DailyForecastItem]]] = {}
        self._nwp_cache: Dict[str, Tuple[float, NWPModelForecast]] = {}
        self._advisory_cache: Dict[str, Tuple[float, AgroAdvisory]] = {}

    def _fetch_weather_parallel(self, location_name: str, target_crop: str) -> Tuple[CurrentWeather, List[DailyForecastItem], NWPModelForecast, AgroAdvisory]:
        """Fetch all meteorological telemetry concurrently in parallel with a 300-second cache."""
        now = time.time()
        loc_key = location_name.strip().lower()
        
        weather_data = self._weather_cache.get(loc_key)
        if weather_data and (now - weather_data[0] < 300.0):
            w_res, fc_res = weather_data[1], weather_data[2]
            future_weather = None
        else:
            w_res, fc_res = None, None
            future_weather = True

        nwp_data = self._nwp_cache.get(loc_key)
        if nwp_data and (now - nwp_data[0] < 300.0):
            nwp_res = nwp_data[1]
            future_nwp = None
        else:
            nwp_res = None
            future_nwp = True

        agro_key = f"{loc_key}_{target_crop.strip().lower()}"
        agro_data = self._advisory_cache.get(agro_key)
        if agro_data and (now - agro_data[0] < 300.0):
            agro_res = agro_data[1]
            future_agro = None
        else:
            agro_res = None
            future_agro = True

        # Execute missing fetches concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            task_w = executor.submit(self.weather_tool.get_current_weather, location_name) if future_weather else None
            task_nwp = executor.submit(self.nwp_tool.analyze_nwp_forecast, location_name) if future_nwp else None
            task_agro = executor.submit(self.advisory_tool.generate_advisory, location_name, target_crop) if future_agro else None

            if task_w:
                w_res, fc_res = task_w.result()
                self._weather_cache[loc_key] = (now, w_res, fc_res)

            if task_nwp:
                nwp_res = task_nwp.result()
                self._nwp_cache[loc_key] = (now, nwp_res)

            if task_agro:
                agro_res = task_agro.result()
                self._advisory_cache[agro_key] = (now, agro_res)

        return w_res, fc_res, nwp_res, agro_res

    def _call_llm_synthesis(
        self,
        prompt: str,
        system_prompt: str = WEATHER_AGENT_SYSTEM_PROMPT
    ) -> Optional[str]:
        """
        Attempts LLM synthesis via available providers (Gemini, Groq, OpenAI, Ollama).
        Returns None if no LLM service is available or responsive.
        """
        # 1. Google Gemini API (if GEMINI_API_KEY is present)
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
                payload = {
                    "contents": [{"parts": [{"text": f"{system_prompt}\n\n{prompt}"}]}],
                    "generationConfig": {"temperature": 0.3, "maxOutputTokens": 800}
                }
                resp = requests.post(url, json=payload, timeout=5.0)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts and "text" in parts[0]:
                            return parts[0]["text"].strip()
            except Exception as e:
                _safe_log("GEMINI SYNTHESIS ERROR", str(e))

        # 2. Groq API (if GROQ_API_KEY is present)
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
                payload = {
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 800
                }
                resp = requests.post(url, json=payload, headers=headers, timeout=5.0)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"].strip()
            except Exception as e:
                _safe_log("GROQ SYNTHESIS ERROR", str(e))

        # 3. Local Ollama (if running)
        if hasattr(self.query_engine, "_is_ollama_alive") and self.query_engine._is_ollama_alive():
            try:
                url = f"{self.config.ollama_host}/api/generate"
                payload = {
                    "model": self.config.llm_model,
                    "prompt": f"{system_prompt}\n\n{prompt}",
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 512}
                }
                resp = requests.post(url, json=payload, timeout=2.0)
                if resp.status_code == 200:
                    return resp.json().get("response", "").strip()
            except Exception:
                pass

        return None

    def _generate_structured_response(
        self,
        resolved_query: ResolvedQuery,
        weather: Optional[CurrentWeather] = None,
        forecasts: Optional[List[DailyForecastItem]] = None,
        nwp: Optional[NWPModelForecast] = None,
        alerts: Optional[List[ExtremeWeatherAlert]] = None,
        advisory: Optional[AgroAdvisory] = None,
        climate: Optional[HistoricalClimateTrend] = None
    ) -> str:
        """
        Synthesizes natural, authoritative responses grounded in real meteorological telemetry.
        Uses intelligent LLM synthesis if available, with a deep universal multi-domain reasoning fallback.
        """
        city = resolved_query.location or (weather.location.name if weather else "your location")
        raw_q = (resolved_query.entities.get("raw_query") or "").strip()
        raw_q_lower = raw_q.lower()
        lang = resolved_query.language

        # Extract Telemetry Metrics
        temp = f"{weather.temperature_c:.1f}°C" if weather else "24.0°C"
        temp_val = weather.temperature_c if weather else 24.0
        feels_like = f"{weather.apparent_temperature_c:.1f}°C" if weather and weather.apparent_temperature_c else temp
        cond = weather.weather_description.lower() if weather else "clear sky"
        precip = weather.precipitation_mm if weather else 0.0
        humid = weather.relative_humidity_pct if weather else 70.0
        wind = f"{weather.wind_speed_kmh:.0f} km/h" if weather else "10 km/h"
        wind_val = weather.wind_speed_kmh if weather else 10.0
        uv = weather.uv_index if weather and weather.uv_index is not None else 4.0
        pressure = f"{weather.surface_pressure_hpa:.0f} hPa" if weather and weather.surface_pressure_hpa else "1012 hPa"
        visibility = f"{weather.visibility_km:.1f} km" if weather and weather.visibility_km else "10.0 km"
        cloud_cover = weather.cloud_cover_pct if weather and weather.cloud_cover_pct is not None else 30.0
        is_raining = precip > 0 or "rain" in cond or "drizzle" in cond or "shower" in cond or "thunderstorm" in cond
        crop = resolved_query.crop or (advisory.target_crop if advisory else "Paddy")

        fc_tomorrow = forecasts[1] if forecasts and len(forecasts) > 1 else (forecasts[0] if forecasts else None)
        fc_day_after = forecasts[2] if forecasts and len(forecasts) > 2 else None
        time_ref = resolved_query.time_reference or "today"

        # -------------------------------------------------------------
        # 1. ATTEMPT FULL LLM SYNTHESIS (Gemini / Groq / Ollama)
        # -------------------------------------------------------------
        fc_summary = ""
        if forecasts:
            fc_lines = [f"{f.date}: {f.weather_description}, High {f.temp_max_c:.0f}°C / Low {f.temp_min_c:.0f}°C, Rain {f.precipitation_probability_pct}%" for f in forecasts[:5]]
            fc_summary = "\n".join(fc_lines)

        lang_map = {
            "en": "English",
            "hi": "pure Devanagari Hindi (हिन्दी)",
            "hinglish": "Romanized Hinglish (Hindi written in English letters)",
            "or": "pure Odia (ଓଡ଼ିଆ script)",
            "bn": "pure Bengali (বাংলা script)",
            "te": "pure Telugu (తెలుగు script)",
            "ta": "pure Tamil (தமிழ் script)",
            "mr": "pure Marathi (मराठी script)",
            "gu": "pure Gujarati (ગુજરાતી script)",
            "kn": "pure Kannada (ಕನ್ನಡ script)",
            "ml": "pure Malayalam (മലയാളം script)",
            "pa": "pure Punjabi (ਪੰਜਾਬੀ script)"
        }
        lang_target_desc = lang_map.get(lang, "natural English")

        llm_prompt = f"""User Question: "{raw_q}"
Location: {city}
Language to reply in: {lang_target_desc}

CRITICAL LANGUAGE REQUIREMENT:
The user query is in {lang_target_desc}. You MUST write your entire response strictly in {lang_target_desc}.
If the language is Odia (or), write the full response in natural Odia script (ଓଡ଼ିଆ).
If Hindi (hi), write in pure Devanagari Hindi.
If Hinglish, write in conversational Hinglish.
Do NOT default to English unless the language is 'en'.

Real-Time Telemetry Data:
- Temperature: {temp} (Feels like: {feels_like})
- Sky Condition: {cond}
- Active Rain: {precip:.1f} mm/h (Is raining: {is_raining})
- Humidity: {humid:.0f}%
- Wind Speed: {wind}
- UV Index: {uv:.1f}
- Atmospheric Pressure: {pressure}
- Cloud Cover: {cloud_cover:.0f}%
- Visibility: {visibility}

Forecast for Upcoming Days:
{fc_summary}

Instructions:
1. Directly and accurately answer the user's question in {lang_target_desc} based on the real weather data.
2. Provide practical, scenario-specific reasoning (e.g., if asking about rain/umbrella, drone flying, travel, workout, etc.).
3. Do NOT make up arbitrary numbers. Use emojis and clear markdown bullet points.
"""
        llm_response = self._call_llm_synthesis(llm_prompt)
        if llm_response and len(llm_response) > 20:
            return llm_response

        # -------------------------------------------------------------
        # 2. UNIVERSAL MULTI-DOMAIN REASONING ENGINE (High-Precision Fallback)
        # -------------------------------------------------------------

        # A. Drone Flying / UAV / Aeromodelling
        if any(w in raw_q_lower for w in ["drone", "fly drone", "flying drone", "uav", "quadcopter"]):
            if is_raining or wind_val > 28.0:
                if lang == "hi":
                    return f"🚁 **आज {city} में ड्रोन उड़ाना सुरक्षित नहीं है!**\n\n• **कारण:** {'बारिश हो रही है' if is_raining else f'हवा की गति तेज है ({wind})'}।\n• **सुरक्षा सलाह:** ड्रोन के मोटर्स व इलेक्ट्रॉनिक्स को सुरक्षित रखने के लिए मौसम साफ़ और हवा शांत (<20 km/h) होने तक प्रतीक्षा करें।"
                elif lang == "hinglish":
                    return f"🚁 **Aaj {city} mein drone fly karna safe nahi hai!**\n\n• **Reason:** {'Abhi barish chal rahi hai' if is_raining else f'Hawa ki speed tez hai ({wind})'}। Drone control khone ya damage ka risk hai. Wind calm hone ka wait karein."
                return f"🚁 **Not recommended to fly a drone in {city} right now!**\n\n• **Hazard:** {'Active precipitation will damage electronic motors.' if is_raining else f'Wind speeds at {wind} exceed safe operational stability for consumer drones.'}\n• **Safety Window:** Wait for winds under 20 km/h and dry skies."
            else:
                if lang == "hi":
                    return f"🚁 **हाँ! {city} में ड्रोन उड़ाने के लिए मौसम अनुकूल है!**\n\n• **हवा की गति:** {wind} (स्थिर व सुरक्षित)\n• **दृश्यता (Visibility):** {visibility} · बादल: {cloud_cover:.0f}%\n• **सलाह:** लाइन-ऑफ-साइट बनाए रखें और बैटरी तापमान पर ध्यान दें।"
                elif lang == "hinglish":
                    return f"🚁 **Haan! Aaj {city} mein drone uda sakte hain!**\n\n• **Wind Speed:** {wind} (safe & stable)\n• **Visibility:** {visibility} · Cloud cover: {cloud_cover:.0f}%\n• Safe flying conditions available."
                return f"🚁 **Good conditions for drone flying in {city}!**\n\n• **Wind Speed:** {wind} (within safe limits < 25 km/h)\n• **Visibility:** {visibility} · Cloud cover: {cloud_cover:.0f}%\n• Skies are favorable for aerial photography and flight stability."

        # B. Stargazing / Astronomy / Night Sky
        if any(w in raw_q_lower for w in ["stargaze", "stargazing", "stars", "telescope", "astronomy", "night sky", "तारों", "आकाश"]):
            if cloud_cover > 50.0 or is_raining:
                if lang == "hi":
                    return f"🔭 **आज रात {city} में तारे देखना (Stargazing) कठिन होगा।**\n\n• **बादल आवरण:** {cloud_cover:.0f}% ({cond})\n• **आर्द्रता:** {humid:.0f}%\n• बादलों के कारण आकाशीय पिंड स्पष्ट दिखाई नहीं देंगे।"
                elif lang == "hinglish":
                    return f"🔭 **Aaj raat {city} mein stargazing karna mushkil hoga.**\n\n• **Cloud Cover:** {cloud_cover:.0f}% ({cond})\n• Sky overcast hone ke karan stars aur planets clear nahi dikhenge."
                return f"🔭 **Poor conditions for stargazing in {city} tonight.**\n\n• **Cloud Cover:** {cloud_cover:.0f}% ({cond})\n• **Humidity:** {humid:.0f}%\n• Dense cloud cover will obstruct telescope and naked-eye celestial visibility."
            else:
                if lang == "hi":
                    return f"✨ **आज रात {city} में तारे देखने के लिए बेहतरीन रात है!**\n\n• **आसमान:** साफ़ ({cloud_cover:.0f}% बादल)\n• **दृश्यता:** {visibility}\n• टेलिस्कोप और खगोलीय अवलोकन के लिए परिस्थितियां आदर्श हैं।"
                elif lang == "hinglish":
                    return f"✨ **Aaj raat {city} mein stargazing ke liye perfect mausam hai!**\n\n• **Sky:** Clear ({cloud_cover:.0f}% clouds)\n• **Visibility:** {visibility}\n• Stars, constellations aur planets clear nazar aayenge."
                return f"✨ **Excellent stargazing conditions in {city} tonight!**\n\n• **Cloud Cover:** Minimal ({cloud_cover:.0f}%)\n• **Atmospheric Visibility:** {visibility}\n• Clear atmospheric columns provide optimal clarity for astronomy and astrophotography."

        # C. Painting / Exterior Staining / House Coating
        if any(w in raw_q_lower for w in ["paint", "painting", "stain", "coating", "color my house", "रंग-रोगन"]):
            if is_raining or humid > 75.0 or (forecasts and forecasts[0].precipitation_probability_pct > 35):
                if lang == "hi":
                    return f"🎨 **आज {city} में घर या दीवार पर पेंट न करें!**\n\n• **कारण:** हवा में नमी {humid:.0f}% है और बारिश का जोखिम है।\n• पेंट ठीक से नहीं सूखेगा और धब्बे पड़ सकते हैं। पेंटिंग के लिए नमी <70% और सूखा मौसम आवश्यक है।"
                elif lang == "hinglish":
                    return f"🎨 **Aaj {city} mein paint ka kaam mat karwao!**\n\n• **Humidity:** {humid:.0f}% aur barish ka risk hai. Paint dry hone mein dikkat hogi aur finishing kharab ho sakti hai."
                return f"🎨 **Do not paint exterior walls or surfaces in {city} today!**\n\n• **Risk:** High humidity ({humid:.0f}%) and active/forecast precipitation will ruin paint curing and adhesion.\n• **Recommendation:** Wait for a 48-hour dry window with humidity under 70%."
            else:
                if lang == "hi":
                    return f"🎨 **हाँ, आज {city} में पेंटिंग का काम किया जा सकता है!**\n\n• **तापमान:** {temp} · आर्द्रता: {humid:.0f}%\n• मौसम सूखा है जिससे पेंट समय पर सूख जाएगा।"
                elif lang == "hinglish":
                    return f"🎨 **Haan, aaj {city} mein paint karwane ke liye badhiya din hai!** Mausam dry hai ({humid:.0f}% humidity) aur dhoop acchi hai."
                return f"🎨 **Favorable conditions for painting in {city} today!**\n\n• **Temperature:** {temp} · **Humidity:** {humid:.0f}%\n• Dry atmospheric conditions provide ideal paint drying and surface curing."

        # D. Hair Frizz / Humidity Comfort / Skin
        if any(w in raw_q_lower for w in ["frizz", "hair", "skin", "sweaty", "chipchip", "chiphcipa", "बाल", "चिपचिपा"]):
            if humid >= 70.0:
                if lang == "hi":
                    return f"💇 **आज {city} में अत्यधिक चिपचिपापन व उमस है!**\n\n• **आर्द्रता:** **{humid:.0f}%** (तापमान: {temp}, अहसास: {feels_like})\n• **सुझाव:** बालों में फ्रिज़ (frizz) बढ़ सकता है। एंटी-फ्रिज़ सीरम का उपयोग करें और सूती कपड़े पहनें।"
                elif lang == "hinglish":
                    return f"💇 **Aaj {city} mein kaafi humidity aur chipchipapan hai!**\n\n• **Humidity:** **{humid:.0f}%** (Feels like: {feels_like})\n• High moisture ki wajah se baal frizzy ho sakte hain. Hydrate rahein aur lightweight clothes pehnein."
                return f"💇 **High humidity alert for {city} today!**\n\n• **Relative Humidity:** **{humid:.0f}%** (Feels like: {feels_like})\n• Elevated atmospheric moisture increases hair frizz and sweat evaporation resistance. Anti-frizz products and breathable cotton wear recommended."
            else:
                if lang == "hi":
                    return f"💇 **आज {city} में उमस सामान्य है ({humid:.0f}%)।** बाल और त्वचा के लिए मौसम आरामदायक है।"
                elif lang == "hinglish":
                    return f"💇 **Aaj {city} mein humidity normal hai ({humid:.0f}%)।** Mausam comfortable rahega."
                return f"💇 **Comfortable humidity levels in {city} today ({humid:.0f}%).** Low frizz risk and pleasant ambient air comfort."

        # E. UV Radiation / Sunscreen / Sunburn
        if any(w in raw_q_lower for w in ["uv", "sunscreen", "sunburn", "tan", "tanning", "धूप", "सनस्क्रीन"]):
            uv_advice_en = "Apply SPF 30+ sunscreen, wear UV-blocking sunglasses, and limit direct exposure between 11 AM – 3 PM." if uv >= 6.0 else "Minimal UV hazard; standard skincare is sufficient."
            if lang == "hi":
                return f"☀️ **{city} में यूवी (UV) इंडेक्स रिपोर्ट:**\n\n• **वर्तमान UV इंडेक्स:** **{uv:.1f}** ({'अत्यधिक / तीव्र' if uv >= 6.0 else 'सामान्य'})\n• **सुझाव:** {'SPF 30+ सनस्क्रीन लगाएं, धूप का चश्मा पहनें और दोपहर में सीधी धूप से बचें।' if uv >= 6.0 else 'यूवी जोखिम कम है, सामान्य रूप से बाहर निकल सकते हैं।'}"
            elif lang == "hinglish":
                return f"☀️ **{city} UV Index Status:**\n\n• **Current UV Level:** **{uv:.1f}** ({'High' if uv >= 6.0 else 'Moderate'})\n• **Tip:** {'SPF 30+ sunscreen lagayein aur dopeher ki tez dhoop se bachein.' if uv >= 6.0 else 'UV risk normal hai.'}"
            return f"☀️ **UV Radiation Index for {city}:**\n\n• **Current UV Level:** **{uv:.1f}** ({'High Solar Intensity' if uv >= 6.0 else 'Low-to-Moderate'})\n• **Action:** {uv_advice_en}"

        # F. Barometric Pressure / Headache / Joint Pain / Migraines
        if any(w in raw_q_lower for w in ["pressure", "headache", "migraine", "joint pain", "barometric", "सिरदर्द"]):
            if lang == "hi":
                return f"🩺 **{city} में वायुमंडलीय दबाव (Barometric Pressure):**\n\n• **वर्तमान दबाव:** **{pressure}** ({cond})\n• **मौसम प्रभाव:** मौसम प्रणाली में बदलाव और नमी ({humid:.0f}%) के कारण संवेदनशील लोगों में हल्का सिरदर्द या माइग्रेन ट्रिगर हो सकता है। हाइड्रेटेड रहें।"
            elif lang == "hinglish":
                return f"🩺 **{city} Atmospheric Pressure:**\n\n• **Current Pressure:** **{pressure}**\n• Weather shifts aur high humidity ({humid:.0f}%) se migraine ya sinus pressure feel ho sakta hai. Plenty of water piyein."
            return f"🩺 **Barometric Pressure & Health Context for {city}:**\n\n• **Surface Pressure:** **{pressure}** with **{cond}** skies\n• **Physiological Impact:** Rapid barometric fluctuations and high humidity ({humid:.0f}%) can influence sinus and migraine sensitivities. Stay well-hydrated and rest in well-ventilated spaces."

        # G. Cycling / Biking / Motorcycle
        if any(w in raw_q_lower for w in ["cycle", "cycling", "bike", "biking", "motorcycle", "राइड"]):
            if is_raining or wind_val > 30.0:
                if lang == "hi":
                    return f"🚴 **आज {city} में साइकिल या बाइक राइडिंग करते समय सतर्क रहें!**\n\n• **कारण:** {'सड़कें गीली हैं (बारिश जारी है)' if is_raining else f'तेज हवा ({wind})'}\n• ब्रेक लगाने की दूरी बढ़ जाएगी। धीमी गति में चलें और वाटरप्रूफ गियर पहनें।"
                elif lang == "hinglish":
                    return f"🚴 **{city} mein cycling/bike ride ke waqt caution rakhein!**\n\n• Roads geeli hain aur wind **{wind}** chal rahi hai. Helmet aur rain gear zaroor use karein."
                return f"🚴 **Adverse cycling and motorcycling conditions in {city}!**\n\n• **Conditions:** {'Wet asphalt and reduced tire braking grip.' if is_raining else f'High crosswinds at {wind}.'}\n• Wear high-visibility gear, allow increased stopping distance, and reduce cornering speeds."
            else:
                if lang == "hi":
                    return f"🚴 **हाँ, आज {city} में साइकिल या बाइक राइडिंग के लिए बढ़िया मौसम है!** तापमान {temp} और हवा {wind} है।"
                elif lang == "hinglish":
                    return f"🚴 **Haan, aaj {city} mein cycling ke liye accha mausam hai!** Temperature {temp} aur smooth roads hain."
                return f"🚴 **Great conditions for cycling and motorcycling in {city}!** Temperature is **{temp}** with dry road surfaces and manageable winds ({wind})."

        # H. Swimming / Pool / Beach
        if any(w in raw_q_lower for w in ["swim", "swimming", "pool", "beach", "तैराकी"]):
            if "thunderstorm" in cond or is_raining:
                if lang == "hi":
                    return f"🏊 **आज {city} में आउटडोर स्विमिंग बिल्कुल न करें!**\n\n• **खतरा:** बिजली कड़कने (Lightning) और बारिश का जोखिम है। खुले पानी में बिजली गिरने का खतरा सबसे ज्यादा होता है।"
                elif lang == "hinglish":
                    return f"🏊 **Aaj outdoor swimming bilkul mat karein!** Thunderstorm aur lightning ke dauran open water mein jana jaanleva ho sakta hai."
                return f"🏊 **Hazardous for outdoor swimming in {city} today!**\n\n• **Critical Hazard:** Active thunderstorm/lightning conditions present severe electrical conduction risks in open water. Remain indoors."
            else:
                if lang == "hi":
                    return f"🏊 **हाँ, आज {city} में स्विमिंग के लिए मौसम अच्छा है!** तापमान **{temp}** है।"
                elif lang == "hinglish":
                    return f"🏊 **Haan, aaj swimming ke liye pleasant weather hai!** Temperature {temp} hai."
                return f"🏊 **Favorable conditions for swimming in {city}!** Water and air temperatures are comfortable at **{temp}** with no convective lightning hazards."

        # I. Lawn Mowing / Yard Maintenance
        if any(w in raw_q_lower for w in ["lawn", "mow", "mowing", "grass", "घास"]):
            if is_raining or (forecasts and forecasts[0].precipitation_probability_pct > 40):
                if lang == "hi":
                    return f"🚜 **आज {city} में घास (Lawn) न काटें!**\n\n• **कारण:** गीली घास काटने से मशीन जाम हो सकती है और घास की जड़ें उखड़ सकती हैं। घास पूरी तरह सूखने की प्रतीक्षा करें।"
                elif lang == "hinglish":
                    return f"🚜 **Aaj lawn mow mat karein!** Geeli ghaas katne se blades choke ho sakti hain aur lawn kharab ho sakta hai."
                return f"🚜 **Skip lawn mowing in {city} today!**\n\n• **Reason:** Wet turf tears unevenly and clogs mower decks. Wait for a dry afternoon when grass blades are completely crisp and dry."
            else:
                if lang == "hi":
                    return f"🚜 **हाँ, आज {city} में लॉन काटने के लिए उपयुक्त दिन है!** मौसम सूखा और साफ़ है।"
                elif lang == "hinglish":
                    return f"🚜 **Haan, aaj lawn mowing ke liye badhiya din hai!**"
                return f"🚜 **Good day for lawn mowing in {city}!** Turf conditions are dry with clear skies."

        # J. Home Ventilation / Open Windows
        if any(w in raw_q_lower for w in ["window", "windows", "ventilate", "ventilation", "खिड़की"]):
            if is_raining or wind_val > 35.0:
                if lang == "hi":
                    return f"🪟 **आज {city} में खिड़कियां बंद रखें!** बारिश की बौछारें और तेज हवा ({wind}) अंदर आ सकती हैं।"
                elif lang == "hinglish":
                    return f"🪟 **Khidkiyan band rakhein!** Barish aur hawa ({wind}) se paani andar aa sakta hai."
                return f"🪟 **Keep windows closed in {city} right now!** Active rain and wind gusts ({wind}) will drive moisture indoors."
            else:
                if lang == "hi":
                    return f"🪟 **हाँ, आज {city} में खिड़कियां खोलकर ताजी हवा ले सकते हैं!** तापमान **{temp}** और हवा {wind} की गति से चल रही है।"
                elif lang == "hinglish":
                    return f"🪟 **Haan, windows open karke fresh breeze enjoy kar sakte hain!**"
                return f"🪟 **Great day to open windows and ventilate in {city}!** Pleasant temperatures at **{temp}** with gentle air circulation ({wind})."

        # K. Solar Panel Generation
        if any(w in raw_q_lower for w in ["solar", "panel", "generation", "सौर"]):
            yield_pct = max(10, int(100 - (cloud_cover * 0.75)))
            if lang == "hi":
                return f"☀️ **{city} में सोलर पैनल दक्षता अनुमान:**\n\n• **बादल आवरण:** {cloud_cover:.0f}%\n• **अनुमानित उत्पादन:** सामान्य का **~{yield_pct}%**\n• { 'बादलों के कारण सोलर उत्पादन में गिरावट रहेगी।' if cloud_cover > 50 else 'साफ़ धूप के कारण सोलर जनरेशन उच्चतम स्तर पर रहेगा।' }"
            elif lang == "hinglish":
                return f"☀️ **Solar Power Generation Estimate for {city}:**\n\n• **Cloud Cover:** {cloud_cover:.0f}%\n• **Estimated Output:** **~{yield_pct}%** of peak capacity."
            return f"☀️ **Solar Panel Generation Outlook for {city}:**\n\n• **Cloud Cover:** {cloud_cover:.0f}%\n• **Estimated Yield Efficiency:** **~{yield_pct}%** of nominal peak capacity.\n• Solar irradiance is {'reduced due to cloud attenuation.' if cloud_cover > 50 else 'optimal for peak photovoltaic generation.'}"

        # L. Location Info Intent
        if resolved_query.intent == CanonicalIntent.LOCATION_INFO:
            if lang == "hi":
                return f"आप अभी **{city}** का मौसम देख रहे हैं।"
            elif lang == "hinglish":
                return f"Aap abhi **{city}** ka mausam dekh rahe hain."
            return f"You're currently viewing weather for **{city}**."

        # M. Casual Conversation
        if resolved_query.intent == CanonicalIntent.CASUAL_CONVERSATION:
            if any(w in raw_q_lower for w in ["joke", "funny", "laugh"]):
                return "Why did the cloud stay home from work? It was feeling a little under the weather! ☁️😄"
            if any(w in raw_q_lower for w in ["thank", "thanks", "thx", "shukriya", "dhanyawad"]):
                return "धन्यवाद! मौसम से जुड़ी कोई भी जानकारी चाहिए हो तो बेझिझक पूछें। 😊" if lang == "hi" else "You're very welcome! Always happy to help with meteorological insights. 😊"
            if any(w in raw_q_lower for w in ["who are you", "who made you", "help"]):
                return f"Hello! I am **WeatherGPT**, your intelligent AI meteorological assistant. I analyze real-time weather, NWP stability, commute safety, and outdoor planning for **{city}**."
            return f"Hello! I'm doing great. How can I help you with weather, forecasts, or outdoor plans in **{city}** today?"

        # N. Commute & Driving
        if resolved_query.intent == CanonicalIntent.TRAVEL_WEATHER or any(w in raw_q_lower for w in ["drive", "driving", "commute", "road", "traffic", "travel", "trip"]):
            if is_raining:
                if lang == "hi":
                    return f"🚗 **{city} में अभी ड्राइव करते समय सावधानी बरतें!**\n\n• सक्रिय बारिश ({precip:.1f} mm/h) और {cond} के कारण सड़कों पर फिसलन है।\n• हेडलाइट्स जलाएं, आगे वाले वाहन से सुरक्षित दूरी रखें और 10-15 मिनट अतिरिक्त समय लेकर चलें।"
                elif lang == "hinglish":
                    return f"🚗 **{city} mein drive/commute karte waqt caution rakhein!**\n\n• Barish ({precip:.1f} mm/h) ke karan roads slippery hain. Safe speed aur extra distance maintain karein."
                return f"🚗 **Exercise caution while driving or commuting in {city} right now!**\n\n• Active rain ({precip:.1f} mm/h) and **{cond}** skies reduce tire traction.\n• Maintain safe following distances, switch on low-beam headlights, and allow 10–15 extra minutes for your commute."
            else:
                if lang == "hi":
                    return f"🚗 **हाँ, अभी {city} में ड्राइव करना और यात्रा करना पूरी तरह सुरक्षित है!**\n\n• मौसम साफ़ है ({temp}), सड़कें सूखी हैं और दृश्यता {visibility} है।"
                elif lang == "hinglish":
                    return f"🚗 **Haan, abhi {city} mein drive karna bilkul safe hai!** Mausam saaf hai ({temp}) aur visibility {visibility} hai."
                return f"🚗 **Yes, it is safe to drive and commute in {city} right now!**\n\n• Skies are **{cond}** with dry road conditions, clear visibility ({visibility}), and comfortable temperatures (**{temp}**)."

        # O. Walk / Workout / Running
        if resolved_query.intent == CanonicalIntent.OUTDOOR_ACTIVITY or any(w in raw_q_lower for w in ["walk", "workout", "run", "running", "jog", "exercise", "fitness", "cricket"]):
            if any(w in raw_q_lower for w in ["cricket"]):
                if is_raining:
                    return f"🏏 Not suitable for cricket in **{city}** right now — rain is active ({temp}) and the pitch/outfield will be wet."
                return f"🏏 Great conditions for cricket in **{city}**! Temperature is **{temp}** with {cond} skies."
            if lang == "hi":
                return f"🏃 **आज {city} में वॉक या कसरत के लिए सबसे अच्छा समय:**\n\n• **सर्वोत्तम समय:** **सुबह (6:00 AM – 8:30 AM)** या **शाम (5:30 PM – 7:30 PM)**\n• **वर्तमान स्थिति:** तापमान **{temp}** (अहसास: {feels_like}), आर्द्रता **{humid:.0f}%**, हवा **{wind}**\n• **सलाह:** {'दोपहर की धूप से बचें और पर्याप्त पानी पिएं।' if temp_val > 28 else 'मौसम बाहरी कसरत के लिए अनुकूल है।'}"
            elif lang == "hinglish":
                return f"🏃 **Aaj {city} mein walk ya workout ke liye best time:**\n\n• **Optimal Windows:** **Morning (6:00 AM – 8:30 AM)** ya **Evening (5:30 PM – 7:30 PM)**\n• **Telemetry:** Temp **{temp}**, Humidity **{humid:.0f}%**, Wind **{wind}**."
            return f"🏃 **Best time for a walk or outdoor workout in {city} today:**\n\n• **Optimal Windows:** **Early Morning (6:00 AM – 8:30 AM)** or **Late Evening (5:30 PM – 7:30 PM)**\n• **Current Telemetry:** Temperature **{temp}** (Feels like: {feels_like}), humidity **{humid:.0f}%**, wind **{wind}**.\n• **Recommendation:** {'Stay well-hydrated and avoid peak midday solar heat.' if temp_val > 28 else 'Weather is favorable for outdoor fitness and walking.'}"

        # P. Gardening & Plant Watering
        if resolved_query.intent == CanonicalIntent.AGRO_ADVISORY or any(w in raw_q_lower for w in ["garden", "gardening", "plant", "plants", "water", "watering", "crop", "spray"]):
            if any(w in raw_q_lower for w in ["spray", "pesticide", "fertilizer"]):
                if is_raining:
                    return f"🌧️ **Hold off on spraying chemicals in {city} today!** Rain ({precip:.1f} mm/h) will wash away applied treatments."
                return f"✅ **Suitable window for spraying in {city} today!** Skies are dry ({temp}), wind is gentle ({wind})."
            if is_raining or (forecasts and forecasts[0].precipitation_probability_pct > 50):
                rain_pct = forecasts[0].precipitation_probability_pct if forecasts else 75
                if lang == "hi":
                    return f"🌱 **आज {city} में पौधों को पानी देने की आवश्यकता नहीं है!**\n\n• बारिश की संभावना सक्रिय है ({rain_pct}%), जिससे मिट्टी में प्राकृतिक नमी बनी रहेगी।\n• अतिरिक्त पानी से जड़ों में पानी भरने (waterlogging) का जोखिम हो सकता है।"
                elif lang == "hinglish":
                    return f"🌱 **Aaj {city} mein paudho ko paani mat daalo!** Rain chances {rain_pct}% hain jisse soil naturally moist rahegi."
                return f"🌱 **Hold off on outdoor watering in {city} today!**\n\n• Rain is active or expected ({rain_pct}% chance), providing natural soil hydration.\n• Additional watering risks over-saturating the roots."
            else:
                if lang == "hi":
                    return f"🌱 **हाँ, आज {city} में पौधों को पानी देने के लिए अच्छा दिन है!** सुबह या शाम के समय पानी दें। तापमान **{temp}** है।"
                elif lang == "hinglish":
                    return f"🌱 **Haan, aaj {city} mein paudho ko paani dene ke liye accha din hai!** Morning ya evening mein dalein."
                return f"🌱 **Yes, today is a good day for gardening and watering plants in {city}!**\n\n• Water during early morning or late afternoon to minimize evaporation. Current temperature is **{temp}** with **{humid:.0f}%** humidity."

        # Q. Weekend & Multi-Day Forecast
        if resolved_query.intent == CanonicalIntent.WEATHER_FORECAST or any(w in raw_q_lower for w in ["weekend", "tomorrow", "forecast", "upcoming", "week"]):
            if time_ref == "weekend" and forecasts and len(forecasts) >= 2:
                sat = forecasts[min(len(forecasts)-2, 1)]
                sun = forecasts[min(len(forecasts)-1, 2)]
                if lang == "hi":
                    return f"📅 **इस वीकेंड {city} का मौसम पूर्वानुमान:**\n\n• **शनिवार:** {sat.weather_description} · तापमान **{sat.temp_max_c:.0f}°C / {sat.temp_min_c:.0f}°C** · बारिश: **{sat.precipitation_probability_pct}%**\n• **रविवार:** {sun.weather_description} · तापमान **{sun.temp_max_c:.0f}°C / {sun.temp_min_c:.0f}°C** · बारिश: **{sun.precipitation_probability_pct}%**\n\nवीकेंड योजनाओं के लिए मौसम अनुकूल रहेगा!"
                elif lang == "hinglish":
                    return f"📅 **Is weekend {city} ka forecast:**\n\n• **Saturday:** {sat.weather_description} · Temp **{sat.temp_max_c:.0f}°C/{sat.temp_min_c:.0f}°C** · Rain: **{sat.precipitation_probability_pct}%**\n• **Sunday:** {sun.weather_description} · Temp **{sun.temp_max_c:.0f}°C/{sun.temp_min_c:.0f}°C** · Rain: **{sun.precipitation_probability_pct}%**"
                return f"📅 **Weekend Weather Outlook for {city}:**\n\n• **Saturday:** {sat.weather_description} · High/Low: **{sat.temp_max_c:.0f}°C / {sat.temp_min_c:.0f}°C** · Rain Risk: **{sat.precipitation_probability_pct}%**\n• **Sunday:** {sun.weather_description} · High/Low: **{sun.temp_max_c:.0f}°C / {sun.temp_min_c:.0f}°C** · Rain Risk: **{sun.precipitation_probability_pct}%**\n\nPlan your outdoor activities accordingly!"
            elif time_ref == "tomorrow" and fc_tomorrow:
                return f"📅 **Tomorrow's Forecast for {city}:**\n\n• Expected: **{fc_tomorrow.weather_description}**\n• High/Low: **{fc_tomorrow.temp_max_c:.1f}°C / {fc_tomorrow.temp_min_c:.1f}°C**\n• Rain Risk: **{fc_tomorrow.precipitation_probability_pct}%** ({fc_tomorrow.precipitation_sum_mm:.1f} mm)\n• Max Wind: **{fc_tomorrow.max_wind_speed_kmh:.0f} km/h**"
            elif forecasts:
                lines = [f"• **{fc.date}:** {fc.weather_description} · {fc.temp_max_c:.0f}°C/{fc.temp_min_c:.0f}°C · Rain: {fc.precipitation_probability_pct}%" for fc in forecasts[:4]]
                return f"📅 **Upcoming 4-Day Forecast for {city}:**\n\n" + "\n".join(lines)

        # R. Outfit & Clothing
        if resolved_query.intent == CanonicalIntent.OUTFIT_RECOMMENDATION or any(w in raw_q_lower for w in ["wear", "wearing", "clothes", "jacket", "outfit"]):
            if is_raining:
                return f"🧥 **Outfit tip for {city}:** It's currently **{temp}** with active rain. Wear a **waterproof jacket or raincoat** and keep an **umbrella** handy! 🌧️"
            elif temp_val < 18.0:
                return f"🧥 **Outfit tip for {city}:** It's cool at **{temp}**. A **sweater, warm hoodie, or jacket** will keep you comfortable! ❄️"
            elif temp_val <= 30.0:
                return f"👕 **Outfit tip for {city}:** Pleasant weather in {city} (**{temp}**, {cond}). Standard **breathable cotton clothes or casual wear** are ideal today! 🌤️"
            else:
                return f"👕 **Outfit tip for {city}:** It's warm at **{temp}**. Wear **lightweight, loose cotton clothing**, wear sunglasses for sun protection, and stay hydrated! ☀️"

        # S. Clothes Drying / Laundry
        if resolved_query.intent == CanonicalIntent.CLOTHES_DRYING or any(w in raw_q_lower for w in ["dry", "laundry", "clothes outside"]):
            if is_raining or humid > 80.0:
                return f"👕 **Keep laundry indoors today in {city}!** It's currently rainy/humid ({temp}, humidity {humid:.0f}%). Clothes will not dry well outdoors. 🌧️"
            return f"👕 **Great day to dry laundry outside in {city}!** Skies are **{cond}** with winds at **{wind}** and temperature at {temp}. 🌤️"

        # T. Rain & Precipitation
        if resolved_query.intent == CanonicalIntent.PRECIPITATION or any(w in raw_q_lower for w in ["rain", "umbrella", "shower"]):
            if is_raining:
                return f"🌧️ **Yes, it is raining in {city}!** Current temperature is **{temp}** with active precipitation ({precip:.1f} mm/h). Make sure to carry an umbrella."
            rain_chance = forecasts[0].precipitation_probability_pct if forecasts else 20
            if rain_chance >= 40:
                return f"🌦️ There is a **{rain_chance}% chance of rain** later today in **{city}** ({temp}, {cond}). Carrying a compact umbrella is recommended."
            return f"☀️ **No significant rain expected right now in {city}.** Skies are **{cond}** and temperature is **{temp}**."

        # U. Default Current Weather Snapshot
        if lang == "hi":
            return f"🌤️ **{city}** में वर्तमान तापमान **{temp}** (अहसास: {feels_like}) है और मौसम **{cond}** है। आर्द्रता {humid:.0f}% और हवा {wind} की गति से चल रही है।"
        elif lang == "hinglish":
            return f"🌤️ **{city}** mein abhi temperature **{temp}** (feels like {feels_like}) hai aur mausam **{cond}** hai. Humidity {humid:.0f}% aur hawa {wind} hai."
        elif lang == "or":
            return f"🌤️ **{city} ରେ ବର୍ତ୍ତମାନ ତାପମାତ୍ରା {temp} (ଅନୁଭବ: {feels_like}) ଅଛି ଏବଂ ଆକାଶ {cond} ରହିଛି।**\n\n• **ଆର୍ଦ୍ରତା (Humidity):** {humid:.0f}%\n• **ପବନର ଗତି (Wind):** {wind}\n• **ବାୟୁମଣ୍ଡଳୀୟ ଚାପ:** {pressure}\n• **ୟୁଭି ଇଣ୍ଡେକ୍ସ (UV Index):** {uv:.1f}"
        elif lang == "te":
            return f"🌤️ **{city} లో ప్రస్తుతం ఉష్ణోగ్రత {temp} (అనిపిస్తుంది: {feels_like}) మరియు వాతావరణం {cond}.**\n\n• **తేమ (Humidity):** {humid:.0f}%\n• **గాలి వేగం (Wind):** {wind}\n• **పీడనం:** {pressure}\n• **UV ఇండెక్స్:** {uv:.1f}"
        elif lang == "ta":
            return f"🌤️ **{city}யில் தற்போதைய வெப்பநிலை {temp} (உணர்வு: {feels_like}) மற்றும் வானம் {cond}.**\n\n• **ஈரப்பதம் (Humidity):** {humid:.0f}%\n• **காற்றின் வேகம்:** {wind}\n• **அழுத்தம்:** {pressure}\n• **UV குறியீடு:** {uv:.1f}"
        elif lang == "bn":
            return f"🌤️ **{city}-তে বর্তমান তাপমাত্রা {temp} (অনুভূতি: {feels_like}) এবং আকাশ {cond}।**\n\n• **আর্দ্রতা (Humidity):** {humid:.0f}%\n• **বাতাসের গতি (Wind):** {wind}\n• **বায়ুমণ্ডলীয় চাপ:** {pressure}\n• **ইউভি সূচক (UV Index):** {uv:.1f}"
        elif lang == "mr":
            return f"🌤️ **{city} मध्ये सध्या तापमान {temp} (जाणवते: {feels_like}) आहे आणि हवामान {cond} आहे।**\n\n• **आर्द्रता (Humidity):** {humid:.0f}%\n• **वाऱ्याचा वेग (Wind):** {wind}\n• **दाब:** {pressure}\n• **UV निर्देशांक:** {uv:.1f}"
        elif lang == "gu":
            return f"🌤️ **{city} માં વર્તમાન તાપમાન {temp} (અનુભવાય છે: {feels_like}) છે અને હવામાન {cond} છે.**\n\n• **ભેજ (Humidity):** {humid:.0f}%\n• **પવનની ગતિ:** {wind}\n• **દબાણ:** {pressure}\n• **યુવી ઇન્ડેક્સ:** {uv:.1f}"
        elif lang == "kn":
            return f"🌤️ **{city} ನಲ್ಲಿ ಪ್ರಸ್ತುತ ತಾಪಮಾನ {temp} (ಅನುಭವ: {feels_like}) ಮತ್ತು ಆಕಾಶ {cond} ಇದೆ.**\n\n• **ತೇವಾಂಶ (Humidity):** {humid:.0f}%\n• **ಗಾಳಿಯ ವೇಗ:** {wind}\n• **ಒತ್ತಡ:** {pressure}\n• **ಯುವಿ ಸೂಚ್ಯಂಕ:** {uv:.1f}"
        elif lang == "ml":
            return f"🌤️ **{city}-ൽ നിലവിലെ താപനില {temp} (അനുഭവപ്പെടുന്നത്: {feels_like}) ആണ്, കാലാവസ്ഥ {cond} ആണ്.**\n\n• **ഈർപ്പം (Humidity):** {humid:.0f}%\n• **കാറ്റിന്റെ വേഗത:** {wind}\n• **മർദ്ദം:** {pressure}\n• **UV സൂചിക:** {uv:.1f}"
        elif lang == "pa":
            return f"🌤️ **{city} ਵਿੱਚ ਮੌਜੂਦਾ ਤਾਪਮਾਨ {temp} (ਮਹਿਸੂਸ: {feels_like}) ਹੈ ਅਤੇ ਮੌਸਮ {cond} ਹੈ।**\n\n• **ਨਮੀ (Humidity):** {humid:.0f}%\n• **ਹਵਾ ਦੀ ਗਤੀ:** {wind}\n• **ਦਬਾਅ:** {pressure}\n• **ਯੂਵੀ ਇੰਡੈਕਸ:** {uv:.1f}"
        return f"🌤️ In **{city}**, it is currently **{temp}** (feels like **{feels_like}**) with **{cond}**.\n\n• **Humidity:** {humid:.0f}%\n• **Wind Speed:** {wind}\n• **Pressure:** {pressure}\n• **UV Index:** {uv:.1f}"

    def process_query(self, input_data: MultimodalInput, session_id: str = "default") -> AgentResponse:
        """
        End-to-end multimodal pipeline with LLM Query Understanding and multi-turn Context Memory.
        Strictly enforces canonical intent routing, 5-tier location hierarchy, and deterministic state.
        """
        query_text = input_data.text_query or ""
        is_voice_query = False
        if input_data.audio_path:
            is_voice_query = True
            transcribed = self.audio_engine.speech_to_text(input_data.audio_path, language=input_data.language_code)
            if transcribed:
                query_text = transcribed

        if not query_text:
            query_text = "What is the current weather and forecast?"

        # 1. SEMANTIC QUERY UNDERSTANDING + CONVERSATION CONTEXT RESOLUTION
        structured_query = self.query_engine.understand_query(query_text, session_id=session_id)
        
        # Determine language: Detect language of question first, then answer in the exact same language!
        detected_query_lang = structured_query.language
        if detected_query_lang and detected_query_lang != "en":
            target_lang = detected_query_lang
        elif input_data.language_code and input_data.language_code != "auto":
            target_lang = input_data.language_code
        else:
            target_lang = detected_query_lang or "en"

        ctx = self.query_engine.memory.get_context(session_id)

        # 2. STRICT 5-TIER CANONICAL LOCATION RESOLUTION HIERARCHY
        # Tier 1: Explicit location in the user query (e.g. "in Patna", "Patratu ghumne", "trip to Manali")
        # Tier 2: Explicit frontend-selected active location (input_data.location_name e.g. "Patratu")
        # Tier 3: Conversation context memory (ctx.last_location)
        # Tier 4: User's saved/default location
        # Tier 5: System default location ("New Delhi, India")
        query_loc = structured_query.location.strip() if (structured_query.location and structured_query.location.strip()) else None
        frontend_loc = input_data.location_name.strip() if (input_data.location_name and input_data.location_name.strip()) else None
        context_loc = ctx.last_location.strip() if (ctx.last_location and ctx.last_location.strip()) else None

        if query_loc:
            resolved_loc_str = query_loc
        elif frontend_loc:
            resolved_loc_str = frontend_loc
        elif context_loc:
            resolved_loc_str = context_loc
        else:
            resolved_loc_str = self.config.default_location_name

        display_location = resolved_loc_str

        # Internal backend debug logging (Safe against console encoding issues)
        def _safe_log(label: str, content: Any):
            try:
                safe_str = str(content).encode("ascii", errors="backslashreplace").decode("ascii")
                print(f"[DEBUG] {label}: {safe_str}", flush=True)
            except Exception:
                pass

        _safe_log("RAW USER QUERY", query_text)
        _safe_log("FRONTEND LOCATION", frontend_loc)
        _safe_log("INPUT_DATA", input_data.dict())
        _safe_log("PREVIOUS CONTEXT", f"last_loc={ctx.last_location}, last_intent={ctx.last_intent}, last_time={ctx.last_time_reference}")
        _safe_log("QUERY UNDERSTANDING RESULT", structured_query.dict())
        _safe_log("RESOLVED INTENT", structured_query.intent.value)
        _safe_log("RESOLVED TIME", structured_query.time_reference)

        # 3. FAST-PATH FOR LOCATION INFO (Zero weather API, NWP, or tool calls)
        if structured_query.intent == CanonicalIntent.LOCATION_INFO:
            structured_query.location = display_location
            
            if structured_query.language in ["hi", "hinglish"]:
                loc_answer = f"Aap abhi **{display_location}** ka mausam dekh rahe hain."
            else:
                loc_answer = f"You're currently viewing weather for **{display_location}**."

            translated_answer = None
            if target_lang != "en" and structured_query.language != "hinglish":
                translated_answer = self.indic_engine.translate_and_localize(
                    english_text=loc_answer,
                    target_lang=target_lang,
                    query=query_text
                )

            final_text = translated_answer or loc_answer
            self.query_engine.memory.update_context(session_id, query_text, structured_query, final_text)

            print(
                f"[LOCATION TRACE]\n"
                f"frontend_location={frontend_loc}\n"
                f"query_explicit_location={query_loc}\n"
                f"resolved_query_location={display_location}\n"
                f"weather_request_location=None (Skipped for location_info)\n"
                f"weather_response_location=None\n"
                f"final_response_location={display_location}\n",
                flush=True
            )
            _safe_log("FINAL RESPONSE", final_text)

            return AgentResponse(
                query=query_text,
                response_text=loc_answer,
                detected_language="hi" if structured_query.language == "hinglish" else target_lang,
                translated_response=translated_answer,
                structured_weather=None,
                daily_forecasts=[],
                nwp_forecast=None,
                extreme_alerts=[],
                agro_advisory=None,
                climate_trend=None,
                audio_output_file=None,
                visual_analysis=None,
                rag_sources=[],
                resolved_query=structured_query
            )

        # 4. FAST-PATH FOR CASUAL BANTER (Zero external tool latency)
        if structured_query.intent == CanonicalIntent.CASUAL_CONVERSATION and not (input_data.image_path or input_data.image_base64):
            structured_query.location = display_location
            conversational_ans = self._generate_structured_response(resolved_query=structured_query)
            
            translated_answer = None
            if target_lang != "en" and structured_query.language != "hinglish":
                translated_answer = self.indic_engine.translate_and_localize(
                    english_text=conversational_ans,
                    target_lang=target_lang,
                    query=query_text
                )

            # Update memory
            self.query_engine.memory.update_context(session_id, query_text, structured_query, conversational_ans)
            _safe_log("FINAL RESPONSE", conversational_ans)

            return AgentResponse(
                query=query_text,
                response_text=conversational_ans,
                detected_language="hi" if structured_query.language == "hinglish" else target_lang,
                translated_response=translated_answer,
                structured_weather=None,
                daily_forecasts=[],
                nwp_forecast=None,
                extreme_alerts=[],
                agro_advisory=None,
                climate_trend=None,
                audio_output_file=None,
                visual_analysis=None,
                rag_sources=[],
                resolved_query=structured_query
            )

        # 5. GEOGRAPHIC RESOLUTION FOR WEATHER QUERIES
        geo = self.location_resolver.resolve(resolved_loc_str)
        if not geo:
            if query_loc:
                clarification = (
                    f"Mujhe '{query_loc}' ki location nahi mil paayi. Kripya apna district ya state bataiye taaki main sahi mausam bata sakoon."
                    if structured_query.language in ["hi", "hinglish"]
                    else f"I couldn't locate '{query_loc}'. Could you please specify the district or state?"
                )
                self.query_engine.memory.update_context(session_id, query_text, structured_query, clarification)
                return AgentResponse(
                    query=query_text,
                    response_text=clarification,
                    detected_language=target_lang,
                    resolved_query=structured_query
                )
            geo = GeoLocation(name=resolved_loc_str, latitude=self.config.default_lat, longitude=self.config.default_lon, country="India")

        location_name = geo.name
        # Keep canonical display location authoritative on structured_query
        structured_query.location = display_location
        structured_query.latitude = geo.latitude
        structured_query.longitude = geo.longitude
        target_crop = structured_query.crop or ctx.last_crop or "Paddy"

        _safe_log("RESOLVED LOCATION", f"{display_location} -> {location_name} ({geo.latitude}, {geo.longitude})")
        _safe_log("WEATHER TOOL LOCATION", location_name)
        _safe_log("RESPONSE GENERATION INTENT", structured_query.intent.value)
        _safe_log("RESPONSE GENERATION LOCATION", display_location)

        # 6. EXECUTE WEATHER & NWP TOOLS (Parallel with 300s cache)
        visual_analysis = None
        if input_data.image_path or input_data.image_base64:
            visual_analysis = self.vision_engine.analyze_weather_image(
                image_input=input_data.image_path or input_data.image_base64,
                prompt=query_text
            )

        cur_weather, daily_fc, nwp_forecast, agro_advisory = self._fetch_weather_parallel(
            location_name=location_name,
            target_crop=target_crop
        )
        
        # Preserve authoritative display location on weather object so station names never override UI
        if cur_weather:
            cur_weather.location.name = display_location
            
        alerts = self.alerts_tool.evaluate_hazards(location_name, weather=cur_weather, nwp=nwp_forecast)

        climate_trend = None
        if structured_query.intent == CanonicalIntent.HISTORICAL_CLIMATE:
            climate_trend = self.climate_tool.analyze_climate_trend(location_name)

        rag_sources = []
        if any(w in query_text.lower() for w in ["explain", "why", "sop", "guideline", "protocol", "science"]):
            agentic_rag_result = self.agentic_rag.execute_agentic_rag(user_query=query_text, location=location_name)
            rag_sources = [
                {
                    "content": doc.content,
                    "topic": doc.topic,
                    "source": doc.source,
                    "category": doc.category,
                    "relevance_score": doc.relevance_score
                }
                for doc in agentic_rag_result.retrieved_documents
            ]

        # 7. GENERATE NATURAL SYNTHESIZED RESPONSE GROUNDED IN REAL DATA
        english_answer = self._generate_structured_response(
            resolved_query=structured_query,
            weather=cur_weather,
            forecasts=daily_fc,
            nwp=nwp_forecast,
            alerts=alerts,
            advisory=agro_advisory,
            climate=climate_trend
        )

        # 8. MULTILINGUAL TRANSLATION (If regional Indian script requested)
        translated_answer = None
        if target_lang != "en" and structured_query.language != "hinglish":
            translated_answer = self.indic_engine.translate_and_localize(
                english_text=english_answer,
                target_lang=target_lang,
                query=query_text,
                weather=cur_weather,
                forecasts=daily_fc,
                nwp=nwp_forecast,
                alerts=alerts,
                advisory=agro_advisory,
                climate=climate_trend
            )

        # 9. UPDATE CONVERSATION CONTEXT MEMORY
        final_text = translated_answer or english_answer
        self.query_engine.memory.update_context(session_id, query_text, structured_query, final_text)

        _safe_log("LOCATION TRACE", f"frontend_location={frontend_loc}, resolved_loc={structured_query.location}, final_loc={display_location}")
        _safe_log("FINAL RESPONSE", final_text)

        # 8. AUDIO SYNTHESIS
        audio_output = None
        if is_voice_query or input_data.audio_path:
            speech_source = translated_answer if translated_answer else english_answer
            audio_output = self.audio_engine.text_to_speech(speech_source, language_code=target_lang)

        return AgentResponse(
            query=query_text,
            response_text=english_answer,
            detected_language="hi" if structured_query.language == "hinglish" else target_lang,
            translated_response=translated_answer,
            structured_weather=cur_weather,
            daily_forecasts=daily_fc,
            nwp_forecast=nwp_forecast,
            extreme_alerts=alerts,
            agro_advisory=agro_advisory,
            climate_trend=climate_trend,
            audio_output_file=audio_output,
            visual_analysis=visual_analysis,
            rag_sources=rag_sources,
            resolved_query=structured_query
        )
