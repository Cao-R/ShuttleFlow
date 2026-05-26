"""
Clarification Agent - 独立使用示例
展示如何在不依赖 ShuttleFlow 的情况下直接使用澄清 Agent
"""

import asyncio
from openai import AsyncOpenAI

from .analyzer import SimpleOpenAILLMClient
from .engine import ClarificationAgent
from .adapter import MainAgentAdapter


async def main():
    """独立使用示例"""
    
    # 1. 初始化 OpenAI 客户端
    llm = AsyncOpenAI(api_key="your-api-key-here")
    
    # 2. 包装为我们的抽象 LLM 客户端
    llm_client = SimpleOpenAILLMClient(llm)
    
    # 3. 创建澄清 Agent 和适配器
    clarification_agent = ClarificationAgent(llm_client)
    adapter = MainAgentAdapter()
    
    # 4. 处理用户原始 Query
    user_query = "帮我做个网站"
    print(f"用户原始输入: {user_query}")
    
    state = await clarification_agent.process_initial_query(user_query)
    
    print("\n=== 生成的澄清需求 ===")
    print(f"Session ID: {state.session_id}")
    print(f"标题: {state.current_requirement.title}")
    print(f"完整度分数: {state.current_requirement.completeness_score}/100")
    print(f"描述: {state.current_requirement.description}")
    
    # 5. 用户确认后，转换为主 Agent 输入
    clarification_agent.confirm(state)
    main_agent_prompt = adapter.convert_to_main_agent_input(state.current_requirement)
    
    print("\n=== 转换后的主 Agent Prompt ===")
    print(main_agent_prompt)


if __name__ == "__main__":
    asyncio.run(main())
