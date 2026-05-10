"""
NeuralDesk Backend — FastAPI App + All Routes
"""

import os
import json
import asyncio
import time
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).parent.parent

# ANSI color helpers for live terminal logging
def _g(t): return f"\033[32m{t}\033[0m"   # green
def _r(t): return f"\033[31m{t}\033[0m"   # red
def _c(t): return f"\033[36m{t}\033[0m"   # cyan
def _d(t): return f"\033[2m{t}\033[0m"    # dim


def build_app() -> FastAPI:
    app = FastAPI(title="NeuralDesk", version="2.0.0")

    from backend.config_manager import ConfigManager
    mgr = ConfigManager()
    hf_token = mgr.get_value("connection.hf_token")
    if hf_token:
        os.environ["HF_TOKEN"] = hf_token
    anthropic_key = mgr.get_value("connection.anthropic_key")
    if anthropic_key:
        os.environ["ANTHROPIC_API_KEY"] = anthropic_key

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Live terminal request logger ─────────────────────────────
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.time()
        resp = await call_next(request)
        ms = int((time.time() - start) * 1000)
        method = request.method
        path = request.url.path
        status = resp.status_code
        color = _g if status < 400 else _r
        print(f"  {_d(time.strftime('%H:%M:%S'))}  {_c(method):10s}  {color(str(status))}  {path}  {_d(str(ms)+'ms')}", flush=True)
        return resp

    # ── Static files ──────────────────────────────────────────────
    frontend_dir = ROOT / "frontend"
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    # ── Root → serve UI ──────────────────────────────────────────
    @app.get("/")
    async def root():
        return FileResponse(str(frontend_dir / "index.html"))

    @app.get("/health")
    async def health():
        return {"status": "ok", "timestamp": time.time()}

    # ─────────────────────────────────────────────────────────────
    # MODELS API
    # ─────────────────────────────────────────────────────────────

    @app.get("/api/models")
    async def list_models():
        from backend.ollama_bridge import OllamaBridge
        bridge = OllamaBridge()
        return await bridge.list_models()

    @app.post("/api/models/pull")
    async def pull_model(request: Request):
        data = await request.json()
        name = data.get("name", "")
        if not name: return {"error": "name required"}
        
        from fastapi.responses import StreamingResponse
        import httpx
        import json
        
        async def stream_pull():
            try:
                async with httpx.AsyncClient(timeout=3600) as c:
                    async with c.stream("POST", "http://127.0.0.1:11434/api/pull", json={"name": name, "stream": True}) as resp:
                        async for line in resp.aiter_lines():
                            if line.strip():
                                yield line + "\n"
            except Exception as e:
                yield json.dumps({"error": str(e)}) + "\n"
                
        return StreamingResponse(stream_pull(), media_type="application/x-ndjson")

    @app.delete("/api/models/{model_name}")
    async def delete_model(model_name: str):
        from backend.model_manager import ModelManager
        mgr = ModelManager()
        return await mgr.delete(model_name)

    @app.post("/api/models/create")
    async def create_model(request: Request):
        """Create a new model from a Modelfile string."""
        data = await request.json()
        name = data.get("name", "").strip()
        modelfile_content = data.get("modelfile", "")
        if not name or not modelfile_content:
            return {"success": False, "error": "name and modelfile required"}
        import tempfile, subprocess, asyncio
        with tempfile.NamedTemporaryFile(mode='w', suffix='.Modelfile', delete=False) as f:
            f.write(modelfile_content)
            tmppath = f.name
        def _run():
            try:
                result = subprocess.run(
                    ["ollama", "create", name, "-f", tmppath],
                    capture_output=True, text=True, timeout=300
                )
                return {"success": result.returncode == 0, "output": result.stdout[-300:]}
            except FileNotFoundError:
                return {"success": False, "error": "ollama not found"}
            except Exception as e:
                return {"success": False, "error": str(e)}
            finally:
                try: os.unlink(tmppath)
                except: pass
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _run)

    @app.get("/api/models/{model_name}/info")
    async def model_info(model_name: str):
        from backend.ollama_bridge import OllamaBridge
        bridge = OllamaBridge()
        return await bridge.model_info(model_name)

    # ─────────────────────────────────────────────────────────────
    # CONFIG API
    # ─────────────────────────────────────────────────────────────

    @app.get("/api/config")
    async def get_config():
        from backend.config_manager import ConfigManager
        return ConfigManager().load()

    @app.post("/api/config")
    async def save_config(request: Request):
        data = await request.json()
        from backend.config_manager import ConfigManager
        mgr = ConfigManager()
        mgr.save(data)
        hf_token = mgr.get_value("connection.hf_token")
        if hf_token:
            os.environ["HF_TOKEN"] = hf_token
        return {"status": "saved"}

    @app.post("/api/config/reset")
    async def reset_config():
        from backend.config_manager import ConfigManager
        cfg = ConfigManager()
        cfg.save(cfg.defaults())
        return cfg.defaults()

    # ─────────────────────────────────────────────────────────────
    # FILE MANAGER API
    # ─────────────────────────────────────────────────────────────

    @app.get("/api/files/browse")
    def browse(path: str = str(Path.home())):
        from backend.file_manager import FileManager
        return FileManager().browse(path)

    @app.post("/api/files/read")
    async def read_file(request: Request):
        data = await request.json()
        from backend.file_manager import FileManager
        return FileManager().read(data["path"])

    @app.post("/api/files/write")
    async def write_file(request: Request):
        data = await request.json()
        from backend.file_manager import FileManager
        return FileManager().write(data["path"], data["content"])

    # ─────────────────────────────────────────────────────────────
    # CHAT SESSION API
    # ─────────────────────────────────────────────────────────────

    @app.get("/api/sessions")
    def list_sessions():
        from backend.chat_session import ChatSession
        return ChatSession.list_all(str(ROOT / "data" / "chat_history"))

    @app.get("/api/sessions/{session_id}")
    def get_session(session_id: str):
        from backend.chat_session import ChatSession
        return ChatSession.load(session_id, str(ROOT / "data" / "chat_history"))

    @app.delete("/api/sessions/{session_id}")
    async def delete_session(session_id: str):
        from backend.chat_session import ChatSession
        ChatSession.delete(session_id, str(ROOT / "data" / "chat_history"))
        return {"deleted": session_id}

    # ─────────────────────────────────────────────────────────────
    # SYSTEM MONITOR API
    # ─────────────────────────────────────────────────────────────

    @app.get("/api/system")
    def system_stats():
        from backend.system_monitor import SystemMonitor
        mon = SystemMonitor()
        data = mon.snapshot()
        data["processes"] = mon.top_processes(20)
        return data

    @app.get("/api/system/processes")
    def system_processes():
        from backend.system_monitor import SystemMonitor
        return SystemMonitor().top_processes(30)

    @app.post("/api/control/kill")
    async def kill_process(request: Request):
        import psutil
        data = await request.json()
        try:
            p = psutil.Process(data["pid"])
            p.terminate()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ─────────────────────────────────────────────────────────────
    # WEBSOCKET: CHAT STREAMING
    # ─────────────────────────────────────────────────────────────

    @app.websocket("/ws/chat")
    async def ws_chat(websocket: WebSocket):
        await websocket.accept()
        from backend.ollama_bridge import OllamaBridge
        from backend.chat_session import ChatSession

        bridge = OllamaBridge()
        history_dir = str(ROOT / "data" / "chat_history")

        try:
            while True:
                raw = await websocket.receive_text()
                req = json.loads(raw)

                message = req.get("message", "")
                model = req.get("model", "qwen2.5:0.5b")
                session_id = req.get("session_id", "default")
                system = req.get("system", "You are a helpful local AI assistant.")
                temperature = float(req.get("temperature", 0.7))
                max_tokens = int(req.get("max_tokens", 2048))
                use_gpu = bool(req.get("use_gpu", True))
                context = req.get("context", [])

                # Save user turn
                ChatSession.append(session_id, "user", message, history_dir)

                full_response = []
                if model == "ALL_AI_MODE":
                    models_res = await bridge.list_models()
                    installed = [m["name"] for m in models_res.get("models", [])]
                    installed = [name for name in installed if name != "ALL_AI_MODE"]
                    
                    if not installed:
                        installed = ["qwen2.5:0.5b"]
                        
                    intro = "### 🌐 MULTRIX X — COLLABORATIVE ENSEMBLE GENERATION (ALL MODE)\nGathering insights and performing real-time knowledge synthesis across all available models.\n\n"
                    full_response.append(intro)
                    await websocket.send_json({"token": intro, "done": False})
                    
                    responses = {}
                    for idx, model_name in enumerate(installed[:3], 1):
                        prefix = f"\n\n---\n\n#### 🟢 [AI {idx}] Model: `{model_name}`\n"
                        full_response.append(prefix)
                        await websocket.send_json({"token": prefix, "done": False})
                        responses[model_name] = []
                        
                        async for chunk in bridge.chat_stream(
                            model=model_name,
                            messages=[{"role": "user", "content": message}],
                            system=system,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            use_gpu=use_gpu,
                        ):
                            if chunk.get("done"):
                                break
                            t = chunk.get("message", {}).get("content", "")
                            if t:
                                responses[model_name].append(t)
                                full_response.append(t)
                                await websocket.send_json({"token": t, "done": False})
                                
                    # Executive consensus synthesis
                    prefix_synth = f"\n\n---\n\n#### 🏆 Executive Consensus & Synthesis\n"
                    full_response.append(prefix_synth)
                    await websocket.send_json({"token": prefix_synth, "done": False})
                    
                    synthesis_prompt = f"We have queried multiple specialized AI models for the prompt: '{message}'.\nHere are their responses:\n\n"
                    for name, resp_list in responses.items():
                        synthesis_prompt += f"--- MODEL: {name} ---\n{''.join(resp_list)}\n\n"
                    synthesis_prompt += "\nCompare and analyze their contributions, check for accuracy, merge their knowledge, and write the absolute best, highly detailed final master response."
                    
                    synthesis_model = installed[0]
                    async for chunk in bridge.chat_stream(
                        model=synthesis_model,
                        messages=[{"role": "user", "content": synthesis_prompt}],
                        system="You are an elite, senior executive coordinator that synthesizes, critiques, and merges multiple AI outputs into the ultimate flawless response.",
                        temperature=temperature,
                        max_tokens=max_tokens,
                        use_gpu=use_gpu,
                    ):
                        if chunk.get("done"):
                            break
                        t = chunk.get("message", {}).get("content", "")
                        if t:
                            full_response.append(t)
                            await websocket.send_json({"token": t, "done": False})
                            
                    await websocket.send_json({"done": True, "full": "".join(full_response)})
                else:
                    async for chunk in bridge.chat_stream(
                        model=model,
                        messages=[{"role": "user", "content": message}],
                        system=system,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        use_gpu=use_gpu,
                    ):
                        if chunk.get("done"):
                            await websocket.send_json({"done": True, "full": "".join(full_response)})
                            break
                        token = chunk.get("message", {}).get("content", "")
                        if token:
                            full_response.append(token)
                            await websocket.send_json({"token": token, "done": False})

                # Save assistant turn
                assistant_text = "".join(full_response)
                
                # AGENTIC FILE ACCESS LOOP
                import re
                read_match = re.search(r"\[READ:\s*(.*?)\]", assistant_text)
                write_match = re.search(r"\[WRITE:\s*(.*?)\](.*?)\[END_WRITE\]", assistant_text, re.DOTALL)
                
                if read_match:
                    path = Path(read_match.group(1).strip().strip('"\''))
                    try:
                        if path.exists() and path.is_file():
                            file_content = path.read_text(encoding="utf-8", errors="ignore")
                            await websocket.send_json({"token": f"\n\n[SYSTEM]: Opened and read file `{path}` successfully. Characters: {len(file_content)}.", "done": False})
                            assistant_text += f"\n\n[SYSTEM]: File content of `{path}`:\n```\n{file_content}\n```"
                        else:
                            await websocket.send_json({"token": f"\n\n[SYSTEM]: File `{path}` not found.", "done": False})
                            assistant_text += f"\n\n[SYSTEM]: File `{path}` not found."
                    except Exception as ex:
                        await websocket.send_json({"token": f"\n\n[SYSTEM]: Error reading `{path}`: {ex}", "done": False})
                        assistant_text += f"\n\n[SYSTEM]: Error reading `{path}`: {ex}"
                elif write_match:
                    path = Path(write_match.group(1).strip().strip('"\''))
                    content = write_match.group(2)
                    try:
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_text(content, encoding="utf-8")
                        await websocket.send_json({"token": f"\n\n[SYSTEM]: Successfully wrote file to `{path}`.", "done": False})
                        assistant_text += f"\n\n[SYSTEM]: Successfully wrote file to `{path}`."
                    except Exception as ex:
                        await websocket.send_json({"token": f"\n\n[SYSTEM]: Error writing to `{path}`: {ex}", "done": False})
                        assistant_text += f"\n\n[SYSTEM]: Error writing to `{path}`: {ex}"

                ChatSession.append(session_id, "assistant", assistant_text, history_dir)

        except WebSocketDisconnect:
            pass
        except Exception as e:
            try:
                await websocket.send_json({"error": str(e), "done": True})
            except Exception:
                pass

    # ─────────────────────────────────────────────────────────────
    # WEBSOCKET: SYSTEM MONITOR LIVE
    # ─────────────────────────────────────────────────────────────

    @app.websocket("/ws/monitor")
    async def ws_monitor(websocket: WebSocket):
        await websocket.accept()
        from backend.system_monitor import SystemMonitor
        monitor = SystemMonitor()
        try:
            while True:
                await websocket.send_json(monitor.snapshot())
                await asyncio.sleep(2)
        except WebSocketDisconnect:
            pass

    return app
