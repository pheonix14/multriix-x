import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import fastapi
    import dotenv
    HAS_SERVER_DEPS = True
except ImportError:
    HAS_SERVER_DEPS = False

class TestServerSetup(unittest.TestCase):
    @unittest.skipUnless(HAS_SERVER_DEPS, "Server dependencies (fastapi, python-dotenv) not installed")
    def test_imports(self):
        import server
        import run
        self.assertIsNotNone(server)
        self.assertIsNotNone(run)
