"""
MULTRIIX X — Main Server
Smart FastAPI server with auto port-switching, WebSockets, and full AI integration.
"""

import asyncio
import json
import os
import sys
import time

# Load .env first
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from core.port_manager import PortManager
from core.config_manager import ConfigManager
from core.pc_controller import PCController
from core.brain_engine import BrainEngine
from core.memory_manager import get_memory_manager
from core.session_manager import get_session_manager
from core.model_mixer import get_mixer
from models.model_router import get_router

# ── App Setup ──────────────────────────────────────────────────────────────────
app = FastAPI(title="MULTRIIX X", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Core Services ──────────────────────────────────────────────────────────────
config_mgr = ConfigManager()
pc_ctrl = PCController()
brain_eng = BrainEngine()
memory_mgr = get_memory_manager()
session_mgr = get_session_manager()
mixer = get_mixer()
router = get_router()

# ── Static Files ───────────────────────────────────────────────────────────────
_frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.isdir(_frontend_dir):
    app.mount("/frontend", StaticFiles(directory=_frontend_dir), name="frontend")

_react_dist = os.path.join(os.path.dirname(__file__), "react_app", "dist")
if os.path.isdir(_react_dist):
    app.mount("/app", StaticFiles(directory=_react_dist, html=True), name="react")

# ── REST Endpoints ─────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "MULTRIIX X ONLINE", "version": "1.0.0", "author": "ZeroX / PHEONIX14 "}

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": time.time()}

# ── Config API ─────────────────────────────────────────────────────────────────

@app.get("/api/config")
async def get_config():
    return config_mgr.config

@app.post("/api/config/update")
async def update_config(request: Request):
    data = await request.json()
    config_mgr.update_bulk(data)
    return {"status": "success"}

@app.post("/api/config/set")
async def set_config_key(request: Request):
    data = await request.json()
    config_mgr.update(data["section"], data["key"], data["value"])
    return {"status": "success"}

# ── PC Control API ─────────────────────────────────────────────────────────────

@app.post("/api/control/command")
async def run_command(request: Request):
    data = await request.json()
    cmd = data.get("command", "")
    timeout = data.get("timeout", 30)
    return pc_ctrl.run_command(cmd, timeout)

@app.get("/api/control/processes")
async def list_processes():
    return pc_ctrl.list_processes()

@app.post("/api/control/kill")
async def kill_process(request: Request):
    data = await request.json()
    return pc_ctrl.kill_process(data["pid"])

@app.get("/api/control/stats")
async def system_stats():
    return pc_ctrl.get_system_stats()

@app.get("/api/control/files")
async def list_files(path: str = "C:/"):
    return pc_ctrl.list_dir(path)

@app.post("/api/control/read")
async def read_file(request: Request):
    data = await request.json()
    return {"content": pc_ctrl.read_file(data["path"])}

@app.post("/api/control/write")
async def write_file(request: Request):
    data = await request.json()
    return pc_ctrl.write_file(data["path"], data["content"])

# ── Memory API ─────────────────────────────────────────────────────────────────

@app.get("/api/memory")
async def get_memory(session_id: str = "default"):
    return {
        "short_term": memory_mgr.get_short_term(session_id),
        "long_term": memory_mgr.get_long_term(),
    }

@app.post("/api/memory/inject")
async def inject_memory(request: Request):
    data = await request.json()
    entry = memory_mgr.inject_memory(data["fact"], data.get("tags", []))
    return entry

@app.delete("/api/memory/{memory_id}")
async def delete_memory(memory_id: str):
    ok = memory_mgr.delete_memory(memory_id)
    return {"success": ok}

@app.post("/api/memory/clear")
async def clear_memory(request: Request):
    data = await request.json()
    session_id = data.get("session_id", "default")
    memory_mgr.clear_short_term(session_id)
    return {"status": "cleared"}

# ── Model API ──────────────────────────────────────────────────────────────────

@app.get("/api/models")
async def list_models():
    return await router.list_available_models()

@app.post("/api/models/pull")
async def pull_model(request: Request):
    data = await request.json()
    model_name = data.get("model")
    from models.ollama_handler import get_ollama_handler
    handler = get_ollama_handler()
    results = []
    async for chunk in handler.pull_model(model_name):
        results.append(chunk)
    return {"status": "done", "log": results[-3:] if results else []}

@app.post("/api/mixer/config")
async def set_mixer_config(request: Request):
    data = await request.json()
    if "ratios" in data:
        mixer.set_ratios(data["ratios"])
    if "mode" in data:
        mixer.set_mode(data["mode"])
    if "enabled" in data:
        mixer.enabled = data["enabled"]
    return mixer.get_config()

@app.get("/api/mixer/config")
async def get_mixer_config():
    return mixer.get_config()

# ── Session API ────────────────────────────────────────────────────────────────

@app.get("/api/sessions")
async def list_sessions():
    return session_mgr.list_sessions()

@app.post("/api/sessions/create")
async def create_session():
    s = session_mgr.create_session()
    return s.to_dict()

# ── WebSocket: Chat ────────────────────────────────────────────────────────────

@app.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            req = json.loads(raw)

            prompt = req.get("message", "")
            session_id = req.get("session_id", "default")
            model = req.get("model", "auto")
            temperature = float(req.get("temperature", 0.7))
            max_tokens = int(req.get("max_tokens", 512))
            mix_mode = req.get("mix", False)
            mix_ratios = req.get("mix_ratios", {"qwen": 0.7, "mistral": 0.3})

            session = session_mgr.get_or_create(session_id)
            system = config_mgr.get("SYSTEM", "system_prompt") or session.system_prompt

            # Inject memory context
            mem_ctx = memory_mgr.get_context_string(session_id)
            if mem_ctx:
                system = system + "\n\n" + mem_ctx

            memory_mgr.add_turn("user", prompt, session_id)
            brain_eng.start_generation()

            start_time = time.time()
            token_count = 0
            full_response = []

            try:
                if mix_mode and mixer.enabled:
                    mixer.set_ratios(mix_ratios)
                    gen = mixer.generate(router, prompt, system, temperature, max_tokens)
                else:
                    gen = router.generate(prompt, system, model, temperature, max_tokens)

                async for chunk in gen:
                    token = chunk.get("response", "")
                    if token:
                        token_count += 1
                        full_response.append(token)
                        # Print to terminal
                        sys.stdout.write(token)
                        sys.stdout.flush()

                        elapsed = time.time() - start_time
                        tps = token_count / elapsed if elapsed > 0 else 0
                        brain_eng.update_token(token, tps)

                    payload = {
                        "token": token,
                        "done": chunk.get("done", False),
                        "active_model": chunk.get("active_model", model),
                        "tps": chunk.get("tps", 0),
                    }
                    if chunk.get("done"):
                        print("\n")  # New line in terminal at the end
                        payload["stats"] = chunk.get("stats", {
                            "tps": token_count / max(time.time() - start_time, 0.001),
                            "total_tokens": token_count,
                        })

                    await websocket.send_json(payload)

            except Exception as e:
                await websocket.send_json({"error": str(e), "done": True})

            brain_eng.stop_generation()
            memory_mgr.add_turn("assistant", "".join(full_response), session_id)
            session.message_count += 1

    except WebSocketDisconnect:
        pass

# ── WebSocket: Brain ───────────────────────────────────────────────────────────

@app.websocket("/ws/brain")
async def ws_brain(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = brain_eng.get_brain_data()
            await websocket.send_json(data)
            await asyncio.sleep(1 / config_mgr.get("UI", "brain_fps") if config_mgr.get("UI", "brain_fps") else 0.033)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

# ── WebSocket: Stats ───────────────────────────────────────────────────────────

@app.websocket("/ws/stats")
async def ws_stats(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            stats = pc_ctrl.get_system_stats()
            await websocket.send_json(stats)
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass

# ── WebSocket: Logs ────────────────────────────────────────────────────────────

_log_buffer = []

@app.websocket("/ws/logs")
async def ws_logs(websocket: WebSocket):
    await websocket.accept()
    try:
        last_index = 0
        while True:
            if last_index < len(_log_buffer):
                for entry in _log_buffer[last_index:]:
                    await websocket.send_json(entry)
                last_index = len(_log_buffer)
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass

# ── Entry Point ────────────────────────────────────────────────────────────────

def start():
    pm = PortManager(
        start_port=config_mgr.get("SERVER", "port_start") or 7860,
        max_port=config_mgr.get("SERVER", "port_max") or 7900,
    )
    port = pm.find_free_port()

    print("""
  ============================================================
  MULTRIIX X - ZEROX EDITION v1.0.0
  ============================================================""")

    print("[*] Checking model connections...")
    try:
        from models.ollama_handler import get_ollama_handler
        loop = asyncio.get_event_loop()
        alive = loop.run_until_complete(get_ollama_handler().health_check())
        if alive:
            print("[+] Ollama connection OK.")
        else:
            print("[-] Ollama connection offline.")
    except Exception as e:
        print(f"[-] Model check failed: {e}")

    print("[*] Loading configuration from config.json...")
    config_mgr.load_config()

    print("[*] Starting Brain Engine background thread...")
    # Brain engine runs passively on generate, no dedicated thread needed unless polling
    
    print("[*] Starting System Stats monitor thread...")
    # PC stats are fetched dynamically, no dedicated thread needed unless logging

    print(f"  MULTRIIX X ONLINE — http://localhost:{port}")
    print(f"  Dashboard  : http://localhost:{port}/frontend/index.html")
    print(f"  API Docs   : http://localhost:{port}/docs")
    print(f"  Health     : http://localhost:{port}/health")
    print("  ============================================================\n")

    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    start()
