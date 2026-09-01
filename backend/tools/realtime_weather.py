"""
Real-time weather retrieval tool integrating OpenWeatherMap (with Air Quality API) and Open-Meteo.
"""
from typing import Dict, Any, Optional, Tuple, List
import requests
from config import AgentConfig
from schemas.weather_schemas import GeoLocation, CurrentWeather, DailyForecastItem


# WMO Weather interpretation codes (WMO Code Table 4677)
WMO_CODE_MAP = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense intensity drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy intensity rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm: Slight or moderate",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail"
}

# OpenWeather AQI index mapping
AQI_CATEGORY_MAP = {
    1: "Good (Clean air)",
    2: "Fair (Acceptable air quality)",
    3: "Moderate (Sensitive individuals affected)",
    4: "Poor (Unhealthy for sensitive groups)",
    5: "Very Poor / Hazardous (Health alert)"
}

# Known coordinates cache for prominent Indian agricultural & urban hubs
INDIAN_CITIES_CACHE = {
    "delhi": (28.6139, 77.2090, "Delhi", "Delhi"),
    "new delhi": (28.6139, 77.2090, "New Delhi", "Delhi"),
    "mumbai": (19.0760, 72.8777, "Mumbai", "Maharashtra"),
    "nagpur": (21.1458, 79.0882, "Nagpur", "Maharashtra"),
    "pune": (18.5204, 73.8567, "Pune", "Maharashtra"),
    "bengaluru": (12.9716, 77.5946, "Bengaluru", "Karnataka"),
    "hyderabad": (17.3850, 78.4867, "Hyderabad", "Telangana"),
    "chennai": (13.0827, 80.2707, "Chennai", "Tamil Nadu"),
    "coimbatore": (11.0168, 76.9558, "Coimbatore", "Tamil Nadu"),
    "kolkata": (22.5726, 88.3639, "Kolkata", "West Bengal"),
    "patna": (25.5941, 85.1376, "Patna", "Bihar"),
    "varanasi": (25.3176, 82.9739, "Varanasi", "Uttar Pradesh"),
    "lucknow": (26.8467, 80.9462, "Lucknow", "Uttar Pradesh"),
    "chandigarh": (30.7333, 76.7794, "Chandigarh", "Punjab"),
    "ludhiana": (30.9010, 75.8573, "Ludhiana", "Punjab"),
    "jaipur": (26.9124, 75.7873, "Jaipur", "Rajasthan"),
    "ahmedabad": (23.0225, 72.5714, "Ahmedabad", "Gujarat"),
    "bhopal": (23.2599, 77.4126, "Bhopal", "Madhya Pradesh"),
    "indore": (22.7196, 75.8577, "Indore", "Madhya Pradesh"),
    "guwahati": (26.1445, 91.7362, "Guwahati", "Assam"),
    "bhubaneswar": (20.2961, 85.8245, "Bhubaneswar", "Odisha")
}


