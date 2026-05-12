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

