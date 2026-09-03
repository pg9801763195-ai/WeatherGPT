"""
Natural Language Query Understanding & Multi-Turn Conversation Memory Engine.
Transforms user natural language queries across English, Hindi, Hinglish, and regional languages
into strongly-typed ResolvedQuery models using LLM semantic reasoning, candidate entity extraction,
dynamic geocoding resolution, and conversational context inheritance.
"""
import re
import json
import time
from typing import Optional, Dict, Any, List, Tuple
from pydantic import BaseModel, Field
import requests

from config import AgentConfig
from schemas.weather_schemas import CanonicalIntent, ResolvedQuery
from core.prompts import QUERY_UNDERSTANDING_SYSTEM_PROMPT
from tools.location_resolver import LocationResolver
from utils.gpu_manager import GPUManager

# Aliases for backwards compatibility
QueryIntent = CanonicalIntent
StructuredQuery = ResolvedQuery

# Comprehensive stopword & vocabulary blocklist to prevent geocoding general language
VOCAB_STOPWORDS = {
    # Pronouns & determiners
    "the", "a", "an", "this", "that", "these", "those", "is", "it", "its", "it's",
    "i", "me", "my", "mine", "we", "us", "our", "you", "your", "he", "him", "his",
    "she", "her", "they", "them", "their", "what", "which", "who", "whom", "whose",
    "where", "when", "why", "how", "all", "any", "both", "each", "few", "more", "most",
    "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than",
    "too", "very", "can", "will", "just", "don", "should", "now", "based", "with",
    "for", "about", "from", "into", "onto", "upon", "under", "over", "above", "below",
    # Verbs & aux
    "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "having", "do", "does", "did", "doing", "would", "could", "should", "shall",
    "might", "must", "get", "got", "give", "tell", "show", "check", "see", "look",
    "take", "bring", "put", "let", "make", "know", "think", "need", "want", "help",
    "carry", "keep", "stay", "water", "watering", "plant", "plants", "spray", "spraying",
    # Weather & clothing terms that must NEVER be geocoded
    "weather", "mausam", "climate", "forecast", "temp", "temperature", "rain", "raining",
    "rainy", "rains", "drizzle", "shower", "showers", "storm", "thunderstorm", "cloud",
    "clouds", "cloudy", "sunny", "sun", "wind", "windy", "humidity", "humid", "pressure",
    "heat", "hot", "cold", "warm", "chill", "chilly", "freeze", "freezing", "frost",
    "fog", "foggy", "mist", "haze", "uv", "aqi", "air", "sky", "skies", "umbrella",
    "chata", "water", "pani", "precipitation", "condition", "conditions", "outlook",
    "clothes", "cloth", "clothing", "wear", "wearing", "wears", "jacket", "hoodie",
    "sweater", "coat", "raincoat", "outfit", "outfits", "dress", "shirt", "pant",
    "tshirt", "jeans", "shorts", "shoes", "dry", "drying", "laundry", "hang", "wash",
    "washing",
    # Activities & Temporal words
    "time", "times", "walk", "walking", "workout", "workouts", "running", "run", "jog",
    "jogging", "exercise", "fitness", "cricket", "sports", "match", "play", "playing",
    "garden", "gardening", "watering", "farming", "crop", "crops", "agriculture",
    "drive", "driving", "commute", "commuting", "road", "roads", "traffic", "ride",
    "travel", "trip", "tour", "visit", "sightseeing", "outdoor", "outdoors", "indoor",
    "indoors", "outside", "inside", "safe", "safety", "unsafe", "risk", "guidance",
    "advice", "suggest", "suggested", "recommend", "report", "window", "windows",
    "today", "tomorrow", "yesterday", "tonight", "morning", "afternoon", "evening",
    "night", "day", "days", "week", "weeks", "weekend", "month", "months", "year",
    "upcoming", "current", "currently", "now", "right", "latest", "past", "history",
    # Conversational & general words
    "good", "bad", "nice", "great", "fine", "best", "car", "bike",
    "plan", "going", "go", "gone", "went",
    "hello", "hi", "hey", "hola", "thanks", "thank", "please", "ok", "okay", "yes",
    "no", "yeah", "yep", "nope", "sure",
    # Hindi / Hinglish vocabulary that must NEVER be geocoded
    "kya", "hai", "hain", "kaisa", "kaise", "kaisi", "ka", "ki", "ke", "ko", "se",
    "me", "mein", "par", "pe", "aaj", "kal", "parso", "parson", "hoga", "hogi", "hoge",
    "rahega", "rahegi", "rahenge", "raha", "rahi", "rahe", "ho", "liye", "batao",
    "bata", "bataiye", "bol", "bolo", "sunao", "kuch", "aur", "or", "bhai", "yaar",
    "sab", "theek", "sahi", "accha", "achha", "mast", "badhiya", "bahar", "nikalna",
    "nikle", "niklo", "jana", "jaana", "jau", "jaye", "jayein", "ghumne", "ghumna",
    "khel", "khele", "khelna", "dhona", "dho", "dhoye", "kapde", "kapda", "pehne",
    "pehnu", "pehnna", "pehna", "sukha", "sukhaye", "sukhayein", "sukhao", "sukhana",
    "barish", "baarish", "pani", "dhan", "chawal", "gehu", "fasal", "kheti", "spray",
    "chhidkaw", "kare", "karein", "karna", "sakte", "sakta", "sakti", "chahiye",
    # Regional Indian language vocabulary that must NEVER be geocoded
    "paus", "padel", "padnar", "ahe", "aahe", "kasa", "kashi", "madhe", "un", "thandi", "sanga",
    "varsham", "paduthunda", "padtada", "padutundha", "ela", "undi", "undhi", "lo", "yenda", "gali", "goda", "cheppandi",
    "mazhai", "peyyuma", "varuma", "eppadi", "irukku", "la", "veiyil", "kulir", "kaatru", "sollunga",
    "barsa", "barsha", "heba", "hebo", "kipari", "kemiti", "re", "chata", "pani", "ajira", "kali", "paga",
    "brishti", "bristi", "hobe", "kemon", "achhe", "te", "gorom", "thanda", "ajke", "kalke", "abohawa",
    "varsad", "padse", "kevo", "chhe", "ma", "garmi", "chhatri", "aaje", "kale",
    "male", "barutha", "hegide", "nalli", "bisi", "seke", "chatri", "heli",
    "mazha", "peyyumo", "enganeyundu", "il", "choodu", "kuda", "parayu",
    "meenh", "painda", "kiven", "ch", "thand", "dasso",
    # Devanagari & Indic general words
    "क्या", "आज", "में", "बारिश", "होगी", "छाता", "साथ", "रखें", "अभी", "बाहर",
    "निकलना", "ड्राइव", "करना", "सुरक्षित", "है", "वॉक", "कसरत", "के", "लिए",
    "सबसे", "अच्छा", "समय", "मौसम", "हिसाब", "से", "पहनना", "सही", "रहेगा",
    "इस", "वीकेंड", "कैसा", "पौधों", "फसलों", "को", "पानी", "देना", "पूर्वानुमान",
    "କଣ", "ଆଜି", "ବର୍ଷା", "ହେବ", "ଛତା", "ନେବା", "ଆବଶ୍ୟକ", "କି", "ବର୍ତ୍ତମାନ",
    "ଯାତ୍ରା", "ବା", "ଡ୍ରାଇଭ", "କରିବା", "ସୁରକ୍ଷିତ", "ଆସନ୍ତାକାଲି", "ପାଣିପାଗ", "ପୂର୍ବାନୁମାନ"
}


