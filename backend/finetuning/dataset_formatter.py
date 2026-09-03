"""
Dataset Formatter for Meteorological & Agro-Advisory Instruction Fine-Tuning.
Exports training pairs in Alpaca and ChatML JSONL formats for LoRA adaptation.
"""
import os
import json
from typing import List, Dict, Any, Optional


class WeatherInstructionDatasetFormatter:
    """Generates instruction-tuning datasets for domain-specific Weather LLM fine-tuning."""

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or os.path.join(os.path.dirname(__file__), "..", "data", "finetuning_splits")
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_sample_instructions(self) -> List[Dict[str, Any]]:
        """Synthesize domain-grounded meteorological and agricultural instruction pairs."""
        return [
            {
                "instruction": "Evaluate the pesticide spray window for Cotton in Vidarbha under the following conditions: Temperature: 31°C, Wind: 18 km/h, Rain Probability: 75% (8mm rain).",
                "input": "",
                "output": "UNSAFE TO SPRAY TODAY. High wind drift (18 km/h > 15 km/h limit) and significant rain probability (75%, 8mm wash-off) will cause pesticide loss and ineffective coverage. Postpone application until wind subsides below 15 km/h and rain clears."
            },
            {
                "instruction": "Interpret GFS NWP model outputs: CAPE is 2400 J/kg, CIN is 10 J/kg, 500hPa geopotential height is 5820m over Coastal Andhra.",
                "input": "",
                "output": "EXTREME CONVECTIVE INSTABILITY. CAPE value of 2400 J/kg with minimal convective inhibition (CIN 10 J/kg) indicates severe thunderstorm, squall line, and lightning hazard. Issue Orange/Red alert for localized heavy rainfall and gusty surface winds."
            },
            {
                "instruction": "According to IPCC AR6 WG1, how is South Asian monsoon extreme precipitation projected to change?",
                "input": "",
                "output": "IPCC AR6 WG1 projects with high confidence that total summer monsoon precipitation in South Asia will increase by 5% to 15% under medium-to-high emission scenarios. Daily precipitation variability will amplify, leading to longer dry spells punctuated by short-duration torrential downpours exceeding 100mm/day."
            }
        ]

    def export_dataset(self, filename: str = "weather_lora_instructions.jsonl") -> str:
        """Export dataset to JSONL file."""
        fpath = os.path.join(self.output_dir, filename)
        data = self.generate_sample_instructions()
        with open(fpath, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        return fpath
