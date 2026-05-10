"""
NeuralDesk — Master Test Runner
Run: python tests/run_tests.py
"""

import sys
import os
import time
import traceback

# Add parent to path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# ANSI
def green(t): return f"\033[32m{t}\033[0m"
def red(t):   return f"\033[31m{t}\033[0m"
def yellow(t):return f"\033[33m{t}\033[0m"
def bold(t):  return f"\033[1m{t}\033[0m"
def dim(t):   return f"\033[2m{t}\033[0m"
def cyan(t):  return f"\033[36m{t}\033[0m"

if sys.platform == "win32":
    import ctypes
    ctypes.windll.kernel32.SetConsoleMode(ctypes.windll.kernel32.GetStdHandle(-11), 7)

# ─────────────────────────────────────────────
RESULTS = {"passed": 0, "failed": 0, "errors": []}

def run_test(name, fn, retries=3):
    for attempt in range(retries):
        try:
            fn()
            RESULTS["passed"] += 1
            print(f"    {green('OK')}  {name}")
            return
        except AssertionError as e:
            if attempt < retries - 1:
                time.sleep(0.3)
                continue
            RESULTS["failed"] += 1
            RESULTS["errors"].append((name, str(e)))
            print(f"    {red('FAIL')}  {name}  {dim(str(e))}")
            return
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(0.3)
                continue
            RESULTS["failed"] += 1
            RESULTS["errors"].append((name, str(e)))
            print(f"    {red('ERR ')}  {name}  {dim(str(e))}")
            return

def suite(name):
    print(f"\n  {cyan(bold(name))}")

# ─────────────────────────────────────────────
# CONFIG MANAGER TESTS
# ─────────────────────────────────────────────
def test_config_manager():
    suite("Config Manager")
    import tempfile, json
    from backend.config_manager import ConfigManager, DEFAULTS

    tmp = tempfile.mktemp(suffix=".json")

    def test_load_defaults():
        cm = ConfigManager(tmp)
        cfg = cm.load()
        assert "chat" in cfg, "missing 'chat' key"
        assert "ui" in cfg, "missing 'ui' key"

    def test_save_reload():
        cm = ConfigManager(tmp)
        cm.set_value("chat.temperature", 1.23)
        cm2 = ConfigManager(tmp)
        val = cm2.get_value("chat.temperature")
        assert abs(float(val) - 1.23) < 0.01, f"expected 1.23 got {val}"

    def test_reset():
        cm = ConfigManager(tmp)
        cm.set_value("chat.temperature", 9.99)
        defaults = cm.reset_to_defaults()
        assert defaults["chat"]["temperature"] == DEFAULTS["chat"]["temperature"]

    def test_invalid_json_recovery():
        # Write corrupt JSON
        with open(tmp, "w") as f:
            f.write("{not valid json!!!")
        cm = ConfigManager(tmp)
        cfg = cm.load()
        assert "chat" in cfg, "should recover to defaults"

    run_test("load_default_config", test_load_defaults)
    run_test("save_and_reload",     test_save_reload)
    run_test("reset_to_defaults",   test_reset)
    run_test("invalid_json_recovery", test_invalid_json_recovery)

    try: os.unlink(tmp)
    except: pass


# ─────────────────────────────────────────────
# FILE MANAGER TESTS
# ─────────────────────────────────────────────
def test_file_manager():
    suite("File Manager")
    import tempfile
    from backend.file_manager import FileManager

    fm = FileManager()
    tmp_dir = tempfile.mkdtemp()
    tmp_file = os.path.join(tmp_dir, "test_nd.txt")

    def test_list_home():
        result = fm.browse(str(os.path.expanduser("~")))
        assert "items" in result, f"browse failed: {result}"
        assert isinstance(result["items"], list)

    def test_read_requirements():
        req = os.path.join(ROOT, "requirements.txt")
        if not os.path.exists(req):
            return  # Skip if no file
        result = fm.read(req)
        assert "content" in result, f"read failed: {result}"
        assert len(result["content"]) > 0

    def test_write_and_verify():
        result = fm.write(tmp_file, "hello neuraldesk")
        assert result.get("success"), f"write failed: {result}"
        read_back = fm.read(tmp_file)
        assert read_back["content"] == "hello neuraldesk"

    def test_backup_created():
        fm.write(tmp_file, "version 1")
        fm.write(tmp_file, "version 2")
        bak = tmp_file + ".bak"
        assert os.path.exists(bak), ".bak file not created"
        content = open(bak).read()
        assert "version 1" in content

    def test_blocked_path():
        result = fm.read("C:\\Windows\\System32\\drivers\\etc\\hosts")
        # Either returns content (ok to read hosts) or returns error — should not crash
        assert isinstance(result, dict)

    run_test("list_home",           test_list_home)
    run_test("read_requirements",   test_read_requirements)
    run_test("write_and_verify",    test_write_and_verify)
    run_test("backup_created",      test_backup_created)
    run_test("blocked_path_safe",   test_blocked_path)


