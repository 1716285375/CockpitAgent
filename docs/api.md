# API

## Health

`GET /health`

## Readiness

`GET /ready`

返回服务可用状态、工具数量、上下文存储模式和 LLM 模式。

## Streaming Chat

`POST /v1/chat/stream`

```json
{
  "session_id": "demo",
  "message": "把空调调到22度",
  "user_id": "user_123",
  "vehicle_id": "vin_xxx"
}
```

返回 SSE 事件：`thinking`、`tool_start`、`tool_end`、`final`、`done`。

## WebSocket Chat

`WS /v1/chat/ws`

连接后发送：

```json
{
  "session_id": "demo",
  "message": "把空调调到22度",
  "user_id": "user_123",
  "vehicle_id": "vin_xxx"
}
```

服务端返回 JSON 事件：`thinking`、`tool_start`、`tool_end`、`final`、`done`。

## Admin Audit Events

`GET /v1/admin/audit/events?limit=50`

返回最近的工具调用审计事件，包含工具名、状态和耗时。

## Tool Schemas

`GET /v1/admin/tools/schemas?format=openai`

返回 OpenAI-compatible tool schema；`format=react` 返回 ReAct prompt 使用的简化 schema。

## Runtime Config

`PATCH /v1/admin/config/runtime`

```json
{
  "config": {
    "agent.max_steps": 4,
    "tools.enabled": ["weather", "ac_control"],
    "prompt.system_template": "..."
  }
}
```

将配置 payload 应用到当前进程中的 Agent executor 和 tool registry。
