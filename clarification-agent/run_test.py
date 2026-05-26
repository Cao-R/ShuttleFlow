"""
澄清 Agent - 交互式测试脚本
支持完整的人机交互流程：
1. 直接确认
2. 继续补充信息  
3. 重新生成
4. 退出
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def load_env():
    """手动加载 .env 文件"""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


def print_separator():
    print("\n" + "=" * 80 + "\n")


def print_menu():
    print("请选择操作：")
    print("  [1] 直接确认需求")
    print("  [2] 继续补充信息")
    print("  [3] 重新生成需求")
    print("  [4] 退出")
    print()


async def main():
    load_env()
    
    from analyzer import BaseLLMClient
    from engine import ClarificationAgent
    
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-4")
    
    if not api_key:
        print("[ERROR] OPENAI_API_KEY not found!")
        return
    
    from openai import AsyncOpenAI
    
    class LLMClient(BaseLLMClient):
        def __init__(self):
            self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
            self.model = model
        
        async def acompletion(self, messages, **kwargs):
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.1),
                max_tokens=kwargs.get("max_tokens", 2048)
            )
            return response.choices[0].message.content or ""
    
    agent = ClarificationAgent(LLMClient())
    
    print("=" * 80)
    print("[CLARIFICATION AGENT] 交互式测试")
    print("=" * 80)
    
    query = input("请输入您的需求：")
    if not query.strip():
        query = "帮我做个网站"
    
    print(f"\n正在分析需求: {query}...")
    
    state = await agent.process_initial_query(query)
    req = state.current_requirement
    
    while True:
        print_separator()
        print("[需求分析结果]")
        print(f"标题: {req.title}")
        print(f"意图: {req.intent_type.value}")
        print(f"完整度: {req.completeness_score}/100")
        print("\n[描述]")
        print(req.description)
        print("\n[目标]")
        for i, obj in enumerate(req.objectives, 1):
            print(f"  {i}. {obj}")
        
        print_separator()
        print_menu()
        
        choice = input("请输入选择 (1-4): ").strip()
        
        if choice == "1":
            print("\n[确认需求]")
            print("正在生成主 Agent 输入格式...")
            agent.confirm(state)
            
            from adapter import MainAgentAdapter
            adapter = MainAgentAdapter()
            prompt = adapter.convert_to_main_agent_input(req)
            
            print_separator()
            print("[主 Agent 输入]")
            print("-" * 80)
            print(prompt)
            print("-" * 80)
            
            # 保存到文件
            output_file = os.path.join(os.path.dirname(__file__), "final_requirement.txt")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(prompt)
            print(f"\n[INFO] 需求已保存到: {output_file}")
            print("\n[SUCCESS] 需求确认完成！")
            break
            
        elif choice == "2":
            print("\n[补充信息]")
            supplement = input("请输入补充信息：")
            if supplement.strip():
                print("正在更新需求...")
                req = await agent.add_user_supplement(state, supplement)
                print("需求已更新！")
            else:
                print("未输入补充信息")
                
        elif choice == "3":
            print("\n[重新生成]")
            print("正在重新生成需求...")
            req = await agent.regenerate(state)
            print("需求已重新生成！")
            
        elif choice == "4":
            print("\n[退出]")
            print("感谢使用澄清 Agent！")
            break
            
        else:
            print("\n[ERROR] 无效输入，请输入 1-4")


if __name__ == "__main__":
    asyncio.run(main())
