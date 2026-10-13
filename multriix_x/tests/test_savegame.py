import unittest
import sys
import os
import tempfile
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.savegame_manager import SavegameManager, SavegameError
from core.memory_manager import MemoryManager


class TestSavegameManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="mx_saves_test_")
        self.tmp_mem = tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json")
        self.tmp_mem.write("[]")
        self.tmp_mem.close()

        self.sm = SavegameManager(saves_dir=self.test_dir)
        self.memory = MemoryManager(short_term_limit=10, memory_file=self.tmp_mem.name)
        # Inject the custom savegame manager into memory
        self.memory._savegame_mgr = self.sm

    def tearDown(self):
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        if os.path.exists(self.tmp_mem.name):
            os.remove(self.tmp_mem.name)

    def test_create_and_inspect_savegame(self):
        self.memory.inject_memory("Multriix supports neural orchestration", tags=["ai", "core"])
        self.memory.add_turn("user", "Hello Multriix", session_id="s1")
        self.memory.add_turn("assistant", "Greetings, Architect.", session_id="s1")

        path, meta = self.memory.save_slot("mission_alpha", description="Initial setup", tags=["launch"])
        self.assertTrue(os.path.exists(path))
        self.assertEqual(meta["slot_name"], "mission_alpha")
        self.assertEqual(meta["stats"]["long_term_facts"], 1)
        self.assertEqual(meta["stats"]["short_term_turns"], 2)

        info = self.sm.inspect_savegame("mission_alpha")
        self.assertTrue(info["valid"])
        self.assertEqual(info["checksum"], meta["checksum"])
        self.assertGreater(info["filesize_bytes"], 0)

    def test_load_savegame_replace(self):
        self.memory.inject_memory("Original memory point")
        self.memory.save_slot("state_1")

        # Clear active memory and add different things
        self.memory.clear_all()
        self.memory.inject_memory("Totally different topic")
        self.assertEqual(len(self.memory.get_long_term()), 1)
        self.assertEqual(self.memory.get_long_term()[0]["fact"], "Totally different topic")

        # Load state_1
        self.memory.load_slot("state_1", merge=False)
        long_term = self.memory.get_long_term()
        self.assertEqual(len(long_term), 1)
        self.assertEqual(long_term[0]["fact"], "Original memory point")

    def test_load_savegame_merge(self):
        # Save state A
        self.memory.inject_memory("Knowledge A: Python optimization", tags=["lang"])
        self.memory.add_turn("user", "Turn 1", session_id="s1")
        self.memory.save_slot("state_a")

        # Create state B
        self.memory.clear_all()
        self.memory.inject_memory("Knowledge B: Rust memory safety", tags=["lang"])
        self.memory.inject_memory("Knowledge A: Python optimization", tags=["lang"])  # Duplicate!
        self.memory.add_turn("user", "Turn 2", session_id="s2")

        # Merge state A into active state B
        self.memory.load_slot("state_a", merge=True)

        long_term = self.memory.get_long_term()
        # Knowledge A should NOT be duplicated
        facts = [f["fact"] for f in long_term]
        self.assertIn("Knowledge A: Python optimization", facts)
        self.assertIn("Knowledge B: Rust memory safety", facts)
        self.assertEqual(len(facts), 2)

        # Both turns should be preserved
        turns = self.memory.get_short_term("s1") + self.memory.get_short_term("s2")
        self.assertEqual(len(turns), 2)

    def test_checksum_tampering_detection(self):
        self.memory.inject_memory("Secure secret blueprint")
        path, _ = self.memory.save_slot("secure_slot")

        # Intentionally tamper with the file payload
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        data["payload"]["long_term"][0]["fact"] = "MALICIOUSLY TAMPERED FACT"

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        # Loading or inspecting should raise SavegameError due to checksum failure
        with self.assertRaises(SavegameError) as ctx:
            self.memory.load_slot("secure_slot")
        self.assertIn("Checksum mismatch", str(ctx.exception))

    def test_quick_save_and_quick_load(self):
        self.memory.inject_memory("Quicksave checkpoint fact")
        self.memory.quick_save(description="Checkpoint before operation")

        self.memory.clear_all()
        self.assertEqual(len(self.memory.get_long_term()), 0)

        self.memory.quick_load()
        self.assertEqual(len(self.memory.get_long_term()), 1)
        self.assertEqual(self.memory.get_long_term()[0]["fact"], "Quicksave checkpoint fact")

    def test_export_and_import_cartridge(self):
        self.memory.inject_memory("Travel Memory for foreign device", tags=["travel", "portable"])
        self.memory.save_slot("origin_slot")

        export_target = os.path.join(self.test_dir, "portable_travel_cartridge.mxsave")
        exported_path = self.memory.export_cartridge("origin_slot", export_target)
        self.assertTrue(os.path.exists(exported_path))

        # Import into another slot name
        imported_info = self.memory.import_cartridge(exported_path, target_slot="imported_slot")
        self.assertEqual(imported_info["slot_name"], "origin_slot")

        # Load imported slot
        self.memory.clear_all()
        self.memory.load_slot("imported_slot")
        self.assertEqual(self.memory.get_long_term()[0]["fact"], "Travel Memory for foreign device")

    def test_list_saves(self):
        self.memory.save_slot("slot_1", description="First slot")
        self.memory.save_slot("slot_2", description="Second slot")

        saves = self.memory.list_saves()
        slot_names = [s.get("slot_name") for s in saves]
        self.assertIn("slot_1", slot_names)
        self.assertIn("slot_2", slot_names)
