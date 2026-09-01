"""Schemas module for Multimodal Weather AI Agent."""
from .weather_schemas import (
    GeoLocation,
    CurrentWeather,
    DailyForecastItem,
    NWPModelForecast,
    ExtremeWeatherAlert,
    AgroAdvisory,
    HistoricalClimateTrend,
    MultimodalInput,
    AgentResponse
)

__all__ = [
    "GeoLocation",
    "CurrentWeather",
    "DailyForecastItem",
    "NWPModelForecast",
    "ExtremeWeatherAlert",
    "AgroAdvisory",
    "HistoricalClimateTrend",
    "MultimodalInput",
    "AgentResponse"
]
