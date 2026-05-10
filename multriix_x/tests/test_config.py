import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestConfigAndCore(unittest.TestCase):
    def test_load_defaults(self):
        from core.config_manager import ConfigManager
        cm = ConfigManager("_test_config.json")
        self.assertIn("IDENTITY", cm.config)
        if os.path.exists("_test_config.json"):
            os.remove("_test_config.json")

    def test_live_update(self):
        from core.config_manager import ConfigManager
        cm = ConfigManager("_test_config2.json")
        cm.update("IDENTITY", "ai_name", "TEST_AI")
        self.assertEqual(cm.get("IDENTITY", "ai_name"), "TEST_AI")
        if os.path.exists("_test_config2.json"):
            os.remove("_test_config2.json")

    def test_find_free_port(self):
        from core.port_manager import PortManager
        pm = PortManager(start_port=9990, max_port=9999)
        port = pm.find_free_port()
        self.assertTrue(9990 <= port <= 9999)

    def test_memory_add_and_retrieve(self):
        from core.memory_manager import MemoryManager
        mm = MemoryManager()
        mm.add_turn("user", "Hello", "test_session")
        turns = mm.get_short_term("test_session")
        self.assertEqual(len(turns), 1)

    def test_session_create(self):
        from core.session_manager import SessionManager
        sm = SessionManager()
        s = sm.create_session("test_sess")
        self.assertEqual(s.id, "test_sess")

    def test_model_mixer_ratios(self):
        from core.model_mixer import ModelMixer
        mm = ModelMixer()
        mm.set_ratios({"qwen": 3, "mistral": 1})
        self.assertAlmostEqual(sum(mm.mix_ratios.values()), 1.0, places=5)
