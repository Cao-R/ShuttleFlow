"""
Clarification Agent - Query 分析器
智能解析用户原始输入，识别意图、提取实体、发现缺失信息和潜在歧义
使用 tenacity 自动重试机制处理 LLM 返回的 JSON 格式错误
"""

import json
from typing import Any, Dict
from tenacity import retry, stop_after_attempt, wait_exponential

from models import AnalysisResult, IntentType


class BaseLLMClient:
    """
    LLM 客户端抽象基类
    解耦设计，不依赖任何特定的 LLM SDK
    用户可以继承此类，轻松接入任何自定义的 LLM 后端
    """
    
    async def acompletion(self, messages: list[Dict[str, Any]], **kwargs) -> str:
        """
        异步调用 LLM，返回纯文本响应
        子类必须实现此方法
        参数:
            messages: OpenAI 格式的消息列表，如 [{"role": "system", "content": "..."}]
            **kwargs: 其他 LLM 调用参数（temperature, max_tokens 等）
        返回:
            LLM 返回的纯文本字符串
        """
        raise NotImplementedError("子类必须实现此方法，提供具体的 LLM 调用逻辑")


class SimpleOpenAILLMClient(BaseLLMClient):
    """
    基于 OpenAI SDK 的简单实现
    直接包装 OpenAI 官方 AsyncOpenAI 客户端，开箱即用
    """
    
    def __init__(self, llm):
        """
        初始化 OpenAI LLM 客户端
        参数:
            llm: OpenAI 官方的 AsyncOpenAI 实例对象
        """
        self.llm = llm
    
    async def acompletion(self, messages: list[Dict[str, Any]], **kwargs) -> str:
        """
        异步调用 OpenAI LLM，自动从响应中提取文本内容
        参数:
            messages: OpenAI 格式的消息列表
            **kwargs: 其他传递给 OpenAI API 的参数
        返回:
            LLM 返回的文本内容字符串
        """
        response = await self.llm.acompletion(messages=messages, **kwargs)
        # 标准 OpenAI 响应格式处理
        if hasattr(response, 'choices') and len(response.choices) > 0:
            return response.choices[0].message.content or ""
        # 兜底处理，兼容其他可能的响应格式
        return str(response)


class QueryAnalyzer:
    """
    Query 智能分析器
    核心功能：接收用户原始 Query，调用 LLM 进行智能分析
    输出结构化的 AnalysisResult，包含意图分类、实体提取、缺失信息、歧义点
    """
    
    # 系统提示词，严格引导 LLM 输出纯 JSON，不要任何其他文字
    SYSTEM_PROMPT = """你是一位专业的需求分析师。请分析用户的 Query，输出严格符合 JSON 格式，不要任何其他文字。

输出 JSON Schema:
{
  "intent_type": "web_development|code_refactor|bug_fix|documentation|other",
  "extracted_entities": ["实体1", "实体2"],
  "missing_info": ["缺失的信息1"],
  "ambiguous_points": ["潜在歧义1"]
}

intent_type 说明:
- web_development: Web 开发相关任务
- code_refactor: 代码重构任务
- bug_fix: Bug 修复任务
- documentation: 文档编写任务
- other: 其他类型任务

只输出纯 JSON，不要 markdown 代码块标记，不要任何解释文字。"""
    
    def __init__(self, llm_client: BaseLLMClient):
        """
        初始化 Query 分析器
        参数:
            llm_client: 实现了 BaseLLMClient 接口的 LLM 客户端实例
        """
        self.llm_client = llm_client
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def analyze(self, query: str) -> AnalysisResult:
        """
        分析用户原始 Query
        使用 tenacity 装饰器，最多自动重试 3 次，指数退避策略等待
        处理 LLM 返回的 JSON 格式错误，直到成功解析或重试耗尽
        参数:
            query: 用户输入的原始自然语言 Query
        返回:
            结构化的 AnalysisResult 对象
        """
        # 构建消息列表，遵循 OpenAI 标准格式
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"请分析以下用户 Query:\n\n{query}"}
        ]
        
        # 调用 LLM，使用低 temperature 保证输出的稳定性和确定性
        raw_response = await self.llm_client.acompletion(messages, temperature=0.1)
        # 清理响应，去掉可能的 markdown 代码块标记
        cleaned_response = self._clean_response(raw_response)
        
        # 解析 JSON 并直接返回 Pydantic 模型对象
        result_dict = json.loads(cleaned_response)
        return AnalysisResult(**result_dict)
    
    def _clean_response(self, response: str) -> str:
        """
        清理 LLM 返回的响应文本，提取纯 JSON 字符串
        处理常见的 LLM 输出问题：比如 LLM 不小心加了 ```json 标记
        参数:
            response: LLM 返回的原始文本
        返回:
            清理后的纯 JSON 字符串
        """
        response = response.strip()
        # 移除开头的 ```json 标记
        if response.startswith("```json"):
            response = response[7:]
        # 移除开头的通用 ``` 标记
        if response.startswith("```"):
            response = response[3:]
        # 移除结尾的 ``` 标记
        if response.endswith("```"):
            response = response[:-3]
        return response.strip()