class ConversationContext(BaseModel):
    """Tracks stateful memory across conversation turns per session."""
    session_id: str = "default"
    last_query: Optional[str] = None
    last_response: Optional[str] = None
    last_location: Optional[str] = None
    last_latitude: Optional[float] = None
    last_longitude: Optional[float] = None
    last_intent: Optional[CanonicalIntent] = None
    last_time_reference: Optional[str] = None
    last_activity: Optional[str] = None
    last_crop: Optional[str] = None
    last_weather_parameters: List[str] = Field(default_factory=list)
    turn_count: int = 0
    updated_at: float = Field(default_factory=time.time)

    # Backwards-compatible properties
    @property
    def current_location(self) -> Optional[str]:
        return self.last_location

    @current_location.setter
    def current_location(self, val: Optional[str]):
        self.last_location = val

    @property
    def current_intent(self) -> Optional[CanonicalIntent]:
        return self.last_intent

    @current_intent.setter
    def current_intent(self, val: Optional[CanonicalIntent]):
        self.last_intent = val

    @property
    def current_time_reference(self) -> Optional[str]:
        return self.last_time_reference

    @current_time_reference.setter
    def current_time_reference(self, val: Optional[str]):
        self.last_time_reference = val

    @property
    def current_activity(self) -> Optional[str]:
        return self.last_activity

    @current_activity.setter
    def current_activity(self, val: Optional[str]):
        self.last_activity = val

    @property
    def current_crop(self) -> Optional[str]:
        return self.last_crop

    @current_crop.setter
    def current_crop(self, val: Optional[str]):
        self.last_crop = val


