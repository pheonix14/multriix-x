from fastapi import APIRouter, Request
from core.config_manager import config_mgr

router = APIRouter()

@router.get("/api/config")
async def get_config():
    return config_mgr.get_all()

@router.post("/api/config/update")
async def update_config(request: Request):
    updates = await request.json()
    for section, keys in updates.items():
        if isinstance(keys, dict):
            for k, v in keys.items():
                config_mgr.set(section, k, v)
        else:
            config_mgr.set("DEFAULT", section, keys)
    return {"status": "success", "config": config_mgr.get_all()}

@router.post("/api/config/set")
async def set_config_key(request: Request):
    data = await request.json()
    section = data.get("section", "DEFAULT")
    key = data.get("key")
    value = data.get("value")
    if key:
        config_mgr.set(section, key, value)
    return {"status": "success"}
