"""NeuralDesk — System Monitor: CPU, RAM, GPU, disk stats."""

import time
import psutil
from typing import Optional


class SystemMonitor:
    """Collects system resource snapshots using psutil."""

    def __init__(self):
        # Prime CPU percent (first call always returns 0.0)
        psutil.cpu_percent(interval=None)

    def snapshot(self) -> dict:
        """Return a full system stats snapshot."""
        cpu_pct = psutil.cpu_percent(interval=None)
        per_core = psutil.cpu_percent(interval=None, percpu=True)
        freq = psutil.cpu_freq()
        ram = psutil.virtual_memory()
        boot_time = psutil.boot_time()

        # Disk - primary partition
        disk_info = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disk_info.append({
                    "path": part.mountpoint,
                    "used_gb": round(usage.used / 1e9, 2),
                    "total_gb": round(usage.total / 1e9, 2),
                    "percent": usage.percent,
                })
            except (PermissionError, OSError):
                continue

        gpu_data = self._get_gpu()

        return {
            "cpu": {
                "percent": cpu_pct,
                "per_core": per_core,
                "freq_mhz": round(freq.current) if freq else None,
                "cores": psutil.cpu_count(logical=False),
                "threads": psutil.cpu_count(logical=True),
            },
            "ram": {
                "used_gb": round(ram.used / 1e9, 2),
                "total_gb": round(ram.total / 1e9, 2),
                "available_gb": round(ram.available / 1e9, 2),
                "percent": ram.percent,
            },
            "gpu": gpu_data,
            "disk": disk_info[:4],  # max 4 drives
            "uptime_seconds": int(time.time() - boot_time),
            "timestamp": time.time(),
        }

    def _get_gpu(self) -> Optional[dict]:
        """Try to get NVIDIA GPU stats via GPUtil."""
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                g = gpus[0]
                return {
                    "name": g.name,
                    "vram_used_gb": round(g.memoryUsed / 1024, 2),
                    "vram_total_gb": round(g.memoryTotal / 1024, 2),
                    "util_percent": g.load * 100,
                    "temp_c": g.temperature,
                }
        except Exception:
            pass
        return None

    def top_processes(self, n: int = 20) -> list:
        """Return top N processes by CPU usage."""
        procs = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info", "status"]):
            try:
                procs.append({
                    "pid": p.info["pid"],
                    "name": p.info["name"],
                    "cpu_percent": p.info["cpu_percent"],
                    "ram_mb": round(p.info["memory_info"].rss / 1e6, 1),
                    "status": p.info["status"],
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return sorted(procs, key=lambda x: x["cpu_percent"], reverse=True)[:n]