class RealtimeWeatherTool:
    """Retrieves real-time weather, air pollution (AQI), and forecasts using OpenWeatherMap & Open-Meteo."""

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()

    def geocode(self, location_query: str) -> GeoLocation:
        """Resolve location name to coordinates using OpenWeatherMap or Open-Meteo Geocoding."""
        cleaned = location_query.strip().lower()
        if cleaned in INDIAN_CITIES_CACHE:
            lat, lon, city, state = INDIAN_CITIES_CACHE[cleaned]
            return GeoLocation(name=city, latitude=lat, longitude=lon, state=state, country="India")

        # 1. Try OpenWeather Direct Geocoding API if key available
        if self.config.openweather_api_key:
            try:
                params = {"q": f"{location_query},IN", "limit": 1, "appid": self.config.openweather_api_key}
                resp = requests.get(self.config.openweather_geo_url, params=params, timeout=4)
                if resp.status_code == 200 and resp.json():
                    item = resp.json()[0]
                    return GeoLocation(
                        name=item.get("name", location_query),
                        latitude=item["lat"],
                        longitude=item["lon"],
                        state=item.get("state", ""),
                        country=item.get("country", "India")
                    )
            except Exception:
                pass

        # 2. Fallback to Open-Meteo Geocoding
        try:
            params = {"name": location_query, "count": 1, "language": "en", "format": "json"}
            resp = requests.get(self.config.open_meteo_geocoding_url, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if "results" in data and len(data["results"]) > 0:
                    item = data["results"][0]
                    return GeoLocation(
                        name=item.get("name", location_query),
                        latitude=item["latitude"],
                        longitude=item["longitude"],
                        state=item.get("admin1", ""),
                        country=item.get("country", "India")
                    )
        except Exception:
            pass

        return GeoLocation(
            name=self.config.default_location_name,
            latitude=self.config.default_lat,
            longitude=self.config.default_lon,
            country="India"
        )

    def fetch_openweather_air_pollution(self, lat: float, lon: float) -> Tuple[Optional[int], Optional[str], Optional[float], Optional[float]]:
        """Fetch real-time Air Quality Index (AQI), PM2.5, and PM10 from OpenWeather."""
        if not self.config.openweather_api_key:
            return None, None, None, None

        try:
            url = f"{self.config.openweather_base_url}/air_pollution"
            params = {"lat": lat, "lon": lon, "appid": self.config.openweather_api_key}
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if "list" in data and len(data["list"]) > 0:
                    item = data["list"][0]
                    aqi_val = item.get("main", {}).get("aqi", 2)
                    comps = item.get("components", {})
                    pm25 = comps.get("pm2_5", 25.0)
                    pm10 = comps.get("pm10", 45.0)
                    aqi_desc = AQI_CATEGORY_MAP.get(aqi_val, "Moderate")
                    return aqi_val, aqi_desc, pm25, pm10
        except Exception:
            pass
        return None, None, None, None

    def fetch_openweather_current(self, geo: GeoLocation) -> Optional[CurrentWeather]:
        """Fetch live meteorological conditions from OpenWeatherMap API."""
        if not self.config.openweather_api_key:
            return None

        try:
            url = f"{self.config.openweather_base_url}/weather"
            params = {
                "lat": geo.latitude,
                "lon": geo.longitude,
                "appid": self.config.openweather_api_key,
                "units": "metric"
            }
            resp = requests.get(url, params=params, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                main = data.get("main", {})
                wind = data.get("wind", {})
                weather_arr = data.get("weather", [{}])[0]
                
                # Fetch Air Pollution AQI
                aqi, aqi_cat, pm25, pm10 = self.fetch_openweather_air_pollution(geo.latitude, geo.longitude)

                return CurrentWeather(
                    location=geo,
                    timestamp=str(data.get("dt", "")),
                    temperature_c=float(main.get("temp", 28.0)),
                    apparent_temperature_c=float(main.get("feels_like", 30.0)),
                    relative_humidity_pct=float(main.get("humidity", 60.0)),
                    precipitation_mm=float(data.get("rain", {}).get("1h", 0.0)),
                    weather_code=int(weather_arr.get("id", 800)),
                    weather_description=weather_arr.get("description", "Clear sky").title(),
                    wind_speed_kmh=float(wind.get("speed", 3.5)) * 3.6,  # m/s to km/h
                    wind_direction_deg=float(wind.get("deg", 180.0)),
                    wind_gusts_kmh=float(wind.get("gust", 5.0)) * 3.6 if "gust" in wind else 0.0,
                    surface_pressure_hpa=float(main.get("pressure", 1012.0)),
                    uv_index=6.0,
                    cloud_cover_pct=float(data.get("clouds", {}).get("all", 10.0)),
                    aqi=aqi,
                    aqi_category=aqi_cat,
                    pm2_5=pm25,
                    pm10=pm10,
                    provider="OpenWeatherMap API"
                )
        except Exception:
            pass
        return None

    def get_current_weather(self, location_query: str) -> Tuple[CurrentWeather, List[DailyForecastItem]]:
        """Fetch current live weather (OpenWeather with Open-Meteo fallback) and multi-day forecast."""
        geo = self.geocode(location_query)
        
        # 1. Try OpenWeatherMap for live surface observations & AQI
        owm_current = self.fetch_openweather_current(geo)

        # 2. Fetch multi-day forecast and ET0 from Open-Meteo
        params = {
            "latitude": geo.latitude,
            "longitude": geo.longitude,
            "current": [
                "temperature_2m", "relative_humidity_2m", "apparent_temperature",
                "precipitation", "weather_code", "surface_pressure",
                "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m", "cloud_cover"
            ],
            "daily": [
                "temperature_2m_max", "temperature_2m_min", "precipitation_sum",
                "precipitation_probability_max", "weather_code", "wind_speed_10m_max",
                "et0_fao_evapotranspiration", "uv_index_max"
            ],
            "timezone": "auto"
        }

        try:
            response = requests.get(self.config.open_meteo_url, params=params, timeout=8)
            response.raise_for_status()
            data = response.json()
            
            cur_raw = data.get("current", {})
            w_code = cur_raw.get("weather_code", 0)
            w_desc = WMO_CODE_MAP.get(w_code, "Partly Cloudy")

            daily_raw = data.get("daily", {})
            uv_today = daily_raw.get("uv_index_max", [0.0])[0] if "uv_index_max" in daily_raw else 0.0

            # If OpenWeather succeeded, use it as primary, augmenting with UV index from Open-Meteo
            if owm_current:
                current = owm_current
                current.uv_index = float(uv_today)
            else:
                current = CurrentWeather(
                    location=geo,
                    timestamp=cur_raw.get("time", ""),
                    temperature_c=float(cur_raw.get("temperature_2m", 25.0)),
                    apparent_temperature_c=float(cur_raw.get("apparent_temperature", 26.0)),
                    relative_humidity_pct=float(cur_raw.get("relative_humidity_2m", 50.0)),
                    precipitation_mm=float(cur_raw.get("precipitation", 0.0)),
                    weather_code=w_code,
                    weather_description=w_desc,
                    wind_speed_kmh=float(cur_raw.get("wind_speed_10m", 10.0)),
                    wind_direction_deg=float(cur_raw.get("wind_direction_10m", 180.0)),
                    wind_gusts_kmh=float(cur_raw.get("wind_gusts_10m", 15.0)),
                    surface_pressure_hpa=float(cur_raw.get("surface_pressure", 1010.0)),
                    uv_index=float(uv_today),
                    cloud_cover_pct=float(cur_raw.get("cloud_cover", 20.0)),
                    provider="Open-Meteo Global API"
                )

            forecasts: List[DailyForecastItem] = []
            if "time" in daily_raw:
                dates = daily_raw["time"]
                for i in range(min(len(dates), 7)):
                    fc_code = daily_raw["weather_code"][i] if "weather_code" in daily_raw else 0
                    et0_val = daily_raw["et0_fao_evapotranspiration"][i] if "et0_fao_evapotranspiration" in daily_raw else 4.0
                    item = DailyForecastItem(
                        date=dates[i],
                        temp_max_c=float(daily_raw["temperature_2m_max"][i]),
                        temp_min_c=float(daily_raw["temperature_2m_min"][i]),
                        precipitation_sum_mm=float(daily_raw["precipitation_sum"][i]),
                        precipitation_probability_pct=int(daily_raw["precipitation_probability_max"][i] or 0),
                        weather_code=fc_code,
                        weather_description=WMO_CODE_MAP.get(fc_code, "Fair"),
                        max_wind_speed_kmh=float(daily_raw["wind_speed_10m_max"][i]),
                        et0_evapotranspiration_mm=float(et0_val)
                    )
                    forecasts.append(item)

            return current, forecasts

        except Exception as e:
            if owm_current:
                return owm_current, []
            
            # Fallback mock weather for offline resilience
            current = CurrentWeather(
                location=geo,
                timestamp="2026-08-31T12:00",
                temperature_c=31.5,
                apparent_temperature_c=35.2,
                relative_humidity_pct=72.0,
                precipitation_mm=0.5,
                weather_code=2,
                weather_description="Partly cloudy with warm breeze",
                wind_speed_kmh=14.5,
                wind_direction_deg=220.0,
                wind_gusts_kmh=22.0,
                surface_pressure_hpa=1008.2,
                uv_index=7.5,
                cloud_cover_pct=45.0,
                provider="Offline Fallback"
            )
            return current, []
