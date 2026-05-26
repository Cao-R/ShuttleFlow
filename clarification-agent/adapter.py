"""
Clarification Agent - 主 Agent 适配器
将澄清后的结构化需求转换为主 Agent 可直接使用的清晰 Markdown 格式 Prompt
完全解耦，无缝对接现有 ShuttleFlow / OpenHands 主 Agent
"""

from models import ClarifiedRequirement


class MainAgentAdapter:
    """
    主 Agent 对接适配器
    核心功能：把 ClarifiedRequirement 结构化对象渲染成一份格式优美、信息完整的 Markdown 文档
    输出的内容可以直接作为消息发送给主 Agent 的 Conversation.send_message()
    不需要修改主 Agent 的任何内部逻辑，零侵入式集成
    """
    
    def convert_to_main_agent_input(self, clarified_req: ClarifiedRequirement) -> str:
        """
        将澄清后的结构化需求转换为主 Agent 可直接使用的清晰 Prompt
        输出格式：完整的 Markdown 文档，包含所有字段
        参数:
            clarified_req: ClarifiedRequirement 结构化需求对象
        返回:
            格式化后的完整 Markdown 字符串，可直接传给主 Agent
        """
        
        # 初始化结果列表，逐段拼接内容
        prompt_parts = [
            # 第一部分：任务标题
            f"# 任务: {clarified_req.title}",
            "",
            # 第二部分：详细描述
            "## 详细描述",
            clarified_req.description,
            "",
            # 第三部分：任务目标
            "## 任务目标",
        ]
        
        # 遍历 objectives，用数字序号格式化
        for i, obj in enumerate(clarified_req.objectives, 1):
            prompt_parts.append(f"{i}. {obj}")
        
        # 第四部分：工作范围 - 范围内
        prompt_parts.extend([
            "",
            "## 工作范围",
            "### 范围内（本次任务要做的内容）",
        ])
        
        # 遍历 in_scope，用列表格式化
        for item in clarified_req.in_scope:
            prompt_parts.append(f"- {item}")
        
        # 第五部分：工作范围 - 范围外
        prompt_parts.extend([
            "",
            "### 范围外（本次任务不要做的内容）",
        ])
        
        # 遍历 out_of_scope，用列表格式化
        for item in clarified_req.out_of_scope:
            prompt_parts.append(f"- {item}")
        
        # 第六部分：推荐技术栈
        prompt_parts.extend([
            "",
            "## 推荐技术栈",
        ])
        
        # 遍历 tech_stack，用列表格式化
        for tech in clarified_req.tech_stack:
            prompt_parts.append(f"- {tech}")
        
        # 第七部分：验收标准
        prompt_parts.extend([
            "",
            "## 验收标准",
        ])
        
        # 遍历 acceptance_criteria，用数字序号格式化
        for i, criteria in enumerate(clarified_req.acceptance_criteria, 1):
            prompt_parts.append(f"{i}. {criteria}")
        
        # 第八部分：执行计划
        prompt_parts.extend([
            "",
            "## 执行计划",
        ])
        
        # 遍历 execution_plan，用数字序号格式化
        for i, step in enumerate(clarified_req.execution_plan, 1):
            prompt_parts.append(f"{i}. {step}")
        
        # 第九部分：附加信息（原始 Query 和完整度分数）
        prompt_parts.extend([
            "",
            "---",
            f"原始用户输入: {clarified_req.original_query}",
            f"需求完整度分数: {clarified_req.completeness_score}/100",
        ])
        
        # 用换行把所有部分拼接成一个完整的字符串
        return "\n".join(prompt_parts)
