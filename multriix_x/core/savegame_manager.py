"""
MULTRIIX X — Advanced Savegame & Portable Memory Manager
Project: MULTRIIX X | Author: Pheonix14 / ZeroX

Provides savegame-style memory cartridges (.mxsave):
- Save / Load memory states to named slots or portable files
- Cryptographic SHA-256 integrity validation to prevent corrupted/tampered saves
- Merge vs Replace modes: travel with memory from one machine to another and combine them
- Metadata manifests: author, description, tags, turn count, fact count, timestamp
- QuickSave (qs) and QuickLoad (ql) slots
"""

import os
import json
import time
import hashlib
import uuid
import shutil
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime


MAGIC_HEADER = "MULTRIIX_SAVEGAME_V2"
DEFAULT_SAVES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saves")
USER_SAVES_DIR = os.path.expanduser("~/.multriix/saves")


class SavegameError(Exception):
    """Raised when savegame operations fail or integrity check is violated."""
    pass


class SavegameManager:
    def __init__(self, saves_dir: Optional[str] = None):
        self.saves_dir = saves_dir or DEFAULT_SAVES_DIR
        os.makedirs(self.saves_dir, exist_ok=True)
        # Also ensure user home saves directory exists for global travel
        try:
            os.makedirs(USER_SAVES_DIR, exist_ok=True)
        except Exception:
            pass

    def _compute_checksum(self, payload_dict: dict) -> str:
        """Compute SHA-256 checksum of payload data."""
        serialized = json.dumps(payload_dict, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()

    def _resolve_slot_path(self, slot_name_or_path: str) -> str:
        """Resolve slot name or path to a full .mxsave file path."""
        # If it's already an explicit file path with extension
        if slot_name_or_path.endswith(".mxsave") or "/" in slot_name_or_path or "\\" in slot_name_or_path:
            return os.path.abspath(slot_name_or_path)

        # Sanitize slot name
        clean_name = "".join(c for c in slot_name_or_path if c.isalnum() or c in ("-", "_")).strip()
        if not clean_name:
            clean_name = "default"
        return os.path.join(self.saves_dir, f"{clean_name}.mxsave")

    def create_savegame(
        self,
        memory_state: dict,
        slot_name: str = "quicksave",
        description: str = "",
        tags: Optional[List[str]] = None,
        author: str = "pheonix14",
        target_path: Optional[str] = None,
    ) -> Tuple[str, dict]:
        """
        Create a portable .mxsave cartridge from current memory state.
        
        Args:
            memory_state: Dict containing 'short_term' and 'long_term' turns/facts.
            slot_name: Name of the save slot.
            description: User note or context for this savegame.
            tags: List of semantic tags (e.g. ['python', 'agent', 'research']).
            author: Author of this memory cartridge.
            target_path: Optional explicit file path to write to (for portable travel).
            
        Returns:
            Tuple of (saved_file_path, manifest_dict)
        """
        short_term = memory_state.get("short_term", [])
        long_term = memory_state.get("long_term", [])

        payload = {
            "short_term": short_term,
            "long_term": long_term,
            "extra_context": memory_state.get("extra_context", {}),
        }

        checksum = self._compute_checksum(payload)

        savegame = {
            "magic": MAGIC_HEADER,
            "schema_version": "2.0.0",
            "metadata": {
                "id": str(uuid.uuid4()),
                "slot_name": slot_name,
                "title": f"Multriix Memory Cartridge [{slot_name}]",
                "description": description or f"Memory snapshot saved on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "author": author,
                "created_at": time.time(),
                "created_iso": datetime.now().isoformat(),
                "tags": tags or ["general"],
                "stats": {
                    "short_term_turns": len(short_term),
                    "long_term_facts": len(long_term),
                },
                "checksum": checksum,
            },
            "payload": payload,
        }

        dest_path = target_path if target_path else self._resolve_slot_path(slot_name)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        # Atomic write with temp file
        temp_path = f"{dest_path}.tmp_{uuid.uuid4().hex[:8]}"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(savegame, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, dest_path)

        return dest_path, savegame["metadata"]

    def inspect_savegame(self, file_or_slot: str) -> dict:
        """
        Inspect a savegame cartridge without loading it.
        Validates magic header and verifies SHA-256 checksum.
        """
        filepath = self._resolve_slot_path(file_or_slot)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Savegame not found: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception as e:
                raise SavegameError(f"Corrupted JSON in savegame {filepath}: {e}")

        # Validate Magic Header
        if data.get("magic") != MAGIC_HEADER:
            raise SavegameError(f"Invalid cartridge header: expected '{MAGIC_HEADER}', got '{data.get('magic')}'")

        meta = data.get("metadata", {})
        payload = data.get("payload", {})

        # Validate Checksum
        recorded_checksum = meta.get("checksum", "")
        actual_checksum = self._compute_checksum(payload)

        is_valid = (recorded_checksum == actual_checksum)
        if not is_valid:
            raise SavegameError(
                f"Integrity check failed! Cartridge may be corrupted or tampered with. "
                f"Expected {recorded_checksum[:12]}..., computed {actual_checksum[:12]}..."
            )

        info = dict(meta)
        info["filepath"] = filepath
        info["filesize_bytes"] = os.path.getsize(filepath)
        info["valid"] = True
        return info

    def load_savegame(
        self,
        file_or_slot: str,
        merge: bool = False,
        current_state: Optional[dict] = None
    ) -> dict:
        """
        Load a savegame cartridge.
        
        Args:
            file_or_slot: Slot name or path to .mxsave file.
            merge: If True, merges incoming facts and turns into current_state
                   instead of replacing everything.
            current_state: The current memory dict if merge=True.
            
        Returns:
            Dict containing the restored (or merged) 'short_term' and 'long_term'.
        """
        filepath = self._resolve_slot_path(file_or_slot)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Savegame not found: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate integrity
        if data.get("magic") != MAGIC_HEADER:
            raise SavegameError(f"Invalid magic header in {filepath}")

        payload = data.get("payload", {})
        meta = data.get("metadata", {})
        recorded_checksum = meta.get("checksum", "")
        if recorded_checksum != self._compute_checksum(payload):
            raise SavegameError(f"Checksum mismatch in savegame {filepath}. File is corrupted.")

        incoming_short = payload.get("short_term", [])
        incoming_long = payload.get("long_term", [])

        if not merge or not current_state:
            # Replace mode (standard savegame load)
            return {
                "short_term": incoming_short,
                "long_term": incoming_long,
                "source_metadata": meta,
            }

        # Merge mode: combine without duplicates
        existing_short = current_state.get("short_term", [])
        existing_long = current_state.get("long_term", [])

        # Merge facts: avoid duplicate facts by string text
        seen_facts = {f.get("fact", "").strip().lower() for f in existing_long if "fact" in f}
        merged_long = list(existing_long)
        for item in incoming_long:
            fact_text = item.get("fact", "").strip().lower()
            if fact_text and fact_text not in seen_facts:
                seen_facts.add(fact_text)
                merged_long.append(item)

        # Merge short-term turns: avoid identical (role, content) turns
        seen_turns = {(t.get("role", ""), t.get("content", "")) for t in existing_short}
        merged_short = list(existing_short)
        for turn in incoming_short:
            turn_key = (turn.get("role", ""), turn.get("content", ""))
            if turn_key not in seen_turns:
                seen_turns.add(turn_key)
                merged_short.append(turn)

        return {
            "short_term": merged_short,
            "long_term": merged_long,
            "source_metadata": meta,
        }

    def list_savegames(self) -> List[dict]:
        """List all available savegame cartridges across project and user directories."""
        results = []
        scanned_paths = set()

        # Scan project saves directory and user home saves directory
        dirs_to_scan = [self.saves_dir, USER_SAVES_DIR]

        for d in dirs_to_scan:
            if not os.path.exists(d):
                continue
            for fname in sorted(os.listdir(d)):
                if fname.endswith(".mxsave"):
                    full_path = os.path.join(d, fname)
                    if full_path in scanned_paths:
                        continue
                    scanned_paths.add(full_path)
                    try:
                        info = self.inspect_savegame(full_path)
                        results.append(info)
                    except Exception as e:
                        results.append({
                            "slot_name": fname[:-7],
                            "filepath": full_path,
                            "valid": False,
                            "error": str(e),
                            "filesize_bytes": os.path.getsize(full_path),
                        })
        return results

    def export_savegame(self, slot_name: str, destination_path: str) -> str:
        """Export a savegame slot to a portable external location."""
        src_path = self._resolve_slot_path(slot_name)
        if not os.path.exists(src_path):
            raise FileNotFoundError(f"Source savegame slot '{slot_name}' does not exist.")

        # Ensure destination has .mxsave extension
        if not destination_path.endswith(".mxsave"):
            destination_path += ".mxsave"

        os.makedirs(os.path.dirname(os.path.abspath(destination_path)), exist_ok=True)
        shutil.copy2(src_path, destination_path)
        return os.path.abspath(destination_path)

    def import_savegame(self, source_path: str, target_slot: Optional[str] = None) -> Tuple[str, dict]:
        """
        Import an external portable .mxsave cartridge into the local saves directory.
        """
        source_path = os.path.abspath(source_path)
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source cartridge file not found: {source_path}")

        info = self.inspect_savegame(source_path)

        slot = target_slot or info.get("slot_name") or os.path.basename(source_path).replace(".mxsave", "")
        dest_path = self._resolve_slot_path(slot)

        shutil.copy2(source_path, dest_path)
        return dest_path, info

    def delete_savegame(self, slot_name: str) -> bool:
        """Delete a savegame slot."""
        path = self._resolve_slot_path(slot_name)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False
