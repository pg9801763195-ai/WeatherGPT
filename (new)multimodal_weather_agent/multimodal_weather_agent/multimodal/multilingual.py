"""
Multilingual Translation and Indic Script Engine.
Supports Hindi, Telugu, Tamil, Marathi, Bengali, Gujarati, Kannada, Malayalam, and Punjabi.
"""
import re
from typing import Dict, Optional
from config import AgentConfig


SCRIPT_RANGES = {
    "hi": (0x0900, 0x097F),  # Devanagari (Hindi, Marathi)
    "mr": (0x0900, 0x097F),  # Devanagari
    "bn": (0x0980, 0x09FF),  # Bengali
    "pa": (0x0A00, 0x0A7F),  # Gurmukhi (Punjabi)
    "gu": (0x0A80, 0x0AFF),  # Gujarati
    "ta": (0x0B80, 0x0BFF),  # Tamil
    "te": (0x0C00, 0x0C7F),  # Telugu
    "kn": (0x0C80, 0x0CFF),  # Kannada
    "ml": (0x0D00, 0x0D7F)   # Malayalam
}

LOCALIZED_HEADERS = {
    "hi": "🌾 **मौसम एवं कृषि सलाह (हिन्दी)**:",
    "te": "🌾 **వాతావరణ మరియు వ్యవసాయ సమాచారం (తెలుగు)**:",
    "ta": "🌾 **வானிலை மற்றும் வேளாண்மை ஆலோசனை (தமிழ்)**:",
    "mr": "🌾 **हवामान आणि शेती सल्ला (मराठी)**:",
    "bn": "🌾 **আবহাওয়া এবং কৃষি পরামর্শ (বাংলা)**:",
    "gu": "🌾 **હવામાન અને કૃષિ સલાહ (ગુજરાતી)**:",
    "kn": "🌾 **ಹವಾಮಾನ ಮತ್ತು ಕೃಷಿ ಸಲಹೆ (ಕನ್ನಡ)**:"
}


class MultilingualEngine:
    """Detects Indic scripts and translates weather advisories for rural communities."""

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()

    def detect_language(self, text: str) -> str:
        """Detect language code based on Unicode character codepoints."""
        if not text:
            return "en"
        
        # Check Indic script ranges
        for char in text:
            code = ord(char)
            for lang, (start, end) in SCRIPT_RANGES.items():
                if start <= code <= end:
                    # Distinguish Marathi from Hindi keywords if needed
                    if lang in ["hi", "mr"]:
                        if any(w in text for w in ["आहे", "नाही", "शेतकरी", "फवारणी", "पाऊस", "हवामान"]):
                            return "mr"
                        return "hi"
                    return lang
        return "en"

    def translate_advisory(self, english_text: str, target_lang: str) -> str:
        """Localize meteorological advice into target regional Indian language."""
        if target_lang == "en" or not english_text:
            return english_text

        header = LOCALIZED_HEADERS.get(target_lang, f"🌾 **Weather Advisory ({target_lang.upper()})**:")
        
        # Quick localized domain replacements for common terms
        replacements = {
            "hi": {
                "Temperature": "तापमान", "Humidity": "नमी / आर्द्रता", "Wind": "हवा की गति",
                "Rain": "बारिश / वर्षा", "Safe to spray": "छिड़काव के लिए सुरक्षित",
                "Unsafe to spray": "छिड़काव न करें", "Withhold irrigation": "सिंचाई रोकें"
            },
            "te": {
                "Temperature": "ఉష్ణోగ్రత", "Humidity": "తేమ శాతం", "Wind": "గాలి వేగం",
                "Rain": "వర్షం", "Safe to spray": "మందుల పిచికారీకి అనుకూలం",
                "Unsafe to spray": "పిచికారీ వాయిదా వేయండి", "Withhold irrigation": "నీటి తడులు ఆపండి"
            },
            "ta": {
                "Temperature": "வெப்பநிலை", "Humidity": "ஈரப்பதம்", "Wind": "காற்றின் வேகம்",
                "Rain": "மழை", "Safe to spray": "மருந்து தெளிக்க உகந்த நேரம்",
                "Unsafe to spray": "மருந்து தெளிப்பதைத் தவிர்க்கவும்", "Withhold irrigation": "பாசனத்தை நிறுத்தி வைக்கவும்"
            },
            "mr": {
                "Temperature": "तापमान", "Humidity": "हवेतील आर्द्रता", "Wind": "वाऱ्याचा वेग",
                "Rain": "पाऊस", "Safe to spray": "औषध फवारणीसाठी अनुकूल",
                "Unsafe to spray": "फवारणी टाळा", "Withhold irrigation": "पाणी देणे थांबवा"
            }
        }

        lang_rep = replacements.get(target_lang, {})
        translated = english_text
        for eng, indic in lang_rep.items():
            translated = translated.replace(eng, indic)

        return f"{header}\n{translated}"
