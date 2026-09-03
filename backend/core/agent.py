"""
Core Multimodal Weather AI Agent Orchestrator ("MausamVani").
Integrates the LLM-based Query Understanding Layer, multi-turn Conversation Memory,
Dynamic Location Resolution, NWP model engine (GFS/WRF), extreme hazard alerts, agro-advisories,
historical climate reanalysis, Agentic RAG, remote sensing vision, and neural Indic voice synthesis.
"""
import os
import re
import time
from datetime import datetime, timedelta
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
        # 0. DYNAMIC TARGET FORECAST & CALENDAR DATE RESOLUTION
        # -------------------------------------------------------------
        target_fc: Optional[DailyForecastItem] = None
        date_label_en = "today"
        date_label_hi = "आज"
        date_label_or = "ଆଜି"
        date_label_hinglish = "aaj"
        is_future = False

        month_map = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'sept': 9, 'september': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        weekday_map = {
            'monday': 0, 'somwar': 0, 'somavara': 0, 'ସୋମବାର': 0,
            'tuesday': 1, 'mangalwar': 1, 'mangalavara': 1, 'ମଙ୍ଗଳବାର': 1,
            'wednesday': 2, 'budhwar': 2, 'budhavara': 2, 'ବୁଧବାର': 2,
            'thursday': 3, 'guruwar': 3, 'guruvara': 3, 'ଗୁରୁବାର': 3,
            'friday': 4, 'shukrawar': 4, 'shukravara': 4, 'ଶୁକ୍ରବାର': 4,
            'saturday': 5, 'shaniwar': 5, 'shanivara': 5, 'ଶନିବାର': 5,
            'sunday': 6, 'ravivar': 6, 'ravivara': 6, 'aitwar': 6, 'ରବିବାର': 6
        }

        # 1. Normalize all Indian numerals (Devanagari, Odia, Bengali, Telugu, etc.) to ASCII digits
        digit_map = {
            '०':'0','१':'1','२':'2','३':'3','४':'4','५':'5','६':'6','७':'7','८':'8','९':'9',
            '୦':'0','୧':'1','୨':'2','୩':'3','୪':'4','୫':'5','୬':'6','୭':'7','୮':'8','୯':'9',
            '০':'0','১':'1','২':'2','৩':'3','৪':'4','৫':'5','৬':'6','৭':'7','৮':'8','৯':'9',
            '౦':'0','౧':'1','౨':'2','౩':'3','౪':'4','౵':'5','౶':'6','౷':'7','౸':'8','౹':'9',
            '૦':'0','૧':'1','૨':'2','૩':'3','૪':'4','૫':'5','૬':'6','૭':'7','૮':'8','૯':'9',
            '੦':'0','੧':'1','੨':'2','੩':'3','੪':'4','੫':'5','੬':'6','੭':'7','੮':'8','੯':'9',
        }
        raw_q_norm = raw_q_lower
        for k, v in digit_map.items():
            raw_q_norm = raw_q_norm.replace(k, v)

        # Match explicit dates (e.g. '6th sept', 'sept 6', '6 september', 'on 6th', '6th ko', '6 tarikh', '६ तारीख', '୬ ତାରିଖ')
        m1 = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s*(?:of\s+)?(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|september|oct|nov|dec)[a-z]*', raw_q_norm)
        m2 = re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|september|oct|nov|dec)[a-z]*\s*(\d{1,2})(?:st|nd|rd|th)?', raw_q_norm)
        
        is_multi_day_count = bool(re.search(r'\b\d{1,2}\s*(?:days?|dino?|din|दिन|ଦିନ|ଦିନର|दिनों)\b', raw_q_norm))
        m3 = None
        if not is_multi_day_count:
            m3 = re.search(r'(?:on\s+the\s+|on\s+|ko\s+|tarikh\s+|date\s+|ତାରିଖ\s*)(\d{1,2})(?:st|nd|rd|th|\s*ko|\s*tarikh|\s*tarik|\s*ତାରିଖ|\s*তারিখ|\s*తేదీ|\s*தேதி|\s*तारीख|\s*date)?\b', raw_q_norm)
            if not m3:
                m3 = re.search(r'\b(\d{1,2})(?:st|nd|rd|th|\s+ko|\s+tarikh|\s+tarik|\s+ତାରିଖ|\s+तारीख|\s+date)\b', raw_q_norm)

        matched_day = None
        matched_month = None
        if m1:
            matched_day = int(m1.group(1))
            mon_s = m1.group(2)[:4] if m1.group(2).startswith('sept') else m1.group(2)[:3]
            matched_month = month_map.get(mon_s)
        elif m2:
            mon_s = m2.group(1)[:4] if m2.group(1).startswith('sept') else m2.group(1)[:3]
            matched_month = month_map.get(mon_s)
            matched_day = int(m2.group(2))
        elif m3:
            matched_day = int(m3.group(1))

        if matched_day and forecasts:
            for f in forecasts:
                try:
                    dt = datetime.strptime(f.date, '%Y-%m-%d')
                    if dt.day == matched_day and (matched_month is None or dt.month == matched_month):
                        target_fc = f
                        date_label_en = f"on {dt.strftime('%A, %d %B')}"
                        date_label_hi = f"{dt.strftime('%d %B')} को"
                        date_label_or = f"{dt.strftime('%d %B')} ରେ"
                        date_label_hinglish = f"{dt.strftime('%d %B')} ko"
                        is_future = True
                        break
                except Exception:
                    pass

        # 2. Match weekdays if date not matched yet
        if not target_fc and forecasts:
            for w_name, w_idx in weekday_map.items():
                if w_name in raw_q_lower or w_name in raw_q:
                    for f in forecasts[1:]:
                        try:
                            dt = datetime.strptime(f.date, '%Y-%m-%d')
                            if dt.weekday() == w_idx:
                                target_fc = f
                                date_label_en = f"on {dt.strftime('%A, %d %B')}"
                                date_label_hi = f"{dt.strftime('%A, %d %B')} को"
                                date_label_or = f"{dt.strftime('%A, %d %B')} ରେ"
                                date_label_hinglish = f"{dt.strftime('%A, %d %B')} ko"
                                is_future = True
                                break
                        except Exception:
                            pass
                    if target_fc:
                        break

        # 3. Match relative terms (tomorrow, day after tomorrow, weekend)
        if not target_fc:
            if time_ref == "tomorrow" and fc_tomorrow:
                target_fc = fc_tomorrow
                date_label_en = "tomorrow"
                date_label_hi = "कल"
                date_label_or = "ଆସନ୍ତାକାଲି"
                date_label_hinglish = "kal"
                is_future = True
            elif time_ref == "day_after_tomorrow" and fc_day_after:
                target_fc = fc_day_after
                date_label_en = "the day after tomorrow"
                date_label_hi = "परसों"
                date_label_or = "ଆରଦିନ"
                date_label_hinglish = "parso"
                is_future = True
            elif time_ref == "weekend" and forecasts and len(forecasts) > 1:
                target_fc = forecasts[1]
                date_label_en = "this weekend"
                date_label_hi = "इस वीकेंड"
                date_label_or = "ଏହି ସପ୍ତାହାନ୍ତରେ"
                date_label_hinglish = "is weekend"
                is_future = True
            elif forecasts:
                target_fc = forecasts[0]

        # -------------------------------------------------------------
        # 1. ATTEMPT FULL LLM SYNTHESIS (Gemini / Groq / Ollama)
        # -------------------------------------------------------------
        fc_summary = ""
        if forecasts:
            fc_lines = [f"{f.date}: {f.weather_description}, High {f.temp_max_c:.0f}°C / Low {f.temp_min_c:.0f}°C, Rain {f.precipitation_probability_pct}%" for f in forecasts[:7]]
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
Target Timeframe / Date: {date_label_en} ({target_fc.date if target_fc else 'today'}) (CRITICAL: Focus your response strictly on this specific day's forecast data!)

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
1. Directly and accurately answer the user's question for the requested time ({time_ref}) in {lang_target_desc} based on the real weather and forecast data.
2. Provide practical, scenario-specific reasoning (e.g., if asking about rain/umbrella, drone flying, travel, workout, etc.).
3. Do NOT make up arbitrary numbers. Use emojis and clear markdown bullet points.
"""
        llm_response = self._call_llm_synthesis(llm_prompt)
        if llm_response and len(llm_response) > 20:
            return llm_response

        # -------------------------------------------------------------
        # 2. UNIVERSAL MULTI-DOMAIN REASONING ENGINE (High-Precision Fallback)
        # -------------------------------------------------------------
        def _has_kw(keywords: List[str]) -> bool:
            for kw in keywords:
                if any(ord(c) > 127 for c in kw):
                    if kw in raw_q_lower:
                        return True
                else:
                    if re.search(r'\b' + re.escape(kw) + r'\b', raw_q_lower):
                        return True
            return False

        # 1. Rain & Precipitation (e.g. umbrella, rain today/tomorrow)
        if resolved_query.intent == CanonicalIntent.PRECIPITATION or _has_kw(["rain", "raining", "umbrella", "shower", "drizzle", "downpour", "बारिश", "बरसात", "छाता", "ବର୍ଷା", "ଛତା", "वर्षा", "पाऊस", "বৃষ্টি", "వర్షం", "மழை"]):
            if is_future and target_fc:
                rain_prob = target_fc.precipitation_probability_pct
                if rain_prob >= 40:
                    if lang == "hi":
                        return f"🌦️ **{date_label_hi} {city} में बारिश के आसार हैं!**\n\n• **बारिश की संभावना:** **{rain_prob}%** (~{target_fc.precipitation_sum_mm:.1f} mm)\n• **पूर्वानुमान:** {target_fc.weather_description}\n• **तापमान:** अधिकतम **{target_fc.temp_max_c:.0f}°C** / न्यूनतम **{target_fc.temp_min_c:.0f}°C**\n• छाता या रेनकोट साथ रखना अच्छा रहेगा।"
                    elif lang == "or":
                        return f"🌦️ **{date_label_or} {city} ରେ ବର୍ଷା ହେବାର ସମ୍ଭାବନା ଅଛି!**\n\n• **ବର୍ଷା ସମ୍ଭାବନା:** **{rain_prob}%** (~{target_fc.precipitation_sum_mm:.1f} mm)\n• **ପୂର୍ବାନୁମାନ:** {target_fc.weather_description}\n• **ତାପମାତ୍ରା:** ସର୍ବାଧିକ **{target_fc.temp_max_c:.0f}°C** / ସର୍ବନିମ୍ନ **{target_fc.temp_min_c:.0f}°C**\n• ଛତା କିମ୍ବା ରେନକୋଟ୍ ସାଙ୍ଗରେ ନିଅନ୍ତୁ।"
                    return f"🌦️ **Rain is likely in {city} {date_label_en}!**\n\n• **Precipitation Probability:** **{rain_prob}%** (~{target_fc.precipitation_sum_mm:.1f} mm)\n• **Forecast:** **{target_fc.weather_description}**\n• **Temperatures:** High **{target_fc.temp_max_c:.0f}°C** / Low **{target_fc.temp_min_c:.0f}°C**\n• Carrying a compact umbrella is recommended."
                else:
                    if lang == "hi":
                        return f"☀️ **{date_label_hi} {city} में बारिश की संभावना कम है।**\n\n• **मौसम:** {target_fc.weather_description}\n• **बारिश का जोखिम:** कम ({rain_prob}%)\n• **तापमान:** अधिकतम **{target_fc.temp_max_c:.0f}°C** / न्यूनतम **{target_fc.temp_min_c:.0f}°C**\n• छाता ले जाने की आवश्यकता नहीं है।"
                    elif lang == "or":
                        return f"☀️ **{date_label_or} {city} ରେ ବର୍ଷା ସମ୍ଭାବନା କମ୍ ଅଛି।**\n\n• **ଆକାଶ:** {target_fc.weather_description}\n• **ବର୍ଷା ଆଶଙ୍କା:** କମ୍ ({rain_prob}%)\n• **ତାପମାତ୍ରା:** ସର୍ବାଧିକ **{target_fc.temp_max_c:.0f}°C** / ସର୍ବନିମ୍ନ **{target_fc.temp_min_c:.0f}°C**"
                    return f"☀️ **No significant rain expected in {city} {date_label_en}.**\n\n• **Skies:** **{target_fc.weather_description}**\n• **Rain Risk:** Low ({rain_prob}%)\n• **Temperatures:** High **{target_fc.temp_max_c:.0f}°C** / Low **{target_fc.temp_min_c:.0f}°C**\n• An umbrella is not necessary today."
            elif is_raining:
                if lang == "hi":
                    return f"🌧️ **हाँ, {city} में अभी बारिश हो रही है!**\n\n• **वर्तमान तापमान:** **{temp}** (बारिश: {precip:.1f} mm/h, {cond})\n• बाहर जाते समय **छाता या रेनकोट** जरूर साथ रखें।"
                return f"🌧️ **Yes, it is raining in {city}!** Current temperature is **{temp}** with active precipitation ({precip:.1f} mm/h). Make sure to carry an umbrella."
            rain_chance = forecasts[0].precipitation_probability_pct if forecasts else 20
            if rain_chance >= 40:
                if lang == "hi":
                    return f"🌦️ **आज {city} में बारिश की {rain_chance}% संभावना है!**\n\n• **मौसम:** {temp}, {cond}\n• एहतियात के तौर पर छोटा छाता साथ रखना अच्छा रहेगा।"
                elif lang == "or":
                    return f"🌦️ **ଆଜି {city} ରେ ବର୍ଷା ହେବାର {rain_chance}% ସମ୍ଭାବନା ଅଛି!**\n\n• **ପାଣିପାଗ:** {temp}, {cond}\n• ସାବଧାନତା ପାଇଁ ଛତା ସାଙ୍ଗରେ ରଖିବା ଭଲ ହେବ।"
                return f"🌦️ There is a **{rain_chance}% chance of rain** later today in **{city}** ({temp}, {cond}). Carrying a compact umbrella is recommended."
            if lang == "hi":
                return f"☀️ **आज {city} में बारिश की संभावना बहुत कम है ({rain_chance}%)।**\n\n• **मौसम:** {temp}, {cond}\n• छाता ले जाने की आवश्यकता नहीं है।"
            elif lang == "or":
                return f"☀️ **ଆଜି {city} ରେ ବର୍ଷା ହେବାର ସମ୍ଭାବନା ବହୁତ କମ୍ ({rain_chance}%)।**\n\n• **ପାଣିପାଗ:** {temp}, {cond}\n• ଛତା ନେବାର ଆବଶ୍ୟକତା ନାହିଁ।"
            return f"☀️ **No significant rain expected right now in {city}.** Skies are **{cond}** and temperature is **{temp}**. An umbrella is not needed today."

        # 2. Travel, Commute & Driving
        if resolved_query.intent == CanonicalIntent.TRAVEL_WEATHER or _has_kw(["drive", "driving", "commute", "road", "traffic", "travel", "trip", "ଯାତ୍ରା", "यात्रा", "बाहर निकलना", "जाना", "ਘੁੰਮਣਾ", "ಪ್ರವಾಸ"]):
            if is_future and target_fc:
                rain_prob = target_fc.precipitation_probability_pct
                is_fc_rain = rain_prob >= 40 or "rain" in target_fc.weather_description.lower() or "thunderstorm" in target_fc.weather_description.lower()
                if is_fc_rain:
                    if lang == "hi":
                        return f"🚗 **{date_label_hi} {city} में यात्रा / ड्राइव करते समय सावधानी बरतें!**\n\n• **पूर्वानुमान:** {target_fc.weather_description} (बारिश का जोखिम: **{rain_prob}%**)\n• **तापमान:** अधिकतम **{target_fc.temp_max_c:.0f}°C** / न्यूनतम **{target_fc.temp_min_c:.0f}°C**\n• **सलाह:** बारिश और गीली सड़कों के कारण यात्रा में अतिरिक्त समय लेकर चलें।"
                    elif lang == "or":
                        return f"🚗 **{date_label_or} {city} ରେ ଯାତ୍ରା / ଡ୍ରାଇଭ୍ କରିବା ସମୟରେ ସତର୍କ ରୁହନ୍ତୁ!**\n\n• **ପୂର୍ବାନୁମାନ:** {target_fc.weather_description} (ବର୍ଷା ସମ୍ଭାବନା: **{rain_prob}%**)\n• **ତାପମାତ୍ରା:** ସର୍ବାଧିକ **{target_fc.temp_max_c:.0f}°C** / ସର୍ବନିମ୍ନ **{target_fc.temp_min_c:.0f}°C**\n• ବର୍ଷା ହେବାର ଆଶଙ୍କା ଥିବାରୁ ଯାତ୍ରା ପାଇଁ ଅତିରିକ୍ତ ସମୟ ରଖନ୍ତୁ।"
                    return f"🚗 **Exercise caution when travelling or commuting in {city} {date_label_en}!**\n\n• **Forecast:** **{target_fc.weather_description}** with **{rain_prob}% chance of rain** ({target_fc.precipitation_sum_mm:.1f} mm).\n• **Temperatures:** High **{target_fc.temp_max_c:.0f}°C** / Low **{target_fc.temp_min_c:.0f}°C**.\n• **Road Guidance:** Wet road surfaces and reduced tire traction expected. Allow extra travel time."
                else:
                    if lang == "hi":
                        return f"🚗 **हाँ, {date_label_hi} {city} में यात्रा और ड्राइव करना पूरी तरह सुरक्षित रहेगा!**\n\n• **पूर्वानुमान:** {target_fc.weather_description}\n• **तापमान:** अधिकतम **{target_fc.temp_max_c:.0f}°C** / न्यूनतम **{target_fc.temp_min_c:.0f}°C**\n• **बारिश का जोखिम:** कम ({rain_prob}%)\n• सड़कें सूखी रहेंगी और यातायात सुगम रहेगा।"
                    elif lang == "or":
                        return f"🚗 **ହଁ, {date_label_or} {city} ରେ ଯାତ୍ରା ଓ ଡ୍ରାଇଭ୍ କରିବା ସମ୍ପୂର୍ଣ୍ଣ ସୁରକ୍ଷିତ ରହିବ!**\n\n• **ପୂର୍ବାନୁମାନ:** {target_fc.weather_description}\n• **ତାପମାତ୍ରା:** ସର୍ବାଧିକ **{target_fc.temp_max_c:.0f}°C** / ସର୍ବନିମ୍ନ **{target_fc.temp_min_c:.0f}°C**\n• **ବର୍ଷା ସମ୍ଭାବନା:** କମ୍ ({rain_prob}%)\n• ରାସ୍ତା ଶୁଖିଲା ରହିବ ଏବଂ ଯାତ୍ରା ପାଇଁ ଅନୁକୂଳ ପରିସ୍ଥିତି ରହିବ।"
                    return f"🚗 **Yes, it is expected to be safe to travel and commute in {city} {date_label_en}!**\n\n• **Forecast:** **{target_fc.weather_description}**\n• **Temperatures:** High **{target_fc.temp_max_c:.0f}°C** / Low **{target_fc.temp_min_c:.0f}°C**\n• **Rain Risk:** Low ({rain_prob}%)\n• **Wind Speed:** Peak {target_fc.max_wind_speed_kmh:.0f} km/h with dry, clear road conditions."
            elif is_raining:
                if lang == "hi":
                    return f"🚗 **{city} में अभी ड्राइव करते समय सावधानी बरतें!**\n\n• सक्रिय बारिश ({precip:.1f} mm/h) और {cond} के कारण सड़कों पर फिसलन है।\n• हेडलाइट्स जलाएं, आगे वाले वाहन से सुरक्षित दूरी रखें और 10-15 मिनट अतिरिक्त समय लेकर चलें।"
                return f"🚗 **Exercise caution while driving or commuting in {city} right now!**\n\n• Active rain ({precip:.1f} mm/h) and **{cond}** skies reduce tire traction.\n• Maintain safe following distances, switch on low-beam headlights, and allow 10–15 extra minutes for your commute."
            else:
                if lang == "hi":
                    return f"🚗 **हाँ, अभी {city} में बाहर निकलना और ड्राइव करना पूरी तरह सुरक्षित है!**\n\n• मौसम साफ़ है ({temp}), सड़कें सूखी हैं और दृश्यता {visibility} है।"
                elif lang == "or":
                    return f"🚗 **ହଁ, ବର୍ତ୍ତମାନ {city} ରେ ଯାତ୍ରା ଓ ଡ୍ରାଇଭ୍ କରିବା ସୁରକ୍ଷିତ ଅଛି!**\n\n• ପାଣିପାଗ ପରିଷ୍କାର ଅଛି ({temp}), ରାସ୍ତା ଶୁଖିଲା ଏବଂ ଦୃଶ୍ୟମାନତା {visibility} ଅଛି।"
                return f"🚗 **Yes, it is safe to drive and commute in {city} right now!**\n\n• Skies are **{cond}** with dry road conditions, clear visibility ({visibility}), and comfortable temperatures (**{temp}**)."

        # 3. Walk / Workout / Running
        if resolved_query.intent == CanonicalIntent.OUTDOOR_ACTIVITY or _has_kw(["walk", "workout", "run", "running", "jog", "exercise", "fitness", "cricket", "वॉक", "कसरत", "दौड़", "ବ୍ୟାୟାମ"]):
            disp_temp_range = f"{target_fc.temp_max_c:.0f}°C / {target_fc.temp_min_c:.0f}°C" if target_fc else temp
            disp_cond = target_fc.weather_description if target_fc else cond
            if _has_kw(["cricket", "क्रिकेट"]):
                if is_raining or (is_future and target_fc and target_fc.precipitation_probability_pct > 50):
                    return f"🏏 Not suitable for cricket in **{city}** {date_label_en} — rain risk is high ({target_fc.precipitation_probability_pct if target_fc else 60}%) and the outfield will be wet."
                return f"🏏 Great conditions for cricket in **{city}** {date_label_en}! Temperature is around **{disp_temp_range}** with {disp_cond} skies."
            if lang == "hi":
                return f"🏃 **{date_label_hi} {city} में वॉक या कसरत के लिए सबसे अच्छा समय:**\n\n• **सर्वोत्तम समय:** **सुबह (6:00 AM – 8:30 AM)** या **शाम (5:30 PM – 7:30 PM)**\n• **पूर्वानुमान:** तापमान **{disp_temp_range}**, मौसम {disp_cond}\n• **सलाह:** पर्याप्त पानी पिएं और दोपहर की सीधी धूप से बचें।"
            return f"🏃 **Best time for a walk or outdoor workout in {city} {date_label_en}:**\n\n• **Optimal Windows:** **Early Morning (6:00 AM – 8:30 AM)** or **Late Evening (5:30 PM – 7:30 PM)**\n• **Forecast:** High/Low **{disp_temp_range}**, condition: {disp_cond}.\n• **Recommendation:** Stay well-hydrated and avoid peak midday heat."

        # 4. Outfit & Clothing
        if resolved_query.intent == CanonicalIntent.OUTFIT_RECOMMENDATION or _has_kw(["wear", "wearing", "clothes", "jacket", "outfit", "पहनना", "कपड़े"]):
            effective_temp = target_fc.temp_max_c if (is_future and target_fc) else temp_val
            effective_rain = (target_fc.precipitation_probability_pct > 40) if (is_future and target_fc) else is_raining
            if effective_rain:
                if lang == "hi":
                    return f"🧥 **{city} के लिए पहनावा सलाह ({date_label_hi}):** बारिश की संभावना है। **वाटरप्रूफ जैकेट या रेनकोट** पहनें और **छाता** साथ रखें! 🌧️"
                return f"🧥 **Outfit tip for {city} ({date_label_en}):** Rain is active or expected. Wear a **waterproof jacket or raincoat** and keep an **umbrella** handy! 🌧️"
            elif effective_temp < 18.0:
                if lang == "hi":
                    return f"🧥 **{city} के लिए पहनावा सलाह ({date_label_hi}):** मौसम ठंडा रहेगा (**{effective_temp:.0f}°C**)। **हल्का स्वेटर, हुडी या जैकेट** पहनना आरामदायक रहेगा! ❄️"
                return f"🧥 **Outfit tip for {city} ({date_label_en}):** It will be cool at **{effective_temp:.0f}°C**. A **sweater, warm hoodie, or jacket** will keep you comfortable! ❄️"
            elif effective_temp <= 30.0:
                if lang == "hi":
                    return f"👕 **{city} के लिए पहनावा सलाह ({date_label_hi}):** मौसम सुहावना है (**{effective_temp:.0f}°C**)। **हल्के सूती कपड़े या कैजुअल परिधान** सबसे उपयुक्त रहेंगे! 🌤️"
                return f"👕 **Outfit tip for {city} ({date_label_en}):** Pleasant weather (**{effective_temp:.0f}°C**). Standard **breathable cotton clothes or casual wear** are ideal! 🌤️"
            else:
                if lang == "hi":
                    return f"👕 **{city} के लिए पहनावा सलाह ({date_label_hi}):** तापमान गर्म रहेगा (**{effective_temp:.0f}°C**)। **ढीले, हल्के सूती (cotton) कपड़े** पहनें, धूप का चश्मा लगाएं और पर्याप्त पानी पिएं! ☀️"
                return f"👕 **Outfit tip for {city} ({date_label_en}):** It's warm (**{effective_temp:.0f}°C**). Wear **lightweight, loose cotton clothing**, wear sunglasses for sun protection, and stay hydrated! ☀️"

        # 5. Gardening & Plant Watering
        if resolved_query.intent == CanonicalIntent.AGRO_ADVISORY or _has_kw(["garden", "gardening", "plant", "plants", "water", "watering", "crop", "spray", "पौधों", "फसलों", "पानी देना", "छिड़काव"]):
            if _has_kw(["spray", "pesticide", "fertilizer", "छिड़कना", "छिड़काव"]):
                if is_raining or (is_future and target_fc and target_fc.precipitation_probability_pct > 40):
                    if lang == "hi":
                        return f"🌧️ **{date_label_hi} {city} में फसलों/पौधों पर कीटनाशक का छिड़काव न करें!**\n\n• बारिश की संभावना ({target_fc.precipitation_probability_pct if target_fc else 60}%) दवा को बहा देगी।"
                    return f"🌧️ **Hold off on spraying chemicals in {city} {date_label_en}!** Rain risk ({target_fc.precipitation_probability_pct if target_fc else 60}%) will wash away applied treatments."
                if lang == "hi":
                    return f"✅ **{date_label_hi} {city} में छिड़काव के लिए अनुकूल समय है!** मौसम सूखा है और हवा शांत है।"
                return f"✅ **Suitable window for spraying in {city} {date_label_en}!** Skies are dry, wind is manageable."
            if is_raining or (is_future and target_fc and target_fc.precipitation_probability_pct > 50):
                rain_pct = target_fc.precipitation_probability_pct if target_fc else 75
                if lang == "hi":
                    return f"🌱 **{date_label_hi} {city} में पौधों को पानी देने की आवश्यकता नहीं है!**\n\n• बारिश की संभावना सक्रिय है ({rain_pct}%), जिससे मिट्टी में प्राकृतिक नमी बनी रहेगी।"
                elif lang == "hinglish":
                    return f"🌱 **{date_label_hinglish} {city} mein paudho ko paani mat daalo!** Rain chances {rain_pct}% hain jisse soil naturally moist rahegi."
                return f"🌱 **Hold off on outdoor watering in {city} {date_label_en}!**\n\n• Rain is expected ({rain_pct}% chance), providing natural soil hydration."
            else:
                if lang == "hi":
                    return f"🌱 **हाँ, {date_label_hi} {city} में पौधों को पानी देने के लिए अच्छा दिन है!**\n\n• वाष्पीकरण से बचने के लिए सुबह जल्दी या शाम के समय पानी दें।"
                elif lang == "hinglish":
                    return f"🌱 **Haan, {date_label_hinglish} {city} mein paudho ko paani dene ke liye accha din hai!** Morning ya evening mein dalein."
                return f"🌱 **Yes, {date_label_en} is a good day for gardening and watering plants in {city}!**\n\n• Water during early morning or late afternoon to minimize evaporation."

        # 6. Weekend & Multi-Day Forecast Window Analysis
        if resolved_query.intent == CanonicalIntent.WEATHER_FORECAST or _has_kw(["weekend", "tomorrow", "forecast", "upcoming", "week", "next", "days", "वीकेंड", "पूर्वानुमान", "कल", "ପୂର୍ବାନୁମାନ", "आने वाले दिन"]):
            def _get_fc_icon(desc: str) -> str:
                d = desc.lower()
                if "thunder" in d or "lightning" in d:
                    return "⛈️"
                elif "rain" in d or "shower" in d:
                    return "🌧️"
                elif "drizzle" in d:
                    return "🌦️"
                elif "cloud" in d or "overcast" in d:
                    return "☁️"
                elif "snow" in d or "ice" in d:
                    return "❄️"
                elif "fog" in d or "mist" in d:
                    return "🌫️"
                elif "clear" in d or "sun" in d:
                    return "☀️"
                return "🌤️"

            def _day_name(fc_date_str: str, target_lang: str) -> str:
                try:
                    dt = datetime.strptime(fc_date_str, "%Y-%m-%d")
                    dow = dt.weekday()
                    en_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                    hi_days = ["सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार", "रविवार"]
                    or_days = ["ସୋମବାର", "ମଙ୍ଗଳବାର", "ବୁଧବାର", "ଗୁରୁବାର", "ଶୁକ୍ରବାର", "ଶନିବାର", "ରବିବାର"]
                    if target_lang == "hi":
                        return f"{hi_days[dow]} ({fc_date_str})"
                    elif target_lang == "or":
                        return f"{or_days[dow]} ({fc_date_str})"
                    return f"{en_days[dow]} ({fc_date_str})"
                except Exception:
                    return fc_date_str

            # A. Weekend Forecast Analysis
            if time_ref == "weekend" and forecasts and len(forecasts) >= 2:
                sat = forecasts[min(len(forecasts)-2, 1)]
                sun = forecasts[min(len(forecasts)-1, 2)]
                sat_icon = _get_fc_icon(sat.weather_description)
                sun_icon = _get_fc_icon(sun.weather_description)
                sat_dow = _day_name(sat.date, lang)
                sun_dow = _day_name(sun.date, lang)
                weekend_rain = max(sat.precipitation_probability_pct, sun.precipitation_probability_pct)

                if lang == "hi":
                    rain_advice = "दोपहर बाद गरज-चमक/हल्की बारिश का जोखिम है, इसलिए छाता साथ रखें।" if weekend_rain >= 40 else "मौसम सूखा व गतिविधियों के लिए अनुकूल रहेगा।"
                    return (
                        f"📅 **{city} वीकेंड मौसम का विस्तृत विश्लेषण:**\n\n"
                        f"📊 **शनिवार व रविवार का पूर्वानुमान:**\n"
                        f"• **{sat_dow}:** {sat_icon} **{sat.weather_description}** · अधिकतम **{sat.temp_max_c:.0f}°C** / न्यूनतम **{sat.temp_min_c:.0f}°C** · बारिश का जोखिम: **{sat.precipitation_probability_pct}%** (~{sat.precipitation_sum_mm:.1f} mm) · हवा: {sat.max_wind_speed_kmh:.0f} km/h\n"
                        f"• **{sun_dow}:** {sun_icon} **{sun.weather_description}** · अधिकतम **{sun.temp_max_c:.0f}°C** / न्यूनतम **{sun.temp_min_c:.0f}°C** · बारिश का जोखिम: **{sun.precipitation_probability_pct}%** (~{sun.precipitation_sum_mm:.1f} mm) · हवा: {sun.max_wind_speed_kmh:.0f} km/h\n\n"
                        f"💡 **योजना व सुझाव:**\n"
                        f"• **आउटडोर प्लान:** {rain_advice}\n"
                        f"• **तापमान:** दिन में गर्माहट (32°C–33°C) रहेगी। सुबह 6:00–9:00 AM का समय आउटडोर वर्कआउट व यात्रा के लिए सर्वोत्तम है।"
                    )
                elif lang == "hinglish":
                    rain_advice = "Afternoon mein rain chances hain, umbrella saath carry karein." if weekend_rain >= 40 else "Mausam mostly clear aur activities ke liye safe rahega."
                    return (
                        f"📅 **{city} Weekend Weather Analysis & Outlook:**\n\n"
                        f"📊 **Weekend Breakdown:**\n"
                        f"• **{sat_dow}:** {sat_icon} **{sat.weather_description}** · High **{sat.temp_max_c:.0f}°C** / Low **{sat.temp_min_c:.0f}°C** · Rain Risk: **{sat.precipitation_probability_pct}%** (~{sat.precipitation_sum_mm:.1f} mm)\n"
                        f"• **{sun_dow}:** {sun_icon} **{sun.weather_description}** · High **{sun.temp_max_c:.0f}°C** / Low **{sun.temp_min_c:.0f}°C** · Rain Risk: **{sun.precipitation_probability_pct}%** (~{sun.precipitation_sum_mm:.1f} mm)\n\n"
                        f"💡 **Practical Tips:**\n"
                        f"• **Outdoors & Travel:** {rain_advice}\n"
                        f"• **Comfort:** Day temperature warm rahega (32°C–33°C). Light cotton wear karein."
                    )
                elif lang == "or":
                    return (
                        f"📅 **{city} ପାଇଁ ୱିକେଣ୍ଡ୍ (ଶନିବାର ଓ ରବିବାର) ପାଣିପାଗ ବିଶ୍ଳେଷଣ:**\n\n"
                        f"📊 **ଦୈନିକ ପୂର୍ବାନୁମାନ:**\n"
                        f"• **{sat_dow}:** {sat_icon} **{sat.weather_description}** · ସର୍ବାଧିକ **{sat.temp_max_c:.0f}°C** / ସର୍ବନିମ୍ନ **{sat.temp_min_c:.0f}°C** · ବର୍ଷା ଆଶଙ୍କା: **{sat.precipitation_probability_pct}%** (~{sat.precipitation_sum_mm:.1f} mm)\n"
                        f"• **{sun_dow}:** {sun_icon} **{sun.weather_description}** · ସର୍ବାଧିକ **{sun.temp_max_c:.0f}°C** / ସର୍ବନିମ୍ନ **{sun.temp_min_c:.0f}°C** · ବର୍ଷା ଆଶଙ୍କା: **{sun.precipitation_probability_pct}%** (~{sun.precipitation_sum_mm:.1f} mm)\n\n"
                        f"💡 **ସତର୍କତା ଓ ପରାମର୍ଶ:**\n"
                        f"• ବାହାରକୁ ଯିବା ସମୟରେ ଛତା ସାଙ୍ଗରେ ରଖନ୍ତୁ ଏବଂ ସକାଳ ସମୟ ଭ୍ରମଣ ପାଇଁ ଅନୁକୂଳ ଅଟେ।"
                    )
                return (
                    f"📅 **Weekend Weather Outlook & Analysis for {city}:**\n\n"
                    f"📊 **Weekend Synoptic Breakdown:**\n"
                    f"• **{sat_dow}:** {sat_icon} **{sat.weather_description}** · High **{sat.temp_max_c:.0f}°C** / Low **{sat.temp_min_c:.0f}°C** · Rain Risk: **{sat.precipitation_probability_pct}%** (~{sat.precipitation_sum_mm:.1f} mm) · Wind: {sat.max_wind_speed_kmh:.0f} km/h\n"
                    f"• **{sun_dow}:** {sun_icon} **{sun.weather_description}** · High **{sun.temp_max_c:.0f}°C** / Low **{sun.temp_min_c:.0f}°C** · Rain Risk: **{sun.precipitation_probability_pct}%** (~{sun.precipitation_sum_mm:.1f} mm) · Wind: {sun.max_wind_speed_kmh:.0f} km/h\n\n"
                    f"💡 **Meteorological Guidance:**\n"
                    f"• **Outdoor Activities & Travel:** {'Scattered precipitation expected; carry an umbrella and plan outdoor events during morning hours.' if weekend_rain >= 40 else 'Dry and favorable conditions for outdoor recreation and travel.'}\n"
                    f"• **Thermal Comfort:** Warm daytime highs around 32°C–33°C. Stay hydrated and opt for breathable cotton clothing."
                )

            # B. Specific Target Date Forecast Analysis (e.g. tomorrow, 6th sept, Sunday)
            elif is_future and target_fc:
                target_icon = _get_fc_icon(target_fc.weather_description)
                target_day_str = _day_name(target_fc.date, lang)
                rain_prob = target_fc.precipitation_probability_pct
                rain_mm = target_fc.precipitation_sum_mm
                is_fc_rain = rain_prob >= 40 or "rain" in target_fc.weather_description.lower() or "thunderstorm" in target_fc.weather_description.lower()

                if lang == "hi":
                    return (
                        f"📅 **{city} के लिए मौसम पूर्वानुमान व विश्लेषण ({date_label_hi} - {target_day_str}):**\n\n"
                        f"• **आसमान व स्थिति:** {target_icon} **{target_fc.weather_description}**\n"
                        f"• **तापमान सीमा:** अधिकतम **{target_fc.temp_max_c:.1f}°C** / न्यूनतम **{target_fc.temp_min_c:.1f}°C**\n"
                        f"• **बारिश की संभावना:** **{rain_prob}%** (अनुमानित मात्रा: ~{rain_mm:.1f} mm)\n"
                        f"• **हवा की गति:** अधिकतम **{target_fc.max_wind_speed_kmh:.0f} km/h**\n\n"
                        f"🔍 **मौसम प्रभाव व सुझाव:**\n"
                        f"• **यात्रा व आवागमन:** {'गीली सड़कों और बारिश के कारण यात्रा में सावधानी बरतें व छाता साथ रखें।' if is_fc_rain else 'सड़कें सूखी रहेंगी और यातायात सुगम रहेगा।'}\n"
                        f"• **पहनावा:** {'हल्का वाटरप्रूफ जैकेट या सूती कपड़े उपयुक्त रहेंगे।' if is_fc_rain else 'हल्के, आरामदायक सूती कपड़े पहनें।'}"
                    )
                elif lang == "hinglish":
                    return (
                        f"📅 **{city} Forecast & Detailed Analysis ({date_label_hinglish} - {target_day_str}):**\n\n"
                        f"• **Expected Weather:** {target_icon} **{target_fc.weather_description}**\n"
                        f"• **Thermal Range:** High **{target_fc.temp_max_c:.1f}°C** / Low **{target_fc.temp_min_c:.1f}°C**\n"
                        f"• **Rain Probability:** **{rain_prob}%** (~{rain_mm:.1f} mm rainfall)\n"
                        f"• **Max Wind Speed:** **{target_fc.max_wind_speed_kmh:.0f} km/h**\n\n"
                        f"🔍 **Key Insights:**\n"
                        f"• **Commute & Outdoor:** {'Barish ka risk hai, umbrella zaroor saath rakhein aur safe drive karein.' if is_fc_rain else 'Dry conditions expected, travel aur outdoor plans ke liye safe din hai.'}"
                    )
                elif lang == "or":
                    return (
                        f"📅 **{city} ର ପାଣିପାଗ ବିଶ୍ଳେଷଣ ({date_label_or} - {target_day_str}):**\n\n"
                        f"• **ଆକାଶ ଓ ପାଣିପାଗ:** {target_icon} **{target_fc.weather_description}**\n"
                        f"• **ତାପମାତ୍ରା:** ସର୍ବାଧିକ **{target_fc.temp_max_c:.1f}°C** / ସର୍ବନିମ୍ନ **{target_fc.temp_min_c:.1f}°C**\n"
                        f"• **ବର୍ଷା ସମ୍ଭାବନା:** **{rain_prob}%** (~{rain_mm:.1f} mm)\n"
                        f"• **ପବନର ଗତି:** ସର୍ବାଧିକ **{target_fc.max_wind_speed_kmh:.0f} km/h**\n\n"
                        f"🔍 **ପରାମର୍ଶ:**\n"
                        f"• {'ବର୍ଷା ହେବାର ଆଶଙ୍କା ଥିବାରୁ ଛତା ସାଙ୍ଗରେ ନିଅନ୍ତୁ ଏବଂ ଯାତ୍ରା ସମୟରେ ସତର୍କ ରୁହନ୍ତୁ।' if is_fc_rain else 'ଯାତ୍ରା ଓ ବାହ୍ୟ କାର୍ଯ୍ୟକଳାପ ପାଇଁ ପାଣିପାଗ ଅନୁକୂଳ ରହିବ।'}"
                    )
                return (
                    f"📅 **Meteorological Analysis for {city} ({date_label_en.capitalize()} - {target_day_str}):**\n\n"
                    f"• **Sky Condition:** {target_icon} **{target_fc.weather_description}**\n"
                    f"• **Thermal Range:** High **{target_fc.temp_max_c:.1f}°C** / Low **{target_fc.temp_min_c:.1f}°C**\n"
                    f"• **Precipitation Dynamics:** **{rain_prob}% Rain Probability** (~{rain_mm:.1f} mm expected)\n"
                    f"• **Peak Wind Speed:** **{target_fc.max_wind_speed_kmh:.0f} km/h**\n\n"
                    f"🔍 **Impact Analysis & Guidance:**\n"
                    f"• **Travel & Commute:** {'Wet asphalt and reduced braking traction expected. Allow extra transit time and carry an umbrella.' if is_fc_rain else 'Dry roads and clear driving conditions expected throughout the day.'}\n"
                    f"• **Outdoor Activities:** {'Plan outdoor workouts during morning windows to avoid midday convective precipitation.' if is_fc_rain else 'Excellent day for outdoor workouts and leisure activities.'}"
                )

            # C. Multi-Day / 7-Day Forecast Window Comprehensive Analysis
            elif forecasts:
                count = min(len(forecasts), 7)
                window_fcs = forecasts[:count]
                high_temps = [f.temp_max_c for f in window_fcs]
                low_temps = [f.temp_min_c for f in window_fcs]
                max_high = max(high_temps)
                min_low = min(low_temps)
                rainy_days_count = sum(1 for f in window_fcs if f.precipitation_probability_pct >= 40 or "rain" in f.weather_description.lower() or "thunder" in f.weather_description.lower())
                total_rain = sum(f.precipitation_sum_mm for f in window_fcs)
                peak_wind = max(f.max_wind_speed_kmh for f in window_fcs)

                if lang == "hi":
                    lines = [f"• **{_day_name(fc.date, 'hi')}:** {_get_fc_icon(fc.weather_description)} {fc.weather_description} · अधिकतम **{fc.temp_max_c:.0f}°C** / न्यूनतम **{fc.temp_min_c:.0f}°C** · बारिश: **{fc.precipitation_probability_pct}%** (~{fc.precipitation_sum_mm:.1f} mm)" for fc in window_fcs]
                    breakdown_str = "\n".join(lines)
                    return (
                        f"📅 **{city} के लिए {count}-दिवसीय विस्तृत मौसम पूर्वानुमान व विश्लेषण:**\n\n"
                        f"📊 **वायुमंडलीय रुझान विश्लेषण (Trend Overview):**\n"
                        f"• **तापमान सीमा:** अधिकतम **{max_high:.0f}°C** और न्यूनतम **{min_low:.0f}°C** के बीच तापमान रहेगा।\n"
                        f"• **वर्षा पैटर्न:** {count} में से **{rainy_days_count} दिन** बारिश/गरज-चमक का जोखिम ($\ge 40\%$) है। कुल अनुमानित बारिश: **~{total_rain:.1f} mm**।\n"
                        f"• **हवा:** अधिकतम हवा की गति **{peak_wind:.0f} km/h** तक रहेगी।\n\n"
                        f"🗓️ **दैनिक पूर्वानुमान विवरण:**\n{breakdown_str}\n\n"
                        f"💡 **महत्वपूर्ण सुझाव:**\n"
                        f"• **यात्रा:** बारिश वाले दिनों में अतिरिक्त समय लेकर चलें और छाता साथ रखें।\n"
                        f"• **कृषि/बागवानी:** उच्च बारिश वाले दिनों में कीटनाशक छिड़काव से बचें।"
                    )
                elif lang == "hinglish":
                    lines = [f"• **{_day_name(fc.date, 'en')}:** {_get_fc_icon(fc.weather_description)} {fc.weather_description} · High **{fc.temp_max_c:.0f}°C** / Low **{fc.temp_min_c:.0f}°C** · Rain: **{fc.precipitation_probability_pct}%** (~{fc.precipitation_sum_mm:.1f} mm)" for fc in window_fcs]
                    breakdown_str = "\n".join(lines)
                    return (
                        f"📅 **{city} {count}-Day Comprehensive Weather Analysis:**\n\n"
                        f"📊 **Trend Summary:**\n"
                        f"• **Temperature Trend:** Highs between **{min(high_temps):.0f}°C – {max_high:.0f}°C**, lows around **{min_low:.0f}°C**.\n"
                        f"• **Precipitation:** **{rainy_days_count} of {count} days** have rain chances $\ge 40\%$. Total estimated rain: **~{total_rain:.1f} mm**.\n\n"
                        f"🗓️ **Daily Breakdown:**\n{breakdown_str}\n\n"
                        f"💡 **Guidance:** Rain wale dino mein compact umbrella zaroor carry karein."
                    )
                elif lang == "or":
                    lines = [f"• **{_day_name(fc.date, 'or')}:** {_get_fc_icon(fc.weather_description)} {fc.weather_description} · ସର୍ବାଧିକ **{fc.temp_max_c:.0f}°C** / ସର୍ବନିମ୍ନ **{fc.temp_min_c:.0f}°C** · ବର୍ଷା: **{fc.precipitation_probability_pct}%** (~{fc.precipitation_sum_mm:.1f} mm)" for fc in window_fcs]
                    breakdown_str = "\n".join(lines)
                    return (
                        f"📅 **{city} ପାଇଁ {count}-ଦିନର ବିସ୍ତୃତ ପାଣିପାଗ ପୂର୍ବାନୁମାନ ଓ ବିଶ୍ଳେଷଣ:**\n\n"
                        f"📊 **ମୁଖ୍ୟ ପାଣିପାଗ ଧାରା:**\n"
                        f"• **ତାପମାତ୍ରା:** ସର୍ବାଧିକ **{max_high:.0f}°C** ଏବଂ ସର୍ବନିମ୍ନ **{min_low:.0f}°C** ରହିବ।\n"
                        f"• **ବର୍ଷା ଆଶଙ୍କା:** {count} ଦିନ ମଧ୍ୟରୁ **{rainy_days_count} ଦିନ** ବର୍ଷା ସମ୍ଭାବନା ଅଛି (~{total_rain:.1f} mm)।\n\n"
                        f"🗓️ **ଦୈନିକ ପୂର୍ବାନୁମାନ ବିବରଣୀ:**\n{breakdown_str}\n\n"
                        f"💡 **ପରାମର୍ଶ:** ବାହାରକୁ ଯିବା ସମୟରେ ଛତା ସାଙ୍ଗରେ ରଖନ୍ତୁ।"
                    )
                lines = [f"• **{_day_name(fc.date, 'en')}:** {_get_fc_icon(fc.weather_description)} {fc.weather_description} · High **{fc.temp_max_c:.0f}°C** / Low **{fc.temp_min_c:.0f}°C** · Rain Risk: **{fc.precipitation_probability_pct}%** (~{fc.precipitation_sum_mm:.1f} mm) · Wind: {fc.max_wind_speed_kmh:.0f} km/h" for fc in window_fcs]
                breakdown_str = "\n".join(lines)
                return (
                    f"📅 **Meteorological Forecast & Trend Analysis for {city} ({count}-Day Outlook):**\n\n"
                    f"📊 **Atmospheric Trend Overview:**\n"
                    f"• **Thermal Profile:** Daytime highs steady between **{min(high_temps):.0f}°C – {max_high:.0f}°C** with night lows hovering near **{min_low:.0f}°C**.\n"
                    f"• **Precipitation Dynamics:** **{rainy_days_count} of {count} days** exhibit convective rain risk ($\ge 40\%$). Cumulative estimated rainfall: **~{total_rain:.1f} mm**.\n"
                    f"• **Wind & Flow:** Peak wind gusts reaching **{peak_wind:.0f} km/h**.\n\n"
                    f"🗓️ **Daily Meteorological Breakdown:**\n{breakdown_str}\n\n"
                    f"💡 **Practical Planning & Recommendations:**\n"
                    f"• **Commute & Travel:** Allow extra transit time on days with $\ge 50\%$ precipitation risk; wet roads will reduce tire traction.\n"
                    f"• **Outdoor Workouts:** Morning hours (6:00 AM – 8:30 AM) offer the most favorable dry windows before daytime solar heating triggers convective showers.\n"
                    f"• **Agro & Lawn Care:** Hold off on agrochemical spraying on high precipitation days to avoid runoff."
                )

        # 7. Clothes Drying / Laundry
        if resolved_query.intent == CanonicalIntent.CLOTHES_DRYING or _has_kw(["dry", "drying", "laundry", "clothes outside", "कपड़े सुखाना"]):
            if is_raining or humid > 80.0 or (is_future and target_fc and target_fc.precipitation_probability_pct > 40):
                return f"👕 **Keep laundry indoors in {city} {date_label_en}!** Rain or high humidity is expected. Clothes will not dry well outdoors. 🌧️"
            return f"👕 **Great day to dry laundry outside in {city} {date_label_en}!** Clear conditions and good ventilation expected. 🌤️"

        # 8. Drone Flying
        if _has_kw(["drone", "uav", "quadcopter", "ड्रोन"]):
            if is_raining or wind_val > 28.0:
                if lang == "hi":
                    return f"🚁 **आज {city} में ड्रोन उड़ाना सुरक्षित नहीं है!**\n\n• **कारण:** {'बारिश हो रही है' if is_raining else f'हवा की गति तेज है ({wind})'}।\n• **सुरक्षा सलाह:** ड्रोन के मोटर्स व इलेक्ट्रॉनिक्स को सुरक्षित रखने के लिए मौसम साफ़ और हवा शांत (<20 km/h) होने तक प्रतीक्षा करें।"
                return f"🚁 **Not recommended to fly a drone in {city} right now!**\n\n• **Hazard:** {'Active precipitation will damage electronic motors.' if is_raining else f'Wind speeds at {wind} exceed safe operational stability for consumer drones.'}\n• **Safety Window:** Wait for winds under 20 km/h and dry skies."
            if lang == "hi":
                return f"🚁 **हाँ! {city} में ड्रोन उड़ाने के लिए मौसम अनुकूल है!**\n\n• **हवा की गति:** {wind} (स्थिर व सुरक्षित)\n• **दृश्यता (Visibility):** {visibility} · बादल: {cloud_cover:.0f}%\n• **सलाह:** लाइन-ऑफ-साइट बनाए रखें और बैटरी तापमान पर ध्यान दें।"
            return f"🚁 **Good conditions for drone flying in {city}!**\n\n• **Wind Speed:** {wind} (within safe limits < 25 km/h)\n• **Visibility:** {visibility} · Cloud cover: {cloud_cover:.0f}%\n• Skies are favorable for aerial photography and flight stability."

        # 9. Stargazing
        if _has_kw(["stargaze", "stargazing", "telescope", "astronomy", "night sky", "तारों", "तारे देखने"]):
            if cloud_cover > 50.0 or is_raining:
                if lang == "hi":
                    return f"🔭 **आज रात {city} में तारे देखना (Stargazing) कठिन होगा।**\n\n• **बादल आवरण:** {cloud_cover:.0f}% ({cond})\n• **आर्द्रता:** {humid:.0f}%\n• बादलों के कारण आकाशीय पिंड स्पष्ट दिखाई नहीं देंगे।"
                return f"🔭 **Poor conditions for stargazing in {city} tonight.**\n\n• **Cloud Cover:** {cloud_cover:.0f}% ({cond})\n• **Humidity:** {humid:.0f}%\n• Dense cloud cover will obstruct telescope and naked-eye celestial visibility."
            if lang == "hi":
                return f"✨ **आज रात {city} में तारे देखने के लिए बेहतरीन रात है!**\n\n• **आसमान:** साफ़ ({cloud_cover:.0f}% बादल)\n• **दृश्यता:** {visibility}\n• टेलिस्कोप और खगोलीय अवलोकन के लिए परिस्थितियां आदर्श हैं।"
            return f"✨ **Excellent stargazing conditions in {city} tonight!**\n\n• **Cloud Cover:** Minimal ({cloud_cover:.0f}%)\n• **Atmospheric Visibility:** {visibility}\n• Clear atmospheric columns provide optimal clarity for astronomy and astrophotography."

        # 10. UV Radiation & Sunscreen
        if _has_kw(["uv", "uv index", "sunscreen", "sunburn", "sun tan", "tanning", "सनस्क्रीन"]):
            uv_advice_en = "Apply SPF 30+ sunscreen, wear UV-blocking sunglasses, and limit direct exposure between 11 AM – 3 PM." if uv >= 6.0 else "Minimal UV hazard; standard skincare is sufficient."
            if lang == "hi":
                return f"☀️ **{city} में यूवी (UV) इंडेक्स रिपोर्ट:**\n\n• **वर्तमान UV इंडेक्स:** **{uv:.1f}** ({'अत्यधिक / तीव्र' if uv >= 6.0 else 'सामान्य'})\n• **सुझाव:** {'SPF 30+ सनस्क्रीन लगाएं, धूप का चश्मा पहनें और दोपहर में सीधी धूप से बचें।' if uv >= 6.0 else 'यूवी जोखिम कम है, सामान्य रूप से बाहर निकल सकते हैं।'}"
            return f"☀️ **UV Radiation Index for {city}:**\n\n• **Current UV Level:** **{uv:.1f}** ({'High Solar Intensity' if uv >= 6.0 else 'Low-to-Moderate'})\n• **Action:** {uv_advice_en}"
            if any(w in raw_q_lower for w in ["spray", "pesticide", "fertilizer"]):
                if is_raining or (is_future and target_fc and target_fc.precipitation_probability_pct > 40):
                    return f"🌧️ **Hold off on spraying chemicals in {city} {date_label_en}!** Rain risk ({target_fc.precipitation_probability_pct if target_fc else 60}%) will wash away applied treatments."
                return f"✅ **Suitable window for spraying in {city} {date_label_en}!** Skies are dry, wind is manageable."
            if is_raining or (is_future and target_fc and target_fc.precipitation_probability_pct > 50):
                rain_pct = target_fc.precipitation_probability_pct if target_fc else 75
                if lang == "hi":
                    return f"🌱 **{date_label_hi} {city} में पौधों को पानी देने की आवश्यकता नहीं है!**\n\n• बारिश की संभावना सक्रिय है ({rain_pct}%), जिससे मिट्टी में प्राकृतिक नमी बनी रहेगी。"
                elif lang == "hinglish":
                    return f"🌱 **{date_label_hinglish} {city} mein paudho ko paani mat daalo!** Rain chances {rain_pct}% hain jisse soil naturally moist rahegi."
                return f"🌱 **Hold off on outdoor watering in {city} {date_label_en}!**\n\n• Rain is expected ({rain_pct}% chance), providing natural soil hydration."
            else:
                if lang == "hi":
                    return f"🌱 **हाँ, {date_label_hi} {city} में पौधों को पानी देने के लिए अच्छा दिन है!** सुबह या शाम के समय पानी दें।"
                elif lang == "hinglish":
                    return f"🌱 **Haan, {date_label_hinglish} {city} mein paudho ko paani dene ke liye accha din hai!** Morning ya evening mein dalein."
                return f"🌱 **Yes, {date_label_en} is a good day for gardening and watering plants in {city}!**\n\n• Water during early morning or late afternoon to minimize evaporation."

        # Q. Weekend & Multi-Day Forecast
        if resolved_query.intent == CanonicalIntent.WEATHER_FORECAST or any(w in raw_q_lower for w in ["weekend", "tomorrow", "forecast", "upcoming", "week", "sept", "september", "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "oct", "nov", "dec"]):
            if is_future and target_fc:
                if lang == "hi":
                    return f"📅 **{city} का मौसम पूर्वानुमान ({date_label_hi}):**\n\n• **अनुमानित मौसम:** {target_fc.weather_description}\n• **तापमान:** अधिकतम **{target_fc.temp_max_c:.1f}°C** / न्यूनतम **{target_fc.temp_min_c:.1f}°C**\n• **बारिश की संभावना:** **{target_fc.precipitation_probability_pct}%** ({target_fc.precipitation_sum_mm:.1f} mm)\n• **हवा की गति:** अधिकतम {target_fc.max_wind_speed_kmh:.0f} km/h"
                elif lang == "hinglish":
                    return f"📅 **{city} ka weather forecast ({date_label_hinglish}):**\n\n• **Expected:** {target_fc.weather_description}\n• **High/Low:** **{target_fc.temp_max_c:.1f}°C / {target_fc.temp_min_c:.1f}°C**\n• **Rain Risk:** **{target_fc.precipitation_probability_pct}%** ({target_fc.precipitation_sum_mm:.1f} mm)\n• **Max Wind:** {target_fc.max_wind_speed_kmh:.0f} km/h"
                elif lang == "or":
                    return f"📅 **{city} ର ପାଣିପାଗ ପୂର୍ବାନୁମାନ ({date_label_or}):**\n\n• **ଆକାଶ:** {target_fc.weather_description}\n• **ତାପମାତ୍ରା:** ସର୍ବାଧିକ **{target_fc.temp_max_c:.1f}°C** / ସର୍ବନିମ୍ନ **{target_fc.temp_min_c:.1f}°C**\n• **ବର୍ଷା ସମ୍ଭାବନା:** **{target_fc.precipitation_probability_pct}%** ({target_fc.precipitation_sum_mm:.1f} mm)\n• **ପବନର ଗତି:** {target_fc.max_wind_speed_kmh:.0f} km/h"
                return f"📅 **Weather Forecast for {city} ({date_label_en}):**\n\n• **Expected:** **{target_fc.weather_description}**\n• **High/Low:** **{target_fc.temp_max_c:.1f}°C / {target_fc.temp_min_c:.1f}°C**\n• **Rain Risk:** **{target_fc.precipitation_probability_pct}%** ({target_fc.precipitation_sum_mm:.1f} mm)\n• **Max Wind:** **{target_fc.max_wind_speed_kmh:.0f} km/h**"
            elif forecasts:
                lines = [f"• **{fc.date}:** {fc.weather_description} · {fc.temp_max_c:.0f}°C/{fc.temp_min_c:.0f}°C · Rain: {fc.precipitation_probability_pct}%" for fc in forecasts[:5]]
                return f"📅 **Upcoming 5-Day Forecast for {city}:**\n\n" + "\n".join(lines)

        # R. Outfit & Clothing
        if resolved_query.intent == CanonicalIntent.OUTFIT_RECOMMENDATION or any(w in raw_q_lower for w in ["wear", "wearing", "clothes", "jacket", "outfit"]):
            effective_temp = target_fc.temp_max_c if (is_future and target_fc) else temp_val
            effective_rain = (target_fc.precipitation_probability_pct > 40) if (is_future and target_fc) else is_raining
            if effective_rain:
                return f"🧥 **Outfit tip for {city} ({date_label_en}):** Rain is active or expected. Wear a **waterproof jacket or raincoat** and keep an **umbrella** handy! 🌧️"
            elif effective_temp < 18.0:
                return f"🧥 **Outfit tip for {city} ({date_label_en}):** It will be cool at **{effective_temp:.0f}°C**. A **sweater, warm hoodie, or jacket** will keep you comfortable! ❄️"
            elif effective_temp <= 30.0:
                return f"👕 **Outfit tip for {city} ({date_label_en}):** Pleasant weather (**{effective_temp:.0f}°C**). Standard **breathable cotton clothes or casual wear** are ideal! 🌤️"
            else:
                return f"👕 **Outfit tip for {city} ({date_label_en}):** It's warm (**{effective_temp:.0f}°C**). Wear **lightweight, loose cotton clothing**, wear sunglasses for sun protection, and stay hydrated! ☀️"



        # U. Default Targeted / Current Weather Snapshot
        if is_future and target_fc:
            if lang == "hi":
                return f"📅 **{city} का मौसम पूर्वानुमान ({date_label_hi}):**\n\n• **मौसम:** {target_fc.weather_description}\n• **तापमान:** अधिकतम **{target_fc.temp_max_c:.1f}°C** / न्यूनतम **{target_fc.temp_min_c:.1f}°C**\n• **बारिश की संभावना:** {target_fc.precipitation_probability_pct}%\n• **हवा:** {target_fc.max_wind_speed_kmh:.0f} km/h"
            elif lang == "hinglish":
                return f"📅 **{city} ka weather ({date_label_hinglish}):**\n\n• **Condition:** {target_fc.weather_description}\n• **High/Low:** **{target_fc.temp_max_c:.1f}°C / {target_fc.temp_min_c:.1f}°C**\n• **Rain Risk:** {target_fc.precipitation_probability_pct}%\n• **Wind:** {target_fc.max_wind_speed_kmh:.0f} km/h"
            elif lang == "or":
                return f"📅 **{city} ର ପାଣିପାଗ ପୂର୍ବାନୁମାନ ({date_label_or}):**\n\n• **ଆକାଶ:** {target_fc.weather_description}\n• **ତାପମାତ୍ରା:** ସର୍ବାଧିକ **{target_fc.temp_max_c:.1f}°C** / ସର୍ବନିମ୍ନ **{target_fc.temp_min_c:.1f}°C**\n• **ବର୍ଷା ସମ୍ଭାବନା:** {target_fc.precipitation_probability_pct}%"
            return f"📅 **Weather Forecast for {city} ({date_label_en}):**\n\n• **Condition:** **{target_fc.weather_description}**\n• **High / Low:** **{target_fc.temp_max_c:.1f}°C / {target_fc.temp_min_c:.1f}°C**\n• **Rain Probability:** **{target_fc.precipitation_probability_pct}%** ({target_fc.precipitation_sum_mm:.1f} mm)\n• **Max Wind Speed:** **{target_fc.max_wind_speed_kmh:.0f} km/h**"

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

        # 8. MULTILINGUAL TRANSLATION (Only if response is still purely English for a regional query)
        def _has_indic_script(text: str) -> bool:
            return any(ord(c) > 127 for c in text)

        translated_answer = None
        if target_lang != "en" and structured_query.language != "hinglish":
            if _has_indic_script(english_answer):
                translated_answer = english_answer
            else:
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
