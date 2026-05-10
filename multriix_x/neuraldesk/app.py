"""
NeuralDesk — One-Command Launcher (MULTRIIX X)
Project: MULTRIIX X | Author: Pheonix14 / ZeroX
Run: python app.py
"""

import os
import sys
import subprocess
import time
import webbrowser
import importlib.util
import socket
import threading

# ── Force UTF-8 on Windows ─────────────────────────────────────────
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

# ── ANSI Color helpers (work on Windows 10+ with VT mode) ──────────
def _enable_ansi():
    """Enable ANSI escape codes on Windows."""
    if sys.platform == "win32":
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

def _c(text, code): return f"\033[{code}m{text}\033[0m"
def green(t):  return _c(t, "32")
def red(t):    return _c(t, "31")
def yellow(t): return _c(t, "33")
def blue(t):   return _c(t, "34")
def cyan(t):   return _c(t, "36")
def bold(t):   return _c(t, "1")
def dim(t):    return _c(t, "2")

def ok(msg):   print(f"  {green('[OK]')}    {msg}")
def fail(msg): print(f"  {red('[FAIL]')}  {msg}")
def info(msg): print(f"  {cyan('[INFO]')}  {msg}")
def warn(msg): print(f"  {yellow('[WARN]')}  {msg}")
def step(msg): print(f"\n{bold(blue(msg))}")

def _clickable_link(url):
    """Return an ANSI hyperlink (works in modern terminals)."""
    return f"\033]8;;{url}\033\\{cyan(url)}\033]8;;\033\\"


# ── STEP 1: BANNER ─────────────────────────────────────────────────
def _banner():
    _enable_ansi()
    print(f"""
{bold(blue('  ============================================'))}
  {bold('MULTRIIX X')}  v1.0  |  {dim('MULTRIIX X by Pheonix14')}
{bold(blue('  ============================================'))}
""")


# ── STEP 2: PYTHON VERSION ─────────────────────────────────────────
def _check_python():
    step("STEP 1 — Checking Python version")
    v = sys.version_info
    if v < (3, 10):
        fail(f"Python 3.10+ required. You have {v.major}.{v.minor}")
        fail("Download: https://www.python.org/downloads/")
        sys.exit(1)
    ok(f"Python {v.major}.{v.minor}.{v.micro}")


# ── STEP 3: AUTO-INSTALL PACKAGES ──────────────────────────────────
REQUIRED_PACKAGES = {
    "fastapi":         "fastapi>=0.110.0",
    "uvicorn":         "uvicorn[standard]>=0.29.0",
    "httpx":           "httpx>=0.27.0",
    "psutil":          "psutil>=5.9.0",
    "dotenv":          "python-dotenv>=1.0.0",
    "websockets":      "websockets>=12.0",
    "aiofiles":        "aiofiles>=23.2.0",
}

def _ensure_packages():
    step("STEP 2 — Checking packages")
    missing = []
    for imp_name, pip_spec in REQUIRED_PACKAGES.items():
        if importlib.util.find_spec(imp_name) is None:
            missing.append(pip_spec)
            warn(f"Missing: {imp_name}")
        else:
            ok(f"{imp_name}")

    if missing:
        info(f"Installing {len(missing)} package(s)...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet"] + missing,
            capture_output=True, text=True
        )
        if result.returncode != 0:
            fail("pip install failed:\n" + result.stderr[:500])
            sys.exit(1)
        ok("All packages installed")
    else:
        ok("All packages present")


# ── STEP 4: CHECK OLLAMA ───────────────────────────────────────────
def _get_ollama_path():
    # Check default Windows path
    win_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Ollama", "ollama.exe")
    if os.path.exists(win_path):
        return win_path
    return "ollama"

