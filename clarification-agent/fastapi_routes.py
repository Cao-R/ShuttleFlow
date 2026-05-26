"""
Clarification Agent - FastAPI 独立路由
可直接挂载到 ShuttleFlow / OpenHands 的现有 FastAPI App 上
完全解耦，不依赖项目内部其他任何模块
"""

from typing import Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from models import ClarificationState, ClarifiedRequirement
from engine import ClarificationAgent
from adapter import MainAgentAdapter


# 创建独立的 APIRouter，指定统一的 URL 前缀和标签
router = APIRouter(prefix="/api/v1/clarification", tags=["clarification"])

# 内存状态存储字典（生产环境可轻松替换为 Redis/数据库）
_states: Dict[str, ClarificationState] = {}
# 全局单例实例，延迟初始化
_agent_instance: ClarificationAgent | None = None
_adapter_instance: MainAgentAdapter | None = None


# ==================== 请求/响应 Pydantic 模型定义 ====================

class StartRequest(BaseModel):
    """开始澄清会话的请求体"""
    query: str = Field(..., description="用户原始输入的自然语言 Query")


class SupplementRequest(BaseModel):
    """用户补充信息的请求体"""
    message: str = Field(..., description="用户输入的补充信息文本")


class ManualUpdateRequest(BaseModel):
    """用户手动编辑更新需求的请求体"""
    requirement: ClarifiedRequirement = Field(..., description="用户手动编辑后的完整结构化需求对象")


class ConfirmResponse(BaseModel):
    """确认需求后的响应体"""
    main_agent_input: str = Field(..., description="格式化后的主 Agent 可直接使用的完整 Prompt 字符串")


# ==================== 全局初始化函数 ====================

def init_clarification_agent(agent: ClarificationAgent, adapter: MainAgentAdapter):
    """
    初始化全局 ClarificationAgent 和 MainAgentAdapter 实例
    在应用启动时调用一次即可
    参数:
        agent: 已配置好的 ClarificationAgent 实例
        adapter: 已配置好的 MainAgentAdapter 实例
    """
    global _agent_instance, _adapter_instance
    _agent_instance = agent
    _adapter_instance = adapter


def _get_agent() -> ClarificationAgent:
    """
    安全获取全局 Agent 实例
    如果未初始化则抛出 500 错误
    返回:
        ClarificationAgent 全局实例
    """
    if not _agent_instance:
        raise HTTPException(status_code=500, detail="ClarificationAgent 未初始化，请先调用 init_clarification_agent()")
    return _agent_instance


def _get_adapter() -> MainAgentAdapter:
    """
    安全获取全局 Adapter 实例
    如果未初始化则抛出 500 错误
    返回:
        MainAgentAdapter 全局实例
    """
    if not _adapter_instance:
        raise HTTPException(status_code=500, detail="MainAgentAdapter 未初始化，请先调用 init_clarification_agent()")
    return _adapter_instance


# ==================== API 端点定义 ====================

@router.post("/start", response_model=ClarificationState, summary="开始新的澄清会话")
async def start_clarification(req: StartRequest):
    """
    开始一个全新的澄清会话
    接收用户原始 Query，自动分析并生成第一版结构化澄清需求
    """
    agent = _get_agent()
    state = await agent.process_initial_query(req.query)
    # 把新生成的状态存入内存字典
    _states[state.session_id] = state
    return state


@router.get("/{session_id}", response_model=ClarificationState, summary="获取澄清会话状态")
async def get_state(session_id: str):
    """
    根据 session_id 获取指定澄清会话的当前状态
    """
    if session_id not in _states:
        raise HTTPException(status_code=404, detail="指定的澄清会话不存在")
    return _states[session_id]


@router.post("/{session_id}/regenerate", response_model=ClarifiedRequirement, summary="重新生成需求")
async def regenerate(session_id: str):
    """
    基于当前会话重新生成一版新的澄清需求
    用户点击"重新生成"按钮时调用
    """
    if session_id not in _states:
        raise HTTPException(status_code=404, detail="指定的澄清会话不存在")
    agent = _get_agent()
    state = _states[session_id]
    req = await agent.regenerate(state)
    return req


@router.post("/{session_id}/supplement", response_model=ClarifiedRequirement, summary="用户补充信息")
async def add_supplement(session_id: str, req: SupplementRequest):
    """
    用户补充新的信息，基于补充信息更新需求
    用户点击"继续补充"按钮时调用
    """
    if session_id not in _states:
        raise HTTPException(status_code=404, detail="指定的澄清会话不存在")
    agent = _get_agent()
    state = _states[session_id]
    new_req = await agent.add_user_supplement(state, req.message)
    return new_req


@router.post("/{session_id}/manual-update", response_model=ClarifiedRequirement, summary="用户手动编辑更新需求")
async def manual_update(session_id: str, req: ManualUpdateRequest):
    """
    用户直接在 UI 上手动编辑了完整的需求对象
    不经过 LLM，直接重新计算完整度分数
    """
    if session_id not in _states:
        raise HTTPException(status_code=404, detail="指定的澄清会话不存在")
    agent = _get_agent()
    state = _states[session_id]
    updated = agent.update_requirement_manually(state, req.requirement)
    return updated


@router.post("/{session_id}/confirm", response_model=ConfirmResponse, summary="确认需求，准备进入主 Agent")
async def confirm(session_id: str):
    """
    用户最终确认需求，标记状态为已确认
    通过 MainAgentAdapter 转换格式，返回主 Agent 可直接使用的 Prompt
    """
    if session_id not in _states:
        raise HTTPException(status_code=404, detail="指定的澄清会话不存在")
    agent = _get_agent()
    adapter = _get_adapter()
    state = _states[session_id]
    
    # 安全检查：确保当前会话已经生成了需求
    if not state.current_requirement:
        raise HTTPException(status_code=400, detail="该会话还没有生成任何需求，无法确认")
    
    # 标记状态为已确认
    agent.confirm(state)
    # 调用适配器转换格式
    main_agent_input = adapter.convert_to_main_agent_input(state.current_requirement)
    
    return ConfirmResponse(main_agent_input=main_agent_input)
