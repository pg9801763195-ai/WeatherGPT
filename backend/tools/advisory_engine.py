"""
Location-based Agro-Meteorological Advisory Engine.
Generates crop-specific spray windows, irrigation schedules, disease risk warnings, and rural livestock guidance.
"""
from typing import Optional, List, Dict, Any
from config import AgentConfig
from schemas.weather_schemas import GeoLocation, CurrentWeather, DailyForecastItem, AgroAdvisory
from tools.realtime_weather import RealtimeWeatherTool


CROP_DISEASE_RULES: Dict[str, Dict[str, Any]] = {
    "cotton": {
        "pests": ["Pink Bollworm", "Whitefly", "Jassids"],
        "trigger": lambda temp, rh, rain: rh > 70 and temp > 28,
        "warning": "High relative humidity and warm temperatures favor Whitefly and sucking pest multiplication in Cotton.",
        "remedy": "Install yellow sticky traps (10/acre) and spray Neem oil (5ml/L) or Flonicamid 50 WG if nymph count exceeds ETL."
    },
    "paddy": {
        "pests": ["Blast disease (Pyricularia oryzae)", "Brown Plant Hopper (BPH)", "Sheath Blight"],
        "trigger": lambda temp, rh, rain: rh > 80 and 20 <= temp <= 30,
        "warning": "Cloudy sky with high humidity (>80%) creates favorable microclimate for Paddy Blast and Sheath Blight.",
        "remedy": "Avoid excess nitrogen fertilizer application. Apply Tricyclazole 75 WP @ 0.6g/L or Hexaconazole 5 EC @ 2ml/L if symptoms appear."
    },
    "rice": {
        "pests": ["Blast disease", "BPH", "Stem Borer"],
        "trigger": lambda temp, rh, rain: rh > 80 and 20 <= temp <= 30,
        "warning": "High atmospheric moisture creates favorable conditions for fungal blast and stem borer activity.",
        "remedy": "Monitor water stagnation in field bunds; apply chlorantraniliprole granules if stem borer dead hearts exceed 5%."
    },
    "wheat": {
        "pests": ["Yellow Rust (Puccinia striiformis)", "Aphids", "Karnal Bunt"],
        "trigger": lambda temp, rh, rain: rh > 75 and 10 <= temp <= 22,
        "warning": "Cool temperatures with high relative humidity and dew favor Yellow Rust stripe infection in Wheat.",
        "remedy": "Inspect leaf underside for yellow powdery pustules; spray Propiconazole 25 EC (Tilt) @ 1ml/L immediately upon spot detection."
    },
    "soybean": {
        "pests": ["Semilooper", "Girdle Beetle", "Yellow Mosaic Virus"],
        "trigger": lambda temp, rh, rain: rh > 75 and rain > 10,
        "warning": "Intermittent rainfall and wet canopy promote Girdle Beetle and defoliating caterpillars.",
        "remedy": "Ensure proper drainage; spray Chlorantraniliprole 18.5 SC @ 0.3ml/L if defoliation exceeds threshold."
    },
    "mustard": {
        "pests": ["Mustard Aphid (Lipaphis erysimi)", "White Rust"],
        "trigger": lambda temp, rh, rain: rh > 70 and temp < 24,
        "warning": "Cloudy, overcast weather with humid conditions accelerates rapid mustard aphid colony infestation.",
        "remedy": "Spray Dimethoate 30 EC @ 1.5 ml/L or Imidacloprid 17.8 SL @ 0.3 ml/L on cloudy morning hours."
    },
    "tomato": {
        "pests": ["Early Blight", "Late Blight", "Fruit Borer"],
        "trigger": lambda temp, rh, rain: rh > 80 and rain > 5,
        "warning": "High air moisture and rain splashes predispose tomato plants to Early and Late Blight fungal attack.",
        "remedy": "Stake plants upright and spray Mancozeb 75 WP @ 2.5g/L or Metalaxyl-Mancozeb @ 2g/L."
    },
    "chilli": {
        "pests": ["Chilli Thrips", "Mites", "Anthracnose / Dieback"],
        "trigger": lambda temp, rh, rain: rh > 70 and temp > 30,
        "warning": "Warm dry spells followed by humid bursts trigger Chilli Leaf Curl (Thrips/Mite complex).",
        "remedy": "Spray Spinosad 45 SC @ 0.3 ml/L or Diafenthiuron 50 WP @ 1g/L on foliage."
    }
}


