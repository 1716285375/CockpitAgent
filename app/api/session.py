from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends

from app.auth.jwt_handler import verify_jwt
from app.context.manager import ContextManager
from app.dependencies import get_context_manager


router = APIRouter(prefix="/v1/sessions", tags=["sessions"])


@router.post("")
async def create_session(_user: dict = Depends(verify_jwt)) -> dict:
    expires_at = datetime.now(UTC) + timedelta(hours=24)
    return {"session_id": str(uuid4()), "expires_at": expires_at.isoformat()}


@router.get("/{session_id}/messages")
async def get_messages(
    session_id: str,
    limit: int = 20,
    _user: dict = Depends(verify_jwt),
    ctx: ContextManager = Depends(get_context_manager),
) -> dict:
    messages = await ctx.load(session_id)
    return {"session_id": session_id, "messages": messages[-limit:]}


@router.delete("/{session_id}")
async def clear_session(
    session_id: str,
    _user: dict = Depends(verify_jwt),
    ctx: ContextManager = Depends(get_context_manager),
) -> dict:
    await ctx.clear(session_id)
    return {"status": "ok", "session_id": session_id}

