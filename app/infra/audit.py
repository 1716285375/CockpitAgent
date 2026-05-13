import time
from dataclasses import dataclass, field
from typing import Any, Protocol
from uuid import uuid4


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
