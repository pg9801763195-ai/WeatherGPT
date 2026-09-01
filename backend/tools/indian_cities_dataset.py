"""
Indian Cities Historical Weather Dataset Engine (Kaggle dataset integration).
Processes multi-decade meteorological observations, annual trends, and extreme event frequencies for Indian cities.
"""
import os
import json
from typing import Dict, Any, List, Optional
from schemas.weather_schemas import GeoLocation, HistoricalClimateTrend


class IndianCitiesHistoricalDataset:
    """Interface to the historical weather dataset for Indian cities (1990-2023+)."""

    def __init__(self, data_path: Optional[str] = None):
        if not data_path:
            data_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "data",
                "historical_indian_cities",
                "indian_cities_weather_archive.json"
            )
        self.data_path = data_path
        self.cities_data: Dict[str, Dict[str, Any]] = {}
        self._load_dataset()

    def _load_dataset(self):
        """Load JSON archive of Indian cities historical weather."""
        if not os.path.exists(self.data_path):
            return

        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                records = json.load(f)
                for record in records:
                    city_key = record["city"].strip().lower()
                    self.cities_data[city_key] = record
        except Exception as e:
            print(f"[IndianCitiesDataset] Warning loading dataset: {e}")

    def query_city_history(self, city_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve raw multi-year historical series for a given Indian city."""
        key = city_name.strip().lower()
        return self.cities_data.get(key)

    def analyze_city_trends(self, city_name: str) -> Optional[HistoricalClimateTrend]:
        """Compute structured historical climate trend from the dataset records."""
        data = self.query_city_history(city_name)
        if not data:
            return None

        metrics = data.get("annual_metrics", [])
        if not metrics:
            return None

        normals = data.get("climatological_normals", {})
        lpa_monsoon = normals.get("lpa_monsoon_rainfall_mm", 800.0)
        
        first_rec = metrics[0]
        last_rec = metrics[-1]
        
        start_year = first_rec["year"]
        end_year = last_rec["year"]
        temp_diff = last_rec["mean_temp_c"] - first_rec["mean_temp_c"]
        
        # Calculate recent monsoon rainfall anomaly
        recent_monsoon = last_rec.get("monsoon_rainfall_mm", lpa_monsoon)
        monsoon_anomaly_pct = ((recent_monsoon - lpa_monsoon) / lpa_monsoon) * 100.0
        
        # Calculate heatwave day frequency shift
        hw_start = first_rec.get("heatwave_days", 10)
        hw_end = last_rec.get("heatwave_days", 20)
        decades = max((end_year - start_year) / 10.0, 1.0)
        hw_shift_per_decade = (hw_end - hw_start) / decades

        summary = (
            f"Kaggle Indian Cities Historical Weather Dataset Analysis for {data['city']}, {data['state']} ({start_year}-{end_year}): "
            f"Observed mean temperature increase of +{temp_diff:.2f}°C (+{normals.get('warming_trend_c_per_decade', 0.35):.2f}°C/decade). "
            f"Monsoon rainfall in recent years shows a {monsoon_anomaly_pct:+.1f}% anomaly compared to the Climatological Normal ({lpa_monsoon} mm). "
            f"Annual heatwave days have escalated from {hw_start} days ({start_year}) to {hw_end} days ({end_year})."
        )

        return HistoricalClimateTrend(
            location=GeoLocation(
                name=data["city"],
                state=data["state"],
                latitude=data["latitude"],
                longitude=data["longitude"],
                country="India"
            ),
            start_year=start_year,
            end_year=end_year,
            mean_temp_change_c=temp_diff,
            monsoon_rainfall_anomaly_pct=monsoon_anomaly_pct,
            heatwave_days_per_decade=hw_shift_per_decade,
            historical_summary=summary
        )
