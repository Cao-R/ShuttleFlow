"""
Clarification Agent - 需求澄清智能体
完全解耦的独立模块，可直接集成到 ShuttleFlow / OpenHands 项目中
"""

__version__ = "1.0.0"

from .models import (
    IntentType,
    AnalysisResult,
    ClarifiedRequirement,
    ClarificationState,
)
from .engine import ClarificationAgent
from .adapter import MainAgentAdapter
from .scorer import CompletenessScorer

__all__ = [
    "IntentType",
    "AnalysisResult",
    "ClarifiedRequirement",
    "ClarificationState",
    "ClarificationAgent",
    "MainAgentAdapter",
    "CompletenessScorer",
]
