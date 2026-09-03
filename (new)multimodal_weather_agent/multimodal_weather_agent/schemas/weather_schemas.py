"""
Data schemas and Pydantic models for Weather, NWP, Alerts, Agro-Advisory, Climate & Voice I/O.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class GeoLocation(BaseModel):
    """Geographical location metadata."""
    name: str = Field(description="City or district name, e.g., 'Nagpur'")
    latitude: float = Field(description="Latitude coordinate")
    longitude: float = Field(description="Longitude coordinate")
    state: Optional[str] = Field(default=None, description="State or province, e.g., 'Maharashtra'")
    country: Optional[str] = Field(default="India", description="Country name")


class CurrentWeather(BaseModel):
    """Real-time current meteorological observations."""
    location: GeoLocation
    timestamp: str
    temperature_c: float = Field(description="Temperature in Celsius")
    apparent_temperature_c: float = Field(description="Feels-like temperature in Celsius")
    relative_humidity_pct: float = Field(description="Relative humidity percentage")
    precipitation_mm: float = Field(default=0.0, description="Precipitation in mm")
    weather_code: int = Field(description="WMO Weather interpretation code")
    weather_description: str = Field(description="Human-readable weather description")
    wind_speed_kmh: float = Field(description="Wind speed in km/h")
    wind_direction_deg: float = Field(description="Wind direction in degrees")
    wind_gusts_kmh: Optional[float] = Field(default=0.0, description="Wind gusts in km/h")
    surface_pressure_hpa: float = Field(description="Surface atmospheric pressure in hPa")
    uv_index: Optional[float] = Field(default=0.0, description="UV Radiation index")
    cloud_cover_pct: Optional[float] = Field(default=0.0, description="Cloud cover percentage")
    aqi: Optional[int] = Field(default=None, description="Air Quality Index (1: Good, 2: Fair, 3: Moderate, 4: Poor, 5: Very Poor)")
    aqi_category: Optional[str] = Field(default=None, description="Air Quality Category, e.g. 'Good', 'Moderate', 'Poor'")
    pm2_5: Optional[float] = Field(default=None, description="PM2.5 particulate matter (μg/m³)")
    pm10: Optional[float] = Field(default=None, description="PM10 particulate matter (μg/m³)")
    provider: Optional[str] = Field(default="OpenWeatherMap / Open-Meteo", description="Source data provider")


class DailyForecastItem(BaseModel):
    """Daily forecast summary item."""
    date: str
    temp_max_c: float
    temp_min_c: float
    precipitation_sum_mm: float
    precipitation_probability_pct: int
    weather_code: int
    weather_description: str
    max_wind_speed_kmh: float
    et0_evapotranspiration_mm: Optional[float] = Field(default=None, description="Reference Evapotranspiration for agriculture")


class NWPForecast(BaseModel):
    """Numerical Weather Prediction (GFS/ECMWF/WRF) model outputs."""
    model_name: str = Field(description="NWP Model, e.g., 'NOAA GFS 0.25' or 'ECMWF IFS'")
    init_time: str = Field(description="Model run initialization timestamp")
    cape_j_kg: float = Field(description="Convective Available Potential Energy (J/kg)")
    cin_j_kg: float = Field(description="Convective Inhibition (J/kg)")
    geopotential_height_500hpa: float = Field(description="500 hPa Geopotential Height (m)")
    lifted_index: Optional[float] = Field(default=None, description="Atmospheric Lifted Index")
    freezing_level_m: Optional[float] = Field(default=None, description="Freezing Level Height (m)")
    boundary_layer_height_m: Optional[float] = Field(default=None, description="Planetary Boundary Layer Height")


class CAPAlert(BaseModel):
    """Common Alerting Protocol (CAP) for severe/extreme weather events."""
    identifier: str
    sender: str = Field(default="India Meteorological Department (IMD) / NDMA")
    event: str = Field(description="Alert type, e.g. 'Severe Cyclone Warning', 'Extreme Heatwave', 'Flash Flood'")
    severity: str = Field(description="Alert severity: 'Extreme', 'Severe', 'Moderate', 'Minor'")
    urgency: str = Field(description="Urgency: 'Immediate', 'Expected', 'Future'")
    headline: str
    description: str
    instruction: str
    area_desc: str
    effective_time: str
    expires_time: str


class AgroAdvisory(BaseModel):
    """Agricultural and farming advisory recommendations."""
    crop_name: str
    growth_stage: str
    spray_window_safe: bool = Field(description="Whether meteorological conditions permit chemical spray")
    spray_recommendation: str = Field(description="Actionable pesticide/herbicide guidance based on wind/rain/temp")
    irrigation_advice: str = Field(description="Evapotranspiration-based irrigation advice")
    pest_disease_risk: str = Field(description="Risk of pest/fungal infestation based on microclimate triggers")
    rural_operations_guidance: List[str] = Field(default_factory=list, description="Specific field tasks advice")


class ClimateTrendAnalysis(BaseModel):
    """Multi-decadal historical climate analysis from Kaggle/ERA5 datasets."""
    location_name: str
    period: str = Field(default="1990 - 2023 (34 Years)")
    mean_temp_change_c: float = Field(description="Mean temperature anomaly change in °C")
    monsoon_rainfall_anomaly_pct: float = Field(description="Monsoon rainfall anomaly compared to normal")
    heatwave_frequency_change_days: float = Field(description="Annual heatwave day changes per decade")
    historical_summary: str = Field(description="Synthesis of multi-decadal trends")


class MultimodalInput(BaseModel):
    """Multimodal input contract supporting text, voice, and vision."""
    text_query: Optional[str] = Field(default=None, description="Natural language prompt")
    audio_path: Optional[str] = Field(default=None, description="Path to voice query audio file (.wav/.mp3)")
    image_path: Optional[str] = Field(default=None, description="Path to Doppler radar / crop foliage image")
    language_code: Optional[str] = Field(default="en", description="User language code ('en', 'hi', 'te', 'ta', etc.)")
    location: Optional[str] = Field(default=None, description="Location override")
    crop: Optional[str] = Field(default=None, description="Crop context (e.g. 'Cotton', 'Paddy')")


class AgentResponse(BaseModel):
    """Unified response contract for the Multimodal Weather AI Agent."""
    response_text: str
    current_weather: Optional[CurrentWeather] = None
    forecasts: List[DailyForecastItem] = Field(default_factory=list)
    nwp_data: Optional[NWPForecast] = None
    active_alerts: List[CAPAlert] = Field(default_factory=list)
    agro_advisory: Optional[AgroAdvisory] = None
    climate_trends: Optional[ClimateTrendAnalysis] = None
    translated_response: Optional[str] = None
    audio_output_file: Optional[str] = None
    retrieval_sources: List[str] = Field(default_factory=list)
