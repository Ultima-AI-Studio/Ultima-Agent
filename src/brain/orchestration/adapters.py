"""底座 ↔ 契约适配器（T3 修复 AD-04 / AD-06，base-polish-20261025）。

对照契约：
- execution-param-contract v0.1 §4：输出协议四段 THOUGHT/ACTION/OBSERVE/FINAL；
- protocol-contract v1.0 §4：错误码语义 E-401/429/403/5xx/6xx/7xx。

底座现状：
- structured 模式用 THOUGHT/TOOL/INPUT/FINAL_ANSWER（openjarvis.agents.orchestrator）；
- 异常为原生类型（StorageError / SecurityBlockError / RuntimeError 等），
  无契约错误码段。

本模块只提供**映射函数**（纯函数，无副作用，可单测）；不拦截任何路径——
产品主路径（intent→queue→reporter）不消费底座 structured 输出，
映射在底座对话路径启用时由调用方显式接线。

写域：仅 H:\\UltimaAI\\UltimaAgent\\ 内。
"""

from __future__ import annotations

import re
from typing import Any

# ── AD-04：底座 structured 四段 → 契约四段 ────────────────────────────────
# 底座输出形如：
#   THOUGHT: <思考>
#   TOOL: <工具名>
#   INPUT: <入参>
#   FINAL_ANSWER: <最终回答>
# 契约要求：THOUGHT / ACTION / OBSERVE / FINAL（execution-param-contract §4）
_BASE_SEGMENT = re.compile(
    r"THOUGHT:\s*(.*?)(?=\nTOOL:|\nINPUT:|\nFINAL_ANSWER:|\Z)",
    re.S,
)
_BASE_TOOL = re.compile(r"TOOL:\s*(.*?)(?=\nINPUT:|\nFINAL_ANSWER:|\Z)", re.S)
_BASE_INPUT = re.compile(r"INPUT:\s*(.*?)(?=\nFINAL_ANSWER:|\Z)", re.S)
_BASE_FINAL = re.compile(r"FINAL_ANSWER:\s*(.*)", re.S)


def map_structured_to_contract(text: str) -> dict[str, str | None]:
    """把底座 structured 输出映射为契约四段（THOUGHT/ACTION/OBSERVE/FINAL）。

    TOOL → ACTION（执行动作）；INPUT → OBSERVE（动作入参作为观察输入）；
    FINAL_ANSWER → FINAL（终答）。段缺失补 None 并显式标注，不编造。
    """
    thought = _match_group(_BASE_SEGMENT, text)
    tool = _match_group(_BASE_TOOL, text)
    inp = _match_group(_BASE_INPUT, text)
    final = _match_group(_BASE_FINAL, text)
    return {
        "THOUGHT": thought,
        "ACTION": tool,
        "OBSERVE": inp,
        "FINAL": final,
    }


def _match_group(pattern: re.Pattern[str], text: str) -> str | None:
    m = pattern.search(text)
    if not m:
        return None
    value = m.group(1).strip()
    return value or None


# ── AD-06：底座异常 → 契约错误码 ─────────────────────────────────────────
# protocol-contract v1.0 §4 错误码语义（E-401/429/403/5xx/6xx/7xx）。
# 底座异常映射为契约码段：未知类型归 E-5xx（内部错误），缺码段不编造。
def map_exception_to_error_code(exc: BaseException) -> str:
    """按底座异常类型返回契约错误码。

    明确规则（可机检，无猜测）：
    - StorageError → E-6xx（存储/持久化）
    - SecurityBlockError → E-403（安全拦截）
    - 限流/频率类 → E-429（限流）
    - 缺依赖/导入 → E-7xx（环境/依赖）
    - 其余 → E-5xx（内部错误）
    """
    name = type(exc).__name__
    if name in ("StorageError", "QueueReadError"):
        return "E-6xx"
    if name in ("SecurityBlockError", "RedactionError", "InjectionBlocked"):
        return "E-403"
    if name in ("RateLimitError", "QuotaExceeded", "Throttled"):
        return "E-429"
    if name in ("ModuleNotFoundError", "ImportError", "FileNotFoundError"):
        return "E-7xx"
    return "E-5xx"


def error_payload(exc: BaseException) -> dict[str, str]:
    """结构化错误回执：错误码 + 类型 + 一句中文说明（I3 失败回执结构化）。"""
    return {
        "code": map_exception_to_error_code(exc),
        "type": type(exc).__name__,
        "message": str(exc) or "未记录错误信息",
    }
