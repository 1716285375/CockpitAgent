from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.jwt_handler import verify_jwt
from app.config.settings import Settings, get_settings, safe_settings
from app.dependencies import get_audit_sink, get_registry
from app.infra.audit import MemoryAuditSink
from app.tools.registry import ToolRegistry


router = APIRouter(prefix="/v1/admin", tags=["admin"])


class ToolToggleRequest(BaseModel):
    enabled: bool


@router.get("/tools")
async def list_tools(_user: dict = Depends(verify_jwt), registry: ToolRegistry = Depends(get_registry)) -> dict:
    return {"tools": registry.list_tools()}


@router.get("/tools/schemas")
async def list_tool_schemas(
    format: str = "openai",
    _user: dict = Depends(verify_jwt),
    registry: ToolRegistry = Depends(get_registry),
) -> dict:
    if format == "react":
        return {"tools": registry.list_schemas()}
    if format == "openai":
        return {"tools": registry.list_openai_tools()}
    return {"tools": registry.list_tools()}


@router.patch("/tools/{tool_name}")
async def toggle_tool(
    tool_name: str,
    req: ToolToggleRequest,
    _user: dict = Depends(verify_jwt),
    registry: ToolRegistry = Depends(get_registry),
) -> dict:
    registry.set_enabled(tool_name, req.enabled)
    return {"status": "ok", "tool": tool_name, "enabled": req.enabled}


@router.get("/config")
async def get_config(_user: dict = Depends(verify_jwt), settings: Settings = Depends(get_settings)) -> dict:
    return {"config": safe_settings(settings)}


@router.get("/audit/events")
async def list_audit_events(
    limit: int = 50,
    _user: dict = Depends(verify_jwt),
    audit_sink: MemoryAuditSink = Depends(get_audit_sink),
) -> dict:
    events = audit_sink.events[-limit:]
    return {
        "events": [
            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "status": event.status,
                "duration_ms": event.duration_ms,
                "metadata": event.metadata,
                "created_at": event.created_at,
            }
            for event in events
        ]
    }
