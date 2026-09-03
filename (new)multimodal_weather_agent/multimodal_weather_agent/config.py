"""
Central configuration for Multimodal Weather & NWP AI Agent (MausamVani).
Supports Gemini API (for LLM reasoning & Google Text-to-Speech / Voice Assistant),
OpenWeather API (live weather + AQI), Ollama (local LLM), Qdrant Vector DB, and NVIDIA GPU.
"""
from dataclasses import dataclass, field
import os
from typing import Dict, List, Optional


@dataclass
class AgentConfig:
    """Central configuration for MausamVani Voice Assistant."""
    
    # Google Gemini API Config (for LLM reasoning, Multimodal Audio/Vision, and Voice Assistant)
    gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    gemini_voice: str = "Pooja"  # Options: Pooja, Chirag, Arvind, Priya, Aoede, Kore, Fenrir
    
    # Ollama LLM & Vision Models (Local Alternative)
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    llm_model: str = os.getenv("WEATHER_LLM_MODEL", "llama3.1:latest")
    vision_model: str = os.getenv("WEATHER_VISION_MODEL", "llava:latest")
    fallback_llm: str = "qwen2.5:7b"
    primary_backend: str = "gemini"  # 'gemini' | 'ollama' | 'auto'
    
    # Hardware & GPU Acceleration (NVIDIA CUDA / RTX 4060)
    use_gpu: bool = os.getenv("USE_GPU", "true").lower() == "true"
    gpu_layers_offload: int = int(os.getenv("GPU_LAYERS_OFFLOAD", "99"))
    whisper_compute_type: str = os.getenv("WHISPER_COMPUTE_TYPE", "float16")
    
    # Temperature & Sampling
    temperature: float = 0.2  # Local LLM temperature
    cloud_temperature: float = 0.5  # Google Gemini Cloud Model Temperature (Updated to 0.5)
    gemini_temperature: float = 0.5
    tts_temperature: float = 0.7  # Google Gemini Text-To-Speech (TTS) Temperature (Updated to 0.7)
    max_tokens: int = 2048
    
    # RAG Vector Store & Embeddings (Primary: Qdrant, Fallback: Chroma, Lexical)
    vector_db_backend: str = os.getenv("VECTOR_DB_BACKEND", "qdrant")  # 'qdrant' | 'chroma' | 'auto'
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chroma_db_dir: str = os.path.join(os.path.dirname(__file__), "rag", "chroma_data")
    qdrant_db_dir: str = os.path.join(os.path.dirname(__file__), "rag", "qdrant_data")
    qdrant_url: Optional[str] = os.getenv("QDRANT_URL", None)
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
    
    # Supported Indian Regional Languages for Voice Assistant & Translation
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
        "pa": "Punjabi (ਪੰਜਾਬੀ)"
    })
    
    # Default Coordinates (Nagpur, Central India Agricultural Hub)
    default_lat: float = 21.1458
    default_lon: float = 79.0882
    default_location_name: str = "Nagpur, Maharashtra"
