# Cockpit Agent

智能座舱大模型 Agent 交互系统 MVP，实现了 `dev.md` 中的核心链路：

- FastAPI 服务与 SSE 流式对话接口
- ReAct 执行器、输出解析、工具编排
- 装饰器/注册中心式 Tool 系统与参数校验
- 内存会话上下文、滑动窗口压缩
- JWT 与 HMAC 签名基础能力
- 本地启发式 LLM fallback，未配置真实模型时也能运行演示

## Quick Start

```bash
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

```bash
curl -N -X POST http://localhost:8000/v1/chat/stream ^
  -H "Content-Type: application/json" ^
  -d "{\"session_id\":\"demo\",\"message\":\"把空调调到22度，然后查一下上海天气\"}"
```

配置真实 OpenAI-compatible 模型：

```bash
set LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
set LLM_API_KEY=sk-xxx
set LLM_MODEL=qwen-max
```

## Test

```bash
pytest
```

