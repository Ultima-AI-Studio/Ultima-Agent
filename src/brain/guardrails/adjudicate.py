"""L8 三级裁决表（M19：AdjudicationTable）。

对齐 jarvis-reverse-architecture M19「三级裁决表」与 G10 永久排除：

- **redline（硬编码红线）**：直接拒绝，不可商量、不可绕过、不进入征询。
  内置红线清单（任务卡明文 + 架构文档永久排除项）：
    1. 越权文件读写（超出声明 scope 的文件操作）
    2. 远程开锁（解锁/开门/授权第三方设备）
    3. 持械（武器/刀具/危险器械相关指令）
    4. 绕过审批（跳过审批门、伪造授权、篡改审计）
    5. 泄露凭证明文（输出明文密钥/口令/token）
    6. 未授权全网采集（未声明目标的批量抓取/爬取）
- **delegable（可商量）**：自决放行 + 事后报备（记录 report 审计事件）。
- **hazard（高危）**：先报告后执行——返回 pending，进入 HazardGate/HS-007 征询，
  授权通过（granted）才允许执行。

判定输出三态：deny（拒绝）/ allow_report（自决+报备）/ pending（征询）。
红线优先于一切；红线命中时既不报备也不征询，直接拒绝。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass(frozen=True)
class AdjudicationDecision:
    """一次裁决判定结果。"""

    verdict: str  # "deny" | "allow_report" | "pending"
    action: str
    category: str  # "redline" | "delegable" | "hazard"
    reason: str
    scope: str = ""

    @property
    def is_deny(self) -> bool:
        return self.verdict == "deny"

    @property
    def is_pending(self) -> bool:
        return self.verdict == "pending"

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict,
            "action": self.action,
            "category": self.category,
            "reason": self.reason,
            "scope": self.scope,
        }


# 红线清单：(正则模式, 说明)。匹配即直接拒绝。
REDLINES: Tuple[Tuple[str, str], ...] = (
    (r"(?:\.env|\.pem|id_rsa|\.key)", "密钥类文件（红线）"),
    (r"(?:输出|打印|显示|读取|导出|发送).*(?:密码|口令|token|api.?key|secret|明文|密钥)", "泄露凭证明文（红线）"),
    (r"解锁|开锁|开门|door.?unlock|remote.?unlock", "远程开锁（红线）"),
    (r"持械|武器|刀具|枪|刀|炸弹|爆炸物|器械", "持械/危险器械（红线）"),
    (r"绕过审批|跳过审批|伪造授权|篡改审计|伪造.*授权|绕过.*闸门|bypass", "绕过审批/审计（红线）"),
    (r"未授权.*(?:抓取|采集|爬取|扫描.*全网)|全网采集|全网.*(?:抓取|爬取)", "未授权全网采集（红线）"),
)

# 高危清单：(正则模式, 说明)。匹配即 pending（先报告后执行）。
HAZARDS: Tuple[Tuple[str, str], ...] = (
    (r"删除.*(?:文件|目录)|清空.*目录|rm\s+-rf|remove.*recursive", "破坏性删除（高危）"),
    (r"格式化|format\s+[a-z]:|磁盘.*清空", "磁盘格式化（高危）"),
    (r"停止|杀掉.*(?:服务|进程|daemon)|kill\s+.*\d+", "进程/服务控制（高危）"),
    (r"发送|发.{0,4}消息|发信息|发布|私信|发帖|评论|点赞|代登录", "对外社交/消息动作（高危）"),
    (r"转账|付款|支付|购买|下单", "资金类动作（高危）"),
    (r"改密码|重置.*密码|新增管理员|提权", "账号/权限变更（高危）"),
)


class AdjudicationTable:
    """三级裁决表：红线直接拒绝 / 可商量自决+报备 / 高危先报告后执行。"""

    def __init__(self, *, audit_path: Optional[str] = None) -> None:
        self._audit_path = audit_path
        self._lock = threading.RLock()
        self._extra_redlines: List[Tuple[str, str]] = []
        self._extra_hazards: List[Tuple[str, str]] = []

    # ------------------------------------------------------------------
    # 规则扩展（运行时追加，append-only）
    # ------------------------------------------------------------------
    def add_redline(self, pattern: str, description: str) -> None:
        with self._lock:
            self._extra_redlines.append((pattern, description))

    def add_hazard(self, pattern: str, description: str) -> None:
        with self._lock:
            self._extra_hazards.append((pattern, description))

    # ------------------------------------------------------------------
    # 判定
    # ------------------------------------------------------------------
    def adjudicate(self, action: str, scope: str = "") -> AdjudicationDecision:
        """对动作做三级裁决。红线优先，其次高危，其余可商量。"""
        with self._lock:
            rules = list(REDLINES) + list(self._extra_redlines)
            hazards = list(HAZARDS) + list(self._extra_hazards)

        for pattern, desc in rules:
            if re.search(pattern, action, re.IGNORECASE):
                d = AdjudicationDecision(
                    verdict="deny", action=action, category="redline",
                    reason=f"命中硬编码红线 [{desc}]（直接拒绝，不可绕过）", scope=scope,
                )
                self._record(d)
                return d

        for pattern, desc in hazards:
            if re.search(pattern, action, re.IGNORECASE):
                d = AdjudicationDecision(
                    verdict="pending", action=action, category="hazard",
                    reason=f"命中高危清单 [{desc}]（先报告后执行，HS-007 征询）", scope=scope,
                )
                self._record(d)
                return d

        d = AdjudicationDecision(
            verdict="allow_report", action=action, category="delegable",
            reason="未命中红线与高危清单，可商量事项自决放行并事后报备", scope=scope,
        )
        self._record(d)
        return d

    # ------------------------------------------------------------------
    # 审计
    # ------------------------------------------------------------------
    def _record(self, decision: AdjudicationDecision) -> None:
        if not self._audit_path:
            return
        try:
            event = (
                "audit.adjudicate.redline" if decision.category == "redline"
                else "audit.adjudicate.hazard" if decision.category == "hazard"
                else "audit.adjudicate.report"
            )
            row = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "source": "ultima.guard.policy",
                "event_type": event,
                "payload": decision.to_dict(),
            }
            Path(self._audit_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self._audit_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        except OSError:
            pass

    # ------------------------------------------------------------------
    # 快照
    # ------------------------------------------------------------------
    def snapshot(self) -> dict:
        with self._lock:
            return {
                "redlines": [r[1] for r in list(REDLINES) + self._extra_redlines],
                "hazards": [r[1] for r in list(HAZARDS) + self._extra_hazards],
            }


__all__ = ["AdjudicationTable", "AdjudicationDecision", "REDLINES", "HAZARDS"]
