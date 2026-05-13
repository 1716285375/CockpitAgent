# Architecture

当前 MVP 按 `dev.md` 分为：

- `app/api`: FastAPI HTTP/SSE 接口
- `app/agent`: ReAct 执行器与输出解析
- `app/llm`: OpenAI-compatible 流式客户端与本地 fallback
- `app/tools`: 工具注册中心和座舱工具
- `app/context`: 会话上下文与摘要压缩
- `app/auth`: JWT 与 HMAC 签名

Redis、MySQL、Nacos 预留在配置层，当前默认使用内存实现保证本地可运行。

Docker Compose can start Redis, MySQL, and Nacos for an integrated local environment. MySQL schema initialization lives in `docker/mysql/init.sql`.
