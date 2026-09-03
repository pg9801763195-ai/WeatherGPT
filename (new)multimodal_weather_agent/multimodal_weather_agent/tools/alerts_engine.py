"""
Extreme Weather Alerts and Early Warning Dissemination Engine.
Complies with IMD / NDMA Common Alerting Protocol (CAP) for severe cyclones, heatwaves, flash floods, and thunderstorms.
"""
from typing import List, Optional
from datetime import datetime
from schemas.weather_schemas import GeoLocation, CurrentWeather, DailyForecastItem, NWPForecast, CAPAlert


class AlertsEngine:
    """Evaluates meteorological anomalies and generates standard CAP early warning alerts."""

    def evaluate_severe_weather_risks(
        self,
        geo: GeoLocation,
        current: CurrentWeather,
        forecasts: List[DailyForecastItem],
        nwp: Optional[NWPForecast] = None
    ) -> List[CAPAlert]:
        """Check criteria for Heatwaves, Severe Cyclones, Flash Floods, and Severe Thunderstorms."""
        alerts: List[CAPAlert] = []
        now_str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        next_24h = "2026-09-04T00:00:00Z"

        # 1. Heatwave & Severe Heatwave
        max_temp_today = max([f.temp_max_c for f in forecasts[:2]] + [current.temperature_c])
        if max_temp_today >= 45.0:
            alerts.append(CAPAlert(
                identifier=f"IMD-HEAT-{geo.name.upper()}-001",
                sender="India Meteorological Department (IMD) - National Weather Forecasting Centre",
                event="Severe Heatwave Warning (Red Alert)",
                severity="Extreme",
                urgency="Immediate",
                headline=f"Severe Heatwave Alert for {geo.name} with temperatures exceeding {max_temp_today:.1f}°C",
                description=f"Persistent severe heatwave conditions observed over {geo.name} and surrounding districts. High risk of heat stroke and severe dehydration.",
                instruction="Stay indoors between 11:00 AM and 4:00 PM. Drink plenty of oral rehydration salts (ORS)/water. Shelter livestock in shaded, ventilated enclosures.",
                area_desc=f"{geo.name}, {geo.state or 'India'}",
                effective_time=now_str,
                expires_time=next_24h
            ))
        elif max_temp_today >= 40.0:
            alerts.append(CAPAlert(
                identifier=f"IMD-HEAT-{geo.name.upper()}-002",
                sender="India Meteorological Department (IMD)",
                event="Heatwave Warning (Orange Alert)",
                severity="Severe",
                urgency="Expected",
                headline=f"Heatwave warning for {geo.name} with maximum temperature around {max_temp_today:.1f}°C",
                description=f"Moderate heat stress expected. Vulnerable populations (infants, elderly, outdoor agricultural laborers) face elevated risks.",
                instruction="Avoid direct sun exposure during peak noon hours. Wear light cotton clothing and carry water during field activities.",
                area_desc=f"{geo.name}, {geo.state or 'India'}",
                effective_time=now_str,
                expires_time=next_24h
            ))

        # 2. Flash Flood & Torrential Downpour
        max_rain_today = max([f.precipitation_sum_mm for f in forecasts[:2]] + [current.precipitation_mm])
        if max_rain_today >= 64.5:
            alerts.append(CAPAlert(
                identifier=f"IMD-RAIN-{geo.name.upper()}-001",
                sender="IMD Flood Meteorological Office / NDMA",
                event="Heavy to Very Heavy Rainfall / Flash Flood Warning",
                severity="Severe" if max_rain_today < 115.5 else "Extreme",
                urgency="Immediate",
                headline=f"Heavy Downpour Alert ({max_rain_today:.1f} mm) with localized inundation risk for {geo.name}",
                description=f"Intense precipitation episode likely to cause localized waterlogging, urban inundation, and field drainage overflow in {geo.name}.",
                instruction="Keep agricultural field drainage bunds open. Avoid crossing submerged bridges or culverts. Shift cattle to higher ground.",
                area_desc=f"{geo.name}, {geo.state or 'India'}",
                effective_time=now_str,
                expires_time=next_24h
            ))

        # 3. Severe Thunderstorm & Lightning Hazard (CAPE > 1500 J/kg or WMO Code 95/96/99)
        cape_val = nwp.cape_j_kg if nwp else 0.0
        if current.weather_code in [95, 96, 99] or cape_val >= 2000.0:
            alerts.append(CAPAlert(
                identifier=f"IMD-THUNDER-{geo.name.upper()}-001",
                sender="IMD Regional Meteorological Centre",
                event="Severe Thunderstorm & Lightning Alert (Orange Alert)",
                severity="Severe",
                urgency="Immediate",
                headline=f"Severe Thunderstorm accompanied by Lightning and Gusty Winds over {geo.name}",
                description=f"High convective instability (CAPE: {cape_val:.0f} J/kg). Squall line development and cloud-to-ground lightning strikes probable.",
                instruction="Take shelter in permanent pucca structures. Do NOT stand under isolated trees, metal sheds, or open electrical poles.",
                area_desc=f"{geo.name}, {geo.state or 'India'}",
                effective_time=now_str,
                expires_time=next_24h
            ))

        # 4. Gale / Cyclonic Winds (Wind > 65 km/h)
        if current.wind_speed_kmh >= 65.0 or current.wind_gusts_kmh >= 75.0:
            alerts.append(CAPAlert(
                identifier=f"IMD-CYCLONE-{geo.name.upper()}-001",
                sender="IMD Cyclone Warning Division / NDMA",
                event="Gale Wind / Cyclonic Storm Advisory",
                severity="Extreme",
                urgency="Immediate",
                headline=f"Gale-force winds ({current.wind_speed_kmh:.1f} km/h, Gusts: {current.wind_gusts_kmh:.1f} km/h) over {geo.name}",
                description=f"Extremely strong surface winds causing damage to thatched roofs, standing crops, and tree branches.",
                instruction="Secure loose rooftop items. Fishermen advised not to venture into deep sea/coastal waters. Move to cyclone shelters.",
                area_desc=f"{geo.name}, {geo.state or 'India'}",
                effective_time=now_str,
                expires_time=next_24h
            ))

        return alerts
