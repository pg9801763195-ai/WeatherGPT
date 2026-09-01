# MausamVani: Open-Source Multimodal Weather, NWP & Agro-Advisory Agent

A multimodal AI Agent engine built for weather intelligence, Numerical Weather Prediction (NWP) diagnostics, agro-meteorological advisories, extreme hazard early warnings, and Indian multilingual voice/vision interactions powered by open-source models (Ollama, Whisper, edge-tts, ChromaDB).

---

## 🌟 Core Capabilities (All 8 Requirements)

1. **Real-time Weather Information Retrieval**
   - High-resolution live surface observations (Temperature, Apparent Temp, Relative Humidity, Pressure, Wind Speed & Gusts, Cloud Cover, UV Index).
   - WMO 4677 standard weather code interpretation.
   - Built-in geocoding supporting global and Indian regional locations.

2. **Natural Language Querying for Weather Forecasts**
   - Conversational multi-day forecasts with daily precipitation probabilities, temperature bounds, and evapotranspiration (ET0).

3. **Integration with Numerical Weather Prediction (NWP) Models**
   - Multi-model integration with **NOAA GFS 0.25°**, **ECMWF IFS**, and **WRF** meso-scale models.
   - Convective Available Potential Energy (**CAPE**), Convective Inhibition (**CIN**), and 500 hPa Geopotential Height diagnostics.
   - Multi-model ensemble spread and atmospheric instability consensus.

4. **Extreme Weather Alerts & Early Warning Dissemination**
   - Compliant with **IMD & NDMA CAP (Common Alerting Protocol)**.
   - Automated threshold detection for Cyclones, Severe Thunderstorms & Lightning (DAMINI protocol), Heatwaves, Flash Floods, and Heavy Rainfall.
   - Actionable safety advisories for rural populations, livestock, and farmers.

5. **Location-Based Forecasting & Agro-Advisory Generation**
   - Crop-specific spray window calculator (checks wind drift, rain wash-off, and evaporation temperature).
   - Dynamic irrigation scheduling comparing ET0 demand against upcoming precipitation.
   - Disease and pest trigger modeling for major crops (Paddy, Cotton, Wheat, Mustard, Soybean, Tomato, Chilli).

6. **Multilingual Support for Indian Languages**
   - Automatic script detection and localized translation for **Hindi, Telugu, Tamil, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi, and Odia**.
   - Agricultural and meteorological domain glossary integration.

7. **Climate Trend & Historical Weather Analysis (Kaggle Indian Cities Dataset)**
   - Integrates the **Kaggle Historical Weather Data for Indian Cities** (`hiteshsoneji/historical-weather-data-for-indian-cities`) spanning 1990–2023 for Delhi, Mumbai, Bengaluru, Chennai, Nagpur, Kolkata, etc.
   - Computes decadal warming rates, annual heatwave escalations, and monsoon anomalies against Climatological Normals.
   - Fallback to global ERA5 reanalysis archives (1950–present).

8. **Voice-Enabled Interaction for Rural Accessibility**
   - Speech-to-Text (STT) via **Whisper**.
   - Text-to-Speech (TTS) via **edge-tts** with regional Indian neural voices and **gTTS** fallback.
   - Generates broadcast-ready `.wav` / `.mp3` voice advisories for community radio and village PA systems.

9. **Agentic RAG Engine (Multi-Hop Planning, Dynamic Routing & Self-RAG)**
   - **Autonomous Query Planner**: Decomposes multifaceted user queries into atomic search sub-goals.
   - **Multi-Source Dynamic Router**: Automatically queries specialized indices (**IPCC AR6 ClimateQA**, **IMD Warning Protocols**, **Agro-Meteorological Crop Guides**, **Kaggle Indian Cities Weather History**).
   - **Self-RAG Relevance Evaluator**: Grades document relevance scores ($0.0\text{ to }1.0$) and filters out unhelpful context.
   - **Self-Correction & Query Rewriting**: Expands narrow search keywords with agronomic and synoptic terms.
   - **Dual Vector Engine**: Supports **Qdrant** and **ChromaDB** with dense vector and BM25 hybrid indexing.

10. **Multimodal Remote Sensing & Crop Vision**
   - Integrates Ollama Vision models (**LLaVA / LLaMA 3.2 Vision**) to interpret Doppler radar reflectivity, satellite infrared cloud scans, and crop foliage stress images.

11. **LoRA (Low-Rank Adaptation) Matrix Fine-Tuning & Hyperparameter Tuning**
   - **Mathematical Formulation**: $W = W_0 + \frac{\alpha}{r} (B \times A)$ decomposing high-dimensional weight updates into low-rank factor matrices ($r \ll d$).
   - **Hyperparameter Grid Search**: Sweeps rank $r \in [4, 8, 16, 32]$, $\alpha$, target modules, and evaluates Pareto-optimal configurations balancing accuracy, loss, and VRAM.
   - **Parameter Efficiency**: Adapts 8B models by tuning $< 0.3\%$ of total parameters ($\sim 22.5\text{ M}$ params, requiring only $\sim 6.9\text{ GB}$ VRAM).
   - **Dataset Formatter & Ollama Exporter**: Exports Alpaca/ChatML JSONL instruction splits and generates Ollama `Modelfile` with `ADAPTER` directives for local deployment.

