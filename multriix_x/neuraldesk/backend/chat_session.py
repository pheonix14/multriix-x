"""NeuralDesk — Chat Session: history, sessions, export."""

import json
import os
import time
import uuid
from pathlib import Path
from typing import Optional


class ChatSession:
    """Manages per-session chat history stored as JSON files."""

    @staticmethod
    def _path(session_id: str, history_dir: str) -> Path:
        return Path(history_dir) / f"{session_id}.json"

    @staticmethod
    def list_all(history_dir: str) -> list:
        """List all sessions with metadata."""
        d = Path(history_dir)
        d.mkdir(parents=True, exist_ok=True)
        sessions = []
        for f in sorted(d.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                messages = data.get("messages", [])
                first_msg = next((m["content"][:60] for m in messages if m["role"] == "user"), "New Chat")
                sessions.append({
                    "id": data.get("id", f.stem),
                    "title": first_msg,
                    "message_count": len(messages),
                    "created": data.get("created", f.stat().st_ctime),
                    "modified": f.stat().st_mtime,
                })
            except Exception:
                continue
        return sessions

    @staticmethod
    def load(session_id: str, history_dir: str) -> dict:
        """Load a single session."""
        p = ChatSession._path(session_id, history_dir)
        if not p.exists():
            return {"id": session_id, "messages": [], "created": time.time()}
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {"id": session_id, "messages": [], "created": time.time()}

    @staticmethod
    def append(session_id: str, role: str, content: str, history_dir: str):
        """Append a single message turn."""
        Path(history_dir).mkdir(parents=True, exist_ok=True)
        p = ChatSession._path(session_id, history_dir)
        data = ChatSession.load(session_id, history_dir)
        data.setdefault("messages", []).append({
            "role": role,
            "content": content,
            "timestamp": time.time(),
        })
        p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def delete(session_id: str, history_dir: str):
        """Delete a session file."""
        p = ChatSession._path(session_id, history_dir)
        if p.exists():
            p.unlink()

    @staticmethod
    def export_txt(session_id: str, history_dir: str) -> str:
        """Export session as plain text."""
        data = ChatSession.load(session_id, history_dir)
        lines = [f"=== Chat Session: {session_id} ===\n"]
        for m in data.get("messages", []):
            role = "You" if m["role"] == "user" else "AI"
            lines.append(f"[{role}]: {m['content']}\n")
        return "\n".join(lines)

    @staticmethod
    def create_new(history_dir: str) -> dict:
        """Create a blank new session and return its metadata."""
        session_id = str(uuid.uuid4())[:8]
        data = {"id": session_id, "messages": [], "created": time.time()}
        p = ChatSession._path(session_id, history_dir)
        Path(history_dir).mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data
