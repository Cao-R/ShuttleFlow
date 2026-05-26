"""
Clarification Agent - Pydantic 数据模型
完全独立，不依赖 ShuttleFlow 内部任何模块
所有模型都使用 Pydantic v2 进行强类型约束，确保数据结构的正确性
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class IntentType(str, Enum):
    """
    意图分类枚举
    将用户的任务自动归类为预定义的几种类型，便于后续生成针对性的需求文档
    """
    WEB_DEVELOPMENT = "web_development"
    CODE_REFACTOR = "code_refactor"
    BUG_FIX = "bug_fix"
    DOCUMENTATION = "documentation"
    OTHER = "other"


class AnalysisResult(BaseModel):
    """
    Query 分析结果数据模型
    存储 LLM 对用户原始输入的智能分析输出
    """
    # 禁止传入未定义的额外字段，保证数据结构严格性
    model_config = ConfigDict(extra="forbid")
    
    intent_type: IntentType = Field(..., description="意图分类，识别用户任务属于哪一类")
    extracted_entities: List[str] = Field(default_factory=list, description="从 Query 中提取的关键实体，如技术栈、文件名等")
    missing_info: List[str] = Field(default_factory=list, description="用户没有提供的关键信息清单")
    ambiguous_points: List[str] = Field(default_factory=list, description="Query 中存在的潜在歧义点")


class ClarifiedRequirement(BaseModel):
    """
    结构化的澄清后需求数据模型
    这是澄清 Agent 最核心的输出，将用户模糊的自然语言转化为一份清晰、完整、可执行的结构化需求文档
    """
    model_config = ConfigDict(extra="forbid")
    
    title: str = Field(..., description="简短明确的任务标题，2-10个字", min_length=2, max_length=100)
    description: str = Field(..., description="详细的任务描述，2-3段，清晰说明要做什么", min_length=10)
    intent_type: IntentType = Field(..., description="意图分类")
    objectives: List[str] = Field(default_factory=list, description="任务目标列表，列出完成本任务要达成的几个核心目标")
    in_scope: List[str] = Field(default_factory=list, description="明确说明哪些内容在本次任务范围内，要做的事情")
    out_of_scope: List[str] = Field(default_factory=list, description="明确说明哪些内容不在本次任务范围内，不要做的事情")
    tech_stack: List[str] = Field(default_factory=list, description="推荐使用的技术栈列表")
    acceptance_criteria: List[str] = Field(default_factory=list, description="可验证的验收标准，明确说明任务完成的标志")
    execution_plan: List[str] = Field(default_factory=list, description="分步骤的执行计划，一步步可落地")
    completeness_score: int = Field(..., ge=0, le=100, description="需求完整度分数，0-100 之间的整数")
    original_query: str = Field(..., description="用户最开始输入的原始 Query，原样保留")


class ClarificationState(BaseModel):
    """
    澄清 Agent 的会话状态数据模型
    维护一次澄清会话的完整生命周期状态，从用户开始输入到最终确认
    """
    model_config = ConfigDict(extra="forbid")
    
    session_id: str = Field(..., description="会话唯一 UUID，用于标识不同的澄清会话")
    original_query: str = Field(..., description="用户最开始输入的原始 Query")
    current_requirement: Optional[ClarifiedRequirement] = Field(None, description="当前最新的澄清后需求对象，初始状态为 None")
    conversation_history: List[dict] = Field(default_factory=list, description="用户与澄清 Agent 的对话历史，记录所有补充信息")
    is_confirmed: bool = Field(False, description="用户是否已经确认了最终的需求，确认后才能进入主 Agent")
    created_at: float = Field(..., description="会话创建的 Unix 时间戳")
    updated_at: float = Field(..., description="会话最后一次更新的 Unix 时间戳")
