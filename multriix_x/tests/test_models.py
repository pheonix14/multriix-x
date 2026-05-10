import unittest
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestModels(unittest.TestCase):
    def test_ollama_handler(self):
        from models.ollama_handler import OllamaHandler
        h = OllamaHandler()
        self.assertIsNotNone(h)
        result = asyncio.run(h.health_check())
        self.assertIsInstance(result, bool)

    def test_qwen_handler(self):
        from models.qwen_handler import QwenHandler
        h = QwenHandler(use_small=True)
        self.assertFalse(h.is_loaded())

    def test_mistral_handler(self):
        from models.mistral_handler import MistralHandler
        h = MistralHandler()
        self.assertIsNotNone(h)

    def test_glm_handler(self):
        from models.glm_handler import GLMHandler
        h = GLMHandler()
        self.assertIsNotNone(h)

    def test_model_router(self):
        from models.model_router import ModelRouter
        r = ModelRouter()
        result = asyncio.run(r.list_available_models())
        self.assertIn("ollama", result)

    def test_standalone_handler(self):
        from models.standalone_handler import StandaloneHandler
        h = StandaloneHandler()
        self.assertFalse(h.loading)
