# ⚡ WeatherGPT: Multimodal AI Meteorological & Atmospheric Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.0+-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org)
[![Vite](https://img.shields.io/badge/Vite-5.0+-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev)
[![MongoDB](https://img.shields.io/badge/MongoDB_Atlas-4.0+-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://mongodb.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)

**WeatherGPT** is a production-grade, multimodal meteorological AI assistant and atmospheric telemetry platform. It provides real-time forecasting, NWP model diagnostics (GFS/WRF/ECMWF), IMD/NDMA extreme weather early warnings, agricultural crop advisories, multi-decadal historical climate analysis, neural voice synthesis in Indian regional languages, and user-owned persistent conversation history powered by **MongoDB Atlas**.

---

## 📁 Repository Structure

```
Weather GPT 1/
├── 📂 frontend/               # React 18 + Vite + TailwindCSS Atmospheric Web Application
│   ├── src/                  # React components, context, services, state management
│   ├── public/               # Static assets & media
│   ├── Dockerfile            # Multi-stage production Nginx container
│   ├── nginx.conf            # Reverse-proxy configuration for /api
│   ├── package.json          # Node dependencies
│   └── vite.config.js        # Vite build & dev server config
│
├── 📂 backend/                # FastAPI Production API & Meteorological Agent Engine
│   ├── auth/                 # JWT security, BCRYPT hashing, OTP verification, SMTP service
│   ├── core/                 # Query understanding engine, multi-turn memory, AI agent
│   ├── db/                   # MongoDB database manager, indexes, and CRUD operations
│   ├── multimodal/           # Neural Edge-TTS voice synthesis & Whisper STT
│   ├── rag/                  # Meteorological RAG vector database & document stores
│   ├── schemas/              # Pydantic schemas and canonical weather intents
│   ├── tools/                # Real-time Open-Meteo API, NWP diagnostics, geocoding
│   ├── server.py             # FastAPI entry point & API routes
│   ├── requirements.txt      # Python production dependencies
│   └── Dockerfile            # Production Python 3.11 container
│
├── 📂 models/                 # Machine Learning, Fine-Tuning & Model Serving
│   ├── lora_tuner.py         # PEFT / LoRA fine-tuning for LLaMA-3.1 & Qwen-2.5
│   ├── dataset_formatter.py  # Climate record & CAP warning dataset synthesizer
│   ├── lora_adapter.py       # LoRA weight merging & adapter management
│   ├── ollama_adapter_exporter.py # Ollama Modelfile exporter
│   └── README.md             # Model fine-tuning guide
│
├── .env                      # Environment configuration
├── .gitignore                # Production gitignore (excludes secrets & build artifacts)
├── docker-compose.yml        # Production multi-container orchestration
├── start_dev.bat             # Windows one-click local launch script
├── start_dev.sh              # Linux / macOS local launch script
└── README.md                 # Project documentation
```


---

## ⚡ Features

1. **Production Authentication & Security**:
   - 3 choices: **Guest** (instant access, zero history persisted), **Sign In / Create Account** (3-step OTP verification + BCRYPT password), **Login** (Email + Password).
   - **PyJWT Tokens**: Non-sensitive claims with HttpOnly cookies & Bearer authorization headers.
   - **Strict IDOR Access Control**: Database queries strictly isolated by authenticated user ID.
2. **Natural Language & Multilingual Understanding**:
   - Full support for English, Hindi, and natural Hinglish.
   - Zero hardcoded city lists: dynamic NER and geocoding.
   - Multi-turn conversation inheritance (inherits locations and temporal references like *"tomorrow"*, *"day after tomorrow"* across turns).
3. **Meteorological Capabilities**:
   - Real-time weather telemetry (temperature, precipitation probability, humidity, UV index, wind speed/direction).
   - Numerical Weather Prediction (NWP) model diagnostics (CAPE, CIN, surface pressure, lifted index).
   - Agricultural advisory engine with crop spray safety windows and soil moisture alerts.
4. **Multimodal Interaction**:
   - Neural regional voice synthesis powered by `edge-tts`.
   - Voice transcription powered by OpenAI Whisper.

---

## 🚀 Quick Start (Local Development)

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- **MongoDB Atlas** connection string (or local MongoDB on port 27017)

### 2. Environment Setup
Configure your settings in the `.env` file in the root directory:

```env
# MongoDB Atlas
MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=weathergpt

# JWT Secret
JWT_SECRET=your-secure-32-character-jwt-secret-key-2026

# SMTP Email Configuration (For live OTPs via Gmail)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_16_char_google_app_password
SMTP_FROM=WeatherGPT <your_email@gmail.com>
SMTP_USE_TLS=true
```

### 3. One-Click Launch

**Windows**:
```cmd
start_dev.bat
```

**Linux / macOS**:
```bash
chmod +x start_dev.sh
./start_dev.sh
```

### 4. Manual Launch
**Backend**:
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend**:
```bash
cd frontend
npm install
npm run dev
```

The web application will be accessible at:
- **Frontend App**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **Interactive OpenAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🐳 Production Deployment with Docker

To deploy the full platform in isolated production containers:

```bash
docker compose up --build -d
```

- **Frontend (Nginx)**: Port `3000` (proxies `/api` to backend)
- **Backend (FastAPI)**: Port `8000`

---

## 📜 License
MIT License. Built for advanced meteorological intelligence.

