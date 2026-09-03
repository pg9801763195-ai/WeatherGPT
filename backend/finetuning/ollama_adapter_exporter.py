"""
Ollama Modelfile Exporter for LoRA Adapters.
Generates Modelfiles to serve LoRA fine-tuned adapters locally via Ollama.
"""
import os
from typing import Optional
from finetuning.lora_adapter import LoRAConfig


class OllamaLoRAExporter:
    """Exports LoRA adapter configuration into an Ollama Modelfile."""

    def __init__(self, base_model: str = "llama3.1:latest", adapter_path: str = "./lora_weather_adapter.gguf"):
        self.base_model = base_model
        self.adapter_path = adapter_path

    def export_modelfile(
        self,
        output_path: str,
        system_prompt: str,
        config: Optional[LoRAConfig] = None
    ) -> str:
        """Create Ollama Modelfile with ADAPTER and PARAMETER directives."""
        cfg = config or LoRAConfig()
        
        content = f"""# Modelfile for MausamVani Weather LoRA Fine-Tuned Agent
FROM {self.base_model}

# Attach Fine-Tuned LoRA Adapter Matrix (Rank={cfg.r}, Alpha={cfg.lora_alpha})
ADAPTER {self.adapter_path}

# Hyperparameters
PARAMETER temperature 0.2
PARAMETER top_p 0.9
PARAMETER stop "<|eot_id|>"
PARAMETER stop "<|end_of_text|>"

# System Prompt
SYSTEM \"\"\"{system_prompt}\"\"\"
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return output_path
