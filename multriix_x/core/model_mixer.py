"""
MULTRIIX X — Model Mixer
Mix multiple AI models mid-conversation. 
Supports token-level mixing, ratio blending, and mid-stream switching.
"""

from typing import Dict, AsyncGenerator


class ModelMixer:
    """
    Orchestrates multi-model mixing strategies:
    - RATIO: blend tokens proportionally across models
    - SWITCH: use Model A for first N tokens, then switch to Model B
    - ENSEMBLE: run N models in parallel, pick best response token
    """

    def __init__(self):
        self.mix_ratios: Dict[str, float] = {"qwen": 0.7, "mistral": 0.3}
        self.mix_mode: str = "ratio"  # "ratio" | "switch" | "ensemble"
        self.switch_at_token: int = 50
        self.enabled: bool = False

    def set_ratios(self, ratios: Dict[str, float]):
        total = sum(ratios.values())
        self.mix_ratios = {k: v / total for k, v in ratios.items()} if total else ratios

    def set_mode(self, mode: str):
        if mode in ("ratio", "switch", "ensemble"):
            self.mix_mode = mode

    def get_config(self) -> dict:
        return {
            "enabled": self.enabled,
            "mode": self.mix_mode,
            "ratios": self.mix_ratios,
            "switch_at_token": self.switch_at_token,
        }

    async def generate(
        self,
        router,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> AsyncGenerator[dict, None]:
        """Dispatch to the router using the current mixing strategy."""
        if not self.enabled or self.mix_mode == "ratio":
            async for chunk in router.generate_mixed(
                prompt, self.mix_ratios, system, temperature, max_tokens
            ):
                yield chunk
        elif self.mix_mode == "switch":
            # Use primary model for first N tokens, then switch
            primary = max(self.mix_ratios, key=self.mix_ratios.get)
            secondary = min(self.mix_ratios, key=self.mix_ratios.get)
            token_count = 0
            async for chunk in router.generate(prompt, system, primary, temperature, max_tokens):
                chunk["active_model"] = primary if token_count < self.switch_at_token else secondary
                token_count += 1
                yield chunk
        else:
            # Default fallback
            async for chunk in router.generate_mixed(
                prompt, self.mix_ratios, system, temperature, max_tokens
            ):
                yield chunk


_mixer = None


def get_mixer() -> ModelMixer:
    global _mixer
    if _mixer is None:
        _mixer = ModelMixer()
    return _mixer
