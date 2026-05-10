from fastapi import APIRouter, Request
from pydantic import BaseModel
from core.pc_controller import PCController
import os

router = APIRouter()
controller = PCController()

class FileRequest(BaseModel):
    path: str
    content: str = None

@router.post("/api/control/read")
async def read_file(req: FileRequest):
    # Security: only allow reading files in current directory or specific files
    safe_path = os.path.basename(req.path)
    if req.path == "Modelfile":
        safe_path = "Modelfile"
    content = controller.read_file(safe_path)
    if isinstance(content, dict) and "error" in content:
        return content
    return {"content": content}

@router.post("/api/control/write")
async def write_file(req: FileRequest):
    safe_path = os.path.basename(req.path)
    if req.path == "Modelfile":
        safe_path = "Modelfile"
    return controller.write_file(safe_path, req.content)

@router.post("/api/control/command")
async def run_command(request: Request):
    pass

@router.get("/api/control/processes")
async def list_processes():
    pass

@router.post("/api/control/kill")
async def kill_process(request: Request):
    pass

@router.get("/api/control/stats")
async def system_stats():
    pass

@router.get("/api/control/files")
async def list_files(path: str = "C:/"):
    pass
