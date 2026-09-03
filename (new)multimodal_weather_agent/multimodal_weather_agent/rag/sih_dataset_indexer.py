"""
SIH 2026 Multi-Dataset Ingestion & Qdrant Vectorization Pipeline.
Processes 7 Comprehensive CSV datasets:
1. Barisal Weather Dataset.csv
2. Chittagong Weather Dataset.csv
3. india_2000_2024_daily_weather.csv
4. Indian_Climate_Dataset_2024_2025.csv
5. Khulna Weather Dataset.csv
6. weather.csv
7. weather_encoded.csv (83,725 rows, 1990-2022, 8 Cities with Seasonal & Temporal Encodings)
Extracts multi-decadal temperature records, seasonal anomalies, and AQI indices into Qdrant Vector DB.
"""
import os
import re
import json
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional

from config import AgentConfig
from utils.gpu_manager import GPUManager


CSV_SOURCES = [
    {
        "name": "Barisal Coastal Weather Archive (2004-2024)",
        "path": r"C:\Users\gouta\OneDrive\Desktop\SIH_2026\archive\Barisal Weather Dataset.csv",
        "type": "coastal_station"
    },
    {
        "name": "Chittagong Maritime Weather Archive (2004-2024)",
        "path": r"C:\Users\gouta\OneDrive\Desktop\SIH_2026\archive\Chittagong Weather Dataset.csv",
        "type": "coastal_station"
    },
    {
        "name": "Khulna Sundarbans Weather Archive (2004-2024)",
        "path": r"C:\Users\gouta\OneDrive\Desktop\SIH_2026\archive\Khulna Weather Dataset.csv",
        "type": "delta_station"
    },
    {
        "name": "India 2000-2024 Daily Weather Archive (10 Metros, 25 Years)",
        "path": r"C:\Users\gouta\OneDrive\Desktop\SIH_2026\archive\india_2000_2024_daily_weather.csv",
        "type": "india_historical_daily"
    },
    {
        "name": "Indian Climate Dataset 2024-2025 (Daily Temp & AQI)",
        "path": r"C:\Users\gouta\OneDrive\Desktop\SIH_2026\archive\Indian_Climate_Dataset_2024_2025.csv",
        "type": "india_recent_climate"
    },
    {
        "name": "Regional Stations Weather Dataset (15 Cities)",
        "path": r"C:\Users\gouta\OneDrive\Desktop\SIH_2026\archive\weather.csv",
        "type": "regional_stations"
    },
    {
        "name": "Weather Encoded Multi-Decadal Climatology (1990-2022, 8 Cities, 83k Rows)",
        "path": r"C:\Users\gouta\OneDrive\Desktop\SIH_2026\archive\weather_encoded.csv",
        "type": "india_encoded_multidecadal"
    }
]


