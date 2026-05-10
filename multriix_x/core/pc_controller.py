import subprocess
import os
import psutil
import platform
import shutil
import time
import base64
from datetime import datetime

try:
    import GPUtil
except ImportError:
    GPUtil = None

class PCController:
    def __init__(self):
        self.os_type = platform.system()

    def run_command(self, cmd, timeout=30):
        try:
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"error": "Command timed out", "exit_code": -1}
        except Exception as e:
            return {"error": str(e), "exit_code": -1}

    def list_dir(self, path):
        try:
            items = os.listdir(path)
            details = []
            for item in items:
                full_path = os.path.join(path, item)
                is_dir = os.path.isdir(full_path)
                details.append({
                    "name": item,
                    "path": full_path,
                    "is_dir": is_dir,
                    "size": os.path.getsize(full_path) if not is_dir else 0,
                    "modified": os.path.getmtime(full_path)
                })
            return details
        except Exception as e:
            return {"error": str(e)}

    def read_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return {"error": str(e)}

    def write_file(self, path, content):
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}

    def get_system_stats(self):
        stats = {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "cpu_cores": psutil.cpu_count(),
            "ram": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "used": psutil.virtual_memory().used,
                "percent": psutil.virtual_memory().percent
            },
            "disk": {},
            "gpu": []
        }
        
        # Disk stats
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                stats["disk"][part.mountpoint] = {
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": usage.percent
                }
            except:
                continue

        # GPU stats
        if GPUtil:
            try:
                gpus = GPUtil.getGPUs()
                for gpu in gpus:
                    stats["gpu"].append({
                        "id": gpu.id,
                        "name": gpu.name,
                        "load": gpu.load * 100,
                        "memory_total": gpu.memoryTotal,
                        "memory_used": gpu.memoryUsed,
                        "temperature": gpu.temperature
                    })
            except:
                pass
                
        return stats

    def list_processes(self):
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return sorted(processes, key=lambda x: x.get('cpu_percent', 0), reverse=True)[:20]

    def kill_process(self, pid):
        try:
            p = psutil.Process(pid)
            p.terminate()
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
