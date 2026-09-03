"""
FastAPI Server connecting the Multimodal Weather AI Agent ("MausamVani")
to the WeatherGPT React Web Interface.

Provides endpoints for:
1. Real-time weather information retrieval
2. Natural language weather & forecast queries
3. NWP Model diagnostics (GFS/WRF/ECMWF, CAPE, CIN, 500hPa)
4. Extreme weather alerts & IMD CAP early warnings
5. Location-based forecasting & crop agro-advisories
6. Multilingual Indian language support (Hindi, Telugu, Tamil, Marathi, etc.)
7. Climate trend & historical analysis (Kaggle Indian Cities dataset)
8. Voice-enabled interaction & edge-tts neural speech synthesis
"""
import os
import sys
import time
import base64
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import AgentConfig
from core.agent import MultimodalWeatherAgent
from schemas.weather_schemas import MultimodalInput, AlertSeverity, CanonicalIntent, ResolvedQuery
from db.mongo_database import MongoDatabaseManager
from auth.security import optional_auth
from auth.auth_router import router as auth_router
from auth.history_router import router as history_router
from multimodal.realtime_mic import RealtimeVoiceDetector

app = FastAPI(
    title="MausamVani Multimodal Weather Agent API",
    description="Backend API connecting the Multimodal Weather AI Agent to the Frontend",
    version="1.0.0"
)

# Enable robust CORS for localhost and production domains (Vercel, Render, Custom domains)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"],
    allow_origin_regex=r"^https?://.*$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize Agent Singleton, Voice Detector, and Database
config = AgentConfig()
agent = MultimodalWeatherAgent(config)
voice_detector = RealtimeVoiceDetector(config)
db = MongoDatabaseManager.get_instance(config.mongodb_uri, config.mongodb_db_name)

# Mount Authentication & Assistant History Sub-Routers
app.include_router(auth_router)
app.include_router(history_router)


# --- Request / Response Schemas ---

class ChatQueryRequest(BaseModel):
    query: str
    location_name: Optional[str] = None
    language_code: Optional[str] = "auto"
    unit: Optional[str] = "C"
    session_id: Optional[str] = "default"
    conversation_id: Optional[str] = None



class TTSRequest(BaseModel):
    text: str
    language_code: Optional[str] = "hi"


# --- API Routes ---

@app.get("/api")
def api_root():
    return {
        "status": "online",
        "service": "MausamVani Multimodal Weather AI Agent API",
        "version": "1.0.0",
        "endpoints": [
            "/api/chat",
            "/api/tts",
            "/api/stt",
            "/api/health",
            "/api/nwp",
            "/api/advisory",
            "/api/alerts",
            "/api/climate"
        ]
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "agent": "MausamVani Multimodal Weather Agent",
        "capabilities": [
            "1. Real-time weather information retrieval",
            "2. Natural language querying for weather forecasts",
            "3. Integration with NWP models (GFS/WRF/ECMWF, CAPE, CIN)",
            "4. Extreme weather alerts and early warnings (IMD/CAP)",
            "5. Location-based forecasting & agro-advisory generation",
            "6. Multilingual support for Indian languages (11 languages)",
            "7. Climate trend & historical weather analysis (Kaggle Indian Cities)",
            "8. Voice-enabled interaction & Neural TTS synthesis",
            "9. Semantic Query Understanding & Multi-turn Conversation Memory"
        ],
        "default_location": config.default_location_name,
        "supported_languages": list(config.supported_languages.keys())
    }


