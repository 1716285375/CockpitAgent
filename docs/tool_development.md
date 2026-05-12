# Tool Development

新增工具步骤：

1. 继承 `app.tools.base.BaseTool`
2. 使用 Pydantic `BaseModel` 定义 `args_schema`
3. 实现 `async execute(...) -> dict`
4. 在 `app/tools/__init__.py` 的 `build_default_registry` 中注册

注册中心会负责参数校验、超时控制、启停开关和异步调用。

