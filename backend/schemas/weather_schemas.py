"""
Pydantic data models and schemas for the Multimodal Weather & NWP AI Agent.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    GREEN = "green"      # Normal / No Warning
    YELLOW = "yellow"    # Be Updated / Watch
    ORANGE = "orange"    # Be Prepared / Alert
    RED = "red"          # Take Action / Warning


class AlertCategory(str, Enum):
    CYCLONE = "Cyclone"
    HEAVY_RAINFALL = "Heavy Rainfall"
    FLASH_FLOOD = "Flash Flood"
    HEATWAVE = "Heatwave"
    COLDWAVE = "Cold Wave"
    THUNDERSTORM = "Thunderstorm & Lightning"
    DROUGHT = "Drought"
    DUST_STORM = "Dust Storm"


class GeoLocation(BaseModel):
    """Geographical location details."""
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
    visibility_km: Optional[float] = Field(default=10.0, description="Horizontal visibility in km")
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


class NWPModelForecast(BaseModel):
    """Numerical Weather Prediction (NWP) model outputs (GFS/ECMWF/WRF)."""
    model_name: str = Field(description="e.g., NOAA GFS 0.25, ECMWF IFS 0.25, or WRF")
    location: GeoLocation
    reference_time: str
    cape_surface_j_kg: float = Field(description="Convective Available Potential Energy (CAPE) in J/kg (thunderstorm potential)")
    cin_surface_j_kg: Optional[float] = Field(default=0.0, description="Convective Inhibition in J/kg")
    total_precip_24h_mm: float = Field(description="Accumulated 24-hour precipitation")
    temp_500hpa_c: Optional[float] = Field(default=None, description="Temperature at 500 hPa pressure level")
    geopotential_height_500hpa_m: Optional[float] = Field(default=None, description="500 hPa Geopotential Height (m)")
    ensemble_spread_std: Optional[float] = Field(default=None, description="Uncertainty spread across ensemble members")
    model_consensus_summary: str = Field(description="Brief consensus summary among NWP models")


class ExtremeWeatherAlert(BaseModel):
    """IMD/CAP formatted extreme weather alert & early warning."""
    alert_id: str
    location: GeoLocation
    category: AlertCategory
    severity: AlertSeverity
    headline: str
    description: str
    safety_instructions: List[str]
    valid_from: str
    valid_to: str
    impact_level: str = Field(description="Low, Moderate, High, Severe")
    suggested_action: str


class AgroAdvisory(BaseModel):
    """Agricultural and rural advisory tailored for crops and local weather."""
    location: GeoLocation
    target_crop: str = Field(description="e.g., Cotton, Paddy, Wheat, Mustard, Soybean")
    crop_stage: Optional[str] = Field(default="Vegetative/Flowering", description="Crop stage")
    irrigation_advice: str = Field(description="Irrigation recommendation based on ET0 and rain forecast")
    spray_window_safe: bool = Field(description="Is it safe to spray pesticides/fertilizers today?")
    spray_recommendation: str = Field(description="Detailed spray advice (rain/wind factor)")
    disease_pest_warning: Optional[str] = Field(default=None, description="Pest or fungal risks due to humidity/temp")
    general_guidance: List[str] = Field(default_factory=list)


class HistoricalClimateTrend(BaseModel):
    """Historical climate analysis and anomaly trends."""
    location: GeoLocation
    start_year: int
    end_year: int
    mean_temp_change_c: float = Field(description="Observed temperature change over the period")
    monsoon_rainfall_anomaly_pct: float = Field(description="Percentage deviation from long-period average (LPA)")
    heatwave_days_per_decade: float = Field(description="Frequency trend of heatwave days")
    historical_summary: str = Field(description="Synthesis of historical shifts in climate for the region")



class CanonicalIntent(str, Enum):
    CURRENT_WEATHER = "current_weather"
    WEATHER_FORECAST = "weather_forecast"
    PRECIPITATION = "precipitation"
    OUTFIT_RECOMMENDATION = "outfit_recommendation"
    CLOTHES_DRYING = "clothes_drying"
    OUTDOOR_ACTIVITY = "outdoor_activity"
    TRAVEL_WEATHER = "travel_weather"
    AGRO_ADVISORY = "agro_advisory"
    WEATHER_ALERT = "weather_alert"
    NWP_ANALYSIS = "nwp_analysis"
    HISTORICAL_CLIMATE = "historical_climate"
    LOCATION_INFO = "location_info"
    CASUAL_CONVERSATION = "casual_conversation"



class ResolvedQuery(BaseModel):
    """Authoritative structured query object representing canonical understanding of user intent and parameters."""
    intent: CanonicalIntent = Field(default=CanonicalIntent.CURRENT_WEATHER, description="Authoritative canonical intent")
    location: str = Field(description="Canonical resolved location name")
    latitude: Optional[float] = Field(default=None, description="Resolved latitude coordinate")
    longitude: Optional[float] = Field(default=None, description="Resolved longitude coordinate")
    time_reference: str = Field(default="today", description="today | tomorrow | day_after_tomorrow | next_3_days | next_7_days | weekend | specific_date | historical")
    target_date: Optional[str] = Field(default=None, description="Explicit date if specified")
    weather_parameters: List[str] = Field(default_factory=lambda: ["general_weather"], description="Target parameters")
    activity: Optional[str] = Field(default=None, description="Activity context (cricket, car_wash, travel, etc.)")
    crop: Optional[str] = Field(default=None, description="Target crop for agro queries")
    language: str = Field(default="en", description="Detected language code")
    is_follow_up: bool = Field(default=False, description="Whether query is a conversational follow-up")
    confidence: float = Field(default=1.0, description="Confidence score")
    entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted entities and metadata")


class MultimodalInput(BaseModel):
    """Input payload to the agent encompassing text, voice audio, or imagery."""
    text_query: Optional[str] = None
    audio_path: Optional[str] = None
    image_path: Optional[str] = None
    image_base64: Optional[str] = None
    language_code: Optional[str] = "auto"
    location_name: Optional[str] = None


class AgentResponse(BaseModel):
    """Unified response from the Multimodal Weather AI Agent."""
    query: str
    response_text: str
    detected_language: str = "en"
    translated_response: Optional[str] = None
    structured_weather: Optional[CurrentWeather] = None
    daily_forecasts: Optional[List[DailyForecastItem]] = None
    nwp_forecast: Optional[NWPModelForecast] = None
    extreme_alerts: Optional[List[ExtremeWeatherAlert]] = None
    agro_advisory: Optional[AgroAdvisory] = None
    climate_trend: Optional[HistoricalClimateTrend] = None
    audio_output_file: Optional[str] = None
    visual_analysis: Optional[str] = None
    rag_sources: Optional[List[Dict[str, Any]]] = None
    resolved_query: Optional[ResolvedQuery] = None

