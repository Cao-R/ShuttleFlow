"""
Clarification Agent - 结构化需求生成器
将模糊需求转化为清晰、完整、可执行的结构化需求文档
输出严格遵循 ClarifiedRequirement 的 JSON Schema
"""

import json
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from models import AnalysisResult, ClarifiedRequirement, IntentType
from analyzer import BaseLLMClient


class RequirementGenerator:
    """
    结构化需求生成器
    核心功能：基于 Query 分析结果，生成一份完整的结构化澄清需求
    输出包含标题、描述、目标、范围、技术栈、验收标准、执行计划等所有字段
    """
    
    # 系统提示词，引导 LLM 扮演经验丰富的技术产品经理
    # 严格要求输出纯 JSON，不要任何其他文字
    SYSTEM_PROMPT = """你是一位经验丰富的技术产品经理。请将用户的模糊需求转化为一份清晰、完整、可执行的结构化需求文档。

输出严格遵循以下 JSON Schema，只输出纯 JSON，不要任何其他文字：
{
  "title": "简短明确的任务标题（2-10个字）",
  "description": "详细的任务描述，2-3段，清晰说明要做什么",
  "intent_type": "web_development|code_refactor|bug_fix|documentation|other",
  "objectives": ["目标1", "目标2"],
  "in_scope": ["范围内的内容1", "范围内的内容2"],
  "out_of_scope": ["范围外的内容1", "范围外的内容2"],
  "tech_stack": ["推荐技术栈1", "推荐技术栈2"],
  "acceptance_criteria": ["验收标准1", "验收标准2"],
  "execution_plan": ["步骤1", "步骤2"],
  "completeness_score": 0-100之间的整数,
  "original_query": "用户原始Query原样返回"
}

要求:
1. acceptance_criteria 必须是可验证的，不能太模糊
2. execution_plan 要具体，一步步可落地
3. in_scope 和 out_of_scope 要明确界定边界
4. completeness_score 根据信息完整度打分，越完整分数越高
5. 只输出纯 JSON，不要 markdown 标记，不要任何解释"""
    
    def __init__(self, llm_client: BaseLLMClient):
        """
        初始化需求生成器
        参数:
            llm_client: 实现了 BaseLLMClient 接口的 LLM 客户端实例
        """
        self.llm_client = llm_client
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate(
        self,
        original_query: str,
        analysis: AnalysisResult,
        additional_context: Optional[str] = None
    ) -> ClarifiedRequirement:
        """
        生成第一版结构化澄清需求
        使用 tenacity 自动重试机制，处理 JSON 格式错误
        参数:
            original_query: 用户最开始输入的原始 Query
            analysis: QueryAnalyzer 输出的 AnalysisResult 分析结果
            additional_context: 可选的额外补充上下文，比如用户后续补充的信息
        返回:
            完整的 ClarifiedRequirement 结构化需求对象
        """
        # 构建用户提示词，把原始 Query 和分析结果都传给 LLM
        user_prompt = f"""用户原始 Query: {original_query}

Query 分析结果:
- 意图类型: {analysis.intent_type.value}
- 提取的实体: {', '.join(analysis.extracted_entities) if analysis.extracted_entities else '无'}
- 缺失的信息: {', '.join(analysis.missing_info) if analysis.missing_info else '无'}
- 潜在歧义: {', '.join(analysis.ambiguous_points) if analysis.ambiguous_points else '无'}
"""
        
        # 如果有额外补充的上下文，追加到提示词中
        if additional_context:
            user_prompt += f"\n用户补充的信息:\n{additional_context}"
        
        # 构建完整的消息列表
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        
        # 调用 LLM，使用中等 temperature 保证输出既有创造性又不失稳定性
        raw_response = await self.llm_client.acompletion(messages, temperature=0.3)
        # 清理响应文本，提取纯 JSON
        cleaned_response = self._clean_response(raw_response)
        
        # 解析 JSON 并返回 Pydantic 模型对象
        result_dict = json.loads(cleaned_response)
        return ClarifiedRequirement(**result_dict)
    
    def _clean_response(self, response: str) -> str:
        """
        清理 LLM 返回的响应文本，提取纯 JSON 字符串
        处理常见的 markdown 代码块标记问题
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
