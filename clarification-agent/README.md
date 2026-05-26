# Clarification Agent - 需求澄清智能体

完全解耦、独立可复用的澄清 Agent 模块，可直接集成到 ShuttleFlow / OpenHands 项目中。

## 📁 目录结构

```
clarification-agent/
├── __init__.py           # 模块入口
├── models.py             # Pydantic 数据模型
├── analyzer.py           # Query 分析器
├── generator.py          # 结构化需求生成器
├── scorer.py             # 完整度评分器
├── engine.py             # 核心引擎
├── adapter.py            # 主 Agent 适配器
├── fastapi_routes.py     # FastAPI 独立路由
├── example_usage.py       # 独立使用示例
└── README.md             # 本文档
```

## 🚀 快速开始

### 方式 1：独立使用（不依赖 ShuttleFlow）

```python
import asyncio
from openai import AsyncOpenAI
from clarification_agent import (
    ClarificationAgent,
    MainAgentAdapter,
    SimpleOpenAILLMClient
)

async def main():
    llm = AsyncOpenAI(api_key="your-api-key")
    llm_client = SimpleOpenAILLMClient(llm)
    
    agent = ClarificationAgent(llm_client)
    adapter = MainAgentAdapter()
    
    state = await agent.process_initial_query("帮我做个网站")
    print(f"生成的需求: {state.current_requirement.title}")
    
    agent.confirm(state)
    main_prompt = adapter.convert_to_main_agent_input(state.current_requirement)
    print(main_prompt)

asyncio.run(main())
```

### 方式 2：集成到 ShuttleFlow / OpenHands FastAPI App

在你的现有 FastAPI 应用启动代码中：

```python
# 1. 导入澄清 Agent
from clarification_agent import (
    ClarificationAgent,
    MainAgentAdapter,
    SimpleOpenAILLMClient,
    fastapi_routes
)

# 2. 在应用启动时初始化
@app.on_event("startup")
async def startup():
    # 复用 ShuttleFlow 现有的 LLM 实例
    existing_llm = get_shuttleflow_llm()
    llm_client = SimpleOpenAILLMClient(existing_llm)
    
    clarification_agent = ClarificationAgent(llm_client)
    adapter = MainAgentAdapter()
    
    fastapi_routes.init_clarification_agent(clarification_agent, adapter)

# 3. 挂载路由到你的 FastAPI App
app.include_router(fastapi_routes.router)
```

## 📡 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/clarification/start` | 开始新的澄清会话 |
| GET | `/api/v1/clarification/{session_id}` | 获取会话状态 |
| POST | `/api/v1/clarification/{session_id}/regenerate` | 重新生成需求 |
| POST | `/api/v1/clarification/{session_id}/supplement` | 用户补充信息 |
| POST | `/api/v1/clarification/{session_id}/manual-update` | 用户手动编辑更新 |
| POST | `/api/v1/clarification/{session_id}/confirm` | 确认需求，获取主 Agent 输入 |

## 📦 依赖要求

```
pydantic >= 2.0
tenacity >= 8.0
fastapi >= 0.100
openai >= 1.0
```

## 🎯 核心特性

1. **完全解耦**：不依赖 ShuttleFlow 内部任何模块
2. **强类型**：全部使用 Pydantic v2 定义数据结构
3. **异步优先**：所有 I/O 操作使用 async/await
4. **自动重试**：tenacity 处理 LLM 格式错误
5. **四种用户操作路径**：直接确认、直接编辑、继续补充、重新生成
6. **完整度评分**：0-100 分可视化展示需求质量
7. **适配器模式**：无缝对接现有主 Agent

## 🔧 自定义 LLM 客户端

如果你的项目使用的不是 OpenAI SDK，只需继承 `BaseLLMClient`：

```python
from clarification_agent.analyzer import BaseLLMClient

class MyCustomLLMClient(BaseLLMClient):
    async def acompletion(self, messages, **kwargs):
        # 你的自定义 LLM 调用逻辑
        response = await my_llm_call(messages)
        return response.text
```
