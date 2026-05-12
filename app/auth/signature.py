import base64
import hashlib
import hmac
import time

from fastapi import Depends, Header, HTTPException, Request, status

from app.auth.nonce import MemoryNonceStore, NonceStore, RedisNonceStore
from app.config.settings import Settings, get_settings


_memory_nonce_store = MemoryNonceStore()
_redis_nonce_stores: dict[str, RedisNonceStore] = {}


def get_nonce_store(settings: Settings = Depends(get_settings)) -> NonceStore:
    if settings.redis_url.startswith("redis://") or settings.redis_url.startswith("rediss://"):
        if settings.redis_url not in _redis_nonce_stores:
            _redis_nonce_stores[settings.redis_url] = RedisNonceStore(settings.redis_url)
        return _redis_nonce_stores[settings.redis_url]
    return _memory_nonce_store


async def verify_signature(
    request: Request,
    x_timestamp: str | None = Header(default=None, alias="X-Timestamp"),
    x_nonce: str | None = Header(default=None, alias="X-Nonce"),
    x_signature: str | None = Header(default=None, alias="X-Signature"),
    settings: Settings = Depends(get_settings),
) -> None:
    if not settings.signature_enabled:
        return

    if not settings.hmac_secret:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="HMAC secret is not configured")
    if not x_timestamp or not x_nonce or not x_signature:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing signature headers")

    try:
        timestamp = int(x_timestamp)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid timestamp") from exc

    if abs(time.time() - timestamp) > settings.signature_window_seconds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Signature timestamp expired")

    body = await request.body()
    body_hash = hashlib.sha256(body).hexdigest()
    string_to_sign = "\n".join([request.method.upper(), request.url.path, x_timestamp, x_nonce, body_hash])
    digest = hmac.new(settings.hmac_secret.encode(), string_to_sign.encode(), hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode()
    if not hmac.compare_digest(expected, x_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    nonce_store = get_nonce_store(settings)
    if not await nonce_store.mark_seen(x_nonce, settings.signature_window_seconds):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Replay nonce")
