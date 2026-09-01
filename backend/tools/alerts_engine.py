"""
Extreme Weather Alert & Early Warning Dissemination Engine.
Complies with IMD / NDMA CAP criteria for Cyclones, Heatwaves, Heavy Rainfall, Flash Floods, and Thunderstorms.
"""
import uuid
from typing import List, Optional
from config import AgentConfig
from schemas.weather_schemas import (
    GeoLocation,
    CurrentWeather,
    NWPModelForecast,
    ExtremeWeatherAlert,
    AlertCategory,
    AlertSeverity
)
from tools.realtime_weather import RealtimeWeatherTool
from tools.nwp_engine import NWPEngineTool


class ExtremeAlertsEngineTool:
    """Detects dangerous meteorological anomalies and generates CAP early warnings."""

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        self.weather_tool = RealtimeWeatherTool(self.config)
        self.nwp_tool = NWPEngineTool(self.config)

    def evaluate_hazards(
        self,
        location_query: str,
        weather: Optional[CurrentWeather] = None,
        nwp: Optional[NWPModelForecast] = None
    ) -> List[ExtremeWeatherAlert]:
        """Evaluate real-time and NWP forecast parameters against meteorological hazard thresholds."""
        if weather is None:
            weather, _ = self.weather_tool.get_current_weather(location_query)
        if nwp is None:
            nwp = self.nwp_tool.analyze_nwp_forecast(location_query)

        geo = weather.location
        alerts: List[ExtremeWeatherAlert] = []

        # 1. Heatwave Hazard Evaluation (IMD Criteria)
        if weather.temperature_c >= 45.0 or (weather.temperature_c >= 40.0 and weather.apparent_temperature_c >= 48.0):
            alerts.append(ExtremeWeatherAlert(
                alert_id=f"IMD-HW-{uuid.uuid4().hex[:6].upper()}",
                location=geo,
                category=AlertCategory.HEATWAVE,
                severity=AlertSeverity.RED if weather.temperature_c >= 45.0 else AlertSeverity.ORANGE,
                headline=f"Severe Heatwave Warning for {geo.name}",
                description=f"Day temperatures reaching {weather.temperature_c:.1f}°C with heat index exceeding {weather.apparent_temperature_c:.1f}°C. Extreme risk of heat exhaustion and sunstroke.",
                safety_instructions=[
                    "Avoid direct sun exposure between 11:00 AM and 4:00 PM.",
                    "Drink ORS, lemon water, butter milk (chaas), and stay continuously hydrated.",
                    "Provide covered shade and adequate clean drinking water for cattle and livestock.",
                    "Postpone strenuous outdoor field work to early morning or late evening hours."
                ],
                valid_from=weather.timestamp,
                valid_to="Next 24 Hours",
                impact_level="Severe",
                suggested_action="Issue red alert sirens, activate cooling centers, and restrict noon outdoor labor."
            ))
        elif weather.temperature_c >= 40.0:
            alerts.append(ExtremeWeatherAlert(
                alert_id=f"IMD-HW-{uuid.uuid4().hex[:6].upper()}",
                location=geo,
                category=AlertCategory.HEATWAVE,
                severity=AlertSeverity.YELLOW,
                headline=f"Heatwave Watch for {geo.name}",
                description=f"Maximum temperature hovering near {weather.temperature_c:.1f}°C.",
                safety_instructions=[
                    "Wear light-colored, loose cotton clothes and cover your head with a cloth or hat.",
                    "Ensure adequate hydration during agricultural activities."
                ],
                valid_from=weather.timestamp,
                valid_to="Next 24 Hours",
                impact_level="Moderate",
                suggested_action="Stay updated with local weather bulletins."
            ))

        # 2. Thunderstorm & Lightning / High CAPE Hazard
        if nwp.cape_surface_j_kg >= 1800 or weather.weather_code in [95, 96, 99]:
            severity = AlertSeverity.ORANGE if nwp.cape_surface_j_kg >= 2200 or weather.weather_code in [96, 99] else AlertSeverity.YELLOW
            alerts.append(ExtremeWeatherAlert(
                alert_id=f"IMD-TS-{uuid.uuid4().hex[:6].upper()}",
                location=geo,
                category=AlertCategory.THUNDERSTORM,
                severity=severity,
                headline=f"Severe Thunderstorm, Squall & Lightning Alert for {geo.name}",
                description=f"Intense convective instability (CAPE: {nwp.cape_surface_j_kg:.0f} J/kg). High likelihood of gusty winds up to {weather.wind_gusts_kmh or 45:.0f} km/h, hail, and cloud-to-ground lightning.",
                safety_instructions=[
                    "DAMINI / Lightning Alert: Take immediate shelter in a pucca building. NEVER stand under isolated tall trees.",
                    "Do not touch metal fences, electric poles, or unplugged wire appliances.",
                    "Suspend all spray and open field operations immediately.",
                    "Farmers should securely moor temporary shed roofs and tether cattle indoors."
                ],
                valid_from=weather.timestamp,
                valid_to="Next 12 Hours",
                impact_level="High",
                suggested_action="Broadcast early warning audio SMS to rural panchayats and local disaster management."
            ))

        # 3. Heavy Rainfall & Flash Flood Hazard (IMD Criteria)
        if nwp.total_precip_24h_mm >= 64.5 or weather.precipitation_mm >= 25.0:
            sev = AlertSeverity.RED if nwp.total_precip_24h_mm >= 115.5 else AlertSeverity.ORANGE
            alerts.append(ExtremeWeatherAlert(
                alert_id=f"IMD-RF-{uuid.uuid4().hex[:6].upper()}",
                location=geo,
                category=AlertCategory.HEAVY_RAINFALL,
                severity=sev,
                headline=f"Heavy to Very Heavy Rainfall Warning for {geo.name}",
                description=f"Expected 24-hour rainfall accumulation of {nwp.total_precip_24h_mm:.1f} mm. Waterlogging in low-lying crop fields and flash flood risks in seasonal rivulets (nullahs).",
                safety_instructions=[
                    "Ensure adequate drainage channels in paddy, cotton, and vegetable fields to prevent root rot.",
                    "Avoid crossing submerged bridges or culverts.",
                    "Store harvested grain in elevated, waterproof storage bins.",
                    "Keep emergency flashlights, drinking water, and essential medicines ready."
                ],
                valid_from=weather.timestamp,
                valid_to="Next 36 Hours",
                impact_level="High" if sev == AlertSeverity.ORANGE else "Critical",
                suggested_action="Activate district flood rescue teams and issue immediate advisory via community radio."
            ))

        # 4. Cyclone / Deep Depression Hazard
        if weather.surface_pressure_hpa < 998.0 and weather.wind_speed_kmh >= 50.0:
            alerts.append(ExtremeWeatherAlert(
                alert_id=f"IMD-CY-{uuid.uuid4().hex[:6].upper()}",
                location=geo,
                category=AlertCategory.CYCLONE,
                severity=AlertSeverity.RED,
                headline=f"Cyclone Early Warning / Storm Surge Alert for {geo.name}",
                description=f"Severe cyclonic disturbance detected. Central pressure dropped to {weather.surface_pressure_hpa:.1f} hPa with sustained gale winds of {weather.wind_speed_kmh:.1f} km/h.",
                safety_instructions=[
                    "Fishermen are strictly advised not to venture into deep sea or coastal waters.",
                    "Evacuate kutcha houses and low-lying coastal villages to designated cyclone shelters.",
                    "Keep dry food rations, battery-operated radios, and first aid kits handy."
                ],
                valid_from=weather.timestamp,
                valid_to="Next 48 Hours",
                impact_level="Severe",
                suggested_action="Trigger State Disaster Response Force (SDRF) / NDRF deployment."
            ))

        # If no severe thresholds met, return a Green status
        if not alerts:
            alerts.append(ExtremeWeatherAlert(
                alert_id=f"IMD-NORM-{uuid.uuid4().hex[:6].upper()}",
                location=geo,
                category=AlertCategory.THUNDERSTORM,
                severity=AlertSeverity.GREEN,
                headline=f"Normal Weather Conditions for {geo.name}",
                description="No extreme weather alerts active. Meteorological parameters are within safe seasonal variations.",
                safety_instructions=["Standard seasonal precautions apply."],
                valid_from=weather.timestamp,
                valid_to="Next 24 Hours",
                impact_level="Low",
                suggested_action="Continue regular agricultural and daily operations."
            ))

        return alerts
