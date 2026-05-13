import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.agent.executor import ReActExecutor
from app.auth.jwt_handler import verify_jwt
from app.auth.signature import verify_signature
from app.config.settings import Settings, get_settings
from app.context.session_lock import SessionLock
from app.dependencies import get_executor, get_session_lock


router = APIRouter(prefix="/v1/chat", tags=["chat"])


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1)
    message: str = Field(min_length=1)
    user_id: str = Field(default="anonymous")
    vehicle_id: str | None = None


def encode_sse(event_type: str, data: Any) -> str:
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/stream")
async def chat_stream(
    req: ChatRequest,
    _signature: None = Depends(verify_signature),
    user: dict = Depends(verify_jwt),
    executor: ReActExecutor = Depends(get_executor),
    session_lock: SessionLock = Depends(get_session_lock),
    settings: Settings = Depends(get_settings),
):
    acquired = await session_lock.acquire(req.session_id, settings.session_lock_ttl_seconds)
    if not acquired:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Session is already processing another request",
        )

    async def event_generator():
        try:
            metadata = {"user_id": req.user_id, "vehicle_id": req.vehicle_id, "auth_sub": user.get("sub")}
            async for event in executor.run(req.session_id, req.message, metadata=metadata):
                yield encode_sse(event.type, event.data)
            yield encode_sse("done", {"session_id": req.session_id})
        finally:
            await session_lock.release(req.session_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
