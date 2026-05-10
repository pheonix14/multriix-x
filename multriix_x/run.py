"""
MULTRIIX X — One-click launcher with watchdog, health checks, and model download.
"""

import os
import sys
import subprocess
import time
import webbrowser

# Change CWD to script's own directory so all relative paths work
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Load .env
from dotenv import load_dotenv
load_dotenv(".env")

from core.port_manager import PortManager


def print_banner():
    print("""
  ============================================================
  MULTRIIX X - ZEROX EDITION  |  PHEONIX14 
  ============================================================""")


def check_requirements():
    print("[INFO] Checking core packages...")
    required = ["fastapi", "uvicorn", "httpx", "psutil", "transformers", "torch", "dotenv"]
    missing = []
    import importlib.util
    for pkg in required:
        print(f"  -> checking {pkg}...")
        check_pkg = pkg if pkg != "dotenv" else "dotenv"
        spec = importlib.util.find_spec(check_pkg)
        if spec is None:
            missing.append(pkg)
    if missing:
        print(f"[INFO] Installing: {', '.join(missing)}")
        subprocess.run([sys.executable, "-m", "pip", "install"] + missing, check=False)
    else:
        print("[PASS] All core packages present.")


def check_ollama():
    print("[INFO] Checking Ollama...")
    import httpx
    try:
        r = httpx.get("http://127.0.0.1:11434/api/tags", timeout=3)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            print(f"[PASS] Ollama online. Models: {models or 'none'}")
            return True, models
    except Exception:
        pass
    print("[WARN] Ollama not running. Will use standalone HuggingFace mode.")
    return False, []


def pull_missing_models(available_models: list):
    wanted = ["qwen2.5:7b", "mistral:7b"]
    for model in wanted:
        base = model.split(":")[0]
        if not any(base in m for m in available_models):
            print(f"[INFO] Pulling {model} via Ollama...")
            try:
                subprocess.run(["ollama", "pull", model], check=True, timeout=600)
                print(f"[PASS] {model} pulled.")
            except Exception as e:
                print(f"[WARN] Could not pull {model}: {e}")


def pull_glm3():
    print("[INFO] Pulling GLM 3 AI Model completely...")
    try:
        from models.glm_handler import get_glm_handler
        h = get_glm_handler()
        h.load()
        print("[PASS] GLM 3 downloaded and loaded.")
    except Exception as e:
        print(f"[WARN] Failed to download GLM 3: {e}")

def run_tests():
    print("[INFO] Running system tests...")
    result = subprocess.run(
        [sys.executable, "-u", "tests/run_all_tests.py"],
        capture_output=False,
    )
    return result.returncode == 0


def main():
    print_banner()

    if sys.version_info < (3, 10):
        print("[FAIL] Python 3.10+ required.")
        sys.exit(1)

    check_requirements()

    ollama_alive, available_models = check_ollama()
    if ollama_alive:
        pull_missing_models(available_models)

    pull_glm3()

    print("[INFO] Tests skipped for faster startup.")

    pm = PortManager()
    port = pm.find_free_port()

    print(f"\n[INFO] Launching MULTRIIX X on port {port} with Watchdog...\n")
    print(f"  Dashboard : http://localhost:{port}/frontend/index.html")
    print(f"  API Docs  : http://localhost:{port}/docs")
    print(f"  Health    : http://localhost:{port}/health\n")

    from core.watchdog import Watchdog
    dog = Watchdog("server.py", port)
    dog.start()

    time.sleep(5)
    webbrowser.open(f"http://localhost:{port}/frontend/index.html")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down MULTRIIX X...")
        dog.stop()


if __name__ == "__main__":
    main()
