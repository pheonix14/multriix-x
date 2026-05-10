import time
import subprocess
import sys
import os
import httpx
import threading

class Watchdog:
    def __init__(self, target_script, port, interval=10):
        self.target_script = target_script
        self.port = port
        self.interval = interval
        self.process = None
        self.running = False
        self.lock = threading.Lock()

    def start(self):
        self.running = True
        print(f"[WATCHDOG] Monitoring {self.target_script} on port {self.port}...")
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def _start_process(self):
        with self.lock:
            if self.process:
                try:
                    self.process.terminate()
                except:
                    pass
            print(f"[WATCHDOG] Launching process: {self.target_script}")
            self.process = subprocess.Popen([sys.executable, self.target_script])

    def _monitor_loop(self):
        self._start_process()
        
        while self.running:
            time.sleep(self.interval)
            
            # Check if process is still alive
            if self.process.poll() is not None:
                print(f"[WATCHDOG] Process {self.target_script} died. Restarting...")
                self._start_process()
                continue

            # Check health via API
            try:
                resp = httpx.get(f"http://localhost:{self.port}/health", timeout=2)
                if resp.status_code != 200:
                    print(f"[WATCHDOG] Health check failed ({resp.status_code}). Restarting...")
                    self._start_process()
            except Exception as e:
                print(f"[WATCHDOG] Server unreachable: {e}. Restarting...")
                self._start_process()

    def stop(self):
        self.running = False
        with self.lock:
            if self.process:
                self.process.terminate()
