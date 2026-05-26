"""
Clarification Agent - 核心引擎
整合所有组件，提供完整的澄清 Agent 功能
对外暴露统一的 API，支持四种用户操作路径
"""

import time
import uuid
from typing import Optional

from models import (
    AnalysisResult,
    ClarifiedRequirement,
    ClarificationState,
)
from analyzer import QueryAnalyzer, BaseLLMClient
from generator import RequirementGenerator
from scorer import CompletenessScorer


class ClarificationAgent:
    """
    澄清 Agent 核心引擎
    整合 QueryAnalyzer、RequirementGenerator、CompletenessScorer 所有组件
    提供完整的生命周期管理：从用户初始输入到最终确认
    支持四种用户操作：
    1. 直接确认
    2. 直接手动编辑
    3. 继续补充信息
    4. 重新生成
    """
    
    def __init__(self, llm_client: BaseLLMClient):
        """
        初始化澄清 Agent 核心引擎
        参数:
            llm_client: 实现了 BaseLLMClient 接口的 LLM 客户端实例
        """
        self.llm_client = llm_client
        # 初始化各个子组件
        self.analyzer = QueryAnalyzer(llm_client)
        self.generator = RequirementGenerator(llm_client)
        self.scorer = CompletenessScorer()
    
    async def process_initial_query(self, query: str) -> ClarificationState:
        """
        处理用户初始输入，生成第一版澄清需求
        完整流程：
        1. 生成唯一的 session_id
        2. 调用 QueryAnalyzer 分析用户 Query
        3. 调用 RequirementGenerator 生成第一版结构化需求
        4. 调用 CompletenessScorer 计算完整度分数
        5. 创建并返回完整的 ClarificationState
        参数:
            query: 用户最开始输入的原始自然语言 Query
        返回:
            全新的 ClarificationState 会话状态对象
        """
        # 生成全局唯一的 UUID 作为会话 ID
        session_id = str(uuid.uuid4())
        # 获取当前 Unix 时间戳作为创建时间
        now = time.time()
        
        # 第一步：分析用户原始 Query
        analysis = await self.analyzer.analyze(query)
        # 第二步：生成第一版结构化澄清需求
        requirement = await self.generator.generate(query, analysis)
        
        # 第三步：用我们的评分器重新计算实际的完整度分数
        # 覆盖 LLM 自己生成的可能不准确的分数
        actual_score = self.scorer.score(requirement)
        requirement.completeness_score = actual_score
        
        # 第四步：创建完整的会话状态对象
        state = ClarificationState(
            session_id=session_id,
            original_query=query,
            current_requirement=requirement,
            conversation_history=[],
            is_confirmed=False,
            created_at=now,
            updated_at=now
        )
        
        return state
    
    async def regenerate(
        self,
        state: ClarificationState,
        additional_context: Optional[str] = None
    ) -> ClarifiedRequirement:
        """
        重新生成需求
        用户点击"重新生成"按钮时调用
        基于原始 Query 重新走一遍分析和生成流程
        参数:
            state: 当前的 ClarificationState 会话状态
            additional_context: 可选的额外补充上下文
        返回:
            新生成的 ClarifiedRequirement 需求对象
        """
        # 重新分析用户原始 Query
        analysis = await self.analyzer.analyze(state.original_query)
        # 重新生成结构化需求
        requirement = await self.generator.generate(
            state.original_query,
            analysis,
            additional_context
        )
        
        # 重新计算实际完整度分数
        actual_score = self.scorer.score(requirement)
        requirement.completeness_score = actual_score
        
        # 更新状态中的当前需求和最后更新时间
        state.current_requirement = requirement
        state.updated_at = time.time()
        
        return requirement
    
    async def add_user_supplement(
        self,
        state: ClarificationState,
        user_message: str
    ) -> ClarifiedRequirement:
        """
        用户补充信息后更新需求
        用户点击"继续补充"按钮，输入补充信息后调用
        把用户的补充信息记录到对话历史中，然后重新生成需求
        参数:
            state: 当前的 ClarificationState 会话状态
            user_message: 用户输入的补充信息文本
        返回:
            更新后的 ClarifiedRequirement 需求对象
        """
        # 把用户的补充消息追加到对话历史中，记录时间戳
        state.conversation_history.append({
            "role": "user",
            "content": user_message,
            "timestamp": time.time()
        })
        
        # 从对话历史构建完整的补充上下文
        full_context = self._build_context_from_history(state)
        # 调用重新生成方法，传入完整的补充上下文
        new_requirement = await self.regenerate(state, full_context)
        
        # 更新最后更新时间
        state.updated_at = time.time()
        return new_requirement
    
    def update_requirement_manually(
        self,
        state: ClarificationState,
        updated_req: ClarifiedRequirement
    ) -> ClarifiedRequirement:
        """
        用户手动编辑需求，重新计算分数
        用户直接在 UI 上修改了 Markdown 内容后调用
        不经过 LLM，直接用用户编辑后的对象重新计算完整度分数
        参数:
            state: 当前的 ClarificationState 会话状态
            updated_req: 用户手动编辑后的 ClarifiedRequirement 对象
        返回:
            更新后的需求对象（分数已重新计算）
        """
        # 用评分器重新计算用户编辑后的需求的完整度分数
        new_score = self.scorer.score(updated_req)
        updated_req.completeness_score = new_score
        
        # 更新状态中的当前需求和最后更新时间
        state.current_requirement = updated_req
        state.updated_at = time.time()
        
        return updated_req
    
    def confirm(self, state: ClarificationState) -> None:
        """
        用户确认需求
        用户点击"确认并继续"按钮时调用
        标记状态为已确认，之后就可以安全地进入主 Agent 了
        参数:
            state: 当前的 ClarificationState 会话状态
        """
        state.is_confirmed = True
        state.updated_at = time.time()
    
    def _build_context_from_history(self, state: ClarificationState) -> str:
        """
        从对话历史构建补充上下文
        把所有用户补充的信息拼接成一个完整的字符串
        传给 LLM 作为额外的上下文参考
        参数:
            state: 当前的 ClarificationState 会话状态
        返回:
            拼接好的补充上下文字符串，如果没有历史则返回 None
        """
        context_parts = []
        # 遍历对话历史，只收集用户角色的消息
        for msg in state.conversation_history:
            if msg.get("role") == "user":
                context_parts.append(f"- 用户补充: {msg.get('content', '')}")
        # 如果有内容就用换行拼接，没有就返回 None
        return "\n".join(context_parts) if context_parts else None
