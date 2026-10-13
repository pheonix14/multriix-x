#!/usr/bin/env python3
"""
MULTRIIX X — CLI Python Bridge
Project: MULTRIIX X | Author: Pheonix14 / ZeroX
Handles direct savegame operations, status inquiries, and tests for the C++ `mx` CLI.
"""

import sys
import os
import json
import argparse
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
MULTRIXX_ROOT = os.path.dirname(HERE)
sys.path.insert(0, MULTRIXX_ROOT)

from core.memory_manager import get_memory_manager
from core.savegame_manager import SavegameManager, SavegameError
from core.port_manager import PortManager


def cmd_save(args):
    mm = get_memory_manager()
    slot = args.slot or "quicksave"
    desc = args.description or f"Snapshot created via mx CLI on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    tags = args.tags.split(",") if args.tags else ["cli", "snapshot"]

    path, meta = mm.save_slot(slot_name=slot, description=desc, tags=tags)
    print(f"\033[32m[OK]\033[0m Memory cartridge saved to slot '\033[1m{slot}\033[0m'")
    print(f"     Path     : {path}")
    print(f"     Checksum : {meta['checksum'][:16]}...")
    print(f"     Facts    : {meta['stats']['long_term_facts']}")
    print(f"     Turns    : {meta['stats']['short_term_turns']}")
    return 0


def cmd_load(args):
    mm = get_memory_manager()
    slot = args.slot_or_path
    merge = args.merge

    try:
        res = mm.load_slot(slot, merge=merge)
        meta = res.get("source_metadata", {})
        action = "Merged" if merge else "Restored"
        print(f"\033[32m[OK]\033[0m {action} memory cartridge from '\033[1m{slot}\033[0m'")
        print(f"     Title    : {meta.get('title', 'Unknown')}")
        print(f"     Author   : {meta.get('author', 'Unknown')}")
        print(f"     Facts    : {len(res.get('long_term', []))}")
        print(f"     Turns    : {len(res.get('short_term', []))}")
        return 0
    except Exception as e:
        print(f"\033[31m[ERROR]\033[0m Failed to load savegame: {e}")
        return 1


def cmd_list(args):
    mm = get_memory_manager()
    saves = mm.list_saves()

    print("\n\033[1;36m=== MULTRIIX X MEMORY CARTRIDGE INVENTORY ===\033[0m")
    if not saves:
        print("  (No savegames found. Create one using 'mx save <name>')\n")
        return 0

    print(f"  {'SLOT / NAME':<20} {'VALID':<8} {'FACTS':<8} {'TURNS':<8} {'SIZE':<10} {'CREATED'}")
    print("  " + "-" * 75)
    for s in saves:
        slot = s.get("slot_name", "unknown")
        valid_str = "\033[32mYES\033[0m" if s.get("valid") else "\033[31mCORRUPT\033[0m"
        stats = s.get("stats", {})
        facts = stats.get("long_term_facts", 0)
        turns = stats.get("short_term_turns", 0)
        size = f"{s.get('filesize_bytes', 0)} B"
        created = s.get("created_iso", "")[:19].replace("T", " ")
        print(f"  {slot:<20} {valid_str:<17} {facts:<8} {turns:<8} {size:<10} {created}")
    print()
    return 0


def cmd_info(args):
    sm = SavegameManager()
    path = args.path
    try:
        info = sm.inspect_savegame(path)
        print("\n\033[1;36m=== MEMORY CARTRIDGE TELEMETRY ===\033[0m")
        print(f"  Slot Name   : {info.get('slot_name')}")
        print(f"  Title       : {info.get('title')}")
        print(f"  Description : {info.get('description')}")
        print(f"  Author      : {info.get('author')}")
        print(f"  Tags        : {', '.join(info.get('tags', []))}")
        print(f"  Created     : {info.get('created_iso')}")
        print(f"  Checksum    : {info.get('checksum')} \033[32m[VERIFIED SHA-256]\033[0m")
        print(f"  Facts Count : {info.get('stats', {}).get('long_term_facts')}")
        print(f"  Turns Count : {info.get('stats', {}).get('short_term_turns')}")
        print(f"  File Path   : {info.get('filepath')}")
        print(f"  File Size   : {info.get('filesize_bytes')} bytes\n")
        return 0
    except Exception as e:
        print(f"\033[31m[ERROR]\033[0m Cartridge inspection failed: {e}")
        return 1


