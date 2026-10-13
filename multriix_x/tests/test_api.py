import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import fastapi
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

class TestAPIEndpoints(unittest.TestCase):
    @unittest.skipUnless(HAS_FASTAPI, "FastAPI is not installed in the test environment")
    def test_routers_exist(self):
        from api.chat_api import router as chat_router
        from api.brain_api import router as brain_router
        from api.control_api import router as control_router
        from api.config_api import router as config_router
        from api.model_api import router as model_router
        self.assertIsNotNone(chat_router)
        self.assertIsNotNone(brain_router)
        self.assertIsNotNone(control_router)
        self.assertIsNotNone(config_router)
        self.assertIsNotNone(model_router)
