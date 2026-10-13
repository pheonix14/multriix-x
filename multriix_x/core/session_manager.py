"""
MULTRIIX X — Session Manager
Multi-session chat management. Each session has its own memory, model, and config.
"""

import uuid
import time
import threading
from typing import Dict, Optional


class Session:
    def __init__(self, session_id: str = None):
        self.id = session_id or str(uuid.uuid4())
        self.created_at = time.time()
        self.last_active = time.time()
        self.model = "auto"
        self.temperature = 0.7
        self.max_tokens = 512
        self.system_prompt = "You are MULTRIIX, a powerful AI assistant built by ZeroX."
        self.message_count = 0

    def touch(self):
        self.last_active = time.time()

    def update(self, **kwargs):
        """Update session parameters dynamically."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.touch()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "message_count": self.message_count,
            "system_prompt": self.system_prompt,
        }


class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, Session] = {}
        self._lock = threading.RLock()

    def create_session(self, session_id: str = None) -> Session:
        with self._lock:
            s = Session(session_id)
            self._sessions[s.id] = s
            return s

    def get_session(self, session_id: str) -> Optional[Session]:
        with self._lock:
            return self._sessions.get(session_id)

    def get_or_create(self, session_id: str) -> Session:
        with self._lock:
            if session_id not in self._sessions:
                return self.create_session(session_id)
            session = self._sessions[session_id]
            session.touch()
            return session

    def list_sessions(self) -> list:
        with self._lock:
            return [s.to_dict() for s in self._sessions.values()]

    def delete_session(self, session_id: str) -> bool:
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False

    def cleanup_old(self, max_age_seconds: int = 3600):
        """Remove sessions older than max_age_seconds."""
        with self._lock:
            now = time.time()
            to_delete = [
                sid for sid, s in self._sessions.items()
                if now - s.last_active > max_age_seconds
            ]
            for sid in to_delete:
                del self._sessions[sid]
            return len(to_delete)


_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
