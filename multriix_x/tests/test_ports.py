import unittest
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.port_manager import PortManager

class TestPortManager(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile("w+", delete=False)
        self.tmp.close()
        self.pm = PortManager(start_port=18500, max_port=18550, port_file=self.tmp.name)

    def tearDown(self):
        if os.path.exists(self.tmp.name):
            os.remove(self.tmp.name)

    def test_port_lifecycle(self):
        free_port = self.pm.find_free_port()
        self.assertGreaterEqual(free_port, 18500)
        self.assertLessEqual(free_port, 18550)

        saved = self.pm.get_saved_port()
        self.assertEqual(saved, free_port)