class ConversationMemory:
    """Manages multi-turn conversation sessions and contextual inheritance."""

    def __init__(self, ttl_seconds: float = 3600.0):
        self._sessions: Dict[str, ConversationContext] = {}
        self.ttl_seconds = ttl_seconds

    def get_context(self, session_id: str = "default") -> ConversationContext:
        """Retrieve existing context or initialize a fresh one."""
        now = time.time()
        if session_id in self._sessions:
            ctx = self._sessions[session_id]
            if now - ctx.updated_at < self.ttl_seconds:
                return ctx

        fresh_ctx = ConversationContext(session_id=session_id, updated_at=now)
        self._sessions[session_id] = fresh_ctx
        return fresh_ctx

    def update_context(self, session_id: str, query: str, resolved_query: ResolvedQuery, response_text: str):
        """Update session state following a processed turn."""
        ctx = self.get_context(session_id)
        ctx.last_query = query
        ctx.last_response = response_text
        if resolved_query.location:
            ctx.last_location = resolved_query.location
            ctx.last_latitude = resolved_query.latitude
            ctx.last_longitude = resolved_query.longitude
        if resolved_query.time_reference:
            ctx.last_time_reference = resolved_query.time_reference
        if resolved_query.activity:
            ctx.last_activity = resolved_query.activity
        if resolved_query.crop:
            ctx.last_crop = resolved_query.crop
        if resolved_query.intent != CanonicalIntent.CASUAL_CONVERSATION:
            ctx.last_intent = resolved_query.intent
        if resolved_query.weather_parameters:
            ctx.last_weather_parameters = resolved_query.weather_parameters
        ctx.turn_count += 1
        ctx.updated_at = time.time()

    def resolve_follow_up(self, resolved: ResolvedQuery, context: ConversationContext) -> ResolvedQuery:
        return self.apply_context_inheritance(resolved, context)

    def apply_context_inheritance(self, resolved: ResolvedQuery, context: ConversationContext) -> ResolvedQuery:
        """
        Applies conversational inheritance rules safely:
        - If location is missing in the query, inherit previous location.
        - If query is an explicit short location comparison (e.g. "and Patna?", "what about Ranchi?", "aur Delhi?"), inherit previous intent.
        - NEVER overwrite an explicit new query's intent, activity, or time reference.
        """
        if context.turn_count > 0:
            raw_q = (resolved.entities.get("raw_query") or "").lower().strip()
            word_count = len(raw_q.split())

            # Never alter LOCATION_INFO or CASUAL_CONVERSATION intents
            if resolved.intent in [CanonicalIntent.LOCATION_INFO, CanonicalIntent.CASUAL_CONVERSATION]:
                return resolved

            # 1. Location follow-up / comparison (ONLY for short comparison queries like "and Patna?", "what about Ranchi?", "aur Delhi?")
            is_pure_location_comparison = bool(
                re.match(r"^(?:and|aur|what about|how about|or)\s+[A-Za-z\u0900-\u097F\s\-]+(?:\?|$)", raw_q)
                or (word_count <= 2 and resolved.location and not re.search(r"\b(rain|barish|drive|walk|workout|weather|forecast|weekend|wear|clothes)\b", raw_q))
            )
            if is_pure_location_comparison and context.last_intent:
                resolved.intent = context.last_intent
                if context.last_activity and not resolved.activity:
                    resolved.activity = context.last_activity
                if context.last_time_reference and resolved.time_reference == "today":
                    resolved.time_reference = context.last_time_reference
                if context.last_crop and not resolved.crop:
                    resolved.crop = context.last_crop

            # 2. Inherit location if completely omitted in current query
            elif not resolved.location and context.last_location:
                resolved.location = context.last_location
                resolved.latitude = context.last_latitude
                resolved.longitude = context.last_longitude

            # 3. Inherit crop only if current intent is AGRO_ADVISORY and crop was not specified
            if resolved.intent == CanonicalIntent.AGRO_ADVISORY and not resolved.crop and context.last_crop:
                resolved.crop = context.last_crop

        return resolved


