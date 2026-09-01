@echo off
title WeatherGPT Local Development Launcher
echo =======================================================
echo  Starting WeatherGPT AI Platform (FastAPI + React Vite)
echo =======================================================
echo.

echo Starting Backend Server on http://localhost:8000 ...
start "WeatherGPT Backend" cmd /k "cd backend && python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 2 /nobreak >nul

echo Starting Frontend Web App on http://localhost:3000 ...
start "WeatherGPT Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo =======================================================
echo  WeatherGPT is running!
echo  - Frontend: http://localhost:3000
echo  - Backend API: http://localhost:8000
echo  - API Docs: http://localhost:8000/docs
echo =======================================================
