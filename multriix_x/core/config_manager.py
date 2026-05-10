import json
import os
import threading

DEFAULT_CONFIG = {
    "IDENTITY": {
        "ai_name": "MULTRIIX",
        "persona": "MULTRIIX X - Advanced AI Control Platform. Intelligent, efficient, and precise.",
        "creator_tag": "ZeroX / PHEONIX14 "
    },
    "BRAIN": {
        "model_primary": "qwen2.5:7b",
        "model_fallback": "mistral:7b",
        "model_mix_enabled": False,
        "mix_ratio": {"qwen": 0.7, "mistral": 0.3},
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "max_tokens": 4096,
        "context_window": 32768,
        "repeat_penalty": 1.1
    },
    "MEMORY": {
        "short_term_turns": 20,
        "long_term_enabled": True,
        "memory_db": "json",
        "auto_summarize": True,
        "inject_memories": True
    },
    "SYSTEM": {
        "system_prompt": "You are MULTRIIX X, a powerful AI control platform built by ZeroX. You have full access to the user's PC and can assist with complex tasks, coding, and system management.",
        "prefix_prompt": "",
        "suffix_prompt": "",
        "stop_sequences": []
    },
    "VOICE": {
        "tts_enabled": False,
        "tts_engine": "edge-tts",
        "voice": "en-US-GuyNeural",
        "stt_enabled": False
    },
    "PC_CONTROL": {
        "shell_enabled": True,
        "shell_whitelist": [],
        "file_access": True,
        "allowed_paths": ["C:/", "D:/"],
        "process_control": True
    },
    "UI": {
        "theme": "tron",
        "brain_fps": 30,
        "show_tokens_per_sec": True,
        "chat_font_size": 14,
        "dark_mode": True
    },
    "SERVER": {
        "host": "127.0.0.1",
        "port_start": 7860,
        "port_max": 7900,
        "reload_on_config_change": False,
        "log_level": "INFO"
    }
}

class ConfigManager:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.config = DEFAULT_CONFIG.copy()
        self.lock = threading.RLock()
        self.load_config()

    def load_config(self):
        with self.lock:
            if os.path.exists(self.config_path):
                try:
                    with open(self.config_path, "r") as f:
                        loaded = json.load(f)
                        self._merge_configs(self.config, loaded)
                except Exception as e:
                    print(f"Error loading config: {e}")
            else:
                self.save_config()

    def _merge_configs(self, target, source):
        for k, v in source.items():
            if k in target and isinstance(target[k], dict) and isinstance(v, dict):
                self._merge_configs(target[k], v)
            else:
                target[k] = v

    def save_config(self):
        with self.lock:
            try:
                with open(self.config_path, "w") as f:
                    json.dump(self.config, f, indent=4)
            except Exception as e:
                print(f"Error saving config: {e}")

    def get(self, section, key=None):
        with self.lock:
            if key:
                return self.config.get(section, {}).get(key)
            return self.config.get(section)

    def update(self, section, key, value):
        with self.lock:
            if section not in self.config:
                self.config[section] = {}
            self.config[section][key] = value
        self.save_config()

    def update_bulk(self, new_config):
        with self.lock:
            self._merge_configs(self.config, new_config)
        self.save_config()

# Singleton instance for imports
config_mgr = ConfigManager()

def get_config_manager():
    return config_mgr

