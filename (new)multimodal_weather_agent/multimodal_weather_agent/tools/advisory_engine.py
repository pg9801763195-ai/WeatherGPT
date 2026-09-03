"""
Location-based Agricultural and Agro-Meteorological Advisory Engine.
Evaluates pesticide/herbicide spray windows, ET0 reference irrigation, and crop pest triggers.
"""
from typing import List, Optional
from schemas.weather_schemas import CurrentWeather, DailyForecastItem, AgroAdvisory


class AdvisoryEngine:
    """Computes field-level agro-meteorological advisories."""

    def generate_crop_advisory(
        self,
        current: CurrentWeather,
        forecasts: List[DailyForecastItem],
        crop_name: str = "Cotton",
        growth_stage: str = "Flowering / Vegetative"
    ) -> AgroAdvisory:
        """Evaluate chemical spray viability, water balance, and fungal/pest triggers."""
        # 1. Chemical Spray Window Assessment
        rain_prob_today = forecasts[0].precipitation_probability_pct if forecasts else 0
        rain_sum_today = forecasts[0].precipitation_sum_mm if forecasts else 0.0
        wind_speed = current.wind_speed_kmh
        temp = current.temperature_c

        reasons = []
        is_safe = True

        if rain_prob_today > 40 or rain_sum_today > 1.0 or current.precipitation_mm > 0.0:
            is_safe = False
            reasons.append(f"rain probability ({rain_prob_today}%, expected {rain_sum_today:.1f}mm rain wash-off)")

        if wind_speed > 15.0:
            is_safe = False
            reasons.append(f"excessive wind drift ({wind_speed:.1f} km/h)")
        elif wind_speed < 3.0:
            reasons.append("very low wind speed (minor thermal inversion risk)")

        if temp > 35.0:
            is_safe = False
            reasons.append(f"high surface temperature ({temp:.1f}°C, chemical volatilization risk)")

        if is_safe:
            spray_msg = f"OPTIMAL SPRAY WINDOW: Safe to spray pesticides/fungicides today. Wind speed ({wind_speed:.1f} km/h) and low rain risk ({rain_prob_today}%) will ensure effective droplet deposition."
        else:
            spray_msg = f"UNSAFE TO SPRAY TODAY due to {', '.join(reasons)}. Postpone pesticide/herbicide application to avoid chemical loss."

        # 2. Irrigation Scheduling based on ET0 & Soil Moisture
        et0_val = forecasts[0].et0_evapotranspiration_mm if forecasts and forecasts[0].et0_evapotranspiration_mm else 4.5
        if rain_sum_today >= 5.0 or rain_prob_today >= 60:
            irrigation_msg = f"WITHHOLD IRRIGATION: Forecast indicates significant rainfall ({rain_sum_today:.1f} mm, {rain_prob_today}% chance). Ensure proper field drainage bunds are open to prevent water stagnation."
        elif et0_val > 5.0:
            irrigation_msg = f"LIGHT IRRIGATION RECOMMENDED: High crop evapotranspiration (ET0: {et0_val:.1f} mm/day). Provide light furrow or drip irrigation during evening hours."
        else:
            irrigation_msg = f"NORMAL IRRIGATION CYCLE: Evapotranspiration is moderate (ET0: {et0_val:.1f} mm/day). Maintain adequate moisture at root zone."

        # 3. Pest & Disease Microclimate Triggers
        pest_warnings = []
        humidity = current.relative_humidity_pct
        crop_lower = crop_name.lower()

        if "cotton" in crop_lower:
            if humidity > 75 and 25 <= temp <= 32:
                pest_warnings.append("High humidity and warm conditions favor Pink Bollworm and Sucking Pests (Whitefly/Thrips). Install yellow sticky traps (5/acre).")
            elif humidity > 85:
                pest_warnings.append("High moisture promotes Bacterial Leaf Blight and Root Rot in Cotton.")
        elif "paddy" in crop_lower or "rice" in crop_lower:
            if humidity > 80 and temp < 30:
                pest_warnings.append("Persistent cloudiness and high humidity promote Blast disease and Brown Planthopper (BPH) development. Inspect plant base regularly.")
        elif "wheat" in crop_lower:
            if temp > 28:
                pest_warnings.append("Early heat stress may shorten grain filling duration. Apply light irrigation.")
        elif "soybean" in crop_lower:
            if rain_sum_today > 10.0 and humidity > 80:
                pest_warnings.append("Risk of Anthracnose / Yellow Mosaic Virus. Avoid inter-cultivation when foliage is wet.")

        pest_risk_str = " | ".join(pest_warnings) if pest_warnings else f"General monitoring advised for {crop_name} at {growth_stage} stage. Relative humidity is {humidity:.0f}% and temperature is {temp:.1f}°C."

        # 4. Rural Operations Guidance
        operations = [
            f"Soil Temperature & Evaporation: Daily ET0 is approx {et0_val:.1f} mm.",
            "Livestock Management: Ensure clean drinking water, adequate ventilation in sheds, and add electrolyte/mineral mixture during warm days.",
            "Fertilizer Top-Dressing: " + ("Postpone fertilizer application until heavy rain subsides." if rain_sum_today > 5.0 else "Apply urea/NPK top-dressing in moist soil conditions.")
        ]

        return AgroAdvisory(
            crop_name=crop_name,
            growth_stage=growth_stage,
            spray_window_safe=is_safe,
            spray_recommendation=spray_msg,
            irrigation_advice=irrigation_msg,
            pest_disease_risk=pest_risk_str,
            rural_operations_guidance=operations
        )