@app.post("/api/chat")
async def handle_chat_query(req: ChatQueryRequest, request: Request):
    """
    Main conversational endpoint coordinating all 8 weather & agro capabilities with multi-turn session memory.
    Supports both Guest mode (unpersisted history) and Authenticated users (persisted MongoDB history).
    """
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        # Check authentication status from JWT Bearer or HttpOnly cookie
        current_user = await optional_auth(request)

        # Build multimodal input
        input_data = MultimodalInput(
            text_query=req.query,
            location_name=req.location_name,
            language_code=req.language_code
        )

        # Process through the Multimodal Agent pipeline with multi-turn session memory
        session_id = req.session_id or "default"
        response = agent.process_query(input_data, session_id=session_id)

        # Determine best display text (translated if non-English query)
        main_text = response.translated_response or response.response_text

        # Construct Rich Action Card contextually matched to canonical resolved intent
        action_card = None
        res_intent = response.resolved_query.intent if response.resolved_query else None
        display_city = response.resolved_query.location if (response.resolved_query and response.resolved_query.location) else (response.structured_weather.location.name if response.structured_weather else "Location")

        if res_intent in [CanonicalIntent.CASUAL_CONVERSATION, CanonicalIntent.LOCATION_INFO]:
            action_card = None
        elif res_intent == CanonicalIntent.AGRO_ADVISORY and response.agro_advisory:
            adv = response.agro_advisory
            action_card = {
                "title": f"{adv.target_crop} Agro Advisory · {display_city}",
                "subtitle": f"Spray: {'SAFE' if adv.spray_window_safe else 'UNSAFE'} · {adv.spray_recommendation[:65]}...",
                "metric": "Safe" if adv.spray_window_safe else "Alert",
                "badge": "AGRO ADVISORY",
                "icon": "agriculture"
            }
        elif res_intent == CanonicalIntent.NWP_ANALYSIS and response.nwp_forecast:
            nwp = response.nwp_forecast
            action_card = {
                "title": f"NWP {nwp.model_name} Diagnostic · {display_city}",
                "subtitle": f"CAPE: {nwp.cape_surface_j_kg:.0f} J/kg · 500hPa: {nwp.geopotential_height_500hpa_m or 5880:.0f}m",
                "metric": f"{nwp.cape_surface_j_kg:.0f} J/kg",
                "badge": "NWP MODEL",
                "icon": "cyclone"
            }
        elif res_intent == CanonicalIntent.WEATHER_ALERT and response.extreme_alerts and len(response.extreme_alerts) > 0:
            al = response.extreme_alerts[0]
            action_card = {
                "title": al.headline or f"Extreme Weather Alert · {display_city}",
                "subtitle": al.description[:90] + "...",
                "metric": al.severity.value.upper(),
                "badge": f"IMD {al.category.value.upper()}",
                "icon": "warning"
            }
        elif res_intent == CanonicalIntent.HISTORICAL_CLIMATE and response.climate_trend:
            cl = response.climate_trend
            action_card = {
                "title": f"{display_city} Climate Trend ({cl.start_year}–{cl.end_year})",
                "subtitle": f"Mean Temp Shift: +{cl.mean_temp_change_c:.2f}°C · Heatwave: +{cl.heatwave_days_per_decade:.1f}d/dec",
                "metric": f"+{cl.mean_temp_change_c:.2f}°C",
                "badge": "CLIMATE ARCHIVE",
                "icon": "trending_up"
            }
        elif res_intent == CanonicalIntent.OUTFIT_RECOMMENDATION and response.structured_weather:
            w = response.structured_weather
            t_str = f"{w.temperature_c:.1f}°C" if req.unit == "C" else f"{(w.temperature_c * 9/5 + 32):.1f}°F"
            action_card = {
                "title": f"{display_city} Outfit Guidance",
                "subtitle": f"Temp: {t_str} · {w.weather_description} · Wind {w.wind_speed_kmh:.0f} km/h",
                "metric": t_str,
                "badge": "OUTFIT ADVICE",
                "icon": "checkroom"
            }
        elif res_intent == CanonicalIntent.CLOTHES_DRYING and response.structured_weather:
            w = response.structured_weather
            t_str = f"{w.temperature_c:.1f}°C" if req.unit == "C" else f"{(w.temperature_c * 9/5 + 32):.1f}°F"
            action_card = {
                "title": f"{display_city} Laundry Conditions",
                "subtitle": f"{w.weather_description} · Humidity {w.relative_humidity_pct:.0f}% · Wind {w.wind_speed_kmh:.0f} km/h",
                "metric": f"{w.relative_humidity_pct:.0f}% RH",
                "badge": "CLOTHES DRYING",
                "icon": "dry_cleaning"
            }
        elif res_intent == CanonicalIntent.TRAVEL_WEATHER and response.structured_weather:
            w = response.structured_weather
            t_str = f"{w.temperature_c:.1f}°C" if req.unit == "C" else f"{(w.temperature_c * 9/5 + 32):.1f}°F"
            action_card = {
                "title": f"{display_city} Travel & Sightseeing",
                "subtitle": f"{w.weather_description} · Rain {w.precipitation_mm:.1f} mm · Wind {w.wind_speed_kmh:.0f} km/h",
                "metric": t_str,
                "badge": "TRAVEL OUTLOOK",
                "icon": "directions_car"
            }
        elif res_intent in [CanonicalIntent.WEATHER_FORECAST, CanonicalIntent.PRECIPITATION] and response.daily_forecasts and len(response.daily_forecasts) > 1:
            fc = response.daily_forecasts[1]
            t_max = f"{fc.temp_max_c:.0f}°C" if req.unit == "C" else f"{(fc.temp_max_c * 9/5 + 32):.0f}°F"
            t_min = f"{fc.temp_min_c:.0f}°C" if req.unit == "C" else f"{(fc.temp_min_c * 9/5 + 32):.0f}°F"
            action_card = {
                "title": f"{display_city} Forecast Outlook",
                "subtitle": f"{fc.weather_description} · Rain {fc.precipitation_probability_pct}% · Wind {fc.max_wind_speed_kmh:.0f} km/h",
                "metric": f"{t_max} / {t_min}",
                "badge": "FORECAST OUTLOOK",
                "icon": "calendar_today"
            }
        elif response.structured_weather:
            w = response.structured_weather
            t_str = f"{w.temperature_c:.1f}°C" if req.unit == "C" else f"{(w.temperature_c * 9/5 + 32):.1f}°F"
            action_card = {
                "title": f"{display_city} Telemetry",
                "subtitle": f"{w.weather_description} · Wind {w.wind_speed_kmh:.0f} km/h · Humidity {w.relative_humidity_pct:.0f}%",
                "metric": t_str,
                "badge": "LIVE TELEMETRY",
                "icon": "wb_sunny"
            }

        # Persistent Assistant History Management for Authenticated Users
        saved_conv_id = None
        user_msg_id = None
        ai_msg_id = None

        if current_user:
            user_id = current_user["id"]
            # 1. Resolve or create conversation thread
            target_conv = None
            if req.conversation_id:
                target_conv = db.get_conversation_with_messages(req.conversation_id, user_id)

            if not target_conv:
                # Derive clean descriptive title from query
                clean_title = req.query.strip().replace("\n", " ")
                if len(clean_title) > 36:
                    clean_title = clean_title[:34] + "..."
                created = db.create_conversation(user_id=user_id, title=clean_title)
                saved_conv_id = created["_id"]
            else:
                saved_conv_id = target_conv["id"]

            # 2. Persist User Message
            user_msg_id = db.add_message(
                conv_id=saved_conv_id,
                user_id=user_id,
                role="user",
                content=req.query
            )

            # 3. Persist AI Response Message
            ai_msg_id = db.add_message(
                conv_id=saved_conv_id,
                user_id=user_id,
                role="assistant",
                content=main_text,
                metadata={
                    "action_card": action_card,
                    "detected_language": response.detected_language,
                    "audio_output_file": response.audio_output_file
                }
            )

        return {
            "query": response.query,
            "response_text": main_text,
            "raw_english_response": response.response_text,
            "translated_response": response.translated_response,
            "detected_language": response.detected_language,
            "action_card": action_card,
            "has_advisory": response.agro_advisory is not None,
            "has_nwp": response.nwp_forecast is not None,
            "has_alerts": response.extreme_alerts is not None and len(response.extreme_alerts) > 0,
            "has_climate": response.climate_trend is not None,
            "audio_output_file": response.audio_output_file,
            "conversation_id": saved_conv_id,
            "is_authenticated": current_user is not None
        }


    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tts")
