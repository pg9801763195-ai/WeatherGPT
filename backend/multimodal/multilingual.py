"""
Indian Multilingual Processing & Localization Engine.
Generates simple, conversational, humanized responses for Hindi, Telugu, Tamil,
Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi, and Odia.
"""
import re
from typing import Optional, Dict, Any, List
from config import AgentConfig


# Unicode ranges for major Indian scripts
SCRIPT_MAP = {
    "hi": range(0x0900, 0x097F),  # Devanagari (Hindi, Marathi)
    "bn": range(0x0980, 0x09FF),  # Bengali
    "pa": range(0x0A00, 0x0A7F),  # Gurmukhi (Punjabi)
    "gu": range(0x0A80, 0x0AFF),  # Gujarati
    "or": range(0x0B00, 0x0B7F),  # Odia
    "ta": range(0x0B80, 0x0BFF),  # Tamil
    "te": range(0x0C00, 0x0C7F),  # Telugu
    "kn": range(0x0C80, 0x0CFF),  # Kannada
    "ml": range(0x0D00, 0x0D7F)   # Malayalam
}

WEATHER_CONDITIONS: Dict[str, Dict[str, str]] = {
    "hi": {
        "clear sky": "साफ धूप",
        "sunny": "धूप",
        "mainly clear": "साफ मौसम",
        "partly cloudy": "हल्के बादल",
        "overcast": "बादल छाए हुए",
        "fog": "कोहरा",
        "drizzle": "हल्की बूंदाबांदी",
        "light rain": "हल्की बारिश",
        "moderate rain": "बारिश",
        "heavy rain": "भारी बारिश",
        "heavy intensity rain": "तेज बारिश",
        "thunderstorm": "गरज-चमक के साथ बारिश"
    },
    "te": {
        "clear sky": "నిర్మలమైన ఆకాశం",
        "sunny": "ఎండ",
        "partly cloudy": "పాక్షిక మేఘాలు",
        "overcast": "దట్టమైన మేఘాలు",
        "light rain": "తేలికపాటి వర్షం",
        "moderate rain": "వర్షం",
        "heavy rain": "భారీ వర్షం",
        "thunderstorm": "ఉరుములతో కూడిన వర్షం"
    },
    "ta": {
        "clear sky": "தெளிவான வானம்",
        "sunny": "வெயில்",
        "partly cloudy": "லேசான மேகம்",
        "overcast": "மேகமூட்டம்",
        "light rain": "லேசான மழை",
        "moderate rain": "மழை",
        "heavy rain": "கனமழை",
        "thunderstorm": "இடி மின்னல் மழை"
    },
    "mr": {
        "clear sky": "स्वच्छ आकाश",
        "sunny": "ऊन",
        "partly cloudy": "अंशतः ढगाळ",
        "overcast": "ढगाळ वातावरण",
        "light rain": "हलका पाऊस",
        "moderate rain": "पाऊस",
        "heavy rain": "मुसळधार पाऊस",
        "thunderstorm": "वादळी पाऊस"
    },
    "bn": {
        "clear sky": "পরিষ্কার আকাশ",
        "sunny": "রোদ",
        "partly cloudy": "আংশিক মেঘলা",
        "overcast": "মেঘলা",
        "light rain": "হালকা বৃষ্টি",
        "moderate rain": "বৃষ্টি",
        "heavy rain": "ভারী বৃষ্টি",
        "thunderstorm": "ঝড়-বৃষ্টি"
    }
}


