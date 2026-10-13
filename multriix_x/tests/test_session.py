import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.session_manager import SessionManager

class TestSessionManager(unittest.TestCase):
    def setUp(self):
        self.mgr = SessionManager()

    def test_session_lifecycle(self):
        sess = self.mgr.create_session("test_sess_1")
        self.assertEqual(sess.id, "test_sess_1")
        
        fetched = self.mgr.get_session("test_sess_1")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.model, "auto")

        # Update session
        sess.update(model="llama3", temperature=0.2)
        self.assertEqual(sess.model, "llama3")
        self.assertEqual(sess.temperature, 0.2)

        # Listing
        sessions = self.mgr.list_sessions()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["id"], "test_sess_1")

        # Deletion
        self.assertTrue(self.mgr.delete_session("test_sess_1"))
        self.assertIsNone(self.mgr.get_session("test_sess_1"))

    def test_get_or_create(self):
        s1 = self.mgr.get_or_create("dynamic_sess")
        s2 = self.mgr.get_or_create("dynamic_sess")
        self.assertEqual(s1.id, s2.id)

    def test_cleanup_old(self):
        sess = self.mgr.create_session("old_sess")
        sess.last_active -= 5000  # simulate expired session
        removed = self.mgr.cleanup_old(max_age_seconds=100)
        self.assertEqual(removed, 1)
        self.assertIsNone(self.mgr.get_session("old_sess"))