class QueryUnderstandingEngine:
    """Semantic Query Understanding Layer powered by Ollama, Dynamic Geocoding, and Resilient Semantic Parsing."""

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        self.memory = ConversationMemory()
        self.location_resolver = LocationResolver(self.config)
        self._ollama_online = False
        self._last_ollama_check = 0.0

    def _is_ollama_alive(self) -> bool:
        """Check Ollama connectivity with cached status."""
        now = time.time()
        if now - self._last_ollama_check < 120.0:
            return self._ollama_online

        self._last_ollama_check = now
        try:
            r = requests.get(f"{self.config.ollama_host}/api/tags", timeout=0.2)
            self._ollama_online = (r.status_code == 200)
        except Exception:
            self._ollama_online = False
        return self._ollama_online

    def _fast_detect_language(self, text: str) -> str:
        """
        Accurately detect Indian language:
        - Odia (or), Bengali (bn), Telugu (te), Tamil (ta), Kannada (kn), Malayalam (ml),
          Gujarati (gu), Punjabi (pa), Marathi (mr), Hindi (hi), or English (en).
        Supports both Native Unicode scripts and Roman transliterations.
        """
        if not text:
            return "en"

        marathi_unicode_markers = ["आहे", "कसा", "कशी", "पाऊस", "पिकांची", "शेती", "हवामान", "वारं", "करावी", "का", "तापमान", "वारा"]

        for char in text:
            code = ord(char)
            if 0x0B00 <= code <= 0x0B7F:
                return "or"  # Odia (Oriya)
            if 0x0980 <= code <= 0x09FF:
                return "bn"  # Bengali / Assamese
            if 0x0C00 <= code <= 0x0C7F:
                return "te"  # Telugu
            if 0x0B80 <= code <= 0x0BFF:
                return "ta"  # Tamil
            if 0x0C80 <= code <= 0x0CFF:
                return "kn"  # Kannada
            if 0x0D00 <= code <= 0x0D7F:
                return "ml"  # Malayalam
            if 0x0A80 <= code <= 0x0AFF:
                return "gu"  # Gujarati
            if 0x0A00 <= code <= 0x0A7F:
                return "pa"  # Punjabi (Gurmukhi)
            if 0x0900 <= code <= 0x097F:
                if any(w in text for w in marathi_unicode_markers):
                    return "mr"  # Marathi in Devanagari
                return "hi"  # Hindi in Devanagari

        # Roman script transliteration markers
        words = set(re.findall(r"\b[a-zA-Z]+\b", text.lower()))

        odia_roman = {"re", "heba", "hebo", "kipari", "barsa", "barsha", "pani", "chata", "ajira", "kali", "paga", "asiba", "kariba", "surakshita", "kemiti", "achhi", "achi", "hele", "thare", "kana", "kete"}
        if len(words.intersection(odia_roman)) >= 1:
            return "or"

        bengali_roman = {"te", "brishti", "hobe", "kemon", "achhe", "ache", "chata", "gorom", "thanda", "bataas", "batash", "bristi", "ajke", "kalke", "abohawa", "abhowa", "bhalo"}
        if len(words.intersection(bengali_roman)) >= 1:
            return "bn"

        telugu_roman = {"lo", "varsham", "paduthunda", "padtada", "ela", "undi", "undhi", "chali", "yenda", "gali", "goda", "repu", "cheppandi", "vundhi", "vuntundhi", "untundi"}
        if len(words.intersection(telugu_roman)) >= 1:
            return "te"

        tamil_roman = {"la", "mazhai", "peyyuma", "varuma", "eppadi", "irukku", "veiyil", "kulir", "kaatru", "kodai", "innaiku", "naalaiku", "sollunga"}
        if len(words.intersection(tamil_roman)) >= 1:
            return "ta"

        marathi_roman = {"madhe", "paus", "padel", "kasa", "aahe", "ahe", "thandi", "un", "kapde", "sheti", "aajcha", "udya", "sang", "sanga"}
        if len(words.intersection(marathi_roman)) >= 1:
            return "mr"

        gujarati_roman = {"ma", "varsad", "padse", "kevo", "chhe", "garmi", "chhatri", "aaje", "kale", "kaho", "hawaamaan"}
        if len(words.intersection(gujarati_roman)) >= 1:
            return "gu"

        kannada_roman = {"nalli", "male", "barutha", "hegide", "bisi", "seke", "chali", "chatri", "ee dina", "nale", "heli"}
        if len(words.intersection(kannada_roman)) >= 1:
            return "kn"

        malayalam_roman = {"il", "mazha", "peyyumo", "enganeyundu", "choodu", "kuda", "innu", "nale", "parayu"}
        if len(words.intersection(malayalam_roman)) >= 1:
            return "ml"

        punjabi_roman = {"ch", "meenh", "painda", "kiven", "thand", "chhatri", "aj", "dasso"}
        if len(words.intersection(punjabi_roman)) >= 1:
            return "pa"

        hindi_roman = {
            "ka", "ki", "ke", "ko", "kya", "hai", "hain", "aaj", "kal", "parso", "parson", "kaise", "kaisa", "kaisi", "raha", "rahi", "rahe",
            "hogi", "hoga", "hoge", "baarish", "barish", "chahiye", "sakte", "sakta", "sakti", "karein", "karna", "kare",
            "bhai", "yaar", "batao", "bataiye", "bata", "btao", "dhup", "dhoop", "garmi", "thand", "thandi", "kapde",
            "khelna", "badhiya", "achha", "accha", "theek", "nahi", "nahin", "dhan", "ghumne", "ghumna",
            "jaana", "jana", "gaadi", "chata", "pehnu", "pehnna", "pehne", "sukha", "sukhana", "sukhayein", "kheti",
            "chhidkaw", "fasal", "paani", "mein", "kitna", "bhi"
        }
        if len(words.intersection(hindi_roman)) >= 1:
            return "hi"

        return "en"

    def _is_safe_location_candidate(self, candidate: str) -> bool:
        """Verify that a candidate string is not composed of ordinary vocabulary or stop words."""
        if not candidate or len(candidate.strip()) < 2:
            return False

        c_clean = candidate.strip().lower()
        parts = re.findall(r"\b[a-zA-Z0-9\u0900-\u0D7F\-]+\b", c_clean)
        if not parts:
            return False

        # If any part of the candidate is in VOCAB_STOPWORDS, it's NOT a safe location candidate
        if any(p in VOCAB_STOPWORDS for p in parts):
            return False

        return True

    def _extract_location_candidates(self, query: str) -> List[str]:
        """
        Extracts potential location candidates strictly using syntactical indicators
        (routes, prepositions, follow-up markers, or isolated capitalized place tokens).
        Never passes arbitrary query words to geocoding.
        """
        q = query.strip()
        candidates: List[str] = []

        # 1. Route / Destination Detection (e.g. 'Ranchi se Patratu jaana hai', 'from Delhi to Manali')
        route_patterns = [
            r"(?:from\s+([A-Za-z\u0900-\u0D7F]+(?:\s+[A-Za-z\u0900-\u0D7F]+)?)\s+to\s+([A-Za-z\u0900-\u0D7F]+(?:\s+[A-Za-z\u0900-\u0D7F]+)?))",
            r"(?:([A-Za-z\u0900-\u0D7F]+(?:\s+[A-Za-z\u0900-\u0D7F]+)?)\s+se\s+([A-Za-z\u0900-\u0D7F]+(?:\s+[A-Za-z\u0900-\u0D7F]+)?)\s+(?:jaana|jana|travel|trip))",
            r"(?:trip\s+to\s+([A-Za-z\u0900-\u0D7F]+(?:\s+[A-Za-z\u0900-\u0D7F]+)?))",
            r"(?:visit\s+([A-Za-z\u0900-\u0D7F]+(?:\s+[A-Za-z\u0900-\u0D7F]+)?))",
            r"(?:travel\s+to\s+([A-Za-z\u0900-\u0D7F]+(?:\s+[A-Za-z\u0900-\u0D7F]+)?))",
            r"(?:going\s+to\s+([A-Za-z\u0900-\u0D7F]+(?:\s+[A-Za-z\u0900-\u0D7F]+)?))",
            r"(?:tour\s+to\s+([A-Za-z\u0900-\u0D7F]+(?:\s+[A-Za-z\u0900-\u0D7F]+)?))",
            r"(?:to\s+([A-Za-z\u0900-\u0D7F]+(?:\s+[A-Za-z\u0900-\u0D7F]+)?))",
        ]
        for pat in route_patterns:
            m = re.search(pat, q, re.IGNORECASE)
            if m:
                if len(m.groups()) == 2 and m.group(2):
                    dest = m.group(2).strip()
                    if self._is_safe_location_candidate(dest):
                        candidates.append(dest)
                elif m.group(1):
                    dest = m.group(1).strip()
                    if self._is_safe_location_candidate(dest):
                        candidates.append(dest)

        # 2. Devanagari & Regional Script Prepositional Markers
        m_hi = re.search(r"([\u0900-\u0D7F]+)\s+(?:में|का|की|के|से|को|के पास)", q)
        if m_hi:
            cand = m_hi.group(1).strip()
            if self._is_safe_location_candidate(cand):
                candidates.append(cand)

        # Odia & Indic script suffix stripping (e.g. ପୁରୀରେ -> ପୁରୀ, ଜଟଣୀରେ -> ଜଟଣୀ)
        odia_words = re.findall(r"[\u0900-\u0D7F]+", q)
        for ow in odia_words:
            # Strip common postpositional suffixes
            stem = re.sub(r"(?:ରେ|କୁ|ପାଇଁ|ର|में|का|की|के|से|को|लो|yil|te)$", "", ow).strip()
            if stem and len(stem) > 1 and self._is_safe_location_candidate(stem):
                candidates.append(stem)

        # 3. Standard Prepositional & Relationship Patterns (of X, in X, at X, near X, around X, across X, over X, X mein, X me, X ka, X ki, X re, X lo, X yil)
        prep_patterns = [
            r"\b(?:of|in|at|near|around|across|over)\s+([A-Za-z\u0900-\u0D7F]+(?:\s+[A-Za-z\u0900-\u0D7F]+)?)\b",
            r"\b([A-Za-z\u0900-\u0D7F]+)\s+(?:mein|me|ka|ki|ke|ke\s+paas|re|lo|yil|te)\b",
            r"\b([A-Za-z\u0900-\u0D7F]+)\s+(?:weather|forecast|temperature|temp|climate|rain|barish|mausam)\b",
            r"\b(?:weather|forecast|temperature|temp|climate|rain|barish|mausam)\s+(?:of\s+|in\s+)?([A-Za-z\u0900-\u0D7F]+)\b",
        ]
        for pat in prep_patterns:
            for m in re.finditer(pat, q, re.IGNORECASE):
                cand = m.group(1).strip()
                if self._is_safe_location_candidate(cand):
                    candidates.append(cand)

        # 4. Follow-up / Comparison location patterns (e.g. "aur Patratu?", "or patratu??", "what about Patna?", "and Patna?")
        followup_loc_patterns = [
            r"(?:what\s+about|how\s+about|and\s+about)\s+([A-Za-z\u0900-\u0D7F]+(?:\s+[A-Za-z\u0900-\u0D7F]+)?)\b",
            r"(?:aur|or|and)\s+([A-Za-z\u0900-\u0D7F]+(?:\s+[A-Za-z\u0900-\u0D7F]+)?)(?:\?|\s|$)",
        ]
        for pat in followup_loc_patterns:
            m = re.search(pat, q, re.IGNORECASE)
            if m:
                cand = m.group(1).strip().rstrip("?").strip()
                if self._is_safe_location_candidate(cand):
                    candidates.append(cand)

        # 5. Non-stopword tokens (including lowercased place names like "ranchi", "patratu", "delhi", "mumbai")
        words = re.findall(r"\b[A-Za-z\u0900-\u0D7F\-]+\b", q)
        for w in words:
            if len(w) > 2 and self._is_safe_location_candidate(w):
                candidates.append(w)

        # Deduplicate while preserving order
        seen = set()
        unique_cands: List[str] = []
        for c in candidates:
            c_clean = c.strip()
            if c_clean.lower() not in seen and len(c_clean) > 1:
                seen.add(c_clean.lower())
                unique_cands.append(c_clean)

        return unique_cands

    def _resolve_best_location(self, query: str) -> Optional[str]:
        """
        Extracts candidate location tokens from query and verifies against dynamic geocoding.
        Returns canonical location name if verified.
        """
        candidates = self._extract_location_candidates(query)
        for cand in candidates:
            geo = self.location_resolver.resolve(cand)
            if geo:
                return geo.name

        # Fallback to the first capitalized non-stop candidate if geocoding is offline
        for cand in candidates:
            if cand and cand[0].isupper() and self._is_safe_location_candidate(cand):
                return cand.title()

        return None

    def _extract_entities_fallback(self, query: str, context: Optional[ConversationContext] = None) -> ResolvedQuery:
        """
        Authoritative deterministic semantic parser implementing canonical intents and entity resolution.
        """
        q = query.strip()
        q_lower = q.lower()
        lang = self._fast_detect_language(q)

        # 1. Location Info Intent ("what's my location?", "where am I?", "meri location kya hai?")
        location_info_patterns = [
            r"\bwhere\s+am\s+i\b",
            r"\bwhere\s+i\s+am\b",
            r"\bwhat(?:'s|s|\s+is)\s+my\s+(?:current\s+)?location\b",
            r"\bwhat(?:'s|s|\s+is)\s+the\s+current\s+location\b",
            r"\bcurrent\s+location\??\b",
            r"\bwhich\s+location\s+(?:am\s+i\s+viewing|is\s+selected|is\s+active)\b",
            r"\bwhich\s+city\s+(?:am\s+i\s+viewing|is\s+selected|is\s+active)\b",
            r"\bwhat\s+(?:city|place|location)\s+is\s+(?:this|selected|active)\b",
            r"\bwhat\s+place\s+is\s+selected\b",
            r"\bmeri\s+location(?:\s+kya\s+hai)?\b",
            r"\bmain\s+kaha(?:n)?\s+hoon\b",
            r"\bhum\s+kaha(?:n)?\s+hain\b",
            r"\bkaun(?:si|sa)\s+(?:city|location|jagah)\s+selected\s+hai\b",
            r"\bkaha(?:n)?\s+ka\s+(?:mausam|weather)\s+hai\b"
        ]
        is_loc_info = any(re.search(pat, q_lower) for pat in location_info_patterns) or any(
            phrase in q_lower for phrase in [
                "whats my location", "what's my location", "what is my location", "where am i",
                "which location am i viewing", "which city is selected", "what city is this",
                "current location", "what place is selected", "meri location kya hai",
                "main kaha hoon", "main kahan hoon", "kaunsi location selected hai"
            ]
        )
        if is_loc_info:
            return ResolvedQuery(
                intent=CanonicalIntent.LOCATION_INFO,
                location="",
                time_reference="today",
                weather_parameters=["location_info"],
                crop=None,
                activity=None,
                language=lang,
                is_follow_up=False,
                confidence=1.0,
                entities={"raw_query": q}
            )

        # 2. Casual Conversation Intent
        casual_greetings = [
            "hello", "hi", "hey", "namaste", "hola", "greetings", "kaise ho", "kaisa hai",
            "kya haal", "kya chal raha", "aur batao", "or bata", "aur bhai", "sab theek",
            "kya kar rahe ho", "who are you", "who made you", "what can you do", "joke", "funny",
            "thanks", "thank you", "shukriya", "dhanyawad", "good night", "bye"
        ]
        is_casual = any(g in q_lower for g in casual_greetings) and not any(w in q_lower for w in [
            "weather", "mausam", "barish", "baarish", "rain", "temp", "forecast", "spray", "crop", "dhan",
            "ghumne", "trip", "outing", "picnic", "travel", "outside", "bahar", "wear", "clothes", "dry",
            "cricket", "wash"
        ])
        if is_casual:
            return ResolvedQuery(
                intent=CanonicalIntent.CASUAL_CONVERSATION,
                location="",
                time_reference="today",
                weather_parameters=[],
                language=lang,
                is_follow_up=False,
                entities={"raw_query": q}
            )

        # 3. Time Reference Extraction (Multilingual & Typo-Tolerant, strictly boundary-aware)
        time_ref = "today"
        if re.search(r"\b(day\s+after\s+tomm?orr?ow|overmorrow|parso|parson|परसों|ଆରଦିନ)\b", q_lower) or re.search(r"(?<![\w\u0900-\u0D7F])(parso|parson|परसों)(?![\w\u0900-\u0D7F])", q_lower):
            time_ref = "day_after_tomorrow"
        elif re.search(r"\b(tomm?orr?ow|tmrw|tmr|next\s+day|upcoming\s+day|agle\s+din|kal)\b", q_lower) or re.search(r"(?<![\w\u0900-\u0D7F])(कल|ଆସନ୍ତାକାଲି|କାଲି|రేపు|நாளை|কাল|আগামীকাল|उद्या|આવતીકાલે|ನಾಳೆ|ਕੱଲ੍ਹ|ਭਲਕੇ)(?![\w\u0900-\u0D7F])", q_lower):
            time_ref = "tomorrow"
        elif re.search(r"\b(weekend|week\s+end|hafta\s+ant|saturday|sunday)\b", q_lower) or re.search(r"(?<![\w\u0900-\u0D7F])(शनिवार|रविवार|ଶନିବାର|ରବିବାର|वीकेंड|सप्ताहांत)(?![\w\u0900-\u0D7F])", q_lower):
            time_ref = "weekend"
        elif re.search(r"\b(week|weekly|7\s*days?|5\s*days?|3\s*days?|next\s*days?|upcoming\s*days?|aane\s*wale\s*din|aane\s*wale\s*dino|agle\s*din|agle\s*kuch\s*din|agle\s*[0-9]+\s*din|सप्ताह|आने\s*वाले|ଆସନ୍ତା\s*[୦-୯0-9]+\s*ଦିନ|ଆସନ୍ତା\s*ଦିନ)\b", q_lower) or re.search(r"(?<![\w\u0900-\u0D7F])(सप्ताह|आने वाले)(?![\w\u0900-\u0D7F])", q_lower):
            time_ref = "next_7_days"
        elif re.search(r"\b(yesterday|beeta\s+kal|history|past|archive)\b", q_lower) or re.search(r"(?<![\w\u0900-\u0D7F])(पिछला)(?![\w\u0900-\u0D7F])", q_lower):
            time_ref = "historical"

        # 4. Location Extraction via Safe Candidate Resolver
        location = self._resolve_best_location(q)

        # 5. Semantic Intent Classification
        intent = CanonicalIntent.CURRENT_WEATHER
        activity = None

        # Check Travel Weather / Commute / Drive / Road Safety ("is it safe to drive or commute?", "trip to Patratu")
        if re.search(r"\b(drive|driving|commute|commuting|road|roads|traffic|ride|riding|travel|trip|sightseeing|tour|visit|outing|picnic)\b", q_lower) or any(
            phrase in q_lower for phrase in [
                "safe to drive", "safe to commute", "safe to travel", "drive safe", "commute safe",
                "go outside", "bahar jana", "bahar jaana", "ghumne", "ghumna", "jau kya", "jaana theek",
                "drive karna", "gaadi chalana", "sadak ka haal", "drive or commute"
            ]
        ) or any(w in q for w in ["ଯାତ୍ରା", "ଡ୍ରାଇଭ୍", "ରାସ୍ତା", "ସୁରକ୍ଷିତ", "ଘୁରିବା", "यात्रा", "सफर", "सड़क", "प्रवास", "घूमने"]):
            intent = CanonicalIntent.TRAVEL_WEATHER
            activity = "commute_drive" if any(w in q_lower for w in ["drive", "driving", "commute", "road", "traffic", "gaadi", "chalana", "ଡ୍ରାଇଭ୍", "ରାସ୍ତା"]) else "travel_sightseeing"

        # Check Outdoor Activity / Workout / Walk / Running / Sports / Car Wash
        elif re.search(r"\b(walk|walking|workout|running|run|jog|jogging|exercise|fitness|cricket|sports|play|playing|match)\b", q_lower) or any(
            phrase in q_lower for phrase in [
                "best time for a walk", "morning walk", "evening walk", "outdoor workout", "go for a walk",
                "cricket match", "khelna", "khel", "workout time", "exercise outside", "morning walk ka time", "walk karne", "walk or outdoor workout"
            ]
        ) or any(w in q for w in ["ବ୍ୟାୟାମ", "ଖେଳ", "କସରତ", "कसरत", "टहलने"]):
            intent = CanonicalIntent.OUTDOOR_ACTIVITY
            activity = "walk_workout" if any(w in q_lower for w in ["walk", "workout", "run", "running", "jog", "exercise", "fitness", "ବ୍ୟାୟାମ"]) else "cricket"

        elif any(w in q_lower for w in ["car wash", "wash my car", "wash my bike", "gaadi dhona", "gadi dhona"]):
            intent = CanonicalIntent.OUTDOOR_ACTIVITY
            activity = "car_wash"

        # Check Agro / Farming / Spraying / Gardening / Plant Watering
        elif re.search(r"\b(garden|gardening|plant|plants|watering|water plants|spray|chhidkaw|kheti|crop|cotton|paddy|rice|wheat|mustard|pest|irrigate|farming|dhan|kapas|kisan)\b", q_lower) or any(
            phrase in q_lower for phrase in ["water plants", "watering plants", "outdoor watering", "water my plants", "paani dena", "paudho ko paani", "fasal", "gardening or outdoor watering"]
        ) or any(w in q for w in ["छिड़काव", "फसल", "धान", "खेती", "सिंचाई", "पौधे", "पौधों", "ଗଛ", "ଚାଷ", "କୃଷି", "ପାଣି ଦେବା"]):
            intent = CanonicalIntent.AGRO_ADVISORY
            activity = "gardening_watering" if any(w in q_lower for w in ["garden", "plant", "water", "paudhe", "paani", "watering", "ଗଛ"]) else "spray"

        # Check Outfit Recommendation ("what clothes should i wear??", "should I wear a jacket?", "kya pehnu")
        elif re.search(r"\b(wear|wearing|jacket|hoodie|sweater|outfit|coat|raincoat|pehne|pehnu|pehnna|pehna)\b", q_lower) or any(
            phrase in q_lower for phrase in ["clothes should i wear", "what should i wear", "what clothes to wear", "what to wear", "kya pehna chahiye", "kya pehnu", "what should i wear today"]
        ) or any(w in q for w in ["ପିନ୍ଧିବା", "ପୋଷାକ", "कपड़े", "पहनना"]):
            intent = CanonicalIntent.OUTFIT_RECOMMENDATION
            activity = "outfit"

        # Check Clothes Drying / Laundry ("can I dry my clothes outside?", "will my clothes dry today?", "kapde sukhana")
        elif re.search(r"\b(dry|drying|sukha|sukhana|sukhane|sukhayein|laundry)\b", q_lower) and any(
            w in q_lower for w in ["clothes", "cloth", "laundry", "kapde", "sukha", "dry", "hang"]
        ) or any(w in q for w in ["ଶୁଖାଇବା", "ସୁଖାଇବା"]):
            intent = CanonicalIntent.CLOTHES_DRYING
            activity = "clothes_drying"

        # Check Weather Forecast & Multi-Day Windows
        elif any(w in q_lower for w in ["forecast", "upcoming", "weekend", "week", "पूर्वानुमान", "अगले", "आने वाले"]) or any(w in q for w in ["ପୂର୍ବାନୁମାନ", "ଆସନ୍ତା", "ଦିନର"]) or time_ref in ["next_7_days", "weekend"]:
            intent = CanonicalIntent.WEATHER_FORECAST

        # Check Rain / Precipitation / Umbrella ("will it rain today?")
        elif any(w in q_lower for w in ["rain", "raining", "rainy", "barish", "baarish", "umbrella", "chata", "shower", "drizzle", "बारिश", "वर्षा", "बरसात", "छाता", "rain ka kya scene"]) or any(w in q for w in ["ବର୍ଷା", "ଛତା", "వర్షం", "மழை", "বৃষ্টি"]):
            intent = CanonicalIntent.PRECIPITATION

        # Check Extreme Alert
        elif any(w in q_lower for w in ["alert", "warning", "cyclone", "flood", "heatwave", "thunderstorm", "hazard", "चेतावनी", "ସତର୍କ"]):
            intent = CanonicalIntent.WEATHER_ALERT

        # Check NWP / Instability
        elif any(w in q_lower for w in ["nwp", "cape", "cin", "gfs", "wrf", "instability", "convective"]):
            intent = CanonicalIntent.NWP_ANALYSIS

        # Check Climate trend
        elif any(w in q_lower for w in ["climate", "trend", "history", "historical", "warming", "decade", "जलवायु"]):
            intent = CanonicalIntent.HISTORICAL_CLIMATE

        # Check Weather Forecast (if future time reference was extracted or explicit forecast word)
        elif time_ref != "today" or any(w in q_lower for w in ["forecast", "upcoming", "weekly", "weekend", "outlook", "पूर्वानुमान"]):
            intent = CanonicalIntent.WEATHER_FORECAST

        # Default Current Weather
        else:
            intent = CanonicalIntent.CURRENT_WEATHER

        # 5. Crop Extraction
        crop = None
        crop_map = {
            "dhan": "Paddy", "paddy": "Paddy", "rice": "Paddy", "chawal": "Paddy", "धान": "Paddy",
            "kapas": "Cotton", "cotton": "Cotton", "कपास": "Cotton",
            "gehu": "Wheat", "wheat": "Wheat", "गेहूं": "Wheat",
            "sarson": "Mustard", "mustard": "Mustard", "सरसों": "Mustard",
            "soybean": "Soybean", "सोयाबीन": "Soybean",
            "tamatar": "Tomato", "tomato": "Tomato", "टमाटर": "Tomato",
            "mirchi": "Chilli", "chilli": "Chilli", "मिर्च": "Chilli"
        }
        for k, v in crop_map.items():
            if re.search(rf"\b{k}\b", q_lower) or k in q:
                crop = v
                break

        # 6. Follow-up Detection (Strictly for explicit prefix triggers or ultra-short queries without domain nouns)
        is_follow_up = False
        if context and context.turn_count > 0:
            if re.match(r"^(?:and|aur|what about|how about|aur batao|and in)\s+", q_lower) or (
                len(q.split()) <= 3 and not re.search(r"\b(weather|mausam|forecast|rain|barish|drive|commute|walk|workout|gardening|water|weekend|wear|clothes)\b", q_lower)
            ):
                is_follow_up = True

        params = ["general_weather"]
        if intent == CanonicalIntent.PRECIPITATION:
            params = ["precipitation"]
        elif intent == CanonicalIntent.OUTFIT_RECOMMENDATION:
            params = ["temperature", "precipitation", "wind"]
        elif intent == CanonicalIntent.CLOTHES_DRYING:
            params = ["precipitation", "humidity", "wind"]
        elif intent == CanonicalIntent.AGRO_ADVISORY:
            params = ["spray_safety", "precipitation", "wind"]
        elif intent in [CanonicalIntent.OUTDOOR_ACTIVITY, CanonicalIntent.TRAVEL_WEATHER]:
            params = ["precipitation", "temperature", "wind", "general_weather"]

        return ResolvedQuery(
            intent=intent,
            location=location or "",
            time_reference=time_ref,
            weather_parameters=params,
            crop=crop,
            activity=activity,
            language=lang,
            is_follow_up=is_follow_up,
            entities={"raw_query": q}
        )

    def understand_query(self, query: str, session_id: str = "default") -> ResolvedQuery:
        """
        Primary Query Understanding pipeline.
        Calls Ollama LLM with strict JSON schema, falling back to dynamic semantic candidate parser if offline.
        """
        context = self.memory.get_context(session_id)
        q_clean = query.strip()

        # Fast-path for single-word casual greetings to maintain < 10ms speed
        if re.match(r"^(hi+|he+y+|he+l+o+|namaste|kaise ho|aur batao|or bata)$", q_clean.lower()):
            lang = self._fast_detect_language(q_clean)
            return ResolvedQuery(
                intent=CanonicalIntent.CASUAL_CONVERSATION,
                location="",
                time_reference="today",
                weather_parameters=[],
                language=lang,
                is_follow_up=False,
                entities={"raw_query": q_clean}
            )

        # Try LLM Semantic Understanding via Ollama
        if self._is_ollama_alive():
            try:
                context_str = f"Previous Context: location={context.last_location or 'None'}, time={context.last_time_reference or 'today'}, activity={context.last_activity or 'None'}, crop={context.last_crop or 'None'}, last_query={context.last_query or 'None'}"
                prompt = f"{QUERY_UNDERSTANDING_SYSTEM_PROMPT}\n\n{context_str}\n\nUser Query: \"{q_clean}\"\nOutput JSON:"

                gpu_opts = GPUManager.get_ollama_gpu_options() if self.config.use_gpu else {"num_gpu": 0}
                payload = {
                    "model": self.config.llm_model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0.0, "num_predict": 256, **gpu_opts}
                }
                resp = requests.post(f"{self.config.ollama_host}/api/generate", json=payload, timeout=1.5)
                if resp.status_code == 200:
                    raw_json = resp.json().get("response", "").strip()
                    raw_json = re.sub(r"^```json\s*", "", raw_json)
                    raw_json = re.sub(r"\s*```$", "", raw_json)
                    data = json.loads(raw_json)

                    raw_loc = data.get("location")
                    verified_loc = None
                    if raw_loc and self._is_safe_location_candidate(raw_loc):
                        geo = self.location_resolver.resolve(raw_loc)
                        verified_loc = geo.name if geo else raw_loc.title()

                    raw_intent = data.get("intent", "current_weather")
                    try:
                        resolved_intent = CanonicalIntent(raw_intent)
                    except ValueError:
                        resolved_intent = CanonicalIntent.CURRENT_WEATHER

                    resolved = ResolvedQuery(
                        intent=resolved_intent,
                        location=verified_loc or "",
                        time_reference=data.get("time_reference", "today"),
                        target_date=data.get("target_date"),
                        weather_parameters=data.get("weather_parameters", ["general_weather"]),
                        crop=data.get("crop"),
                        activity=data.get("activity") or data.get("activity_context"),
                        language=data.get("language", self._fast_detect_language(q_clean)),
                        is_follow_up=data.get("is_follow_up", False),
                        entities={"raw_query": q_clean, **data.get("entities", {})}
                    )
                    return self.memory.resolve_follow_up(resolved, context)
            except Exception:
                pass

        # Fallback to deterministic semantic candidate parser with geocoding verification
        resolved_fallback = self._extract_entities_fallback(q_clean, context)
        return self.memory.resolve_follow_up(resolved_fallback, context)
