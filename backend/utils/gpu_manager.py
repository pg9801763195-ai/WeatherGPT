"""
GPU Acceleration & Hardware Optimization Manager.
Detects NVIDIA CUDA hardware (e.g., RTX 4060 8GB VRAM) and configures optimal GPU acceleration
for Ollama LLMs/Vision, Whisper Speech-to-Text, Dense Embedding models, and LoRA fine-tuning.
"""
import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple


@dataclass
class GPUHardwareProfile:
    """Hardware diagnostics profile for CUDA acceleration."""
    has_cuda_gpu: bool
    gpu_name: str
    total_vram_mb: int
    free_vram_mb: int
    driver_version: str
    cuda_version: str
    recommended_precision: str  # 'fp16' | 'bf16' | 'int8' | 'fp32'
    max_recommended_llm_size: str  # e.g. '8B Q4_K_M (4.9 GB VRAM)'


class GPUManager:
    """Detects, optimizes, and dispatches workloads to available NVIDIA GPUs."""

    _cached_profile: Optional[GPUHardwareProfile] = None

    @classmethod
    def get_hardware_profile(cls) -> GPUHardwareProfile:
        """Inspect system hardware and return active GPU profile."""
        if cls._cached_profile is not None:
            return cls._cached_profile

        has_cuda = False
        gpu_name = "CPU Only"
        total_vram = 0
        free_vram = 0
        driver_ver = "N/A"
        cuda_ver = "N/A"

        # 1. Try PyTorch CUDA if available
        try:
            import torch
            if torch.cuda.is_available():
                has_cuda = True
                gpu_name = torch.cuda.get_device_name(0)
                total_vram = int(torch.cuda.get_device_properties(0).total_memory / (1024 * 1024))
                # Free VRAM
                free_bytes, total_bytes = torch.cuda.mem_get_info()
                free_vram = int(free_bytes / (1024 * 1024))
                cuda_ver = torch.version.cuda or "CUDA Active"
        except Exception:
            pass

        # 2. Fallback / Augment with nvidia-smi CLI
        if not has_cuda and shutil.which("nvidia-smi"):
            try:
                cmd = ["nvidia-smi", "--query-gpu=name,memory.total,memory.free,driver_version", "--format=csv,noheader,nounits"]
                output = subprocess.check_output(cmd, encoding="utf-8", timeout=3).strip()
                if output:
                    parts = [p.strip() for p in output.split(",")]
                    if len(parts) >= 4:
                        has_cuda = True
                        gpu_name = parts[0]
                        total_vram = int(float(parts[1]))
                        free_vram = int(float(parts[2]))
                        driver_ver = parts[3]
                        cuda_ver = "CUDA Driver Ready"
            except Exception:
                pass

        # Determine optimal precision and LLM capacity for 8GB VRAM (e.g. RTX 4060)
        if total_vram >= 7000:
            rec_precision = "fp16"
            rec_llm = "8B Q4_K_M (4.9 GB VRAM - 100% GPU Offload)"
        elif total_vram >= 4000:
            rec_precision = "fp16"
            rec_llm = "7B / 3B Q4_K_M (Partial / Full Offload)"
        else:
            rec_precision = "fp32"
            rec_llm = "CPU / Low Memory Quantization"

        profile = GPUHardwareProfile(
            has_cuda_gpu=has_cuda,
            gpu_name=gpu_name,
            total_vram_mb=total_vram,
            free_vram_mb=free_vram,
            driver_version=driver_ver,
            cuda_version=cuda_ver,
            recommended_precision=rec_precision,
            max_recommended_llm_size=rec_llm
        )
        cls._cached_profile = profile
        return profile

    @classmethod
    def get_ollama_gpu_options(cls) -> Dict[str, Any]:
        """Generate optimal GPU offload parameters for Ollama API calls."""
        prof = cls.get_hardware_profile()
        if prof.has_cuda_gpu:
            return {
                "num_gpu": 99,       # Offload all transformer layers to GPU
                "main_gpu": 0,
                "f16_kv": True,      # Half-precision Key-Value cache for memory savings
                "num_thread": 8
            }
        return {"num_gpu": 0, "num_thread": 4}

    @classmethod
    def get_whisper_device_config(cls) -> Tuple[str, str]:
        """Return optimal (device, compute_type) for Whisper speech-to-text."""
        prof = cls.get_hardware_profile()
        if prof.has_cuda_gpu:
            # RTX 4060 supports native FP16 and INT8_FLOAT16 Tensor Cores
            return "cuda", "float16"
        return "cpu", "int8"

    @classmethod
    def get_embedding_device(cls) -> str:
        """Return optimal device for dense embeddings and vector encoders."""
        prof = cls.get_hardware_profile()
        return "cuda" if prof.has_cuda_gpu else "cpu"
