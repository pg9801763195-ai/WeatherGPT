"""
Configuration settings for the Multimodal Weather & NWP AI Agent.
"""
from dataclasses import dataclass, field
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env files with override=True
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"), override=True)
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=True)



@dataclass
class AgentConfig:
    """Central configuration for Ollama models, NWP endpoints, RAG, and Multimodal components."""
    
    # Ollama LLM & Vision Models
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    llm_model: str = os.getenv("WEATHER_LLM_MODEL", "llama3.1:latest")
    vision_model: str = os.getenv("WEATHER_VISION_MODEL", "llava:latest")
    fallback_llm: str = "qwen2.5:7b"
    
    # Hardware & GPU Acceleration (NVIDIA CUDA / RTX 4060)
    use_gpu: bool = os.getenv("USE_GPU", "true").lower() == "true"
    gpu_layers_offload: int = int(os.getenv("GPU_LAYERS_OFFLOAD", "99"))  # Offload all layers to GPU
    whisper_compute_type: str = os.getenv("WHISPER_COMPUTE_TYPE", "float16")
    
    # Temperature & Sampling
    temperature: float = 0.2
    max_tokens: int = 2048
    
    # RAG Vector Store & Embeddings (Primary: Qdrant, Fallback: Chroma, Lexical)
    vector_db_backend: str = os.getenv("VECTOR_DB_BACKEND", "qdrant")  # 'qdrant' | 'chroma' | 'auto'
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chroma_db_dir: str = os.path.join(os.path.dirname(__file__), "rag", "chroma_data")
    qdrant_db_dir: str = os.path.join(os.path.dirname(__file__), "rag", "qdrant_data")
    qdrant_url: Optional[str] = os.getenv("QDRANT_URL", None)  # None uses embedded/local disk mode
    qdrant_api_key: Optional[str] = os.getenv("QDRANT_API_KEY", None)
    rag_top_k: int = 3
    
    # Weather APIs & NWP Config
    open_meteo_url: str = "https://api.open-meteo.com/v1/forecast"
    open_meteo_nwp_url: str = "https://ensemble-api.open-meteo.com/v1/ensemble"
    open_meteo_historical_url: str = "https://archive-api.open-meteo.com/v1/archive"
    open_meteo_geocoding_url: str = "https://geocoding-api.open-meteo.com/v1/search"
    openweather_api_key: Optional[str] = os.getenv("OPENWEATHER_API_KEY", None)
    openweather_base_url: str = "https://api.openweathermap.org/data/2.5"

    openweather_geo_url: str = "https://api.openweathermap.org/geo/1.0/direct"
    
    # Supported Indian Regional Languages for Multilingual Support
    supported_languages: Dict[str, str] = field(default_factory=lambda: {
        "en": "English",
        "hi": "Hindi (हिन्दी)",
        "te": "Telugu (తెలుగు)",
        "ta": "Tamil (தமிழ்)",
        "bn": "Bengali (বাংলা)",
        "mr": "Marathi (मराठी)",
        "gu": "Gujarati (ગુજરાતી)",
        "kn": "Kannada (ಕನ್ನಡ)",
        "ml": "Malayalam (മലയാളം)",
        "pa": "Punjabi (ਪੰਜਾਬੀ)",
        "or": "Odia (ଓଡ଼ିଆ)"
    })
    
    # Edge-TTS voice mappings for Indian languages
    tts_voice_map: Dict[str, str] = field(default_factory=lambda: {
        "en": "en-IN-NeerjaNeural",
        "hi": "hi-IN-SwaraNeural",
        "te": "te-IN-MohanNeural",
        "ta": "ta-IN-PallaviNeural",
        "bn": "bn-IN-TanishaaNeural",
        "mr": "mr-IN-AarohiNeural",
        "gu": "gu-IN-DhwaniNeural",
        "kn": "kn-IN-GaganNeural",
        "ml": "ml-IN-SobhanaNeural",
        "pa": "pa-IN-GurpreetNeural"
    })
    
    # Default Location (e.g. New Delhi, India)
    default_lat: float = 28.6139
    default_lon: float = 77.2090
    default_location_name: str = "New Delhi, India"

    # MongoDB Database Configuration
    mongodb_uri: str = os.getenv("MONGODB_URI", os.getenv("DATABASE_URL", "mongodb://localhost:27017"))
    mongodb_db_name: str = os.getenv("MONGODB_DB_NAME", "weathergpt")

    # JWT Authentication
    jwt_secret: str = os.getenv("JWT_SECRET", "weathergpt_production_super_secret_jwt_key_2026_change_in_env")
    jwt_expires_in: str = os.getenv("JWT_EXPIRES_IN", "7d")  # 7 days
    jwt_algorithm: str = "HS256"

    # Password & OTP Security
    bcrypt_salt_rounds: int = int(os.getenv("BCRYPT_SALT_ROUNDS", "12"))
    otp_expiry_minutes: int = int(os.getenv("OTP_EXPIRY_MINUTES", "5"))
    otp_max_attempts: int = int(os.getenv("OTP_MAX_ATTEMPTS", "5"))

    # Email Delivery Configuration (HTTP APIs for Cloud Hosts like Render + SMTP fallback)
    resend_api_key: Optional[str] = os.getenv("RESEND_API_KEY", None)
    brevo_api_key: Optional[str] = os.getenv("BREVO_API_KEY", None)
    smtp_host: Optional[str] = os.getenv("SMTP_HOST", os.getenv("EMAIL_HOST", None))
    smtp_port: int = int(os.getenv("SMTP_PORT", os.getenv("EMAIL_PORT", "587")))
    smtp_user: Optional[str] = os.getenv("SMTP_USER", os.getenv("EMAIL_USER", None))
    smtp_password: Optional[str] = os.getenv("SMTP_PASSWORD", os.getenv("EMAIL_PASSWORD", None))
    smtp_from: str = os.getenv("SMTP_FROM", os.getenv("EMAIL_FROM", "WeatherGPT <onboarding@resend.dev>"))
    smtp_use_tls: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