def _check_ollama():
    step("STEP 3 — Checking Ollama")
    try:
        import httpx
        r = httpx.get("http://127.0.0.1:11434/api/tags", timeout=1.5)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            ok(f"Ollama online — {len(models)} model(s) installed")
            return True, models
    except Exception:
        pass

    warn("Ollama not detected. Attempting to start it...")
    ollama_exe = _get_ollama_path()
    try:
        subprocess.Popen([ollama_exe, "serve"],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
        for _ in range(15):
            time.sleep(1)
            try:
                import httpx
                r = httpx.get("http://127.0.0.1:11434/api/tags", timeout=1.0)
                if r.status_code == 200:
                    ok("Ollama started successfully")
                    return True, []
            except Exception:
                pass
        warn("Ollama did not start in time.")
        warn("Please install Ollama: https://ollama.com")
        warn("Chat will not work until Ollama is running.")
        return False, []
    except FileNotFoundError:
        warn("Ollama binary not found — please install from https://ollama.com")
        return False, []


# ── STEP 5: CHECK MODELS ───────────────────────────────────────────
def _check_models(ollama_alive: bool, models: list):
    step("STEP 4 — Checking AI models")
    if not ollama_alive:
        warn("Skipping model check (Ollama offline)")
        return

    if not models:
        info("No models installed. Pulling a default model...")
        info("Downloading qwen2.5:0.5b (small, fast, good for testing)...")
        ollama_exe = _get_ollama_path()
        try:
            subprocess.run([ollama_exe, "pull", "qwen2.5:0.5b"], timeout=600)
            ok("qwen2.5:0.5b downloaded and ready!")
        except FileNotFoundError:
            warn("ollama CLI not found — cannot pull model")
        except subprocess.TimeoutExpired:
            warn("Download timed out")
    else:
        for m in models[:5]:
            ok(f"Model ready: {m}")
        if len(models) > 5:
            ok(f"  ...and {len(models)-5} more")


# ── STEP 6: FIND FREE PORT ─────────────────────────────────────────
def _find_port(start=3000, end=3099) -> int:
    step("STEP 5 — Finding port")
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if s.connect_ex(("localhost", port)) != 0:
                if port != start:
                    ok(f"Port {start} busy → using {port}")
                else:
                    ok(f"Using port {port}")
                return port
    raise RuntimeError("No free port found in range 3000-3099")


# ── STEP 7: LAUNCH SERVER ──────────────────────────────────────────
def _launch_server(port: int):
    step("STEP 6 — Starting server")

    # Save port for other processes
    data_dir = os.path.join(ROOT, "data")
    os.makedirs(data_dir, exist_ok=True)
    with open(os.path.join(data_dir, ".port"), "w") as f:
        f.write(str(port))

    from backend.server import build_app
    import uvicorn

    app = build_app()

    server_config = uvicorn.Config(
        app, host="127.0.0.1", port=port, log_level="warning"
    )
    server = uvicorn.Server(server_config)

    # Run in thread so we can continue
    t = threading.Thread(target=server.run, daemon=True)
    t.start()

    # Wait up to 8 seconds for /health
    info("Waiting for server to be ready...")
    import httpx
    for _ in range(16):
        time.sleep(0.5)
        try:
            r = httpx.get(f"http://localhost:{port}/health", timeout=1)
            if r.status_code == 200:
                ok("Server is ready!")
                return server, t
        except Exception:
            pass

    warn("Server did not respond in time — check for errors above")
    return server, t


# ── STEP 8: OPEN BROWSER + KEEP ALIVE ─────────────────────────────
def _open_and_wait(port: int):
    url = f"http://localhost:{port}"

    print(f"""
{green('  +---------------------------------------+')}
{green('  |')}  {bold(green('MULTRIIX X is running!'))}                {green('|')}
{green('  |')}  {bold('Open:')}  {_clickable_link(url)}  {green('|')}
{green('  |')}  Press {bold('Ctrl+C')} to stop                  {green('|')}
{green('  +---------------------------------------+')}
""")

    # Open browser
    def _open_browser():
        time.sleep(0.5)
        webbrowser.open(url)
    threading.Thread(target=_open_browser, daemon=True).start()

    # Live log: print real-time request info
    info("Live activity log (requests will appear here):")
    print(dim("  ─" * 30))

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n\n  {yellow('MULTRIIX X stopped.')} Goodbye!\n")
        sys.exit(0)


# ── MAIN ───────────────────────────────────────────────────────────
def main():
    _banner()
    _check_python()
    _ensure_packages()
    ollama_alive, models = _check_ollama()
    _check_models(ollama_alive, models)
    port = _find_port()
    _launch_server(port)
    _open_and_wait(port)


if __name__ == "__main__":
    main()