class IndicLanguageEngine:
    """Handles script detection and simple, natural, conversational Indian language synthesis."""

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()

    def detect_language(self, text: str) -> str:
        """Detect Indian regional script or default to English."""
        if not text:
            return "en"

        marathi_keywords = ["आहे", "कसा", "पाऊस", "पिकांची", "शेती", "हवामान", "वारं", "करावी", "का"]
        script_scores = {k: 0 for k in SCRIPT_MAP.keys()}

        for char in text:
            code = ord(char)
            for lang, crange in SCRIPT_MAP.items():
                if code in crange:
                    script_scores[lang] += 1

        top_lang = max(script_scores, key=script_scores.get)
        if script_scores[top_lang] > 1:
            if top_lang == "hi":
                if any(w in text for w in marathi_keywords):
                    return "mr"
            return top_lang

        return "en"

    def generate_native_language_response(
        self,
        lang: str,
        query: str,
        weather: Any,
        forecasts: List[Any],
        nwp: Any,
        alerts: List[Any],
        advisory: Any,
        climate: Optional[Any] = None
    ) -> str:
        """
        Generates clean, humanized, simple responses with zero bureaucratic clutter.
        """
        q = query.lower()
        city = weather.location.name
        temp = f"{weather.temperature_c:.1f}°C"
        feels = f"{weather.apparent_temperature_c:.1f}°C"
        cond_raw = weather.weather_description.lower()
        cond = WEATHER_CONDITIONS.get(lang, {}).get(cond_raw, cond_raw)
        humid = f"{weather.relative_humidity_pct:.0f}%"
        wind = f"{weather.wind_speed_kmh:.0f} km/h"
        precip = weather.precipitation_mm
        is_raining = precip > 0 or "rain" in cond_raw or "drizzle" in cond_raw

        crop_hi_map = {
            "Paddy": "धान", "Rice": "धान", "Cotton": "कपास", "Wheat": "गेहूं",
            "Mustard": "सरसों", "Soybean": "सोयाबीन", "Tomato": "टमाटर", "Chilli": "मिर्च"
        }
        crop = crop_hi_map.get(advisory.target_crop if advisory else "फसल", "फसल")

        # -------------------------------------------------------------
        # 1. HINDI (हिन्दी) - Simple & Humanized
        # -------------------------------------------------------------
        if lang == "hi":
            # (A) Casual Greetings - Pure conversational response
            if re.search(r"^(नमस्ते|प्रणाम|हेलो|हाय|हे|शुभ प्रभात|शुभ संध्या|आप कौन हैं|मदद|कैसे हो|क्या हाल)", query) or any(w in q for w in ["hello", "hi", "namaste", "hii", "heyy"]):
                return "नमस्ते! मैं आपकी क्या मदद कर सकता हूँ? आप मुझसे मौसम, बारिश, कल के पूर्वानुमान या फसलों की सलाह के बारे में पूछ सकते हैं। 😊"

            # (B) Farming / Spray / Crop Query
            if any(w in query for w in ["छिड़काव", "स्प्रे", "फसल", "धान", "कपास", "गेहूं", "सरसों", "सिंचाई", "कीट", "दवा", "खाद", "spray", "crop", "paddy", "cotton", "farming"]):
                if is_raining or not advisory.spray_window_safe:
                    return (
                        f"🌧️ **आज {city} में बारिश हो रही है, इसलिए {crop} की फसल में छिड़काव न करें।**\n\n"
                        f"अभी तापमान **{temp}** है और बारिश जारी है। अगर आप अभी दवा डालेंगे तो वह पानी के साथ बह जाएगी और फायदा नहीं होगा।\n\n"
                        f"💡 **आज के लिए सलाह:**\n"
                        f"• **छिड़काव टालें:** मौसम साफ होने तक रुकें।\n"
                        f"• **सिंचाई न करें:** बारिश काफी है, खेतों से फालतू पानी निकलने का रास्ता खुला रखें।"
                    )
                else:
                    return (
                        f"✅ **हाँ, आज {city} में मौसम साफ है और {crop} में छिड़काव किया जा सकता है।**\n\n"
                        f"वर्तमान तापमान **{temp}** है और हवा की गति सामान्य ({wind}) है, जिससे दवा सही तरीके से लगेगी।"
                    )

            # (C) Rain / Umbrella Query
            if any(w in query for w in ["बारिश", "पानी", "वर्षा", "छाता", "बरसात", "rain", "umbrella"]):
                if is_raining:
                    return (
                        f"🌧️ **हाँ, अभी {city} में बारिश हो रही है!**\n\n"
                        f"तापमान **{temp}** है और बारिश हो रही है। बाहर जाते समय छाता या रेनकोट जरूर साथ रखें।"
                    )
                else:
                    rain_prob = forecasts[0].precipitation_probability_pct if forecasts else 20
                    if rain_prob >= 40:
                        return (
                            f"🌦️ **आज {city} में बारिश के {rain_prob}% आसार हैं।**\n\n"
                            f"अभी तापमान **{temp}** है और {cond} है। सावधानी के लिए छाता साथ रखना अच्छा रहेगा।"
                        )
                    else:
                        return (
                            f"☀️ **नहीं, आज {city} में बारिश की संभावना नहीं है।**\n\n"
                            f"आसमान **{cond}** रहेगा और तापमान **{temp}** के आसपास बना रहेगा।"
                        )

            # (D) Temperature / Weather in general
            return (
                f"🌤️ **{city} में अभी {temp} तापमान है और {cond} है।**\n\n"
                f"हवा में नमी **{humid}** और हवा की गति **{wind}** है।"
            )

        # -------------------------------------------------------------
        # 2. TELUGU (తెలుగు) - Simple & Humanized
        # -------------------------------------------------------------
        if lang == "te":
            if any(w in query for w in ["spray", "వరి", "పత్తి", "పిచికారీ", "సాగు"]):
                if is_raining:
                    return (
                        f"🌧️ **ఈరోజు {city} లో వర్షం పడుతోంది, కాబట్టి పంటలపై మందులు పిచికారీ చేయవద్దు.**\n\n"
                        f"ప్రస్తుత ఉష్ణోగ్రత **{temp}**. వర్షం వల్ల మందు కొట్టుకుపోతుంది. వాతావరణం పొడిగా ఉండే వరకు ఆగండి."
                    )
                return f"✅ **ఈరోజు {city} లో వాతావరణం బాగుంది ({temp}), పిచికారీ చేసుకోవచ్చు.**"
            return f"🌤️ **{city} లో ప్రస్తుతం ఉష్ణోగ్రత {temp}, ఆకాశం {cond}.**"

        # -------------------------------------------------------------
        # 3. TAMIL (தமிழ்) - Simple & Humanized
        # -------------------------------------------------------------
        if lang == "ta":
            if any(w in query for w in ["மழை", "விவசாயம்", "பூச்சிக்கொல்லி", "நெல்"]):
                if is_raining:
                    return (
                        f"🌧️ **இன்று {city}யில் மழை பெய்வதால் பூச்சிக்கொல்லி தெளிக்க வேண்டாம்.**\n\n"
                        f"தற்போதைய வெப்பநிலை **{temp}**. மழை நின்ற பிறகு தெளிப்பதே நல்லது."
                    )
                return f"✅ **இன்று {city}யில் வானிலை சீராக உள்ளது ({temp}), தெளிக்கலாம்.**"
            return f"🌤️ **{city}யில் தற்போதைய வெப்பநிலை {temp}, வானம் {cond}.**"

        # -------------------------------------------------------------
        # 4. MARATHI (मराठी) - Simple & Humanized
        # -------------------------------------------------------------
        if lang == "mr":
            if any(w in query for w in ["पाऊस", "फवारणी", "पीक", "कापूस"]):
                if is_raining:
                    return (
                        f"🌧️ **आज {city} मध्ये पाऊस सुरू आहे, त्यामुळे पिकांवर फवारणी करू नका.**\n\n"
                        f"सध्या तापमान **{temp}** आहे. पावसामुळे औषध वाहून जाईल, त्यामुळे हवामान उघडण्याची वाट पाहा."
                    )
                return f"✅ **आज {city} मध्ये हवामान अनुकूल आहे ({temp}), फवारणी करू शकता.**"
            return f"🌤️ **{city} मध्ये सध्या तापमान {temp} आहे आणि {cond} आहे.**"

        # Fallback to simple Hindi
        return self.generate_native_language_response("hi", query, weather, forecasts, nwp, alerts, advisory, climate)

    def translate_and_localize(
        self,
        english_text: str,
        target_lang: str,
        query: str = "",
        weather: Any = None,
        forecasts: List[Any] = None,
        nwp: Any = None,
        alerts: List[Any] = None,
        advisory: Any = None,
        climate: Optional[Any] = None
    ) -> str:
        if target_lang == "en" or not target_lang:
            return english_text

        if weather and advisory:
            return self.generate_native_language_response(
                lang=target_lang,
                query=query or "",
                weather=weather,
                forecasts=forecasts or [],
                nwp=nwp,
                alerts=alerts or [],
                advisory=advisory,
                climate=climate
            )

        return english_text
