"""NeuralDesk — File Manager: full filesystem browser and editor."""

import os
import shutil
import time
from pathlib import Path
from typing import Optional

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

LANG_MAP = {
    ".py": "python", ".js": "javascript", ".ts": "typescript",
    ".json": "json", ".yaml": "yaml", ".yml": "yaml",
    ".sh": "shell", ".bash": "shell", ".md": "markdown",
    ".html": "html", ".css": "css", ".txt": "plaintext",
    ".toml": "toml", ".ini": "ini", ".cfg": "ini",
}


class FileManager:
    """Full filesystem browser and atomic editor."""

    def browse(self, path: str) -> dict:
        """List directory contents."""
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return {"error": f"Path not found: {path}"}
        if not p.is_dir():
            return {"error": f"Not a directory: {path}"}

        items = []
        try:
            for entry in sorted(p.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
                try:
                    stat = entry.stat()
                    is_modelfile = entry.name.lower() in ("modelfile",) or entry.suffix == ""
                    items.append({
                        "name": entry.name,
                        "type": "folder" if entry.is_dir() else "file",
                        "size_bytes": stat.st_size if entry.is_file() else 0,
                        "modified": stat.st_mtime,
                        "is_modelfile": is_modelfile and entry.is_file(),
                        "path": str(entry),
                        "extension": entry.suffix.lower(),
                    })
                except (PermissionError, OSError):
                    continue
        except PermissionError:
            return {"error": "Permission denied"}

        return {
            "path": str(p),
            "parent": str(p.parent),
            "name": p.name,
            "items": items,
        }

    def read(self, path: str) -> dict:
        """Read a file and return its content with metadata."""
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return {"error": f"File not found: {path}"}
        if p.is_dir():
            return {"error": "Cannot read a directory as file"}

        size = p.stat().st_size
        if size > MAX_FILE_SIZE:
            return {
                "error": f"File too large ({size // 1024}KB). Max is 5MB.",
                "path": str(p), "size_bytes": size,
            }

        try:
            content = p.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return {"error": str(e)}

        lang = LANG_MAP.get(p.suffix.lower(), "plaintext")
        if p.name.lower() == "modelfile":
            lang = "dockerfile"

        return {
            "path": str(p),
            "content": content,
            "size_bytes": size,
            "lines": content.count("\n") + 1,
            "language": lang,
            "modified": p.stat().st_mtime,
        }

    def write(self, path: str, content: str) -> dict:
        """Atomically write file with .bak backup."""
        p = Path(path).expanduser().resolve()
        p.parent.mkdir(parents=True, exist_ok=True)

        # Create backup
        backup_path = None
        if p.exists():
            backup_path = str(p) + ".bak"
            try:
                shutil.copy2(str(p), backup_path)
            except Exception:
                pass

        # Atomic write: write to temp then rename
        tmp = p.with_suffix(".tmp~")
        try:
            tmp.write_text(content, encoding="utf-8")
            tmp.replace(p)
            return {
                "success": True,
                "path": str(p),
                "bytes_written": len(content.encode("utf-8")),
                "backup_path": backup_path,
            }
        except Exception as e:
            try:
                tmp.unlink()
            except Exception:
                pass
            return {"success": False, "error": str(e)}

    def delete(self, path: str) -> dict:
        """Move file to trash or delete."""
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return {"error": "Path not found"}
        try:
            try:
                import send2trash
                send2trash.send2trash(str(p))
                return {"success": True, "trashed": True}
            except ImportError:
                if p.is_dir():
                    shutil.rmtree(str(p))
                else:
                    p.unlink()
                return {"success": True, "trashed": False}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_modelfiles(self) -> list:
        """Search common locations for Ollama Modelfiles."""
        locations = [
            Path.home() / ".ollama",
            Path.home() / "ollama",
            Path("/usr/share/ollama"),
            Path.cwd(),
        ]
        results = []
        for loc in locations:
            if not loc.exists():
                continue
            try:
                for p in loc.rglob("*"):
                    if p.name.lower() == "modelfile" and p.is_file():
                        try:
                            preview = p.read_text(encoding="utf-8", errors="replace")[:200]
                            results.append({
                                "path": str(p),
                                "model_name": p.parent.name,
                                "content_preview": preview,
                            })
                        except Exception:
                            pass
            except (PermissionError, OSError):
                continue
        return results
