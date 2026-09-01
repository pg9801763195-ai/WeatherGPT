"""
Weather & Climate Instruction Dataset Formatter for LoRA Fine-Tuning.
Formats meteorological, agro-advisory, NWP diagnostics, and Indian multilingual records into standard Alpaca/ChatML/LLaMA-3 JSONL training splits.
"""
import os
import json
from typing import List, Dict, Any, Optional


class WeatherInstructionDatasetFormatter:
    """Creates curated instruction-tuning pairs for LoRA adaptation of open-source LLMs."""

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "finetuning_splits"
        )
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_instruction_samples(self) -> List[Dict[str, str]]:
        """Generate high-quality domain-specific instruction examples across weather tasks."""
        samples = [
            # 1. NWP Convective Instability & CAPE Interpretation
            {
                "instruction": "Analyze the atmospheric convective parameters and evaluate thunderstorm potential for the given location.",
                "input": "Location: Nagpur, Maharashtra. Model: NOAA GFS 0.25. CAPE: 2450 J/kg, CIN: 18 J/kg, 500 hPa Temp: -8.2°C, Surface Dewpoint: 24°C.",
                "output": "Assessment: Extremely high convective instability. Surface-based CAPE of 2450 J/kg with minimal Convective Inhibition (18 J/kg) indicates explosive updraft potential. Expect severe thunderstorms, squall lines with wind gusts exceeding 60 km/h, and localized hail during late afternoon peak solar insolation. Action: Issue Orange Alert for agricultural fields and power utilities."
            },
            # 2. Agro-Advisory: Spray Window & ET0 Irrigation
            {
                "instruction": "Determine the pesticide spray window safety and irrigation schedule for cotton crop based on current meteorological forecast.",
                "input": "Location: Coimbatore. Crop: Cotton (Flowering stage). Forecast: Wind 18 km/h, Rain probability 80% (expected 12mm), Temp 31°C.",
                "output": "Advisory:\n1. Pesticide Spray Window: UNSAFE TO SPRAY. Wind speeds > 15 km/h will cause chemical drift, and high rainfall probability (80%) will wash away foliar applications.\n2. Irrigation Scheduling: WITHHOLD IRRIGATION. Predicted 12mm precipitation satisfies crop water requirement (ET0: 4.8mm/day). Ensure field drainage bunds are clear to prevent water stagnation and root hypoxia."
            },
            # 3. IMD CAP Extreme Weather Alert Generation
            {
                "instruction": "Format an authoritative IMD Common Alerting Protocol (CAP) bulletin for an impending cyclonic disturbance.",
                "input": "System: Deep Depression in Bay of Bengal. Central Pressure: 994 hPa. Sustained Wind: 75 km/h. Coast Target: Odisha-Andhra coast.",
                "output": "IMD CAP BULLETINA ID: IMD-CY-BOB-04\nCategory: Cyclonic Storm\nSeverity: RED (Take Action)\nHeadline: Cyclonic Storm Warning for Coastal Odisha and Northern Andhra Pradesh\nImpact: Sea condition very rough to high. Gale winds 75-85 km/h gusting to 95 km/h.\nSafety Guidelines:\n1. Total suspension of fishing operations over deep sea.\n2. Evacuate low-lying kutcha settlements within 5km of coastline.\n3. Mobilize NDRF/ODRAF disaster response teams immediately."
            },
            # 4. IPCC AR6 Climate Projection Interpretation
            {
                "instruction": "Synthesize IPCC AR6 Working Group projections for the Indian Summer Monsoon and regional agriculture.",
                "input": "Query: How will climate change affect the South Asian monsoon variability and wheat yields according to IPCC AR6?",
                "output": "Based on IPCC AR6 WG1 & WG2:\n1. Monsoon Trends: Summer monsoon precipitation will increase in volume but exhibit severe interannual variability with longer dry spells interrupted by intense downpours.\n2. Agricultural Impact: Unchecked warming of 1.5°C to 2.0°C is projected to reduce Indian wheat yield by 5-15% due to terminal heat stress during grain filling. Recommended adaptation includes drought-hardy seed varieties, drip irrigation, and micro-climate agroforestry buffers."
            },
            # 5. Multilingual Localization (Hindi)
            {
                "instruction": "Translate and localize the following extreme heatwave warning into clear Hindi for rural farmers.",
                "input": "Warning: Severe Heatwave in Varanasi. Temperature reaching 46.2°C. Avoid outdoor field labor between 11 AM and 4 PM. Keep livestock hydrated in shaded sheds.",
                "output": "🌾 **लू (Heatwave) की गंभीर चेतावनी - वाराणसी**:\nदिन का अधिकतम तापमान 46.2°C तक पहुँचने की संभावना है।\n1. किसान भाई सुबह 11:00 बजे से दोपहर 4:00 बजे तक खुले खेतों में काम करने से बचें।\n2. पशुओं को छायादार बाड़ों में रखें तथा पर्याप्त स्वच्छ पानी व ओआरएस (ORS)/नींबू पानी पिएं।"
            }
        ]
        return samples

    def export_dataset(self, filename: str = "weather_lora_instructions.jsonl") -> str:
        """Save formatted dataset to JSONL for HuggingFace / LLaMA-Factory / Unsloth fine-tuning."""
        file_path = os.path.join(self.output_dir, filename)
        samples = self.generate_instruction_samples()
        with open(file_path, "w", encoding="utf-8") as f:
            for s in samples:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
        return file_path
