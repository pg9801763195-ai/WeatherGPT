"""
PyTorch LoRA (Low-Rank Adaptation) Matrix Architecture with CUDA GPU Acceleration.
Implements mathematical low-rank matrix decomposition W = W0 + (alpha/r) * (B @ A) as a torch.nn.Module
supporting CUDA tensors, FP16/BF16 mixed precision, optimizer updates, and zero-latency weight merging.
"""
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


@dataclass
class LoRAConfig:
    """Configuration hyperparameters for LoRA matrix adaptation."""
    r: int = 16  # Low-rank dimension (r << min(d_in, d_out))
    lora_alpha: int = 32  # Scaling factor (scaling = lora_alpha / r)
    lora_dropout: float = 0.05
    target_modules: List[str] = field(default_factory=lambda: [
        "q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"
    ])
    bias: str = "none"
    device: str = "cuda" if HAS_TORCH and torch.cuda.is_available() else "cpu"
    dtype: str = "float32"

    @property
    def scaling(self) -> float:
        return self.lora_alpha / self.r if self.r > 0 else 1.0


if HAS_TORCH:
    class LoRALinear(nn.Module):
        """
        PyTorch Low-Rank Adaptation (LoRA) Linear Layer with CUDA GPU support.
        Forward: h = x @ W0.T + (alpha/r) * (dropout(x) @ lora_A.T @ lora_B.T)
        """

        def __init__(
            self,
            in_features: int,
            out_features: int,
            config: Optional[LoRAConfig] = None,
            layer_name: str = "q_proj",
            base_linear: Optional[nn.Linear] = None
        ):
            super().__init__()
            self.in_features = in_features
            self.out_features = out_features
            self.config = config or LoRAConfig()
            self.layer_name = layer_name
            self.r = self.config.r
            self.scaling = self.config.scaling
            self.merged = False

            self.target_device = torch.device(self.config.device if torch.cuda.is_available() else "cpu")
            self.target_dtype = getattr(torch, self.config.dtype, torch.float32)

            if base_linear is not None:
                self.base_layer = base_linear
                self.base_layer.weight.requires_grad = False
            else:
                self.base_layer = nn.Linear(in_features, out_features, bias=(self.config.bias != "none"))
                self.base_layer.weight.requires_grad = False
                if self.base_layer.bias is not None:
                    self.base_layer.bias.requires_grad = (self.config.bias == "all")

            self.base_layer.to(device=self.target_device, dtype=self.target_dtype)

            if self.r > 0:
                self.lora_dropout = nn.Dropout(p=self.config.lora_dropout) if self.config.lora_dropout > 0.0 else nn.Identity()
                self.lora_A = nn.Parameter(torch.empty((self.r, in_features), dtype=self.target_dtype, device=self.target_device))
                nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
                self.lora_B = nn.Parameter(torch.zeros((out_features, self.r), dtype=self.target_dtype, device=self.target_device))
            else:
                self.lora_A = None
                self.lora_B = None

        def forward(self, x: Any) -> torch.Tensor:
            """Forward pass with GPU tensor operations."""
            if not isinstance(x, torch.Tensor):
                x = torch.as_tensor(x, dtype=self.target_dtype, device=self.target_device)
            else:
                if x.device != self.target_device:
                    x = x.to(device=self.target_device)
                if x.dtype != self.target_dtype:
                    x = x.to(dtype=self.target_dtype)

            base_out = self.base_layer(x)

            if self.r > 0 and not self.merged and self.lora_A is not None and self.lora_B is not None:
                dropped_x = self.lora_dropout(x)
                lora_out = F.linear(F.linear(dropped_x, self.lora_A), self.lora_B) * self.scaling
                return base_out + lora_out

            return base_out

        def get_delta_weight(self) -> torch.Tensor:
            """Compute Delta W = (alpha/r) * (B @ A)."""
            if self.r > 0 and self.lora_A is not None and self.lora_B is not None:
                return (self.lora_B @ self.lora_A) * self.scaling
            return torch.zeros((self.out_features, self.in_features), dtype=self.target_dtype, device=self.target_device)

        def merge_weights(self):
            """Fold LoRA delta matrix into base weights W = W0 + Delta W for zero-overhead inference."""
            if self.r > 0 and not self.merged:
                with torch.no_grad():
                    delta = self.get_delta_weight()
                    self.base_layer.weight.data += delta
                self.merged = True

        def unmerge_weights(self):
            """Subtract LoRA delta matrix to restore original base weights W0."""
            if self.r > 0 and self.merged:
                with torch.no_grad():
                    delta = self.get_delta_weight()
                    self.base_layer.weight.data -= delta
                self.merged = False

        def count_parameters(self) -> Tuple[int, int]:
            """Return (trainable_lora_params, frozen_base_params)."""
            trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
            frozen = sum(p.numel() for p in self.parameters() if not p.requires_grad)
            return trainable, frozen

