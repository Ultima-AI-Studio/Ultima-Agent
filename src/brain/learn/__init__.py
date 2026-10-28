"""S11 学习闭环（M21 深化 · 阶段二智能陪伴）。

轨迹采集 → 评测 → 改进 三段闭环，不做模型微调前期。
"""

from .trace_collector import TraceCollector, TraceRecord
from .evaluator import Evaluator, EvalReport
from .improver import Improver, ImprovementAction

__all__ = [
    "TraceCollector", "TraceRecord",
    "Evaluator", "EvalReport",
    "Improver", "ImprovementAction",
]