@app.post("/api/tts/synthesize")
async def generate_speech(req: TTSRequest):
    """
    Synthesize text-to-speech audio using edge-tts with Indian regional neural voices.
    Returns audio as base64 for direct browser playback.
    """
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    lang = req.language_code or "hi"
    clean_text = agent.audio_engine.prepare_speech_text(req.text, lang)
    if not clean_text:
        clean_text = "Weather update."
    if len(clean_text) > 400:
        clean_text = clean_text[:397] + "..."

    voice = agent.config.tts_voice_map.get(lang, "hi-IN-SwaraNeural")
    out_dir = agent.audio_engine.output_dir
    filename = f"tts_{lang}_{int(time.time()*1000)}.mp3"
    out_path = os.path.join(out_dir, filename)

    try:
        import edge_tts
        comm = edge_tts.Communicate(clean_text, voice)
        await comm.save(out_path)

        with open(out_path, "rb") as f:
            audio_bytes = f.read()

        b64_str = base64.b64encode(audio_bytes).decode("utf-8")
        return {
            "status": "success",
            "audio_base64": b64_str,
            "format": "audio/mp3",
            "language": lang
        }
    except Exception as e:
        fallback_path = agent.audio_engine.text_to_speech(req.text, language_code=lang)
        if os.path.exists(fallback_path):
            with open(fallback_path, "rb") as f:
                b64_str = base64.b64encode(f.read()).decode("utf-8")
            return {
                "status": "success",
                "audio_base64": b64_str,
                "format": "audio/wav" if fallback_path.endswith(".wav") else "audio/mp3",
                "language": lang
            }
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/stt")
async def handle_speech_to_text(file: UploadFile = File(...), language: Optional[str] = "auto"):
    """
    Transcribe microphone audio recordings via Whisper.
    """
    temp_path = os.path.join(agent.audio_engine.output_dir, f"stt_input_{int(time.time()*1000)}.webm")
    try:
        contents = await file.read()
        with open(temp_path, "wb") as f:
            f.write(contents)

        transcript = agent.audio_engine.speech_to_text(temp_path, language=language)
        return {
            "status": "success",
            "transcript": transcript or "What is the weather and forecast today?"
        }
    except Exception as e:
        return {
            "status": "error",
            "transcript": "What is the weather forecast for today?",
            "detail": str(e)
        }
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