else:
    class LoRALinear:
        def __init__(self, in_features: int, out_features: int, config: Optional[LoRAConfig] = None, layer_name: str = "q_proj"):
            import numpy as np
            self.in_features = in_features
            self.out_features = out_features
            self.config = config or LoRAConfig()
            self.r = self.config.r
            self.scaling = self.config.scaling
            self.merged = False
            self.weight = np.random.randn(out_features, in_features).astype(np.float32) * 0.02
            self.lora_A = np.random.randn(self.r, in_features).astype(np.float32) * (1.0 / math.sqrt(max(self.r, 1))) if self.r > 0 else None
            self.lora_B = np.zeros((out_features, self.r), dtype=np.float32) if self.r > 0 else None

        def forward(self, x):
            import numpy as np
            res = np.matmul(x, self.weight.T)
            if self.r > 0 and not self.merged:
                res += np.matmul(np.matmul(x, self.lora_A.T), self.lora_B.T) * self.scaling
            return res

        def count_parameters(self) -> Tuple[int, int]:
            frozen = self.weight.size
            trainable = (self.lora_A.size + self.lora_B.size) if self.r > 0 else 0
            return trainable, frozen


def apply_lora_to_model(
    hidden_size: int = 4096,
    num_layers: int = 32,
    config: Optional[LoRAConfig] = None
) -> Dict[str, Any]:
    """
    Profile applying LoRA adapter matrices to an 8B LLM (e.g. LLaMA-3.1-8B or Qwen-2.5-7B).
    Computes parameter efficiency and adapter memory footprint in O(1) analytical time.
    """
    cfg = config or LoRAConfig()
    total_frozen_params = 0
    total_trainable_params = 0
    layers_adapted = {}

    module_shapes = {
        "q_proj": (hidden_size, hidden_size),
        "k_proj": (hidden_size, hidden_size),
        "v_proj": (hidden_size, hidden_size),
        "o_proj": (hidden_size, hidden_size),
        "gate_proj": (int(hidden_size * 3.5), hidden_size),
        "up_proj": (int(hidden_size * 3.5), hidden_size),
        "down_proj": (hidden_size, int(hidden_size * 3.5))
    }

    for layer_idx in range(num_layers):
        for mod_name in cfg.target_modules:
            if mod_name in module_shapes:
                d_out, d_in = module_shapes[mod_name]
                frozen = d_out * d_in
                trainable = (d_in * cfg.r) + (d_out * cfg.r) if cfg.r > 0 else 0
                total_trainable_params += trainable
                total_frozen_params += frozen
                
                key = f"model.layers.{layer_idx}.self_attn.{mod_name}"
                layers_adapted[key] = {
                    "in_features": d_in,
                    "out_features": d_out,
                    "rank": cfg.r,
                    "scaling": cfg.scaling,
                    "trainable_params": trainable
                }

    trainable_pct = (total_trainable_params / (total_frozen_params + total_trainable_params)) * 100.0
    memory_footprint_mb = (total_trainable_params * 4) / (1024 * 1024)

    return {
        "config": cfg,
        "total_frozen_parameters": total_frozen_params,
        "total_trainable_parameters": total_trainable_params,
        "trainable_percentage": trainable_pct,
        "adapter_memory_footprint_mb": memory_footprint_mb,
        "layers_adapted_count": len(layers_adapted),
        "sample_adapted_layers": list(layers_adapted.keys())[:4]
    }
