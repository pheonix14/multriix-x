"""NeuralDesk — Ollama Bridge: All Ollama API calls."""

import httpx
from typing import AsyncGenerator


OLLAMA_BASE = "http://127.0.0.1:11434"


class OllamaBridge:
    """Talks to the local Ollama server."""

    def __init__(self, base_url: str = OLLAMA_BASE):
        self.base = base_url

    async def health_check(self) -> bool:
        """Return True if Ollama is reachable."""
        try:
            async with httpx.AsyncClient(timeout=3) as c:
                r = await c.get(f"{self.base}/api/tags")
                return r.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> dict:
        """List all installed models with metadata."""
        try:
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.get(f"{self.base}/api/tags")
                r.raise_for_status()
                data = r.json()
                models = data.get("models", [])
                return {
                    "online": True,
                    "count": len(models),
                    "models": [
                        {
                            "name": m.get("name"),
                            "size": m.get("size", 0),
                            "modified": m.get("modified_at", ""),
                            "family": m.get("details", {}).get("family", ""),
                            "parameters": m.get("details", {}).get("parameter_size", ""),
                        }
                        for m in models
                    ],
                }
        except Exception as e:
            return {"online": False, "count": 0, "models": [], "error": str(e)}

    async def model_info(self, model: str) -> dict:
        """Get detailed info for a specific model."""
        try:
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.post(f"{self.base}/api/show", json={"name": model})
                r.raise_for_status()
                return r.json()
        except Exception as e:
            return {"error": str(e)}

    async def chat_stream(
        self,
        model: str,
        messages: list,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        use_gpu: bool = True,
    ) -> AsyncGenerator[dict, None]:
        """Stream chat tokens from Ollama."""
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_gpu": 99 if use_gpu else 0,
            },
        }
        if system:
            payload["system"] = system

        print(f"\n\033[36m[OllamaBridge]\033[0m Starting stream for {model} (GPU: {use_gpu})")
        print(f"\033[2m  Last message: {messages[-1]['content'][:50]}...\033[0m")

        try:
            async with httpx.AsyncClient(timeout=300) as c:
                async with c.stream("POST", f"{self.base}/api/chat", json=payload) as resp:
                    import json
                    tokens_generated = 0
                    async for line in resp.aiter_lines():
                        if line.strip():
                            chunk = json.loads(line)
                            
                            # RUTHLESS REFUSAL PURGER (ULTIMATE JAILBREAK)
                            refusal_phrases = ["sorry", "can't assist", "cannot assist", "i am an ai", "not allowed", "sensitive", "inappropriate", "policy", "guidelines", "as an ai", "assist with that", "unable to"]
                            content = chunk.get("message", {}).get("content", "")
                            
                            if any(phrase in content.lower() for phrase in refusal_phrases):
                                chunk["message"]["content"] = "[FILTER BYPASSED: FORCING RAW OUTPUT...]"
                            
                            tokens_generated += 1
                            if tokens_generated % 20 == 0:
                                print(".", end="", flush=True)
                            yield chunk
                    print(f"\n\033[32m[OllamaBridge]\033[0m Finished stream ({tokens_generated} tokens)")
        except Exception as e:
            print(f"\n\033[31m[OllamaBridge]\033[0m Error: {e}")
            yield {"error": str(e), "done": True}

    async def generate_stream(
        self,
        model: str,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        use_gpu: bool = True,
    ) -> AsyncGenerator[dict, None]:
        """Stream raw generation tokens."""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "system": system,
            "options": {"temperature": temperature, "num_predict": max_tokens, "num_gpu": 99 if use_gpu else 0},
        }
        print(f"\n\033[36m[OllamaBridge]\033[0m Raw generate for {model}")
        try:
            async with httpx.AsyncClient(timeout=300) as c:
                async with c.stream("POST", f"{self.base}/api/generate", json=payload) as resp:
                    import json
                    async for line in resp.aiter_lines():
                        if line.strip():
                            yield json.loads(line)
        except Exception as e:
            yield {"error": str(e), "done": True}