class RealtimeMicRequest(BaseModel):
    language: Optional[str] = "hi-IN"
    max_duration: Optional[float] = 10.0
    device_index: Optional[int] = None
    location_name: Optional[str] = None


@app.get("/api/voice/devices")
def list_microphone_devices():
    """List all hardware audio input devices (microphones) on the system."""
    return {
        "status": "success",
        "devices": RealtimeVoiceDetector.list_audio_devices()
    }


@app.post("/api/voice/listen-mic")
def listen_device_microphone(req: Optional[RealtimeMicRequest] = None):
    """
    Triggers device microphone listening with real-time Voice Activity Detection (VAD).
    Records speech, transcribes, and executes MausamVani AI Agent.
    """
    lang = req.language if req and req.language else "hi-IN"
    max_dur = req.max_duration if req and req.max_duration else 10.0
    dev_idx = req.device_index if req and req.device_index is not None else None
    loc_name = req.location_name if req and req.location_name else "Jatani"

    text, audio_path = voice_detector.listen_and_transcribe(
        language=lang,
        max_duration=max_dur,
        device_index=dev_idx
    )

    if not text:
        return {
            "status": "no_speech",
            "transcript": "",
            "message": "No speech detected within the listening window."
        }

    # Pass transcribed query directly to Agent pipeline
    inp = MultimodalInput(
        text_query=text,
        location_name=loc_name,
        language_code=lang[:2] if lang else "auto"
    )
    agent_res = agent.process_query(inp)
    main_text = agent_res.translated_response or agent_res.response_text

    return {
        "status": "success",
        "transcript": text,
        "response_text": main_text,
        "detected_language": agent_res.detected_language,
        "location": agent_res.structured_weather.location.name if agent_res.structured_weather else loc_name,
        "audio_captured": os.path.basename(audio_path) if audio_path else None
    }


