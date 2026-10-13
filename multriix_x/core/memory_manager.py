"""
MULTRIIX X — Memory Manager
Short-term conversation memory + long-term persistent JSON store.
Auto-summarization and memory injection into prompts.
"""

import os
import json
import time
import uuid
import threading
from typing import List, Dict, Optional
from datetime import datetime


DEFAULT_MEMORY_FILE = os.path.join(os.path.dirname(__file__), "..", "memory_store.json")


class MemoryManager:
    def __init__(self, short_term_limit: int = 20, memory_file: Optional[str] = None):
        self.short_term: List[Dict] = []  # recent turns
        self.long_term: List[Dict] = []   # persistent facts/summaries
        self.short_term_limit = short_term_limit
        self.memory_file = memory_file or DEFAULT_MEMORY_FILE
        self._lock = threading.RLock()
        self._load_long_term()

    def _load_long_term(self):
        with self._lock:
            try:
                if os.path.exists(self.memory_file):
                    with open(self.memory_file, "r", encoding="utf-8") as f:
                        self.long_term = json.load(f)
            except Exception:
                self.long_term = []

    def _save_long_term(self):
        with self._lock:
            try:
                with open(self.memory_file, "w", encoding="utf-8") as f:
                    json.dump(self.long_term, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[MEMORY] Save error: {e}")

    def add_turn(self, role: str, content: str, session_id: str = "default"):
        """Add a conversation turn to short-term memory."""
        with self._lock:
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
        with self._lock:
            entry = {
                "id": str(uuid.uuid4()),
                "fact": fact,
                "tags": tags or [],
                "created_at": datetime.now().isoformat(),
            }
            self.long_term.append(entry)
            self._save_long_term()
            return entry

    def search_memory(self, query: str = "", tag: Optional[str] = None) -> List[Dict]:
        """Search persistent memories by keyword and/or tag."""
        with self._lock:
            query_lower = query.lower().strip()
            results = []
            for mem in self.long_term:
                fact_match = query_lower in mem.get("fact", "").lower() if query_lower else True
                tag_match = (tag in mem.get("tags", [])) if tag else True
                if fact_match and tag_match:
                    results.append(mem)
            return results

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
        with self._lock:
            return [t for t in self.short_term if t["session_id"] == session_id]

    def get_long_term(self) -> List[Dict]:
        with self._lock:
            return list(self.long_term)

    def delete_memory(self, memory_id: str) -> bool:
        with self._lock:
            before = len(self.long_term)
            self.long_term = [m for m in self.long_term if m["id"] != memory_id]
            if len(self.long_term) < before:
                self._save_long_term()
                return True
            return False

    def clear_short_term(self, session_id: str = "default"):
        with self._lock:
            self.short_term = [t for t in self.short_term if t["session_id"] != session_id]

    def clear_all(self):
        with self._lock:
            self.short_term = []
            self.long_term = []
            self._save_long_term()

    def export(self) -> dict:
        with self._lock:
            return {"short_term": list(self.short_term), "long_term": list(self.long_term)}


_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