# ─────────────────────────────────────────────
# CHAT SESSION TESTS
# ─────────────────────────────────────────────
def test_chat_session():
    suite("Chat Session")
    import tempfile
    from backend.chat_session import ChatSession

    tmp_dir = tempfile.mkdtemp()

    def test_new_session():
        s = ChatSession.create_new(tmp_dir)
        assert "id" in s
        assert isinstance(s["id"], str) and len(s["id"]) > 0

    def test_save_message():
        ChatSession.append("test_sess", "user", "hello", tmp_dir)
        data = ChatSession.load("test_sess", tmp_dir)
        assert len(data["messages"]) == 1
        assert data["messages"][0]["content"] == "hello"

    def test_load_history():
        ChatSession.append("hist_sess", "user", "msg1", tmp_dir)
        ChatSession.append("hist_sess", "assistant", "reply1", tmp_dir)
        data = ChatSession.load("hist_sess", tmp_dir)
        assert len(data["messages"]) == 2

    def test_export_txt():
        ChatSession.append("export_sess", "user", "export test", tmp_dir)
        txt = ChatSession.export_txt("export_sess", tmp_dir)
        assert "export test" in txt

    def test_delete_session():
        ChatSession.append("del_sess", "user", "to delete", tmp_dir)
        ChatSession.delete("del_sess", tmp_dir)
        p = os.path.join(tmp_dir, "del_sess.json")
        assert not os.path.exists(p)

    run_test("new_session",    test_new_session)
    run_test("save_message",   test_save_message)
    run_test("load_history",   test_load_history)
    run_test("export_txt",     test_export_txt)
    run_test("delete_session", test_delete_session)


# ─────────────────────────────────────────────
# OLLAMA BRIDGE TESTS (graceful offline)
# ─────────────────────────────────────────────
def test_ollama_bridge():
    suite("Ollama Bridge")
    import asyncio
    from backend.ollama_bridge import OllamaBridge

    bridge = OllamaBridge()

    def test_check_running():
        alive = asyncio.run(bridge.health_check())
        assert isinstance(alive, bool)

    def test_list_models():
        result = asyncio.run(bridge.list_models())
        assert isinstance(result, dict)
        assert "online" in result
        assert "models" in result

    def test_invalid_model_graceful():
        async def _gen():
            chunks = []
            async for c in bridge.chat_stream("nonexistent:model999",
                                              [{"role":"user","content":"hi"}]):
                chunks.append(c)
                if c.get("done") or c.get("error"):
                    break
            return chunks
        chunks = asyncio.run(_gen())
        # Should return error dict, not crash
        assert isinstance(chunks, list)

    run_test("check_running",         test_check_running)
    run_test("list_models",           test_list_models)
    run_test("invalid_model_graceful",test_invalid_model_graceful)


# ─────────────────────────────────────────────
# SYSTEM MONITOR TESTS
# ─────────────────────────────────────────────
def test_system_monitor():
    suite("System Monitor")
    from backend.system_monitor import SystemMonitor

    mon = SystemMonitor()

    def test_snapshot_keys():
        s = mon.snapshot()
        assert "cpu" in s
        assert "ram" in s
        assert "disk" in s
        assert "uptime_seconds" in s

    def test_cpu_values():
        s = mon.snapshot()
        assert 0 <= s["cpu"]["percent"] <= 100

    def test_ram_values():
        s = mon.snapshot()
        assert s["ram"]["total_gb"] > 0
        assert s["ram"]["percent"] >= 0

    def test_top_processes():
        procs = mon.top_processes(5)
        assert isinstance(procs, list)
        assert len(procs) <= 5

    run_test("snapshot_keys",   test_snapshot_keys)
    run_test("cpu_values",      test_cpu_values)
    run_test("ram_values",      test_ram_values)
    run_test("top_processes",   test_top_processes)


# ─────────────────────────────────────────────
# MAIN RUNNER
# ─────────────────────────────────────────────
def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    print(f"\n{bold('=' * 44)}")
    print(f"  NeuralDesk -- Test Suite")
    print(f"  multriix_x  |  Pheonix14 / ZeroX")
    print(f"{bold('=' * 44)}")

    test_config_manager()
    test_file_manager()
    test_chat_session()
    test_ollama_bridge()
    test_system_monitor()

    total = RESULTS["passed"] + RESULTS["failed"]
    print(f"\n{bold('=' * 44)}")
    print(f"  {bold('RESULTS')}")
    print(f"  Total:   {total}")
    print(f"  Passed:  {green(str(RESULTS['passed']))} {'OK' if RESULTS['failed'] == 0 else ''}")
    print(f"  Failed:  {red(str(RESULTS['failed'])) if RESULTS['failed'] else green('0')}")

    if RESULTS["errors"]:
        print(f"\n  {bold(red('Failures:'))}")
        for name, err in RESULTS["errors"]:
            print(f"    - {name}: {dim(err[:100])}")

    if RESULTS["failed"] == 0:
        print(f"\n  {bold(green('Status:  READY TO LAUNCH!'))} 🚀")
    else:
        print(f"\n  {bold(yellow('Status:  FIX FAILURES ABOVE'))}")

    print(f"{bold('=' * 44)}\n")
    sys.exit(0 if RESULTS["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
