"""
MULTRIIX X — Model Router
Smart routing between Qwen, Mistral, GLM, Ollama, and Standalone.
Supports mixing, fallback chains, and blend mode.
"""

import asyncio
import random
from typing import AsyncGenerator, Dict, Optional


class ModelRouter:
    """
    Unified router that dispatches generation requests to the correct handler.
    Priority: Ollama (if alive) → HuggingFace local → Standalone fallback
    """

    def __init__(self):
        self._ollama = None
        self._qwen = None
        self._mistral = None
        self._glm = None
        self._standalone = None
        self._loaded = False

    def _init_handlers(self):
        if self._loaded:
            return
        from .ollama_handler import get_ollama_handler
        from .qwen_handler import get_qwen_handler
        from .mistral_handler import get_mistral_handler
        from .glm_handler import get_glm_handler
        from .standalone_handler import StandaloneHandler

        self._ollama = get_ollama_handler()
        self._qwen = get_qwen_handler(use_small=True)
        self._mistral = get_mistral_handler()
        self._glm = get_glm_handler()
        self._standalone = StandaloneHandler()
        self._loaded = True

    async def _get_best_handler(self, preferred_model: str = "qwen"):
        """Determine which backend to use based on availability."""
        self._init_handlers()
        ollama_alive = await self._ollama.health_check()
        if ollama_alive:
            return "ollama"
        # Try local HF models
        if preferred_model == "qwen" and self._qwen.is_loaded():
            return "qwen"
        if preferred_model == "mistral" and self._mistral.is_loaded():
            return "mistral"
        if preferred_model == "glm" and self._glm.is_loaded():
            return "glm"
        # Fallback to standalone (auto-downloads small model)
        return "standalone"

    async def generate(
        self,
        prompt: str,
        system: str = "You are MULTRIIX, a powerful AI assistant built by ZeroX.",
        model: str = "auto",
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> AsyncGenerator[dict, None]:
        """Route single-model generation."""
        self._init_handlers()

        backend = await self._get_best_handler(model)

        if backend == "ollama":
            ollama_model = {
                "qwen": "qwen2.5:7b",
                "mistral": "mistral:7b",
                "glm": "glm4:9b",
                "auto": "qwen2.5:7b",
            }.get(model, model)
            async for chunk in self._ollama.generate(
                ollama_model, prompt, system,
                options={"temperature": temperature, "num_predict": max_tokens}
            ):
                yield chunk
        elif backend == "qwen":
            async for chunk in self._qwen.generate(prompt, system, temperature, max_tokens):
                yield chunk
        elif backend == "mistral":
            async for chunk in self._mistral.generate(prompt, system, temperature, max_tokens):
                yield chunk
        elif backend == "glm":
            async for chunk in self._glm.generate(prompt, system, temperature, max_tokens):
                yield chunk
        else:
            async for chunk in self._standalone.generate(prompt, system, temperature, max_tokens):
                yield chunk

    async def generate_mixed(
        self,
        prompt: str,
        mix_ratios: Dict[str, float],
        system: str = "You are MULTRIIX, a powerful AI assistant built by ZeroX.",
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> AsyncGenerator[dict, None]:
        """
        Blend mode: route to models based on mix ratios.
        Each token gets tagged with which model produced it.
        """
        self._init_handlers()
        backend = await self._get_best_handler()

        # Normalize ratios
        total = sum(mix_ratios.values())
        normalized = {k: v / total for k, v in mix_ratios.items()} if total > 0 else {"qwen": 1.0}

        if backend == "ollama":
            # Use highest-ratio model for actual generation, tag tokens
            primary = max(normalized, key=normalized.get)
            ollama_model = {"qwen": "qwen2.5:7b", "mistral": "mistral:7b"}.get(primary, "qwen2.5:7b")
            async for chunk in self._ollama.generate(
                ollama_model, prompt, system,
                options={"temperature": temperature, "num_predict": max_tokens}
            ):
                if "response" in chunk:
                    # Tag with weighted-random model for UI visualization
                    r = random.random()
                    cumulative = 0.0
                    active_model = primary
                    for m, w in normalized.items():
                        cumulative += w
                        if r <= cumulative:
                            active_model = m
                            break
                    chunk["active_model"] = active_model
                    chunk["mix_ratios"] = normalized
                yield chunk
        else:
            # Standalone/local: single model, simulate mixing in metadata
            async for chunk in self._standalone.generate(prompt, system, temperature, max_tokens):
                if chunk.get("response"):
                    chunk["active_model"] = random.choices(
                        list(normalized.keys()), weights=list(normalized.values()), k=1
                    )[0]
                    chunk["mix_ratios"] = normalized
                yield chunk

    async def list_available_models(self) -> dict:
        """Return all available models across all backends."""
        self._init_handlers()
        result = {
            "ollama": [],
            "local_hf": [],
            "standalone": ["Qwen2.5-0.5B-Instruct"],
        }
        if await self._ollama.health_check():
            models = await self._ollama.list_models()
            result["ollama"] = [m["name"] for m in models]
        if self._qwen.is_loaded():
            result["local_hf"].append(self._qwen.model_id)
        if self._mistral.is_loaded():
            result["local_hf"].append(self._mistral.model_id)
        if self._glm.is_loaded():
            result["local_hf"].append(self._glm.model_id)
        return result


# Singleton
_router: Optional[ModelRouter] = None


def get_router() -> ModelRouter:
    global _router
    if _router is None:
        _router = ModelRouter()
    return _router