---

## 🏗️ Architecture

```
                               ┌────────────────────────────────────────────────────────┐
                               │           Multimodal Weather Agent Core                │
                               │  (Ollama: LLaMA 3.1 / Qwen 2.5 / LLaMA 3.2 Vision)     │
                               └──────────────────────┬─────────────────────────────────┘
                                                      │
         ┌─────────────────────────┬──────────────────┼──────────────────┬────────────────────────┐
         │                         │                  │                  │                        │
         ▼                         ▼                  ▼                  ▼                        ▼
┌──────────────────┐      ┌─────────────────┐ ┌───────────────┐ ┌──────────────────┐      ┌───────────────┐
│ Multimodal I/O   │      │ Weather Tools   │ │ NWP Engine    │ │ Extreme Alert    │      │ Local RAG     │
├──────────────────┤      ├─────────────────┤ ├───────────────┤ ├──────────────────┤      ├───────────────┤
│ • Whisper (STT)  │      │ • Open-Meteo    │ │ • GFS 0.25°   │ │ • IMD CAP Alerts │      │ • ChromaDB    │
│ • edge-tts (TTS) │      │ • OpenWeather   │ │ • ECMWF IFS   │ │ • Anomaly Radar  │      │ • BGE-M3      │
│ • Vision Engine  │      │ • Historical    │ │ • WRF Regional│ │ • Cyclone/Flood  │      │ • Agro Guides │
│ • Indic Langs    │      │ • Agro Advisory │ │ • NetCDF/GRIB2│ │ • Heatwave Warn  │      │ • IMD Docs    │
└──────────────────┘      └─────────────────┘ └───────────────┘ └──────────────────┘      └───────────────┘
```

---

## 🚀 Quickstart

### 1. Installation

```bash
pip install -r requirements.txt
```

### 2. Ollama Setup (Local Open-Source LLMs)

Start Ollama and pull your preferred text and vision models:

```bash
# Pull LLM for reasoning & translation
ollama pull llama3.1:latest
# Or Qwen 2.5:
# ollama pull qwen2.5:7b

# Pull Multimodal Vision model
ollama pull llava:latest
# Or LLaMA 3.2 Vision:
# ollama pull llama3.2-vision:11b
```

### 3. Python Usage

```python
from config import AgentConfig
from core.agent import MultimodalWeatherAgent
from schemas.weather_schemas import MultimodalInput

# Initialize agent
config = AgentConfig(
    ollama_host="http://localhost:11434",
    llm_model="llama3.1:latest",
    vision_model="llava:latest"
)
agent = MultimodalWeatherAgent(config)

# 1. Text Query with Location & Crop Advisory
response = agent.process_query(MultimodalInput(
    text_query="Is it safe to spray pesticide on cotton in Nagpur today?"
))
print(response.response_text)

# 2. Multilingual Query in Hindi
hindi_resp = agent.process_query(MultimodalInput(
    text_query="क्या कल वाराणसी में बारिश होगी?",
    language_code="hi"
))
print(hindi_resp.translated_response)

# 3. Voice Query Input (STT -> Reasoning -> TTS Voice Output)
voice_resp = agent.process_query(MultimodalInput(
    audio_path="sample_query.wav",
    language_code="te"
))
print(f"Generated Audio File: {voice_resp.audio_output_file}")
```

### 4. Run Comprehensive Verification Suite

To verify all 8 test cases in a single execution:

```bash
python examples/demo_all_cases.py
```

---

## 📁 Repository Structure

```
multimodal_weather_agent/
├── config.py                     # Central configuration for Ollama, endpoints & voices
├── requirements.txt              # Dependencies
├── README.md                     # Documentation
├── main.py                       # High-level entrypoint
├── schemas/
│   ├── __init__.py
│   └── weather_schemas.py        # Pydantic schemas (NWP, Alerts, Advisory, Weather)
├── tools/
│   ├── __init__.py
│   ├── realtime_weather.py       # Live surface weather & 7-day forecast
│   ├── nwp_engine.py             # NOAA GFS 0.25, ECMWF & WRF CAPE diagnostics
│   ├── alerts_engine.py          # IMD/NDMA CAP Extreme weather early warning system
│   ├── advisory_engine.py        # Spray windows, irrigation & crop pest triggers
│   └── historical_climate.py     # ERA5 reanalysis & monsoon anomaly analysis
├── rag/
│   ├── __init__.py
│   ├── hybrid_retriever.py       # Dense vector (ChromaDB) + BM25 keyword retriever
│   └── knowledge_data/           # IMD SOPs, crop guides, and disaster protocols
│       ├── imd_advisories.json
│       ├── crop_weather_guides.json
│       └── extreme_weather_sops.json
├── multimodal/
│   ├── __init__.py
│   ├── vision_engine.py          # Radar reflectivity & satellite cloud interpreter
│   ├── audio_engine.py           # Whisper STT & edge-tts/gTTS regional voice synthesizer
│   └── multilingual.py           # Indic language detection & translation engine
└── examples/
    ├── __init__.py
    └── demo_all_cases.py         # Complete verification test suite for all 8 requirements
```
