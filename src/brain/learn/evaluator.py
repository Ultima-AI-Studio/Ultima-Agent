"""S11 学习闭环 · 评测器（M21 深化 · 阶段二智能陪伴）。

对批次执行轨迹评分：成功率 / 平均耗时 / 兜底命中（replanned 兜底次数），
输出评测报告与基准线（baseline）。评分可复算（确定性规则），不引入随机。

对齐蓝图 §4.3.1 阶段二第 5 项「轨迹 → 评测 → 改进闭环（不做模型微调前期）」：
- 评测输出：EvalReport（批次数 / 成功率 / 平均耗时 / p90 耗时 / 兜底次数 /
  状态分布 / 各意图成功率 / 基准线断言）
- 基准线：首次评测即建立基线；后续评测与基线比较，产生升降信号供改进器消费
- 确定性：同一输入同一结果（纯函数式计算，无时间依赖）

设计约束：
- 只读：不修改轨迹；不修改审计日志
- 可复算：结果可重复计算（排序稳定、无随机）
- 写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence

from .trace_collector import TraceRecord


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _p90(sorted_values: list[float]) -> float:
    """P90 分位（升序）。空列表返回 0.0。"""
    if not sorted_values:
        return 0.0
    idx = max(0, min(len(sorted_values) - 1, int(len(sorted_values) * 0.9)))
    return sorted_values[idx]


@dataclass(frozen=True, slots=True)
class EvalReport:
    """一次轨迹批次评测报告。"""

    ts: str
    total: int
    success: int
    rejected: int
    replanned: int
    partial: int
    unknown: int
    success_rate: float                # 0.0 ~ 1.0
    avg_duration_ms: float
    p90_duration_ms: float
    fallback_hits: int                 # replanned 次数（兜底命中）
    by_intent: dict[str, dict[str, Any]]
    baseline: Optional[dict[str, Any]] = None
    signal: str = "no_baseline"        # no_baseline | steady | improved | degraded
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "ts": self.ts, "total": self.total, "success": self.success,
            "rejected": self.rejected, "replanned": self.replanned,
            "partial": self.partial, "unknown": self.unknown,
            "success_rate": self.success_rate,
            "avg_duration_ms": self.avg_duration_ms,
            "p90_duration_ms": self.p90_duration_ms,
            "fallback_hits": self.fallback_hits,
            "by_intent": {k: dict(v) for k, v in self.by_intent.items()},
            "baseline": self.baseline, "signal": self.signal, "notes": self.notes,
        }


class Evaluator:
    """批次轨迹评测器（确定性、可复算）。"""

    def __init__(
        self,
        *,
        baseline_path: Optional[str | Path] = None,
        success_rate_delta: float = 0.05,
        duration_delta_ms: float = 100.0,
    ) -> None:
        """参数：
        - baseline_path：基准线持久化文件（None = 内存基准，不落盘）
        - success_rate_delta：成功率升降判定阈值（绝对值）
        - duration_delta_ms：平均耗时升降判定阈值
        """
        self.baseline_path = Path(baseline_path) if baseline_path else None
        self.success_rate_delta = success_rate_delta
        self.duration_delta_ms = duration_delta_ms
        self._memory_baseline: Optional[dict[str, Any]] = None

    # -- 评测入口 ------------------------------------------------------------

    def evaluate(self, traces: Sequence[TraceRecord]) -> EvalReport:
        """对轨迹批次评测，并与既有基准线比较产生信号。"""
        total = len(traces)
        success = sum(1 for t in traces if t.status == "approved")
        rejected = sum(1 for t in traces if t.status == "rejected")
        replanned = sum(1 for t in traces if t.status == "replanned")
        partial = sum(1 for t in traces if t.status == "partial")
        unknown = sum(1 for t in traces if t.status == "unknown")

        durations = [t.durations_ms.get("total", 0.0) for t in traces if t.durations_ms.get("total", 0.0) > 0]
        avg_ms = round(sum(durations) / len(durations), 1) if durations else 0.0
        p90 = _p90(sorted(durations)) if durations else 0.0
        success_rate = round(success / total, 4) if total else 0.0

        # 各意图聚合
        by_intent: dict[str, dict[str, Any]] = {}
        for t in traces:
            intent = t.intent or "unknown"
            bucket = by_intent.setdefault(intent, {"total": 0, "success": 0, "rejected": 0, "replanned": 0})
            bucket["total"] += 1
            if t.status == "approved":
                bucket["success"] += 1
            elif t.status == "rejected":
                bucket["rejected"] += 1
            elif t.status == "replanned":
                bucket["replanned"] += 1
        for intent, bucket in by_intent.items():
            bucket["success_rate"] = round(bucket["success"] / bucket["total"], 4) if bucket["total"] else 0.0

        # 基准线比较
        baseline = self._load_baseline()
        signal = "no_baseline"
        if baseline is not None:
            base_rate = float(baseline.get("success_rate", 0.0))
            base_avg = float(baseline.get("avg_duration_ms", 0.0))
            if success_rate >= base_rate + self.success_rate_delta:
                signal = "improved"
            elif success_rate <= base_rate - self.success_rate_delta:
                signal = "degraded"
            elif avg_ms <= base_avg - self.duration_delta_ms:
                signal = "improved"
            elif avg_ms >= base_avg + self.duration_delta_ms:
                signal = "degraded"
            else:
                signal = "steady"

        report = EvalReport(
            ts=_now_iso(), total=total, success=success, rejected=rejected,
            replanned=replanned, partial=partial, unknown=unknown,
            success_rate=success_rate, avg_duration_ms=avg_ms, p90_duration_ms=p90,
            fallback_hits=replanned, by_intent=by_intent,
            baseline=baseline, signal=signal,
        )

        # 首次评测（无既有基准）即建立基线：内存基线始终建立，
        # 有 baseline_path 时同时落盘（供后续批次与改进器消费）。
        if total > 0 and baseline is None:
            self._save_baseline(report)
        return report

    # -- 基准线持久化 --------------------------------------------------------

    def _load_baseline(self) -> Optional[dict[str, Any]]:
        if self.baseline_path is not None and self.baseline_path.exists():
            try:
                import json
                with self.baseline_path.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
                if isinstance(data, dict):
                    return data
            except (OSError, ValueError):
                return None
        return self._memory_baseline

    def _save_baseline(self, report: EvalReport) -> None:
        baseline = {
            "ts": report.ts, "total": report.total,
            "success_rate": report.success_rate,
            "avg_duration_ms": report.avg_duration_ms,
            "p90_duration_ms": report.p90_duration_ms,
            "fallback_hits": report.fallback_hits,
        }
        self._memory_baseline = baseline
        if self.baseline_path is not None:
            import json
            self.baseline_path.parent.mkdir(parents=True, exist_ok=True)
            with self.baseline_path.open("w", encoding="utf-8") as fh:
                json.dump(baseline, fh, ensure_ascii=False, indent=2)


__all__ = ["Evaluator", "EvalReport"]
