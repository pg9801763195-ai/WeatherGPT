"""
Location Resolution & Geocoding Engine.
Dynamically resolves arbitrary cities, towns, tourist destinations, districts, states, and villages
using OpenWeather Direct Geocoding API and Open-Meteo Global Search with in-memory caching.
Eliminates reliance on hardcoded city dictionaries.
"""
import re
import requests
from typing import Optional, Tuple, Dict
from schemas.weather_schemas import GeoLocation
from config import AgentConfig


class LocationResolver:
    """High-performance geocoding and location disambiguation resolver."""

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        self._geo_cache: Dict[str, GeoLocation] = {}

    def resolve(self, location_query: str) -> Optional[GeoLocation]:
        """
        Resolves location name to canonical GeoLocation with coordinates, district, state, and country.
        Returns None if location is genuinely unrecognized.
        """
        if not location_query or not location_query.strip():
            return None

        clean_name = location_query.strip()
        cache_key = clean_name.lower()

        # Check cache
        if cache_key in self._geo_cache:
            return self._geo_cache[cache_key]

        # 1. Try OpenWeather Direct Geocoding (Priority for Indian cities, towns & tourist spots)
        if self.config.openweather_api_key:
            try:
                # Try with country code IN first
                params = {"q": f"{clean_name},IN", "limit": 1, "appid": self.config.openweather_api_key}
                resp = requests.get(self.config.openweather_geo_url, params=params, timeout=3.5)
                if resp.status_code == 200 and resp.json():
                    item = resp.json()[0]
                    geo = GeoLocation(
                        name=item.get("name", clean_name),
                        latitude=float(item["lat"]),
                        longitude=float(item["lon"]),
                        state=item.get("state", ""),
                        country=item.get("country", "India")
                    )
                    self._geo_cache[cache_key] = geo
                    return geo
                
                # Try global search if IN yielded nothing
                params_global = {"q": clean_name, "limit": 1, "appid": self.config.openweather_api_key}
                resp_g = requests.get(self.config.openweather_geo_url, params=params_global, timeout=3.5)
                if resp_g.status_code == 200 and resp_g.json():
                    item = resp_g.json()[0]
                    geo = GeoLocation(
                        name=item.get("name", clean_name),
                        latitude=float(item["lat"]),
                        longitude=float(item["lon"]),
                        state=item.get("state", ""),
                        country=item.get("country", "")
                    )
                    self._geo_cache[cache_key] = geo
                    return geo
            except Exception:
                pass

        # 2. Fallback to Open-Meteo Global Geocoding API
        try:
            params = {"name": clean_name, "count": 1, "language": "en", "format": "json"}
            resp = requests.get(self.config.open_meteo_geocoding_url, params=params, timeout=3.5)
            if resp.status_code == 200:
                data = resp.json()
                if "results" in data and len(data["results"]) > 0:
                    item = data["results"][0]
                    geo = GeoLocation(
                        name=item.get("name", clean_name),
                        latitude=float(item["latitude"]),
                        longitude=float(item["longitude"]),
                        state=item.get("admin1", ""),
                        country=item.get("country", "India")
                    )
                    self._geo_cache[cache_key] = geo
                    return geo
        except Exception:
            pass

        return None

    def is_valid_location(self, candidate_name: str) -> bool:
        """Fast check to verify if a candidate token/phrase is a real geographic place."""
        if not candidate_name or len(candidate_name.strip()) < 2:
            return False
        return self.resolve(candidate_name) is not None
