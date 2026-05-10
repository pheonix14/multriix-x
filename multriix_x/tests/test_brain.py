import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestBrain(unittest.TestCase):
    def test_brain_data_structure(self):
        from core.brain_engine import BrainEngine
        be = BrainEngine()
        data = be.get_brain_data()
        self.assertIn("nodes", data)
        self.assertIn("connections", data)
        self.assertIn("thinking", data)

    def test_generation_toggle(self):
        from core.brain_engine import BrainEngine
        be = BrainEngine()
        be.start_generation()
        self.assertTrue(be.get_brain_data()["thinking"])
        be.stop_generation()
        self.assertFalse(be.get_brain_data()["thinking"])
