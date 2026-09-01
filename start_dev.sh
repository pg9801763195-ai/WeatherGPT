#!/usr/bin/env bash
# ==============================================================================
# WeatherGPT Local Development Launcher (Linux / macOS)
# ==============================================================================

echo "======================================================="
echo " Starting WeatherGPT AI Platform (FastAPI + React Vite)"
echo "======================================================="

# Trap Ctrl+C to kill child processes
trap 'kill $(jobs -p)' EXIT

# Start Backend
echo "Starting Backend Server on http://localhost:8000 ..."
(cd backend && python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload) &

sleep 2

# Start Frontend
echo "Starting Frontend Web App on http://localhost:3000 ..."
(cd frontend && npm run dev) &

wait