class AgroAdvisoryTool:
    """Generates localized agricultural advisories, spray windows, and irrigation schedules."""

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        self.weather_tool = RealtimeWeatherTool(self.config)

    def generate_advisory(
        self,
        location_query: str,
        target_crop: str = "Paddy",
        crop_stage: str = "Vegetative"
    ) -> AgroAdvisory:
        """Evaluate weather parameters and compute agricultural recommendations."""
        weather, forecasts = self.weather_tool.get_current_weather(location_query)
        geo = weather.location
        
        # 1. Evaluate Spray Window
        # Safe spray requires: Wind < 15 km/h, Rain probability < 35%, Temp < 35°C
        rain_next_24h = forecasts[0].precipitation_sum_mm if forecasts else weather.precipitation_mm
        rain_prob = forecasts[0].precipitation_probability_pct if forecasts else 20
        wind_speed = weather.wind_speed_kmh
        temp = weather.temperature_c

        spray_safe = (wind_speed <= 16.0) and (rain_prob <= 35) and (rain_next_24h < 5.0) and (temp <= 36.0)
        
        if spray_safe:
            spray_recommendation = (
                f"SAFE SPRAY WINDOW ACTIVE: Wind speed is gentle ({wind_speed:.1f} km/h), rain risk is low ({rain_prob}%), "
                f"and temperature is {temp:.1f}°C. Best spraying hours are 7:00 AM - 10:30 AM or 4:00 PM - 6:00 PM."
            )
        else:
            reasons = []
            if wind_speed > 16.0:
                reasons.append(f"high wind drift ({wind_speed:.1f} km/h)")
            if rain_prob > 35 or rain_next_24h >= 5.0:
                reasons.append(f"rain probability ({rain_prob}%, expected {rain_next_24h:.1f}mm rain wash-off)")
            if temp > 36.0:
                reasons.append(f"excess heat ({temp:.1f}°C causing rapid droplet evaporation)")
            spray_recommendation = f"UNSAFE TO SPRAY TODAY due to {', '.join(reasons)}. Postpone pesticide/herbicide application to avoid chemical loss."

        # 2. Irrigation Scheduling (ET0 vs Expected Rain)
        et0 = forecasts[0].et0_evapotranspiration_mm if forecasts and forecasts[0].et0_evapotranspiration_mm else 4.5
        if rain_next_24h >= 15.0 or rain_prob >= 70:
            irrigation_advice = (
                f"WITHHOLD IRRIGATION: Forecast indicates significant rainfall ({rain_next_24h:.1f} mm, {rain_prob}% chance). "
                f"Ensure proper field drainage bunds are open to prevent water stagnation."
            )
        elif rain_next_24h >= 5.0:
            irrigation_advice = (
                f"LIGHT / DELAYED IRRIGATION: Moderate showers ({rain_next_24h:.1f} mm) expected. Apply light irrigation only if topsoil is completely dry."
            )
        else:
            irrigation_advice = (
                f"APPLY REGULAR IRRIGATION: Evapotranspiration demand is {et0:.1f} mm/day with negligible rain expected. "
                f"Irrigate during evening hours to maintain optimal root-zone moisture."
            )

        # 3. Pest & Disease Diagnostics
        crop_key = target_crop.strip().lower()
        pest_warning = None
        remedy_text = None
        if crop_key in CROP_DISEASE_RULES:
            rule = CROP_DISEASE_RULES[crop_key]
            if rule["trigger"](weather.temperature_c, weather.relative_humidity_pct, weather.precipitation_mm):
                pest_warning = f"{rule['warning']} Suggested action: {rule['remedy']}"
        
        if not pest_warning:
            pest_warning = f"General monitoring advised for {target_crop} at {crop_stage} stage. Relative humidity is {weather.relative_humidity_pct:.0f}% and temperature is {weather.temperature_c:.1f}°C."

        # 4. General Rural Guidance
        guidance = [
            f"Soil Temperature & Evaporation: Daily ET0 is approx {et0:.1f} mm.",
            "Livestock Management: Ensure clean drinking water, adequate ventilation in sheds, and add electrolyte/mineral mixture during warm days.",
            f"Fertilizer Top-Dressing: {'Ideal time for top-dressing' if (rain_prob < 50 and rain_next_24h < 10) else 'Postpone fertilizer application until heavy rain subsides.'}"
        ]

        return AgroAdvisory(
            location=geo,
            target_crop=target_crop,
            crop_stage=crop_stage,
            irrigation_advice=irrigation_advice,
            spray_window_safe=spray_safe,
            spray_recommendation=spray_recommendation,
            disease_pest_warning=pest_warning,
            general_guidance=guidance
        )