def cmd_export(args):
    mm = get_memory_manager()
    slot = args.slot
    target = args.destination
    try:
        exported = mm.export_cartridge(slot, target)
        print(f"\033[32m[OK]\033[0m Cartridge successfully exported for travel:")
        print(f"     Destination: \033[1m{exported}\033[0m")
        return 0
    except Exception as e:
        print(f"\033[31m[ERROR]\033[0m Export failed: {e}")
        return 1


def cmd_import(args):
    mm = get_memory_manager()
    source = args.source
    slot = args.slot
    try:
        info = mm.import_cartridge(source, target_slot=slot, merge=args.merge)
        print(f"\033[32m[OK]\033[0m Imported cartridge '\033[1m{info.get('slot_name')}\033[0m' successfully!")
        if args.merge:
            print(f"     Active memory merged seamlessly.")
        return 0
    except Exception as e:
        print(f"\033[31m[ERROR]\033[0m Import failed: {e}")
        return 1


def cmd_status(args):
    pm = PortManager()
    saved_port = pm.get_saved_port()
    in_use = pm.is_port_in_use(saved_port)
    mm = get_memory_manager()
    facts = len(mm.get_long_term())
    turns = len(mm.get_short_term())
    saves_count = len(mm.list_saves())

    status_str = f"\033[32mONLINE\033[0m (Port {saved_port})" if in_use else "\033[33mSTANDBY\033[0m (Ready to launch)"

    print("\n\033[1;36m=== MULTRIIX X SYSTEM STATUS ===\033[0m")
    print(f"  Core Engine    : {status_str}")
    print(f"  Active Facts   : {facts}")
    print(f"  Active Turns   : {turns}")
    print(f"  Savegame Slots : {saves_count}")
    print(f"  Root Path      : {MULTRIXX_ROOT}\n")
    return 0


def cmd_test(args):
    from tests.run_all_tests import run_all
    success = run_all()
    return 0 if success else 1


def main():
    parser = argparse.ArgumentParser(description="Multriix X CLI Bridge")
    subparsers = parser.add_subparsers(dest="command")

    # save
    p_save = subparsers.add_parser("save")
    p_save.add_argument("slot", nargs="?", default="quicksave")
    p_save.add_argument("-d", "--description", default="")
    p_save.add_argument("-t", "--tags", default="")

    # load
    p_load = subparsers.add_parser("load")
    p_load.add_argument("slot_or_path")
    p_load.add_argument("--merge", action="store_true")

    # list
    subparsers.add_parser("list")

    # info
    p_info = subparsers.add_parser("info")
    p_info.add_argument("path")

    # export
    p_export = subparsers.add_parser("export")
    p_export.add_argument("slot")
    p_export.add_argument("destination")

    # import
    p_import = subparsers.add_parser("import")
    p_import.add_argument("source")
    p_import.add_argument("slot", nargs="?", default=None)
    p_import.add_argument("--merge", action="store_true")

    # status
    subparsers.add_parser("status")

    # test
    subparsers.add_parser("test")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1

    handlers = {
        "save": cmd_save,
        "load": cmd_load,
        "list": cmd_list,
        "info": cmd_info,
        "export": cmd_export,
        "import": cmd_import,
        "status": cmd_status,
        "test": cmd_test,
    }

    handler = handlers.get(args.command)
    if handler:
        return handler(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
