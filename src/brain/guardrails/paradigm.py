"""L10 范式闸门（M26：7 环流程强制检查 + 防直达能力）。

对齐 interaction-paradigm.md §1 与 jarvis-reverse-architecture M26：

7 环标准交互流程（不可跨环、不可跳过）：
    ① 意图识别 intent → ② 领域定义 domain → ③ 排版组合 layout
  → ④ 样式 style → ⑤ 动效 motion → ⑥ 呈现窗口 present → ⑦ 语音汇报 report

- 每 flowId 维护环进度；声明当前环必须严格等于上一环 + 1，跳环/重复/回退拒绝；
- **防直达能力**：任何对外能力交付（呈现/汇报/执行）前必须 7 环全绿，
  `assert_complete` 未过即拒绝——不得跳过范式直达能力；
- 环未全绿时 report/present 环不可到达（fail-closed）；
- 状态机线程安全；审计留痕写 append-only 事件流。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence


# 7 环固定序（唯一权威）
FLOW_RINGS: Tuple[str, ...] = (
    "intent",      # ① 意图识别
    "domain",      # ② 领域定义
    "layout",      # ③ 排版组合
    "style",       # ④ 样式
    "motion",      # ⑤ 动效
    "present",     # ⑥ 呈现窗口
    "report",      # ⑦ 语音汇报
)
RING_INDEX = {name: i for i, name in enumerate(FLOW_RINGS)}


@dataclass(frozen=True)
class ParadigmDecision:
    """一次 7 环流程判定结果。"""

    allowed: bool
    flow_id: str
    step: str
    reason: str
    passed_rings: tuple
    completed: bool = False

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "flow_id": self.flow_id,
            "step": self.step,
            "reason": self.reason,
            "passed_rings": list(self.passed_rings),
            "completed": self.completed,
        }


class ParadigmGate:
    """7 环流程强制检查闸门（驻留，fail-closed）。"""

    def __init__(self, *, audit_path: Optional[str] = None) -> None:
        self._progress: Dict[str, List[str]] = {}
        self._lock = threading.RLock()
        self._audit_path = audit_path

    # ------------------------------------------------------------------
    # 流程推进（环环相扣）
    # ------------------------------------------------------------------
    def advance(self, flow_id: str, step: str) -> ParadigmDecision:
        """声明当前环。必须严格顺序推进：重复/跳环/回退拒绝。

        step 允许别名：中文环名（意图/领域/排版/样式/动效/呈现/汇报）
        与英文环名（intent/domain/layout/style/motion/present/report）。
        """
        norm = self._normalize_step(step)
        with self._lock:
            passed = list(self._progress.get(flow_id, []))
            expected = FLOW_RINGS[len(passed)] if len(passed) < len(FLOW_RINGS) else None
            if norm not in RING_INDEX:
                d = ParadigmDecision(False, flow_id, step, f"未知环节: {step}", tuple(passed))
                self._record(d)
                return d
            if expected is None:
                d = ParadigmDecision(
                    False, flow_id, step,
                    "流程已完整走完 7 环，禁止重复推进", tuple(passed), completed=True,
                )
                self._record(d)
                return d
            if norm != expected:
                d = ParadigmDecision(
                    False, flow_id, step,
                    f"环节顺序违规：当前应推进 [{expected}]，收到 [{norm}]（不可跳环/回退/重复）",
                    tuple(passed),
                )
                self._record(d)
                return d
            passed.append(norm)
            self._progress[flow_id] = passed
            completed = len(passed) == len(FLOW_RINGS)
            d = ParadigmDecision(True, flow_id, step, f"环节 [{norm}] 通过", tuple(passed), completed)
            self._record(d)
            return d

    # ------------------------------------------------------------------
    # 防直达能力：对外交付前必须全绿
    # ------------------------------------------------------------------
    def assert_complete(self, flow_id: str, *, target: str = "对外能力") -> ParadigmDecision:
        """7 环未全绿时拒绝抵达目标（防直达能力，fail-closed）。"""
        with self._lock:
            passed = list(self._progress.get(flow_id, []))
            if len(passed) < len(FLOW_RINGS):
                missing = FLOW_RINGS[len(passed)]
                d = ParadigmDecision(
                    False, flow_id, target,
                    f"防直达能力：7 环未走完，缺失 [{missing}]（不得跳过范式直达能力）",
                    tuple(passed),
                )
                self._record(d)
                return d
            d = ParadigmDecision(True, flow_id, target, "7 环已全绿，允许对外交付", tuple(passed), True)
            self._record(d)
            return d

    def progress(self, flow_id: str) -> List[str]:
        with self._lock:
            return list(self._progress.get(flow_id, []))

    def reset_flow(self, flow_id: str) -> None:
        with self._lock:
            self._progress.pop(flow_id, None)

    # ------------------------------------------------------------------
    # 审计
    # ------------------------------------------------------------------
    def _record(self, decision: ParadigmDecision) -> None:
        if not self._audit_path:
            return
        try:
            event = (
                "audit.paradigm.denied" if not decision.allowed
                else "audit.paradigm.complete" if decision.completed
                else "audit.paradigm.passed"
            )
            row = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "source": "ultima.paradigm.flow",
                "event_type": event,
                "payload": decision.to_dict(),
            }
            Path(self._audit_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self._audit_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        except OSError:
            pass

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "rings": list(FLOW_RINGS),
                "active_flows": {
                    fid: self._progress[fid] for fid in sorted(self._progress)
                },
            }

    @staticmethod
    def _normalize_step(step: str) -> str:
        alias = {
            "意图": "intent", "意图识别": "intent",
            "领域": "domain", "领域定义": "domain",
            "排版": "layout", "排版组合": "layout",
            "样式": "style",
            "动效": "motion",
            "呈现": "present", "呈现窗口": "present",
            "汇报": "report", "语音汇报": "report",
        }
        return alias.get(step.strip(), step.strip())


__all__ = ["ParadigmGate", "ParadigmDecision", "FLOW_RINGS", "RING_INDEX"]
