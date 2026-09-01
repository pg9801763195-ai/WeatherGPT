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
        Synthesizes natural, authoritative responses strictly routed by resolved_query.intent
        and grounded in real meteorological telemetry.
        """
        intent = resolved_query.intent
        lang = resolved_query.language
        city = resolved_query.location or (weather.location.name if weather else "your location")
        temp = f"{weather.temperature_c:.1f}°C" if weather else "24.0°C"
        temp_val = weather.temperature_c if weather else 24.0
        cond = weather.weather_description.lower() if weather else "clear sky"
        precip = weather.precipitation_mm if weather else 0.0
        humid = weather.relative_humidity_pct if weather else 70.0
        wind = f"{weather.wind_speed_kmh:.0f} km/h" if weather else "10 km/h"
        is_raining = precip > 0 or "rain" in cond or "drizzle" in cond
        crop = resolved_query.crop or (advisory.target_crop if advisory else "Paddy")

        # Future Forecast Selectors
        fc_tomorrow = forecasts[1] if forecasts and len(forecasts) > 1 else (forecasts[0] if forecasts else None)
        fc_day_after = forecasts[2] if forecasts and len(forecasts) > 2 else None
        time_ref = resolved_query.time_reference or "today"

        # =============================================================
        # 0. LOCATION INFO INTENT ("what's my location?", "where am I?")
        # =============================================================
        if intent == CanonicalIntent.LOCATION_INFO:
            if lang in ["hi", "hinglish"]:
                return f"Aap abhi **{city}** ka mausam dekh rahe hain."
            return f"You're currently viewing weather for **{city}**."

        # =============================================================
        # 1. CASUAL CONVERSATION INTENT (No unasked weather dumps)
        # =============================================================
        if intent == CanonicalIntent.CASUAL_CONVERSATION:
            raw_q = (resolved_query.entities.get("raw_query") or "").lower()
            if any(w in raw_q for w in ["joke", "funny", "laugh"]):
                jokes = [
                    "Why did the cloud stay home from work? It was feeling a little under the weather! ☁️😄",
                    "What did one raindrop say to the other? Two's company, three's a cloud! 🌧️",
                    "What kind of shorts do clouds wear? Thunderwear! ⚡😂"
                ]
                import random
                return f"Here's one for you:\n\n{random.choice(jokes)}"

            if any(w in raw_q for w in ["thank", "thanks", "thx", "shukriya", "dhanyawad"]):
                if lang in ["hi", "hinglish"]:
                    return "Shukriya bhai! Always glad to help. Kuch aur poochna ho toh bejhijhak batao! 😊"
                return "You're very welcome! Always happy to help. Let me know if you need anything else! 😊"

            if any(w in raw_q for w in ["bye", "good night", "goodnight", "see you"]):
                if lang in ["hi", "hinglish"]:
                    return "Good night! Apna khayal rakhna aur badhiya aaram karo. 🌙"
                return "Good night and take care! Have a great rest. 🌙"

            if any(w in raw_q for w in ["hinglish", "hindi me", "baat kar sakte", "who are you", "who made you"]):
                return "Haan bilkul! Main **WeatherGPT (MausamVani)** hoon. Main English, Hindi, Hinglish, Telugu, Tamil, Marathi aur regional bhashaon mein baat kar sakta hoon. Bataiye, kya madad karoon? 😊"

            if lang in ["hi", "hinglish"]:
                return "Main bilkul badhiya hoon bhai! Aap batao, sab kaisa chal raha hai aur main aapki kya madad kar sakta hoon?"
            return "Hey there! I'm doing great. How's your day going? What can I help you with today?"

        # =============================================================
        # 2. OUTFIT RECOMMENDATION INTENT ("what clothes should i wear??")
        # =============================================================
        if intent == CanonicalIntent.OUTFIT_RECOMMENDATION:
            if is_raining:
                if lang in ["hi", "hinglish"]:
                    return f"🧥 **Outfit tip for {city}:** Abhi {city} mein **{temp}** ke sath barish ho rahi hai. Bahar nikalte waqt **raincoat ya waterproof jacket** pehno aur **chata (umbrella)** zaroor saath rakho! 🌧️"
                return f"🧥 **Outfit tip for {city}:** It's currently **{temp}** with active rain. Definitely wear a **raincoat or waterproof jacket** and keep an **umbrella** handy! 🌧️"
            elif temp_val < 15.0:
                if lang in ["hi", "hinglish"]:
                    return f"🧥 **Outfit tip for {city}:** Abhi {city} mein thand hai (**{temp}**). Ek **warm jacket, sweater ya hoodie** pehnna comfortable rahega! ❄️"
                return f"🧥 **Outfit tip for {city}:** It's quite cool at **{temp}**. A **warm jacket, sweater, or hoodie** will keep you comfortable! ❄️"
            elif temp_val < 22.0:
                if lang in ["hi", "hinglish"]:
                    return f"🧥 **Outfit tip for {city}:** Mausam thoda thanda hai (**{temp}**). Ek **light jacket, sweatshirt ya full-sleeve shirt** acchi rahegi. 🍂"
                return f"🧥 **Outfit tip for {city}:** It's a bit brisk at **{temp}**. A **light jacket, cardigan, or long-sleeve layer** is recommended. 🍂"
            elif temp_val <= 30.0:
                if lang in ["hi", "hinglish"]:
                    return f"👕 **Outfit tip for {city}:** {city} mein mausam comfortable hai (**{temp}**, {cond}). Normal **cotton t-shirt/shirt aur casual wear** bilkul sahi rahega! 🌤️"
                return f"👕 **Outfit tip for {city}:** Pleasant and comfortable weather in {city} (**{temp}**, {cond}). Standard **casual wear or breathable cotton clothes** are perfect today! 🌤️"
            else:
                if lang in ["hi", "hinglish"]:
                    return f"👕 **Outfit tip for {city}:** {city} mein garmi hai (**{temp}**). **Light, loose-fitting cotton kapde** pehnein, dhoop se bachne ke liye sunglasses/cap lagayein aur paani peete rahein! ☀️"
                return f"👕 **Outfit tip for {city}:** It's warm at **{temp}**. Wear **lightweight, breathable cotton clothing**, consider sunglasses/hat for sun protection, and stay well hydrated! ☀️"

        # =============================================================
        # 3. CLOTHES DRYING INTENT ("can I dry my clothes outside?")
        # =============================================================
        if intent == CanonicalIntent.CLOTHES_DRYING:
            if is_raining or humid > 85.0:
                if lang in ["hi", "hinglish"]:
                    return f"👕 **Kapde bahar mat daaliye!** {city} mein abhi barish/nami hai ({temp}, humidity {humid:.0f}%). Kapde andar hi sukhayein taaki geelapan aur badbu na aaye. 🌧️"
                return f"👕 **Keep the laundry indoors today!** In **{city}**, conditions are rainy/humid ({temp}, humidity {humid:.0f}%). Clothes will not dry well outdoors. 🌧️"
            else:
                if lang in ["hi", "hinglish"]:
                    return f"👕 **Haan, {city} mein kapde bahar daal sakte hain!** Mausam **{cond}** hai aur hawa {wind} ki raftaar se chal rahi hai ({temp}), kapde jaldi sookh jayenge. 🌤️"
                return f"👕 **Great day to hang laundry outside in {city}!** Skies are **{cond}** with winds at **{wind}** and {temp}, which will dry your clothes quickly. 🌤️"

        # =============================================================
        # 4. TRAVEL WEATHER & SIGHTSEEING ("kal Patratu ghumne jau kya?")
        # =============================================================
        if intent == CanonicalIntent.TRAVEL_WEATHER:
            target_fc = fc_tomorrow if time_ref == "tomorrow" else (fc_day_after if time_ref == "day_after_tomorrow" else None)
            if target_fc:
                t_max = f"{target_fc.temp_max_c:.1f}°C"
                t_min = f"{target_fc.temp_min_c:.1f}°C"
                rain_p = target_fc.precipitation_probability_pct
                rain_s = f"{target_fc.precipitation_sum_mm:.1f} mm"
                desc = target_fc.weather_description
                wind_fc = f"{target_fc.max_wind_speed_kmh:.0f} km/h"
                time_label = "Kal" if time_ref == "tomorrow" else ("Parso" if time_ref == "day_after_tomorrow" else "Agle din")
                time_label_en = "Tomorrow" if time_ref == "tomorrow" else ("Day after tomorrow" if time_ref == "day_after_tomorrow" else "The upcoming day")

                if rain_p >= 45 or "thunderstorm" in desc.lower() or "heavy rain" in desc.lower():
                    if lang in ["hi", "hinglish"]:
                        return (
                            f"🌧️ **{time_label} {city} ghumne jana thoda mushkil ho sakta hai.**\n\n"
                            f"{time_label} {city} mein barish ki sambhavna **{rain_p}%** hai ({rain_s} anumanit barish) aur mausam **{desc}** rahega. Hawa {wind_fc} ki speed se chal sakti hai.\n\n"
                            f"💡 **Salah:** Agar aap trip plan kar rahe hain toh umbrella/raincoat zaroor saath rakhein ya mausam khulne tak plan postpone karna behtar rahega."
                        )
                    return (
                        f"🌧️ **Visiting {city} {time_label_en.lower()} may face weather challenges.**\n\n"
                        f"There is a **{rain_p}% chance of rain** ({rain_s}) with **{desc}** conditions and winds up to {wind_fc}. Highs will reach **{t_max}** / Lows **{t_min}**.\n\n"
                        f"💡 **Tip:** Keep rain gear handy or consider postponing outdoor sightseeing."
                    )
                else:
                    if lang in ["hi", "hinglish"]:
                        return (
                            f"🌤️ **Haan! {time_label} {city} ghumne ke liye badhiya din hai!**\n\n"
                            f"Mausam mukhyatah **{desc}** rahega.\n"
                            f"• **Temperature:** Max **{t_max}** · Min **{t_min}**\n"
                            f"• **Barish ke chances:** Sirf **{rain_p}%** ({rain_s})\n"
                            f"• **Hawa ki speed:** **{wind_fc}**\n\n"
                            f"Mausam comfortable rahega, aap ghumne ka plan bana sakte hain! 🚗"
                        )
                    return (
                        f"🌤️ **Yes! {time_label_en} looks great for a trip to {city}!**\n\n"
                        f"Conditions: **{desc}**\n"
                        f"• **Temperature:** High **{t_max}** · Low **{t_min}**\n"
                        f"• **Rain Risk:** Only **{rain_p}%** ({rain_s})\n"
                        f"• **Wind Speed:** **{wind_fc}**\n\n"
                        f"Weather is favorable for outdoor travel and sightseeing! 🚗"
                    )
            else:
                if is_raining:
                    if lang in ["hi", "hinglish"]:
                        return f"🌧️ **Abhi {city} mein barish ho rahi hai ({temp}, {cond})**, isliye bahar ghumne nikalte waqt chata zaroor le lena ya barish thamne ka wait karein."
                    return f"🌧️ **It is currently raining in {city} ({temp}, {cond}).** We recommend keeping an umbrella handy if you're heading out for sightseeing."
                if lang in ["hi", "hinglish"]:
                    return f"🌤️ **Haan, aaj {city} mein mausam saaf hai ({temp}, {cond})!** Aap ghumne ja sakte hain."
                return f"🌤️ **Great weather for an outing in {city} today!** Current temperature is **{temp}** with {cond} skies."

        # =============================================================
        # 5. OUTDOOR ACTIVITY (Cricket, Sports, Car Wash)
        # =============================================================
        if intent == CanonicalIntent.OUTDOOR_ACTIVITY:
            act = resolved_query.activity or "general_outdoor"
            if act == "cricket" or "cricket" in (resolved_query.entities.get("raw_query") or "").lower():
                if is_raining:
                    if lang in ["hi", "hinglish"]:
                        return f"🏏 **Abhi bahar cricket khelna mushkil hai** — {city} mein barish ho rahi hai ({temp}) aur ground geela hoga. Mausam khulne ka intezaar karo!"
                    return f"🏏 **Not suitable for cricket in {city} right now.** It's currently raining ({temp}) and pitch/outfield conditions will be wet."
                if lang in ["hi", "hinglish"]:
                    return f"🏏 **Mausam badhiya hai!** {city} mein abhi {temp} temperature hai aur barish nahi hai, aap cricket khel sakte hain."
                return f"🏏 **Great conditions for cricket in {city}!** Temperature is **{temp}** with {cond} skies and gentle wind ({wind})."

            if act == "car_wash" or "car" in (resolved_query.entities.get("raw_query") or "").lower():
                if is_raining:
                    if lang in ["hi", "hinglish"]:
                        return f"🚗 **Aaj gaadi mat dhoiye!** {city} mein barish chal rahi hai, sadak par keechad aur paani se gaadi turant gandi ho jayegi."
                    return f"🚗 **I'd recommend skipping the car wash today!** It's currently raining in **{city}** ({temp}), so wet and muddy roads will dirty your car right away."
                if lang in ["hi", "hinglish"]:
                    return f"🚗 **Haan, aaj gaadi wash karne ke liye accha din hai!** Mausam saaf hai ({temp}, {cond})."
                return f"🚗 **Great day for a car wash!** Skies in **{city}** are **{cond}** with low rain risk."

            # General outdoor
            if is_raining:
                return f"🌧️ Outdoor activities in **{city}** may be disrupted by active rain ({temp})."
            return f"🌤️ Conditions in **{city}** are favorable for outdoor activities ({temp}, {cond})."

        # =============================================================
        # 6. WEATHER FORECAST (Tomorrow, Parso, Multi-Day)
        # =============================================================
        if intent == CanonicalIntent.WEATHER_FORECAST:
            if time_ref == "tomorrow" and fc_tomorrow:
                t_max = f"{fc_tomorrow.temp_max_c:.1f}°C"
                t_min = f"{fc_tomorrow.temp_min_c:.1f}°C"
                rain_p = fc_tomorrow.precipitation_probability_pct
                rain_s = f"{fc_tomorrow.precipitation_sum_mm:.1f} mm"
                fc_desc = fc_tomorrow.weather_description
                fc_wind = f"{fc_tomorrow.max_wind_speed_kmh:.0f} km/h"

                if lang in ["hi", "hinglish"]:
                    return (
                        f"📅 **Kal {city} ka mausam:**\n\n"
                        f"Kal **{fc_desc}** rehne ki sambhavna hai.\n"
                        f"• **Temperature:** Max **{t_max}** · Min **{t_min}**\n"
                        f"• **Barish ke chances:** **{rain_p}%** ({rain_s})\n"
                        f"• **Hawa ki speed:** **{fc_wind}**"
                    )
                return (
                    f"📅 **Tomorrow's Forecast for {city}:**\n\n"
                    f"Expected skies: **{fc_desc}**\n"
                    f"• **Temperature:** High **{t_max}** · Low **{t_min}**\n"
                    f"• **Precipitation Risk:** **{rain_p}%** ({rain_s})\n"
                    f"• **Wind Speed:** up to **{fc_wind}**"
                )

            if time_ref == "day_after_tomorrow" and fc_day_after:
                if lang in ["hi", "hinglish"]:
                    return (
                        f"📅 **Parso {city} ka mausam:**\n\n"
                        f"Mausam **{fc_day_after.weather_description}** rahega.\n"
                        f"• **Temperature:** Max **{fc_day_after.temp_max_c:.1f}°C** · Min **{fc_day_after.temp_min_c:.1f}°C**\n"
                        f"• **Barish ke chances:** **{fc_day_after.precipitation_probability_pct}%**"
                    )
                return (
                    f"📅 **Day After Tomorrow Forecast for {city}:**\n\n"
                    f"Conditions: **{fc_day_after.weather_description}**\n"
                    f"• **Temperature:** High **{fc_day_after.temp_max_c:.1f}°C** · Low **{fc_day_after.temp_min_c:.1f}°C**\n"
                    f"• **Precipitation Probability:** **{fc_day_after.precipitation_probability_pct}%**"
                )

            if time_ref in ["next_3_days", "next_7_days", "weekend"] and forecasts:
                lines = []
                for fc in forecasts[:4]:
                    lines.append(f"• **{fc.date}:** {fc.weather_description} · {fc.temp_max_c:.0f}°C/{fc.temp_min_c:.0f}°C · Rain: {fc.precipitation_probability_pct}%")
                if lang in ["hi", "hinglish"]:
                    return f"📅 **{city} ka agle kuch din ka forecast:**\n\n" + "\n".join(lines)
                return f"📅 **Upcoming Forecast for {city}:**\n\n" + "\n".join(lines)

        # =============================================================
        # 7. PRECIPITATION / RAIN INTENT ("will it rain?")
        # =============================================================
        if intent == CanonicalIntent.PRECIPITATION:
            if time_ref == "tomorrow" and fc_tomorrow:
                rain_p = fc_tomorrow.precipitation_probability_pct
                rain_s = f"{fc_tomorrow.precipitation_sum_mm:.1f} mm"
                if rain_p >= 45:
                    if lang in ["hi", "hinglish"]:
                        return f"🌧️ **Haan, kal {city} mein barish hone ke sambhavna {rain_p}% hai** ({rain_s} anumanit barish). Chata saath rakhein."
                    return f"🌧️ **Yes, expect rain in {city} tomorrow!** Probability is **{rain_p}%** with around **{rain_s}** precipitation. Keep an umbrella handy."
                else:
                    if lang in ["hi", "hinglish"]:
                        return f"☀️ **Nahi, kal {city} mein barish ke chances kam hain ({rain_p}%).** Mausam mukhyatah saaf rahega."
                    return f"☀️ **No significant rain expected in {city} tomorrow.** Rain probability is only **{rain_p}%**."

            if is_raining:
                if lang in ["hi", "hinglish"]:
                    return f"🌧️ **Haan, abhi {city} mein barish ho rahi hai!**\n\nTemperature **{temp}** hai aur barish jari hai ({precip:.1f} mm/h). Bahar nikalte waqt chata zaroor le lena."
                return f"🌧️ **Yes, it is raining in {city}!** Current temperature is **{temp}** with active rain ({precip:.1f} mm/h). Make sure to carry an umbrella if you're heading outside."
            else:
                rain_prob = forecasts[0].precipitation_probability_pct if forecasts else 15
                if rain_prob >= 40:
                    if lang in ["hi", "hinglish"]:
                        return f"🌦️ **Aaj {city} mein barish ke {rain_prob}% chances hain.** Abhi temperature **{temp}** hai aur aakash mein {cond} hai. Chata saath rakhna accha rahega."
                    return f"🌦️ There is a **{rain_prob}% chance of rain** later today in **{city}** ({temp}, {cond}). Keeping a small umbrella handy is a good idea."
                else:
                    if lang in ["hi", "hinglish"]:
                        return f"☀️ **Nahi, aaj {city} mein barish ke chances kam hain.** Mausam {cond} rahega aur temperature **{temp}** ke aas paas rahega."
                    return f"☀️ **No rain expected right now in {city}.** Skies are **{cond}** and temperature is **{temp}**."

        # =============================================================
        # 8. AGRO / FARMING ADVISORY
        # =============================================================
        if intent == CanonicalIntent.AGRO_ADVISORY:
            spray_safe = advisory.spray_window_safe if advisory else not is_raining
            if is_raining or not spray_safe:
                if lang in ["hi", "hinglish"]:
                    return (
                        f"🌧️ **Abhi {city} mein {crop} ki fasal mein spray mat karna.**\n\n"
                        f"Barish/nami ke karan dawa beh sakti hai. Mausam saaf hone tak intezaar karein.\n\n"
                        f"💡 **Salah:** Spray postpone karein aur drainage open rakhein."
                    )
                return (
                    f"🌧️ **Hold off on spraying {crop} in {city} today.**\n\n"
                    f"Current conditions ({temp}, active rain/moisture) will wash away applied chemicals.\n\n"
                    f"💡 **Tip:** Postpone spraying until dry, calm weather returns."
                )
            else:
                if lang in ["hi", "hinglish"]:
                    return f"✅ **Haan, aaj {city} mein {crop} mein spray kiya ja sakta hai!** Mausam saaf hai ({temp}), hawa {wind} hai."
                return f"✅ **Suitable window for spraying {crop} in {city} today!** Skies are clear, temperature is **{temp}**, and wind is gentle ({wind})."

        # =============================================================
        # 9. NWP / METEOROLOGY ANALYSIS
        # =============================================================
        if intent == CanonicalIntent.NWP_ANALYSIS:
            cape = nwp.cape_surface_j_kg if nwp else 450.0
            risk = "high thunderstorm chance" if cape > 1500 else "moderate convective activity" if cape > 800 else "stable atmospheric column"
            return f"🌀 **NWP GFS Model Diagnostic for {city}:** Surface CAPE is **{cape:.0f} J/kg** with CIN **{nwp.cin_surface_j_kg if nwp else 0.0:.0f} J/kg**, signaling **{risk}** over the next 24 hours."

        # =============================================================
        # 10. EXTREME WEATHER ALERTS
        # =============================================================
        if intent == CanonicalIntent.WEATHER_ALERT:
            if alerts and alerts[0].severity != AlertSeverity.GREEN:
                al = alerts[0]
                return f"⚠️ **{al.headline}**\n\n{al.description}\n\n**Action:** {al.suggested_action}"
            return f"✅ **No active severe weather alerts for {city}.** Meteorological conditions are within nominal safety thresholds."

        # =============================================================
        # 11. HISTORICAL CLIMATE
        # =============================================================
        if intent == CanonicalIntent.HISTORICAL_CLIMATE and climate:
            return (
                f"📈 **Historical Climate Analysis for {city} ({climate.start_year}–{climate.end_year}):**\n\n"
                f"• **Mean Temperature Shift:** +{climate.mean_temp_change_c:.2f}°C\n"
                f"• **Monsoon Rainfall Anomaly:** {climate.monsoon_rainfall_anomaly_pct:+.1f}%\n"
                f"• **Heatwave Escalation:** +{climate.heatwave_days_per_decade:.1f} days/decade"
            )

        # =============================================================
        # 12. CURRENT WEATHER (Default Intent)
        # =============================================================
        if lang in ["hi", "hinglish"]:
            return f"🌤️ **{city}** mein abhi temperature **{temp}** hai aur mausam **{cond}** hai. Humidity {humid:.0f}% aur hawa {wind} ki speed se chal rahi hai."
        return f"🌤️ In **{city}**, it is currently **{temp}** with **{cond}**.\n\nHumidity is {humid:.0f}% and wind is {wind}."

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
        target_lang = input_data.language_code or structured_query.language
        if target_lang == "auto":
            target_lang = structured_query.language

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

        print(
            f"[LOCATION TRACE]\n"
            f"frontend_location={frontend_loc}\n"
            f"query_explicit_location={query_loc}\n"
            f"resolved_query_location={structured_query.location}\n"
            f"weather_request_location={location_name} ({geo.latitude}, {geo.longitude})\n"
            f"weather_response_location={cur_weather.location.name if cur_weather else 'N/A'}\n"
            f"final_response_location={display_location}\n",
            flush=True
        )
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
