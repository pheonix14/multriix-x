import unittest
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.memory_manager import MemoryManager

class TestMemoryManager(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json")
        self.tmp.write("[]")
        self.tmp.close()
        self.memory = MemoryManager(short_term_limit=5, memory_file=self.tmp.name)

    def tearDown(self):
        if os.path.exists(self.tmp.name):
            os.remove(self.tmp.name)

    def test_short_term_turns(self):
        self.memory.add_turn("user", "Hello", session_id="s1")
        self.memory.add_turn("assistant", "Hi there", session_id="s1")
        turns = self.memory.get_short_term("s1")
        self.assertEqual(len(turns), 2)
        self.assertEqual(turns[0]["content"], "Hello")
        self.assertEqual(turns[1]["content"], "Hi there")

    def test_persistent_memory_injection_and_search(self):
        entry = self.memory.inject_memory("User prefers Python and Rust", tags=["tech", "pref"])
        self.assertIn("id", entry)
        long_term = self.memory.get_long_term()
        self.assertEqual(len(long_term), 1)

        # Search by keyword
        res = self.memory.search_memory("Python")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["id"], entry["id"])

        # Search by tag
        res_tag = self.memory.search_memory("", tag="tech")
        self.assertEqual(len(res_tag), 1)

        # Non-matching search
        res_none = self.memory.search_memory("Cobol")
        self.assertEqual(len(res_none), 0)

    def test_context_string_generation(self):
        self.memory.inject_memory("Special API key configured")
        self.memory.add_turn("user", "What is the status?", session_id="sess_a")
        context = self.memory.get_context_string(session_id="sess_a")
        self.assertIn("PERSISTENT MEMORIES", context)
        self.assertIn("Special API key configured", context)
        self.assertIn("What is the status?", context)

    def test_delete_memory(self):
        entry = self.memory.inject_memory("Temporary note")
        self.assertTrue(self.memory.delete_memory(entry["id"]))
        self.assertEqual(len(self.memory.get_long_term()), 0)
        self.assertFalse(self.memory.delete_memory("non-existent-id"))
