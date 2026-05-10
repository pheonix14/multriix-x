"""
MULTRIIX X — Master Test Suite
Tests all core modules. Runs until 100% pass.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

def run_all():
    print("\n" + "=" * 60)
    print("  MULTRIIX X — MASTER TEST SUITE")
    print("=" * 60)

    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 60)
    print("  MULTRIIX X TEST REPORT")
    print("=" * 60)
    print(f"  Total  : {result.testsRun}")
    print(f"  Passed : {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  Failed : {len(result.failures) + len(result.errors)}")

    if result.wasSuccessful():
        print("  Status : ALL SYSTEMS GO - PRODUCTION READY")
    else:
        print("  Status : FAILURES DETECTED - SEE ABOVE")
        for fail in result.failures + result.errors:
            print(f"\n  [FAIL] {fail[0]}")
            print(f"  {fail[1][:300]}")

    print("=" * 60 + "\n")
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
