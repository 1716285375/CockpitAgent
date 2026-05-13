# API

## Health

`GET /health`

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