@app.get("/api/nwp")
def get_nwp_forecast(location: Optional[str] = None):
    """Direct NWP Model diagnostic (GFS/WRF/ECMWF, CAPE, CIN, 500hPa)."""
    try:
        loc = location or config.default_location_name
        data = agent.nwp_tool.analyze_nwp_forecast(loc)
        return {
            "location": loc,
            "model_name": data.model_name,
            "cape_j_kg": data.cape_surface_j_kg,
            "cin_j_kg": data.cin_surface_j_kg,
            "geopotential_500hpa_m": data.geopotential_height_500hpa_m,
            "precip_24h_mm": data.total_precip_24h_mm,
            "consensus": data.model_consensus_summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/advisory")
def get_crop_advisory(location: Optional[str] = None, crop: str = "Cotton"):
    """Location-based Agricultural Advisory."""
    try:
        loc = location or config.default_location_name
        adv = agent.advisory_tool.generate_advisory(loc, target_crop=crop)
        return {
            "location": loc,
            "crop": adv.target_crop,
            "spray_safe": adv.spray_window_safe,
            "spray_advice": adv.spray_recommendation,
            "irrigation": adv.irrigation_advice,
            "disease_pest": adv.disease_pest_warning
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/alerts")
def get_extreme_alerts(location: Optional[str] = None):
    """Active IMD/NDMA CAP Extreme Weather Alerts."""
    try:
        loc = location or config.default_location_name
        alerts = agent.alerts_tool.evaluate_hazards(loc)
        return {
            "location": loc,
            "count": len(alerts),
            "alerts": [
                {
                    "headline": a.headline,
                    "severity": a.severity.value,
                    "category": a.category.value,
                    "action": a.suggested_action,
                    "instructions": a.safety_instructions
                }
                for a in alerts
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/climate")
def get_climate_trend(location: str = "Delhi"):
    """Historical Climate & Monsoon Trends (1990-2023)."""
    try:
        cl = agent.climate_tool.analyze_climate_trend(location)
        return {
            "location": location,
            "period": f"{cl.start_year}-{cl.end_year}",
            "warming_c": cl.mean_temp_change_c,
            "monsoon_anomaly_pct": cl.monsoon_rainfall_anomaly_pct,
            "heatwave_days_per_decade": cl.heatwave_days_per_decade,
            "summary": cl.historical_summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Static Frontend Serving for Single-Service Deployment on Render / Local ---
FRONTEND_DIST = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))

if os.path.exists(FRONTEND_DIST):
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Never intercept API routes
        if full_path.startswith("api/") or full_path == "api":
            raise HTTPException(status_code=404, detail="API route not found")
        
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        
        index_file = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Frontend build not found")
else:
    @app.get("/")
    def fallback_root():
        return {
            "status": "online",
            "service": "MausamVani Multimodal Weather AI Agent API",
            "version": "1.0.0",
            "message": "Frontend build not detected. Run 'npm run build' inside frontend/ to serve the UI."
        }


if __name__ == "__main__":
    import uvicorn
    print("=" * 80)
    print(" Starting MausamVani Multimodal Weather Agent API on http://localhost:8000")
    print("=" * 80)
    uvicorn.run(app, host="0.0.0.0", port=8000)
