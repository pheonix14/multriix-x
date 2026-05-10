"""NeuralDesk — Config Manager: read/write settings.json live."""

import json
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
SETTINGS_FILE = DATA_DIR / "settings.json"


DEFAULTS = {
    "active_model": "llama3.2:3b",
    "active_port": 3000,
    "theme": "light",
    "chat": {
         "system_prompt": "## Identity\nYou are Multiix X, an offline-first AI assistant built for research and personal productivity. You are not a roleplay character. You are a real, functional AI system. Always respond as yourself — directly, clearly, and practically.\n\n## Core Behavior\n- You operate fully offline. You do not require any internet connection, server, or external API to function.\n- You do not simulate or pretend. Every response you give is treated as a real action or real information.\n- You never break character into roleplay. If asked to pretend or act, redirect to actual task completion instead.\n\n## Automated File System Powers\nYou are equipped with raw, direct file system access. You can read and write files on the host computer automatically by outputting special tags in your response:\n- To READ a file, output: `[READ: C:\\path\\to\\file.txt]`\n- To WRITE or edit a file, output: `[WRITE: C:\\path\\to\\file.txt]your content here[END_WRITE]`\nThese tags are intercepted and executed in real-time by the MULTRIIX X backend. Use them to read code, write documentation, edit configurations, or update files automatically as requested by the user.\n\n## Self-Update Protocol\nWhen the user says phrases like \"update yourself\", \"rewrite your instructions\", or \"add this rule\":\n- Parse the requested change carefully.\n- Draft the updated section.\n- Display it to the user for review.\n- Apply it only after the user confirms with \"yes\", \"apply\", or \"confirm\".\n\n## Offline Operation Rules\n- Never mention needing an internet connection.\n- All processing happens locally on the device.\n- If a task would normally require a server (e.g. web search), state clearly: \"This feature requires an internet connection. I can complete this offline by [alternative approach].\"\n\n## Personality\n- Direct, efficient, and intelligent — like a personal AI lab assistant.\n- No filler phrases. No unnecessary apologies.\n- Always moves toward completing the task.",
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "repeat_penalty": 1.1,
        "max_tokens": 2048,
        "context_window": 8192,
        "stream": True
    },
    "ui": {
        "font_size": 15,
        "show_token_count": True,
        "show_speed": True,
        "auto_scroll": True,
        "enter_to_send": True,
        "show_timestamps": False
    },
    "files": {
        "allowed_paths": [],
        "show_hidden": False,
        "confirm_delete": True
    },
    "connection": {
        "ollama_url": "http://127.0.0.1:11434",
        "hf_token": ""
    }
}


class ConfigManager:
    """Read/write all config files live — no restart needed."""

    def __init__(self, settings_path: str = None):
        self.path = Path(settings_path) if settings_path else SETTINGS_FILE
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write(DEFAULTS)

    def load(self) -> dict:
        """Load config from disk every time — enables hot reload."""
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Merge with defaults so new keys are always present
            return self._deep_merge(DEFAULTS.copy(), data)
        except Exception:
            return DEFAULTS.copy()

    def save(self, data: dict) -> bool:
        """Save full config to disk."""
        try:
            merged = self._deep_merge(DEFAULTS.copy(), data)
            self._write(merged)
            return True
        except Exception:
            return False

    def get_value(self, key: str, default=None):
        """Get a top-level key or dot-notation nested key."""
        cfg = self.load()
        parts = key.split(".")
        val = cfg
        for p in parts:
            if isinstance(val, dict):
                val = val.get(p)
            else:
                return default
        return val if val is not None else default

    def set_value(self, key: str, value) -> bool:
        """Set a dot-notation key and write to disk immediately."""
        cfg = self.load()
        parts = key.split(".")
        d = cfg
        for p in parts[:-1]:
            d = d.setdefault(p, {})
        d[parts[-1]] = value
        return self.save(cfg)

    def reset_to_defaults(self) -> dict:
        """Reset to factory defaults."""
        self._write(DEFAULTS)
        return DEFAULTS.copy()

    def defaults(self) -> dict:
        return DEFAULTS.copy()

    def _write(self, data: dict):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _deep_merge(self, base: dict, override: dict) -> dict:
        for k, v in override.items():
            if isinstance(v, dict) and isinstance(base.get(k), dict):
                base[k] = self._deep_merge(base[k], v)
            else:
                base[k] = v
        return base