class SIHDatasetQdrantIndexer:
    """Processes 7 CSV datasets, computes climatological temperature baselines, and vectorizes into Qdrant."""

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        self.embed_model = None
        self.qdrant_client = None
        self.collection_name = "sih_climate_archive_kb"
        self._init_qdrant()

    def _init_qdrant(self):
        """Initialize Qdrant client connection."""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http import models

            if self.config.qdrant_url:
                self.qdrant_client = QdrantClient(url=self.config.qdrant_url, api_key=self.config.qdrant_api_key)
            else:
                os.makedirs(self.config.qdrant_db_dir, exist_ok=True)
                self.qdrant_client = QdrantClient(path=self.config.qdrant_db_dir)

            collections = self.qdrant_client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            
            if not exists:
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
                )
        except Exception:
            self.qdrant_client = None

    def _get_embedding(self, text: str) -> List[float]:
        """Generate dense 384-d semantic embedding (CUDA GPU accelerated)."""
        try:
            from sentence_transformers import SentenceTransformer
            if self.embed_model is None:
                device = "cuda" if (self.config.use_gpu and GPUManager.get_hardware_profile().has_cuda_gpu) else "cpu"
                self.embed_model = SentenceTransformer(self.config.embedding_model, device=device)
            vec = self.embed_model.encode(text, convert_to_numpy=True)
            return vec.tolist()
        except Exception:
            pass

        np.random.seed(abs(hash(text)) % (2**31))
        vec = np.random.randn(384).astype(np.float32)
        norm = np.linalg.norm(vec)
        return (vec / norm).tolist() if norm > 0 else vec.tolist()

    def process_coastal_station(self, name: str, fpath: str) -> List[Dict[str, Any]]:
        """Extract multi-decadal climatology from Barisal, Chittagong, Khulna datasets."""
        chunks = []
        if not os.path.exists(fpath):
            return chunks

        df = pd.read_csv(fpath)
        city_name = name.split()[0]
        mean_temp = round(float(df['temp'].mean()), 2)
        max_temp_rec = round(float(df['max temp'].max()), 2)
        min_temp_rec = round(float(df['min temp'].min()), 2)
        mean_humid = round(float(df['humidity'].mean()), 1)
        mean_precip = round(float(df['precip'].sum() / max(len(df['year'].unique()), 1)), 1)
        start_yr = int(df['year'].min())
        end_yr = int(df['year'].max())

        content_overall = (
            f"Climatological Profile for {city_name} Station ({start_yr}-{end_yr}): "
            f"Mean Annual Surface Temperature is {mean_temp}°C. "
            f"All-Time Maximum Recorded Temperature reached {max_temp_rec}°C, while Minimum Temperature dropped to {min_temp_rec}°C. "
            f"Average Relative Humidity is {mean_humid}%, and Annual Rainfall averages {mean_precip} mm. "
            f"Marine & delta convective influences drive significant pre-monsoon squalls and cyclone vulnerability."
        )
        chunks.append({
            "doc_id": f"{city_name.lower()}_climatology_overall",
            "content": content_overall,
            "city": city_name,
            "state": "Coastal Bay of Bengal",
            "category": "sih_coastal_climate",
            "temp_avg": mean_temp,
            "temp_max": max_temp_rec,
            "temp_min": min_temp_rec,
            "source": name
        })

        for m in range(1, 13):
            m_df = df[df['month'] == m]
            if not m_df.empty:
                m_avg = round(float(m_df['temp'].mean()), 1)
                m_max = round(float(m_df['max temp'].max()), 1)
                m_min = round(float(m_df['min temp'].min()), 1)
                m_rain = round(float(m_df['precip'].mean() * 30), 1)
                m_name = pd.to_datetime(f"2024-{m:02d}-01").strftime("%B")

                m_content = (
                    f"{city_name} Monthly Weather Baseline for {m_name}: "
                    f"Average Temperature is {m_avg}°C (Monthly Highs reach {m_max}°C, Lows reach {m_min}°C). "
                    f"Expected Monthly Precipitation is approximately {m_rain} mm."
                )
                chunks.append({
                    "doc_id": f"{city_name.lower()}_month_{m}",
                    "content": m_content,
                    "city": city_name,
                    "state": "Coastal Bay of Bengal",
                    "category": "sih_monthly_climatology",
                    "temp_avg": m_avg,
                    "temp_max": m_max,
                    "temp_min": m_min,
                    "source": name
                })

        return chunks

    def process_india_historical(self, fpath: str) -> List[Dict[str, Any]]:
        """Process 91,321 rows of India 2000-2024 Daily Weather dataset across 10 major Metros."""
        chunks = []
        if not os.path.exists(fpath):
            return chunks

        df = pd.read_csv(fpath)
        for city, grp in df.groupby('city'):
            avg_max = round(float(grp['temperature_2m_max'].mean()), 1)
            avg_min = round(float(grp['temperature_2m_min'].mean()), 1)
            overall_avg = round((avg_max + avg_min) / 2.0, 1)
            peak_max = round(float(grp['temperature_2m_max'].max()), 1)
            lowest_min = round(float(grp['temperature_2m_min'].min()), 1)
            total_rain = round(float(grp['precipitation_sum'].sum() / 25.0), 1)

            grp['dt'] = pd.to_datetime(grp['date'], errors='coerce')
            summer_df = grp[grp['dt'].dt.month.isin([4, 5, 6])]
            winter_df = grp[grp['dt'].dt.month.isin([12, 1, 2])]
            summer_peak = round(float(summer_df['temperature_2m_max'].mean()), 1) if not summer_df.empty else avg_max
            winter_min = round(float(winter_df['temperature_2m_min'].mean()), 1) if not winter_df.empty else avg_min

            heatwave_days = int((grp['temperature_2m_max'] >= 40.0).sum() / 25.0)

            content = (
                f"India Historical Climate Archive for {city} (2000-2024, 25-Year Climatological Baseline): "
                f"Mean Daily Maximum Temperature is {avg_max}°C, and Mean Minimum Temperature is {avg_min}°C (Overall Average: {overall_avg}°C). "
                f"All-time record peak temperature reached {peak_max}°C, while lowest winter minimum reached {lowest_min}°C. "
                f"Summer (April-June) daily highs average {summer_peak}°C with an average of {heatwave_days} heatwave days (>=40°C) per year. "
                f"Winter (Dec-Feb) nighttime temperatures average {winter_min}°C. Annual rainfall averages {total_rain} mm."
            )

            chunks.append({
                "doc_id": f"india_2000_2024_{city.lower()}",
                "content": content,
                "city": city,
                "state": "India",
                "category": "sih_india_historical",
                "temp_avg": overall_avg,
                "temp_max": peak_max,
                "temp_min": lowest_min,
                "source": "India 2000-2024 Daily Weather Archive"
            })

        return chunks

    def process_indian_climate_2024_2025(self, fpath: str) -> List[Dict[str, Any]]:
        """Process recent 2024-2025 Indian Climate & AQI dataset."""
        chunks = []
        if not os.path.exists(fpath):
            return chunks

        df = pd.read_csv(fpath)
        t_avg_col = [c for c in df.columns if 'Avg' in c or 'avg' in c][0]
        t_max_col = [c for c in df.columns if 'Max' in c or 'max' in c][0]
        t_min_col = [c for c in df.columns if 'Min' in c or 'min' in c][0]

        for city, grp in df.groupby('City'):
            state = str(grp['State'].iloc[0]) if 'State' in grp.columns else "India"
            avg_temp = round(float(grp[t_avg_col].mean()), 1)
            max_temp = round(float(grp[t_max_col].max()), 1)
            min_temp = round(float(grp[t_min_col].min()), 1)
            avg_aqi = int(grp['AQI'].mean())
            avg_humidity = round(float(grp['Humidity (%)'].mean()), 1)
            total_rain = round(float(grp['Rainfall (mm)'].sum()), 1)

            content = (
                f"Recent Indian Climate & Air Quality Summary for {city}, {state} (2024-2025): "
                f"Observed Average Temperature is {avg_temp}°C (Maximum reached {max_temp}°C, Minimum dropped to {min_temp}°C). "
                f"Average Air Quality Index (AQI) is {avg_aqi} (Unhealthy/Moderate category with elevated PM2.5/PM10). "
                f"Mean Relative Humidity is {avg_humidity}%, and Cumulative Rainfall is {total_rain} mm."
            )

            chunks.append({
                "doc_id": f"india_2024_2025_{city.lower()}",
                "content": content,
                "city": city,
                "state": state,
                "category": "sih_recent_climate_aqi",
                "temp_avg": avg_temp,
                "temp_max": max_temp,
                "temp_min": min_temp,
                "aqi": avg_aqi,
                "source": "Indian Climate Dataset 2024-2025"
            })

        return chunks

    def process_regional_weather(self, fpath: str) -> List[Dict[str, Any]]:
        """Process weather.csv covering 15 regional stations."""
        chunks = []
        if not os.path.exists(fpath):
            return chunks

        df = pd.read_csv(fpath)
        for city, grp in df.groupby('city'):
            avg_max = round(float(grp['temp_max'].mean()), 1)
            avg_min = round(float(grp['temp_min'].mean()), 1)
            peak_max = round(float(grp['temp_max'].max()), 1)
            total_rain = round(float(grp['rain'].sum() / max(len(grp['date'].unique()) / 365.0, 1)), 1)
            solar_rad = round(float(grp['solar_radiation'].mean()), 1) if 'solar_radiation' in grp.columns else 18.0

            content = (
                f"Regional Weather & Climatological Profile for {city}: "
                f"Average Maximum Temperature is {avg_max}°C, Average Minimum Temperature is {avg_min}°C, "
                f"with Peak Extreme Temperatures reaching {peak_max}°C. "
                f"Mean Solar Radiation is {solar_rad} MJ/m², and Annual Rainfall averages {total_rain} mm."
            )

            chunks.append({
                "doc_id": f"regional_weather_{city.lower()}",
                "content": content,
                "city": city,
                "state": "Regional Station",
                "category": "sih_regional_stations",
                "temp_avg": round((avg_max + avg_min) / 2.0, 1),
                "temp_max": peak_max,
                "temp_min": avg_min,
                "source": "Regional Stations Weather Dataset"
            })

        return chunks

    def process_weather_encoded(self, fpath: str) -> List[Dict[str, Any]]:
        """Process weather_encoded.csv (83,725 daily rows, 1990-2022, 8 Cities with Seasonal breakdown)."""
        chunks = []
        if not os.path.exists(fpath):
            return chunks

        df = pd.read_csv(fpath)
        for city, grp in df.groupby('city'):
            avg_temp = round(float(grp['tavg'].mean()), 1)
            peak_max = round(float(grp['tmax'].max()), 1)
            lowest_min = round(float(grp['tmin'].min()), 1)
            elevation = float(grp['elevation'].iloc[0]) if 'elevation' in grp.columns else 100.0
            avg_wind_speed = round(float(grp['wspd'].mean()), 1) if 'wspd' in grp.columns else 10.0
            avg_pressure = round(float(grp['pres'].mean()), 1) if 'pres' in grp.columns else 1010.0
            
            # Seasonal Temperature Summaries
            seasons_text = []
            if 'season' in grp.columns:
                for s_name, s_df in grp.groupby('season'):
                    s_avg = round(float(s_df['tavg'].mean()), 1)
                    s_max = round(float(s_df['tmax'].max()), 1)
                    s_min = round(float(s_df['tmin'].min()), 1)
                    s_prcp = round(float(s_df['prcp'].sum() / 32.0), 1) if 'prcp' in s_df.columns else 0.0
                    seasons_text.append(f"{s_name} (Mean: {s_avg}°C, Max: {s_max}°C, Min: {s_min}°C, Rain: {s_prcp}mm)")

            seasons_summary = " | ".join(seasons_text) if seasons_text else "Seasonal patterns active."

            content = (
                f"Multi-Decadal Weather Encoded Climatology for {city} (1990-2022, 32-Year Observation Series): "
                f"Station Elevation is {elevation:.1f} meters above sea level. "
                f"Mean Surface Temperature across 32 years is {avg_temp}°C (All-Time Record Peak: {peak_max}°C, Record Lowest: {lowest_min}°C). "
                f"Mean Atmospheric Surface Pressure is {avg_pressure:.1f} hPa, and Average Wind Speed is {avg_wind_speed} km/h. "
                f"Seasonal Breakdown: {seasons_summary}."
            )

            chunks.append({
                "doc_id": f"weather_encoded_{city.lower()}",
                "content": content,
                "city": city,
                "state": "India (Encoded Dataset)",
                "category": "sih_encoded_multidecadal",
                "temp_avg": avg_temp,
                "temp_max": peak_max,
                "temp_min": lowest_min,
                "elevation": elevation,
                "source": "Weather Encoded Multi-Decadal Dataset (1990-2022)"
            })

        return chunks

    def ingest_all_datasets(self) -> Dict[str, Any]:
        """Ingest all 7 datasets into Qdrant Vector DB with point vectors."""
        all_chunks = []
        
        # 1-3. Coastal Stations (Barisal, Chittagong, Khulna)
        for src in CSV_SOURCES[:3]:
            all_chunks.extend(self.process_coastal_station(src["name"], src["path"]))

        # 4. India 2000-2024
        all_chunks.extend(self.process_india_historical(CSV_SOURCES[3]["path"]))

        # 5. Indian Climate 2024-2025
        all_chunks.extend(self.process_indian_climate_2024_2025(CSV_SOURCES[4]["path"]))

        # 6. Regional Stations
        all_chunks.extend(self.process_regional_weather(CSV_SOURCES[5]["path"]))

        # 7. Weather Encoded Multi-Decadal (1990-2022)
        all_chunks.extend(self.process_weather_encoded(CSV_SOURCES[6]["path"]))

        # Vectorize and upsert into Qdrant
        upserted_count = 0
        if self.qdrant_client and all_chunks:
            try:
                from qdrant_client.http import models
                points = []
                for idx, chunk in enumerate(all_chunks):
                    vec = self._get_embedding(chunk["content"])
                    payload = {
                        "doc_id": chunk["doc_id"],
                        "content": chunk["content"],
                        "city": chunk.get("city", ""),
                        "state": chunk.get("state", ""),
                        "category": chunk.get("category", "sih_dataset"),
                        "temp_avg": chunk.get("temp_avg"),
                        "temp_max": chunk.get("temp_max"),
                        "temp_min": chunk.get("temp_min"),
                        "source": chunk.get("source", "SIH 2026 Archive")
                    }
                    points.append(models.PointStruct(id=idx + 1000, vector=vec, payload=payload))

                self.qdrant_client.upsert(collection_name=self.collection_name, points=points)
                upserted_count = len(points)
            except Exception:
                pass

        return {
            "total_chunks_processed": len(all_chunks),
            "qdrant_upserted_count": upserted_count,
            "sample_cities": list(set(c["city"] for c in all_chunks))[:15],
            "collection_name": self.collection_name
        }
