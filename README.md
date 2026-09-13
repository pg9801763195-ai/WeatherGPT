# 🌤️ MausamVani (WeatherGPT)
### *Next-Generation Multimodal Meteorological AI Agent, Agro-Advisory & Disaster Intelligence System*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.x-61DAFB.svg?logo=react&logoColor=black)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-5.x-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev/)
[![Google Auth](https://img.shields.io/badge/Auth-Google_OAuth_2.0_%2B_JWT-4285F4.svg?logo=google&logoColor=white)](https://developers.google.com/identity)
[![Qdrant](https://img.shields.io/badge/Vector_DB-Qdrant-DC2626.svg?logo=qdrant&logoColor=white)](https://qdrant.tech/)
[![Ollama](https://img.shields.io/badge/Local_LLM-Llama_3.1_%7C_Qwen_2.5-black.svg?logo=ollama&logoColor=white)](https://ollama.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📖 Executive Summary

**MausamVani (WeatherGPT)** is an autonomous, multimodal meteorological AI agent designed to bridge the agricultural, linguistic, and digital divide across India. Moving beyond passive numerical dashboards, WeatherGPT translates live atmospheric telemetry and satellite physics into **actionable human intelligence** through conversational voice, computer vision, and agentic reasoning in **11 Indian languages**.

`
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             MAUSAMVANI AGENT CORE                                │
├───────────────────┬───────────────────┬───────────────────┬──────────────────────┤
│ 1. MULTIMODAL     │ 2. INDIC VOICE    │ 3. AGENTIC RAG    │ 4. AUTH & USER       │
│    VISION         │    INTELLIGENCE   │    ENGINE         │    INTELLIGENCE      │
│ Sky, Radar & Crop │ Real-time Mic VAD │ IMD SOPs + ICAR   │ Google OAuth 2.0     │
│ damage diagnosis  │ & Neural TTS for  │ Crop guides via   │ + Sync for History,  │
│ via LLaVA/Gemini  │ 11 languages      │ Qdrant Vector DB  │ Cities & Preferences │
└───────────────────┴───────────────────┴───────────────────┴──────────────────────┘
`

---

## 🌟 Full Feature Breakdown

### 🔐 1. Authentication & Personalized Profile Management
- **Google OAuth 2.0 Integration:** Seamless One-Click Sign-In / Sign-Up with Google (@react-oauth/google / Google Identity Services).
- **Secure Email/Password JWT Auth:** bcrypt-hashed credentials with stateless JWT token lifecycle management.
- **Cross-Device Cloud Sync:**
  - Synchronizes **Saved Cities** & Favorite Weather Stations.
  - Preserves **Multi-turn Assistant Conversation History** across sessions.
  - Saves custom user preferences (Default Units °C/°F, Preferred Language, Theme).

---

### 🎙️ 2. Indic Voice Intelligence & Real-Time Microphones (11 Languages)
- **Bidirectional Multilingual Voice:** Ask queries via voice in your mother tongue; receive high-fidelity neural spoken audio responses.
- **Phonetic Normalizer Transformer:** Real-time transliteration engine for authentic pronunciation in native scripts (including authentic Odia, Bengali, Telugu, Tamil, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Hindi, and Indian English).
- **Dual Mic System:**
  - 🌐 Web Mic: Browser Web Audio API & MediaRecorder streaming (cloud-ready).
  - 🎙️ Device Mic: Hardware Python sounddevice with Energy-based Voice Activity Detection (VAD) for local/IoT setups.
- **Voice Modal Controls:** Independent mic pause/toggle, dedicated **🔄 Reset Mic** button, and zero-prompt accidental submission guards.

---

### 👁️ 3. Multimodal Meteorological Vision Engine
- **Visual Sky & Cloud Classifier:** Diagnoses cloud types (*Cumulonimbus, Altostratus, Cirrostratus*) and calculates precipitation risks directly from sky photos.
- **Crop Damage & Field Health Diagnosis:** Identifies moisture stress, hail damage, and waterlogging from farmer-uploaded field images.
- **Doppler & Satellite Image Reading:** Interprets radar reflectivity color scales and cyclone satellite tracks into simple safety advice.

---

### 🌾 4. Agentic Agro-Meteorological Advisory (ICAR Grounded)
- Ingests **ICAR (Indian Council of Agricultural Research)** crop weather calendars.
- Real-time agronomic guidance for **Kharif, Rabi, and Zaid** crops (Paddy, Wheat, Cotton, Mustard, Sugarcane, Pulses):
  - **Pesticide / Fertilizer Spray Windows:** Prevents chemical drift by blocking spraying during high winds (>15 km/h) or upcoming rain.
  - **Sowing & Soil Moisture Optimization:** Calculates evapotranspiration and optimal soil moisture stages.

---

### 🚨 5. Disaster Warning SOPs & Physics-Grounded NWP Ensembles
- **Official IMD Warning Protocols:** Color-coded alert thresholds (**Green, Yellow, Orange, Red**) indexed in Qdrant Vector DB.
- **Convective Instability Telemetry:** Computes **CAPE (Convective Available Potential Energy)**, Lifted Index, and Wind Shear for early lightning and thunderstorm detection.
- **Multi-Model Physics Consensus:** Aggregates ECMWF IFS, GFS (NOAA), ICON (DWD), and GEM (Canada) ensemble spreads.

---

### 🗺️ 6. Live Doppler Radar & Interactive Weather Map
- **OpenStreetMap Engine:** Interactive mapping built with Leaflet.js.
- **Live Doppler Radar Loop:** 2-hour historical radar loop + 30-minute predictive nowcast precipitation stream via RainViewer.
- **Multi-Point Regional Telemetry Grid:** 8 directional sector probes (North, South, East, West corridors) displaying live thermal heat contours, rotating wind particle arrows, and cloud cover opacity.
- **Click-to-Locate:** Reverse-geocodes any clicked point on Earth to fetch instant localized telemetry.

---

### 📊 7. 30-Year Historical Climate Analysis
- Multi-decade meteorological records (1990–2023+) from **Kaggle Indian Cities Dataset** and **ERA5 Reanalysis**.
- Computes Long Period Average (LPA) monsoon rainfall deviations and extreme temperature trends.

---

## 🛠️ Architecture & Tech Stack

`mermaid
graph TD
    User([👤 User: Voice / Image / Text / Google Login]) --> Frontend[⚛️ React 18 + Vite UI]
    Frontend -->|REST / JWT / Web Audio| Backend[⚡ FastAPI Server]
    
    Backend --> Auth[🔐 Google OAuth 2.0 & JWT Router]
    Auth --> UserDB[(🍃 MongoDB / SQLite)]
    
    Backend --> Router{🧭 Intent & Language Router}
    Router -->|Speech-to-Text| STT[🎙️ Whisper / Google STT]
    Router -->|Vision Analysis| Vision[👁️ LLaVA / Gemini Vision]
    Router -->|Meteorological RAG| VectorDB[(🔴 Qdrant Vector Store)]
    Router -->|Live Telemetry| NWP[🛰️ Open-Meteo & OpenWeather APIs]
    Router -->|Historical Archive| Archive[(📊 30-Year Climate Dataset)]
    
    VectorDB --> Agent[🧠 Multimodal Reasoning Agent]
    NWP --> Agent
    Archive --> Agent
    
    Agent -->|Structured Advisory| Synthesis[🔊 Indic Neural TTS]
    Synthesis --> Frontend
`

| Layer | Technologies Used |
| :--- | :--- |
| **Frontend** | React 18, Vite, Google OAuth SDK (@react-oauth/google), Leaflet.js, Canvas Wind Particles, Lucide Icons, Glassmorphism CSS |
| **Backend** | Python 3.10+, FastAPI, Uvicorn, PyTorch, PyJWT, passlib, sounddevice, edge-tts, gTTS |
| **Authentication** | Google OAuth 2.0, JWT Tokens, bcrypt password hashing |
| **Vector DB & RAG** | Qdrant Vector Database, ChromaDB, sentence-transformers/all-MiniLM-L6-v2, BM25 Ranker |
| **LLMs & Vision** | Google Gemini 2.0 Flash, Meta LLaMA 3.1 (8B via Ollama), Qwen 2.5 (7B), LLaVA 1.6, Custom LoRA Adapter |
| **Telemetry APIs** | Open-Meteo Global NWP & Ensemble API, OpenWeather One Call 3.0, RainViewer API, BigDataCloud Geocoding |
| **Database** | MongoDB (User Profiles, Saved Locations & Chat History), SQLite (Local Fallback) |

---

## 📁 Project Directory Layout

`
WeatherGPT/
├── backend/
│   ├── auth/                  # Google OAuth 2.0, JWT Router & User Models
│   │   ├── auth_router.py     # Login, Register, Google Auth & Profile Endpoints
│   │   └── user_db.py         # MongoDB / SQLite User Persistence Layer
│   ├── core/                  # Multimodal Agent, Memory & Intent Engine
│   │   ├── agent.py           # Master Autonomous Agent Pipeline
│   │   ├── query_understanding.py  # Language Classifier & Overlap Intent Resolver
│   │   └── voice_assistant.py # Live Session Voice Loop
│   ├── data/                  # Historical Climate & SIH Fine-Tuning Splits
│   ├── finetuning/            # LoRA Dataset Formatters & Ollama Exporters
│   ├── multimodal/            # Audio & Computer Vision Engines
│   │   ├── audio_engine.py    # Whisper STT & Indic Phonetic Neural TTS
│   │   ├── realtime_mic.py    # Hardware Voice Activity Detection (VAD)
│   │   └── vision_engine.py   # Cloud, Sky & Crop Computer Vision
│   ├── rag/                   # Qdrant Vector Search & Knowledge Base
│   │   ├── agentic_rag.py     # Hybrid Dense-Sparse RAG Controller
│   │   └── knowledge_data/    # IMD SOPs, ICAR Crop Guides & IPCC Reports
│   ├── tools/                 # Real-time Physics & Weather Tool Suite
│   │   ├── realtime_weather.py# OpenWeather & Open-Meteo Ingestion
│   │   ├── nwp_engine.py      # Numerical Weather Prediction & CAPE Index
│   │   ├── advisory_engine.py # ICAR Agricultural & Human Activity Engine
│   │   └── historical_climate.py # 30-Year Trend & Anomaly Evaluator
│   ├── server.py              # FastAPI Main Application & API Gateway
│   └── config.py              # Central System Configuration
├── frontend/
│   ├── src/
│   │   ├── components/        # UI (AuthModal, VoiceModal, MapTab, AssistantTab)
│   │   ├── context/           # React Context (AuthContext, WeatherContext)
│   │   ├── services/          # API Services (aiAgentService, weatherApi)
│   │   └── utils/             # Multilingual Translations (11 Languages)
│   ├── package.json
│   └── vite.config.js
└── models/                    # LoRA Adapters & SIH Modelfiles
`

---

## 🚀 Step-by-Step Installation & Local Setup

### Prerequisites
- **Node.js** (18.x or higher)
- **Python** (3.10 or higher)
- **MongoDB** (Local instance or MongoDB Atlas URI)

---

### 1. Clone the Repository
`ash
git clone https://github.com/pg9801763195-ai/WeatherGPT.git
cd WeatherGPT
`

---

### 2. Backend Setup
`ash
# Navigate to the backend directory
cd backend

# Create and activate Python virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install all backend dependencies
pip install -r requirements.txt

# Configure your environment variables in .env
cat <<EOT >> .env
# AI & Weather API Keys
GEMINI_API_KEY=your_google_gemini_api_key
OPENWEATHER_API_KEY=your_openweather_api_key

# Authentication & Database
JWT_SECRET=your_super_secret_jwt_key
GOOGLE_CLIENT_ID=your_google_oauth_client_id.apps.googleusercontent.com
MONGODB_URI=mongodb://localhost:27017/weathergpt

# Execution Modes
PRIMARY_BACKEND=auto
VECTOR_DB_BACKEND=qdrant
USE_GPU=true
EOT

# Start the Backend Server
python -m uvicorn server:app --reload --port 8000
`
*Backend API will run at http://localhost:8000 (Interactive Swagger documentation at http://localhost:8000/docs).*

---

### 3. Frontend Setup
`ash
# Open a new terminal and navigate to the frontend
cd frontend

# Install Node modules
npm install

# Configure Frontend environment variables in .env
cat <<EOT >> .env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_GOOGLE_CLIENT_ID=your_google_oauth_client_id.apps.googleusercontent.com
EOT

# Start Vite Development Server
npm run dev
`
*Frontend will be live at http://localhost:3000.*

---

### 4. Optional Local Edge LLM (via Ollama)
To run WeatherGPT 100% offline without cloud API keys:
`ash
# Pull required local models
ollama pull llama3.1:latest
ollama pull llava:latest
ollama pull qwen2.5:7b

# In backend/.env, set:
PRIMARY_BACKEND=ollama
`

---

## 🌐 Supported Indian Regional Languages

| Language | Code | Native Script | Spoken Neural Voice |
| :--- | :---: | :--- | :--- |
| **Hindi** | hi | हिन्दी | hi-IN-SwaraNeural |
| **Odia** | or | ଓଡ଼ିଆ | Phonetic Indic Transformer (hi-IN-SwaraNeural) |
| **Bengali** | n | বাংলা | n-IN-TanishaaNeural |
| **Telugu** | 	e | తెలుగు | 	e-IN-MohanNeural |
| **Tamil** | 	a | தமிழ் | 	a-IN-PallaviNeural |
| **Marathi** | mr | मराठी | mr-IN-AarohiNeural |
| **Gujarati** | gu | ગુજરાતી | gu-IN-DhwaniNeural |
| **Kannada** | kn | ಕನ್ನಡ | kn-IN-GaganNeural |
| **Malayalam** | ml | മലയാളം | ml-IN-SobhanaNeural |
| **Punjabi** | pa | ਪੰਜਾਬੀ | pa-IN-GurpreetNeural |
| **English** | en | English | en-IN-NeerjaNeural |

---

## 📡 API Reference Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| POST | /api/auth/google | Authenticates Google OAuth ID token & issues JWT. |
| POST | /api/auth/login | Standard email/password user login. |
| POST | /api/auth/register | Registers new user account with hashed password. |
| GET | /api/auth/me | Fetches authenticated user profile and saved state. |
| POST | /api/chat | Main Multimodal Reasoning Agent (text/audio/image). |
| POST | /api/tts | Synthesizes regional Indian speech audio (returns base64 MP3). |
| POST | /api/stt | Transcribes voice input files using Whisper. |
| POST | /api/voice/listen-mic | Activates real-time hardware microphone VAD. |
| GET | /api/nwp | Returns physics ensemble forecast, CAPE, and rain probability. |
| GET | /api/advisory | Computes ICAR-compliant agricultural and travel safety advice. |
| GET | /api/alerts | Fetches color-coded IMD disaster warnings & SOPs. |
| GET | /api/climate | Retrieves 30-year historical climate baselines and LPA deviations. |

---

## ⚖️ License
This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.
