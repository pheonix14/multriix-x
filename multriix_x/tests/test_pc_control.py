import unittest
import sys
import os
import tempfile

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
        test_dir = tempfile.gettempdir()
        items = pc.list_dir(test_dir)
        self.assertIsInstance(items, list)

    def test_file_read_write(self):
        from core.pc_controller import PCController
        pc = PCController()
        with tempfile.NamedTemporaryFile("w+", delete=False) as tf:
            tf_path = tf.name
        try:
            write_res = pc.write_file(tf_path, "multriix_test_payload")
            self.assertTrue(write_res.get("success", False))
            content = pc.read_file(tf_path)
            self.assertEqual(content, "multriix_test_payload")
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)
