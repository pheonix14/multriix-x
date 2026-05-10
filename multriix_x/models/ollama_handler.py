"""
MULTRIIX X — Ollama Handler
Full production Ollama API bridge.
Lists, streams, pulls, and manages any Ollama model dynamically.
"""

import os
import json
import asyncio
import httpx
from typing import AsyncGenerator, Optional, List

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
TIMEOUT = httpx.Timeout(None, connect=5.0)


class OllamaHandler:
    """
    Full Ollama API bridge with health checks, dynamic model listing,
    streaming generation, and model pull/delete management.
    """

    def __init__(self, base_url: str = None):
        self.base_url = base_url or OLLAMA_BASE_URL
        self._alive = False

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(3.0)) as client:
                r = await client.get(f"{self.base_url}/api/tags")
                self._alive = r.status_code == 200
                return self._alive
        except Exception:
            self._alive = False
            return False

    async def list_models(self) -> List[dict]:
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                r = await client.get(f"{self.base_url}/api/tags")
                if r.status_code == 200:
                    return r.json().get("models", [])
        except Exception as e:
            print(f"[OLLAMA] list_models error: {e}")
        return []

    async def generate(
        self,
        model: str,
        prompt: str,
        system: str = "",
        stream: bool = True,
        options: dict = None,
    ) -> AsyncGenerator[dict, None]:
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": stream,
            "options": options or {},
        }
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                async with client.stream(
                    "POST", f"{self.base_url}/api/generate", json=payload
                ) as response:
                    async for line in response.aiter_lines():
                        if line.strip():
                            data = json.loads(line)
                            yield data
                            if data.get("done"):
                                break
        except Exception as e:
            yield {"error": str(e), "done": True}

    async def pull_model(self, model: str) -> AsyncGenerator[dict, None]:
        """Pull a model from Ollama registry with progress streaming."""
        payload = {"name": model, "stream": True}
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                async with client.stream(
                    "POST", f"{self.base_url}/api/pull", json=payload
                ) as response:
                    async for line in response.aiter_lines():
                        if line.strip():
                            yield json.loads(line)
        except Exception as e:
            yield {"error": str(e)}

    async def delete_model(self, model: str) -> bool:
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                r = await client.delete(
                    f"{self.base_url}/api/delete", json={"name": model}
                )
                return r.status_code == 200
        except Exception:
            return False


_ollama_handler: Optional[OllamaHandler] = None


def get_ollama_handler() -> OllamaHandler:
    global _ollama_handler
    if _ollama_handler is None:
        _ollama_handler = OllamaHandler()
    return _ollama_handler
