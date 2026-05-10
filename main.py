"""
MULTRIIX X — Master Entry Point
Author: Pheonix14 / ZeroX

Usage:
    python main.py              → Launch NeuralDesk (AI Manager + Chat UI)
    python main.py --legacy     → Launch original MULTRIIX X server
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

def main():
    args = sys.argv[1:]
    legacy_mode = '--legacy' in args

    if legacy_mode:
        # Original MULTRIIX X server (TRON/ARES interface)
        print("[MULTRIIX X] Starting legacy TRON server...")
        os.chdir(os.path.join(HERE, "multriix_x"))
        sys.path.insert(0, os.path.join(HERE, "multriix_x"))
        from run import main as run_main
        run_main()
    else:
        # NEW: NeuralDesk — clean AI manager (default)
        neuraldesk_dir = os.path.join(HERE, "multriix_x", "neuraldesk")
        os.chdir(neuraldesk_dir)
        sys.path.insert(0, neuraldesk_dir)
        from app import main as nd_main
        nd_main()


if __name__ == "__main__":
    main()
