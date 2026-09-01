# WeatherGPT Meteorological AI Models & LoRA Fine-Tuning

This directory contains the machine learning tools, LoRA fine-tuning scripts, synthetic meteorological dataset generators, and Ollama adapter export utilities for WeatherGPT.

---

## Architecture & Components

1. **`lora_tuner.py`**:
   - Parameter-Efficient Fine-Tuning (PEFT) with LoRA on top of **LLaMA-3.1 / Qwen-2.5**.
   - Supports 4-bit / 8-bit quantization (QLoRA) for NVIDIA RTX GPUs.
   - Fine-tunes specialized weights for Indian agro-meteorology, extreme weather classification, and atmospheric thermodynamics.

2. **`dataset_formatter.py`**:
   - Converts multi-decadal historical climate records and IMD CAP early warnings into instruction-tuning datasets (`alpaca` and `chatml` formats).

3. **`lora_adapter.py` & `ollama_adapter_exporter.py`**:
   - Merges LoRA weights and creates an **Ollama Modelfile** ready to serve with `ollama create weathergpt -f Modelfile`.

---

## Quick Usage

### 1. Prepare Meteorological Dataset
```bash
python dataset_formatter.py --output dataset_weathergpt.json
```

### 2. Train LoRA Adapter
```bash
python lora_tuner.py --base_model unsloth/Meta-Llama-3.1-8B-Instruct --dataset dataset_weathergpt.json --epochs 3
```

### 3. Export to Ollama
```bash
python ollama_adapter_exporter.py --adapter_path ./lora_weights --model_name weathergpt
ollama run weathergpt
```
