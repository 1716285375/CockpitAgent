import asyncio

from app.infra.audit import MemoryAuditSink
from app.tools import build_default_registry


def test_tool_registry_records_audit_events():
    audit_sink = MemoryAuditSink()
    registry = build_default_registry(cache_ttl_seconds=60, audit_sink=audit_sink)

    async def run():
        await registry.invoke("weather", {"city": "上海"})
        await registry.invoke("weather", {"city": "上海"})

    asyncio.run(run())

    assert [event.status for event in audit_sink.events] == ["success", "cache_hit"]
    assert audit_sink.events[0].event_type == "tool_invocation"
    assert audit_sink.events[0].metadata["tool"] == "weather"
