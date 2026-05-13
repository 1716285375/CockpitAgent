import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.agent.executor import ReActExecutor
from app.auth.jwt_handler import verify_jwt
from app.auth.rate_limit import RateLimiter
from app.auth.signature import verify_signature
from app.config.settings import Settings, get_settings
from app.context.session_lock import SessionLock
from app.dependencies import get_executor, get_rate_limiter, get_session_lock


router = APIRouter(prefix="/v1/chat", tags=["chat"])


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1)
    message: str = Field(min_length=1)
    user_id: str = Field(default="anonymous")
    vehicle_id: str | None = None


class ChatWebSocketRequest(BaseModel):
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
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
    settings: Settings = Depends(get_settings),
):
    if len(req.message) > settings.chat_max_message_chars:
        raise HTTPException(
            status_code=413,
            detail="Message is too long",
        )

    if settings.rate_limit_enabled:
        key = f"chat:{user.get('sub') or req.user_id}"
        limit = await rate_limiter.check(key, settings.rate_limit_requests, settings.rate_limit_window_seconds)
        if not limit.allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(limit.reset_seconds)},
            )

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
        finally:
            await session_lock.release(req.session_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.websocket("/ws")
async def chat_websocket(
    websocket: WebSocket,
    executor: ReActExecutor = Depends(get_executor),
    session_lock: SessionLock = Depends(get_session_lock),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
    settings: Settings = Depends(get_settings),
):
    await websocket.accept()
    try:
        payload = await websocket.receive_json()
        req = ChatWebSocketRequest(**payload)
    except Exception:
        await websocket.send_json({"event": "error", "data": {"message": "Invalid websocket payload"}})
        await websocket.close(code=1003)
        return

    if len(req.message) > settings.chat_max_message_chars:
        await websocket.send_json({"event": "error", "data": {"message": "Message is too long"}})
        await websocket.close(code=1009)
        return

    if settings.rate_limit_enabled:
        limit = await rate_limiter.check(
            f"chat:{req.user_id}",
            settings.rate_limit_requests,
            settings.rate_limit_window_seconds,
        )
        if not limit.allowed:
            await websocket.send_json(
                {
                    "event": "error",
                    "data": {"message": "Rate limit exceeded", "retry_after": limit.reset_seconds},
                }
            )
            await websocket.close(code=1013)
            return

    acquired = await session_lock.acquire(req.session_id, settings.session_lock_ttl_seconds)
    if not acquired:
        await websocket.send_json(
            {"event": "error", "data": {"message": "Session is already processing another request"}}
        )
        await websocket.close(code=1013)
        return

    try:
        metadata = {"user_id": req.user_id, "vehicle_id": req.vehicle_id, "auth_sub": None}
        async for event in executor.run(req.session_id, req.message, metadata=metadata):
            await websocket.send_json({"event": event.type, "data": event.data})
    except WebSocketDisconnect:
        return
    finally:
        await session_lock.release(req.session_id)
        await websocket.close()
