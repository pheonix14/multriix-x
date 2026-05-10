"""
MULTRIIX X — Memory Manager
Short-term conversation memory + long-term persistent JSON store.
Auto-summarization and memory injection into prompts.
"""

import os
import json
import time
import uuid
from typing import List, Dict, Optional
from datetime import datetime


MEMORY_FILE = os.path.join(os.path.dirname(__file__), "..", "memory_store.json")


class MemoryManager:
    def __init__(self, short_term_limit: int = 20):
        self.short_term: List[Dict] = []  # recent turns
        self.long_term: List[Dict] = []   # persistent facts/summaries
        self.short_term_limit = short_term_limit
        self._load_long_term()

    def _load_long_term(self):
        try:
            if os.path.exists(MEMORY_FILE):
                with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                    self.long_term = json.load(f)
        except Exception:
            self.long_term = []

    def _save_long_term(self):
        try:
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.long_term, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[MEMORY] Save error: {e}")

    def add_turn(self, role: str, content: str, session_id: str = "default"):
        """Add a conversation turn to short-term memory."""
        self.short_term.append({
            "id": str(uuid.uuid4()),
            "role": role,
            "content": content,
            "session_id": session_id,
            "timestamp": time.time(),
        })
        # Trim if over limit
        if len(self.short_term) > self.short_term_limit * 2:
            self.short_term = self.short_term[-(self.short_term_limit * 2):]

    def inject_memory(self, fact: str, tags: List[str] = None):
        """Manually inject a persistent fact into long-term memory."""
        entry = {
            "id": str(uuid.uuid4()),
            "fact": fact,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
        }
        self.long_term.append(entry)
        self._save_long_term()
        return entry

    def get_context_string(self, session_id: str = "default", max_turns: int = 10) -> str:
        """Build a context string to inject into system prompt."""
        lines = []
        # Add relevant long-term memories
        if self.long_term:
            lines.append("=== PERSISTENT MEMORIES ===")
            for mem in self.long_term[-5:]:
                lines.append(f"- {mem['fact']}")

        # Add recent short-term turns
        session_turns = [t for t in self.short_term if t["session_id"] == session_id]
        recent = session_turns[-max_turns:]
        if recent:
            lines.append("=== RECENT CONVERSATION ===")
            for turn in recent:
                lines.append(f"{turn['role'].upper()}: {turn['content'][:200]}")

        return "\n".join(lines)

    def get_short_term(self, session_id: str = "default") -> List[Dict]:
        return [t for t in self.short_term if t["session_id"] == session_id]

    def get_long_term(self) -> List[Dict]:
        return self.long_term

    def delete_memory(self, memory_id: str) -> bool:
        before = len(self.long_term)
        self.long_term = [m for m in self.long_term if m["id"] != memory_id]
        if len(self.long_term) < before:
            self._save_long_term()
            return True
        return False

    def clear_short_term(self, session_id: str = "default"):
        self.short_term = [t for t in self.short_term if t["session_id"] != session_id]

    def clear_all(self):
        self.short_term = []
        self.long_term = []
        self._save_long_term()

    def export(self) -> dict:
        return {"short_term": self.short_term, "long_term": self.long_term}


_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
