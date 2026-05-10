from fastapi import APIRouter, Request
from models.model_router import get_router

router = APIRouter()

@router.get("/api/models")
async def list_models():
    router_instance = get_router()
    models = await router_instance.list_available_models()
    return models

@router.post("/api/models/pull")
async def pull_model(request: Request):
    data = await request.json()
    model = data.get("model")
    # Stub for now
    return {"status": "pulling", "model": model}

@router.post("/api/mixer/config")
async def set_mixer_config(request: Request):
    pass

@router.get("/api/mixer/config")
async def get_mixer_config():
    pass
