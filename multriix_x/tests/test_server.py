import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestServerSetup(unittest.TestCase):
    def test_imports(self):
        try:
            import server
            import run
        except ImportError:
            self.fail("Could not import server or run")
