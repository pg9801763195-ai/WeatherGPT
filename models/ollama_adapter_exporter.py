"""
Ollama Modelfile Exporter for LoRA Adapters.
Generates GGUF / Ollama Modelfile configurations to serve the fine-tuned LoRA adapter locally.
"""
import os
from typing import Optional
from finetuning.lora_adapter import LoRAConfig


class OllamaLoRAExporter:
    """Exports Ollama Modelfile configuration for serving fine-tuned LoRA adapters."""

    def __init__(self, base_model: str = "llama3.1:latest", adapter_path: str = "./lora_weather_adapter.gguf"):
        self.base_model = base_model
        self.adapter_path = adapter_path

    def generate_modelfile_content(self, system_prompt: str, config: Optional[LoRAConfig] = None) -> str:
        """Create structured Modelfile text."""
        cfg = config or LoRAConfig()
        modelfile = f"""# Modelfile for MausamVani Fine-Tuned Weather & Agro-Advisory Agent
# Base Model: {self.base_model}
# LoRA Hyperparameters: Rank={cfg.r}, Alpha={cfg.lora_alpha}, Scaling={cfg.scaling}

FROM {self.base_model}

# Attach Fine-Tuned LoRA Adapter Matrix
ADAPTER {self.adapter_path}

# Runtime Sampling Parameters
PARAMETER temperature 0.2
PARAMETER top_p 0.9
PARAMETER stop "<|eot_id|>"
PARAMETER stop "<|start_header_id|>"
PARAMETER stop "<|end_header_id|>"

# Domain Specialized System Prompt
SYSTEM \"\"\"{system_prompt.strip()}\"\"\"
"""
        return modelfile

    def export_modelfile(self, output_path: str, system_prompt: str, config: Optional[LoRAConfig] = None) -> str:
        """Save Modelfile to disk."""
        content = self.generate_modelfile_content(system_prompt, config)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return output_path
