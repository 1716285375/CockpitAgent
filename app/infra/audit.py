import json
import time
from dataclasses import dataclass, field
from typing import Any, Protocol
from uuid import uuid4

from app.tools.preference.user_preference import parse_mysql_dsn


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    event_type: str
    status: str
    duration_ms: float
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


class AuditSink(Protocol):
    async def record(self, event: AuditEvent) -> None:
        ...


class MemoryAuditSink:
    def __init__(self):
        self.events: list[AuditEvent] = []

    async def record(self, event: AuditEvent) -> None:
        self.events.append(event)


class MySQLAuditSink:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.connection_kwargs = parse_mysql_dsn(dsn)

    async def record(self, event: AuditEvent) -> None:
        import aiomysql

        conn = await aiomysql.connect(**self.connection_kwargs)
        try:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """
                    INSERT INTO audit_events (event_id, event_type, status, duration_ms, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        event.event_id,
                        event.event_type,
                        event.status,
                        event.duration_ms,
                        json.dumps(event.metadata, ensure_ascii=False),
                    ),
                )
                await conn.commit()
        finally:
            conn.close()


def build_audit_event(
    event_type: str,
    status: str,
    started_at: float,
    metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    return AuditEvent(
        event_id=str(uuid4()),
        event_type=event_type,
        status=status,
        duration_ms=(time.perf_counter() - started_at) * 1000,
        metadata=metadata or {},
    )
