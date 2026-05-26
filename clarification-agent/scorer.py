"""
Clarification Agent - 完整度评分器
计算需求完整度分数（0-100）
基于5个维度加权计算，客观评估需求的质量
"""

from models import ClarifiedRequirement


class CompletenessScorer:
    """
    需求完整度评分器
    采用5个维度加权评分体系，总分100分
    维度权重分配：
    - 目标明确性：25分
    - 范围清晰度：25分
    - 技术约束：20分
    - 验收标准：20分
    - 执行计划：10分
    """
    
    def score(self, requirement: ClarifiedRequirement) -> int:
        """
        计算需求完整度总分
        把5个维度的得分加起来，取不超过100的最小值
        参数:
            requirement: ClarifiedRequirement 结构化需求对象
        返回:
            0-100 之间的完整度分数
        """
        total = 0
        
        # 累加5个维度的得分
        total += self._score_description(requirement)
        total += self._score_scope(requirement)
        total += self._score_tech_stack(requirement)
        total += self._score_acceptance(requirement)
        total += self._score_plan(requirement)
        
        # 确保分数不超过100
        return min(total, 100)
    
    def _score_description(self, req: ClarifiedRequirement) -> int:
        """
        维度1：目标明确性 - 25分
        评分规则：
        - 标题长度 >= 5 字符：得10分
        - 描述长度 >= 30 字符：得15分
        总分上限25分
        """
        score = 0
        if req.title and len(req.title) >= 5:
            score += 10
        if req.description and len(req.description) >= 30:
            score += 15
        return min(score, 25)
    
    def _score_scope(self, req: ClarifiedRequirement) -> int:
        """
        维度2：范围清晰度 - 25分
        评分规则：
        - in_scope 至少有1项：得12分
        - out_of_scope 至少有1项：得13分
        总分上限25分
        """
        score = 0
        if req.in_scope and len(req.in_scope) >= 1:
            score += 12
        if req.out_of_scope and len(req.out_of_scope) >= 1:
            score += 13
        return min(score, 25)
    
    def _score_tech_stack(self, req: ClarifiedRequirement) -> int:
        """
        维度3：技术约束 - 20分
        评分规则：
        - tech_stack 至少有1项：直接得20分
        总分上限20分
        """
        score = 0
        if req.tech_stack and len(req.tech_stack) >= 1:
            score += 20
        return min(score, 20)
    
    def _score_acceptance(self, req: ClarifiedRequirement) -> int:
        """
        维度4：验收标准 - 20分
        评分规则：
        - acceptance_criteria 至少有2项：得20分
        - acceptance_criteria 至少有1项：得10分
        总分上限20分
        """
        score = 0
        if req.acceptance_criteria and len(req.acceptance_criteria) >= 2:
            score += 20
        elif req.acceptance_criteria and len(req.acceptance_criteria) >= 1:
            score += 10
        return min(score, 20)
    
    def _score_plan(self, req: ClarifiedRequirement) -> int:
        """
        维度5：执行计划 - 10分
        评分规则：
        - execution_plan 至少有3项：得10分
        - execution_plan 至少有1项：得5分
        总分上限10分
        """
        score = 0
        if req.execution_plan and len(req.execution_plan) >= 3:
            score += 10
        elif req.execution_plan and len(req.execution_plan) >= 1:
            score += 5
        return min(score, 10)
