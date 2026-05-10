import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestPCControl(unittest.TestCase):
    def test_system_stats(self):
        from core.pc_controller import PCController
        pc = PCController()
        stats = pc.get_system_stats()
        self.assertIn("cpu_percent", stats)
        self.assertIn("ram", stats)

    def test_run_command(self):
        from core.pc_controller import PCController
        pc = PCController()
        result = pc.run_command("echo MULTRIIX_TEST")
        self.assertIn("MULTRIIX_TEST", result.get("stdout", ""))

    def test_list_dir(self):
        from core.pc_controller import PCController
        pc = PCController()
        items = pc.list_dir("C:/")
        self.assertIsInstance(items, list)
