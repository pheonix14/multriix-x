"""NeuralDesk — Model Manager: pull, delete, switch models."""

import subprocess
import asyncio
from backend.ollama_bridge import OllamaBridge


class ModelManager:
    """Manages Ollama model lifecycle."""

    def __init__(self):
        self.bridge = OllamaBridge()

    async def pull(self, name: str) -> dict:
        """Pull a model from Ollama registry (blocking in background thread)."""
        if not name:
            return {"error": "Model name required"}

        import os
        def _get_ollama_path():
            win_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Ollama", "ollama.exe")
            return win_path if os.path.exists(win_path) else "ollama"

        def _do_pull():
            try:
                exe = _get_ollama_path()
                result = subprocess.run(
                    [exe, "pull", name],
                    capture_output=True, text=True, timeout=900
                )
                return {"success": result.returncode == 0, "output": result.stdout[-500:]}
            except FileNotFoundError:
                return {"error": "ollama CLI not found"}
            except subprocess.TimeoutExpired:
                return {"error": "Download timed out after 15 minutes"}
            except Exception as e:
                return {"error": str(e)}

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _do_pull)

    async def delete(self, name: str) -> dict:
        """Delete a model from Ollama."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r = await c.delete("http://127.0.0.1:11434/api/delete", json={"name": name})
                r.raise_for_status()
                return {"deleted": name}
        except Exception as e:
            return {"error": str(e)}

    async def get_status(self, name: str) -> str:
        """Return 'running', 'installed', or 'not_installed'."""
        data = await self.bridge.list_models()
        names = [m["name"] for m in data.get("models", [])]
        if name in names:
            return "installed"
        return "not_installed"
