"""Python 侧的状态词适配层 —— 不是全系统权威源。

`ccpm/lib.sh` 仍是判定权威：`is_done_status` 认 `closed|completed|done`，
`active_conflicts` 只把 `in-progress/in_progress` 当活动任务。本模块只把「工单可能
写出的状态词」收敛成三个规范值，供 Python 侧做入参校验，不改变任何判定结果。

三条边界（来自 2026-11-09 的第三方审计，Codex 提出，已复核）：

1. **不接管看板。** `kanban_update.py` 操作的是看板 `state`（`Done/Blocked/Doing/
   Review`，首字母大写）与 todo `status`
   （`in-progress/completed/not-started`），是另一个数据域。强行导入只会把两套
   状态机搅在一起。
2. **`status` 与 `result` 不合并。** `status` 是工单生命周期
   （`open → in-progress → closed`）；`result` 是单次派发的结果（`done`/`blocked`）。
   合并会把「被挡过一次」读成「工单永久 blocked」，连累 `depends_on` /
   `conflicts_with`。
3. **`blocked` 只属于 `result`。** 它归一成 status 时返回 `None`（未知），
   而不是被升级成一个合法的生命周期状态。
"""

from __future__ import annotations

STATUS_CANON = ("open", "in-progress", "closed")

# 别名只做拼写归一，不新增语义：`done` / `completed` 与 `closed` 在 ccpm
# `is_done_status` 里本来就是同一个完成态。
STATUS_ALIASES = {
    "in_progress": "in-progress",
    "completed": "closed",
    "done": "closed",
}

# 现有 emitter（`codex_channel.py:221`）只产生这两个值。
# `failed` 目前没有真实生产者，也没有消费者，登记进来就是造一个空契约。
RESULT_CANON = ("done", "blocked")


def normalize_status(raw: object) -> str | None:
    """规范状态；未知、缺失或非字符串时返回 ``None``。"""
    if not isinstance(raw, str):
        return None
    value = raw.strip()
    if not value:
        return None
    if value in STATUS_CANON:
        return value
    return STATUS_ALIASES.get(value)


def normalize_result(raw: object) -> str | None:
    """规范派发结果；不在 ``RESULT_CANON`` 内返回 ``None``。"""
    if not isinstance(raw, str):
        return None
    value = raw.strip()
    return value if value in RESULT_CANON else None


def is_done_status(raw: object) -> bool:
    """与 ccpm ``is_done_status`` 对齐：只有完成态。"""
    return normalize_status(raw) == "closed"


def is_active_status(raw: object) -> bool:
    """与 ccpm ``active_conflicts`` 对齐：只有进行中算活动。"""
    return normalize_status(raw) == "in-progress"


# 工单 frontmatter 允许写出的全部状态词（规范值 + 别名），供入参校验使用。
STATUS_WORDS = frozenset(STATUS_CANON) | frozenset(STATUS_ALIASES)
