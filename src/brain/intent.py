"""Deterministic intent parsing for the task-status text command."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


TASK_STATUS_INTENT = "task.status.query"
CAPABILITY_INTENT = "capability.query"

_DOMAIN = re.compile(r"任务|队列")
_STATUS_ASPECT = re.compile(r"状态|进度|进展|情况|执行|完成|失败|卡住|冻结|排队")
_IMPLICIT_STATUS = re.compile(r"队列|任务.{0,6}(?:怎么样|什么情况)")
_REQUEST = re.compile(r"查(?:询|看|查)?|查看|看(?:看|下|一下)?|汇报|告诉|怎么样|什么情况|有哪些")
_REQUEST_ACTION = r"(?:查(?:询|看|查)?|查看|看(?:看|下|一下)?|汇报|告诉)"
_NEGATED_REQUEST = re.compile(
    r"(?:(?:先|暂时|目前|现在)?(?<!能)(?<!可)(?<!要)"
    r"不(?:需要|用|必|想|要)?(?:再)?|无需|别(?:再)?|不要|不用|不必|不想|不是要)"
    rf".{{0,8}}{_REQUEST_ACTION}"
)
_COMPLETED_REQUEST = re.compile(
    rf"(?:已经|曾经|刚才|之前|昨天|前天|上次|过去).{{0,12}}"
    rf"{_REQUEST_ACTION}.{{0,8}}(?:过|完|了)|"
    rf"{_REQUEST_ACTION}(?:过|完|了).{{0,12}}(?:任务|队列)|"
    rf"(?:任务|队列).{{0,12}}{_REQUEST_ACTION}(?:过|完|了)|"
    rf"(?:讨论|提到|说)(?:过|了).{{0,12}}{_REQUEST_ACTION}"
)
_REPORTED_REQUEST = re.compile(
    rf"(?:他说|她说|他们说|有人说|(?:日志|记录|文档).{{0,6}}(?:写着|写了|提到)|"
    rf"提到|转述|引用).{{0,12}}{_REQUEST_ACTION}"
)
_FEATURE_DISCUSSION = re.compile(
    rf"{_REQUEST_ACTION}.{{0,12}}(?:任务|队列).{{0,8}}(?:这个|该)?功能"
    r".{0,8}(?:以后|之后|后续).{0,8}(?:再做|实现|处理)"
)
_REFERENCE_ONLY = re.compile(
    r"(?:如果|假如).{0,18}(?:查|查询|查看|看).{0,12}(?:怎么|如何)|"
    r"(?:怎么|如何).{0,12}(?:说|问)|"
    r"(?:写进|写入|复制|解释).{0,12}(?:文档|命令|句子)|"
    r"(?:是一个命令|这句话|这个命令)|"
    r"(?:刚才|之前).{0,8}(?:已经)?(?:查|查询|查看|看).{0,8}(?:过|了)"
)


@dataclass(frozen=True, slots=True)
class IntentResult:
    matched: bool
    intent: str | None
    scope: str | None
    should_interrupt: bool
    reason: str


def parse_task_status_intent(text: str | None) -> IntentResult:
    """Recognize explicit task-status requests within a deliberately narrow boundary.

    This is an offline rule set for the frozen v0.3 text scenario, not a general
    natural-language classifier.  Ambiguous statements stay silent.
    """
    normalized = _normalize(text)
    if not normalized:
        return _no_match("空输入")
    if _NEGATED_REQUEST.search(normalized):
        return _no_match("明确否定")
    if _COMPLETED_REQUEST.search(normalized):
        return _no_match("已完成的历史陈述")
    if _REPORTED_REQUEST.search(normalized):
        return _no_match("转述而非当前请求")
    if _FEATURE_DISCUSSION.search(normalized):
        return _no_match("讨论功能而非当前请求")
    if _REFERENCE_ONLY.search(normalized):
        return _no_match("引用或讨论命令")
    if _looks_like_quoted_command(normalized):
        return _no_match("引用命令")
    if not _DOMAIN.search(normalized):
        return _no_match("未出现任务域")
    if not (_STATUS_ASPECT.search(normalized) or _IMPLICIT_STATUS.search(normalized)):
        return _no_match("未出现状态维度")
    if not _REQUEST.search(normalized):
        return _no_match("没有明确请求")
    return IntentResult(True, TASK_STATUS_INTENT, "all", True, "明确查询任务状态")


_CAPABILITY_DOMAIN = re.compile(
    r"能力|本领|技能|功能|插件|本事|都会|能干|能做什么|会做什么|干什么用|有什么用|擅长"
)
_CAPABILITY_PAST = re.compile(
    r"(?:昨天|刚才|之前|上次|已经|曾经|以前).{0,12}(?:问|说|提|查)(?:过|了)?.{0,10}(?:能力|技能|功能|本领|都会|能干)"
)
_CAPABILITY_REQUEST = re.compile(
    r"有(?:什么|哪些)|会(?:什么|些|做)?|能(?:做|干)?|做什么(?:用)?|"
    r"有什么用|是什么|了解|介绍一下?|介绍下|列一下|盘点"
)


def parse_capability_intent(text: str | None) -> IntentResult:
    """识别能力清单查询（capability.query）。

    与任务状态查询互斥：仅当同时出现能力域词与请求词才命中；
    否定/转述/历史陈述/功能讨论/引用一律不命中（与任务查询同一套防误判）。
    """
    normalized = _normalize(text)
    if not normalized:
        return _no_match("空输入")
    if _NEGATED_REQUEST.search(normalized):
        return _no_match("明确否定")
    if _COMPLETED_REQUEST.search(normalized):
        return _no_match("已完成的历史陈述")
    if _REPORTED_REQUEST.search(normalized):
        return _no_match("转述而非当前请求")
    if _FEATURE_DISCUSSION.search(normalized):
        return _no_match("讨论功能而非当前请求")
    if _REFERENCE_ONLY.search(normalized):
        return _no_match("引用或讨论命令")
    if _looks_like_quoted_command(normalized):
        return _no_match("引用命令")
    if _CAPABILITY_PAST.search(normalized):
        return _no_match("能力相关历史陈述")
    if not _CAPABILITY_DOMAIN.search(normalized):
        return _no_match("未出现能力域")
    if not _CAPABILITY_REQUEST.search(normalized):
        return _no_match("没有明确能力请求")
    return IntentResult(True, CAPABILITY_INTENT, "all", True, "明确查询能力清单")


# 繁→简最小映射（语音链路 ASR 输出繁体，如「任務/狀態/隊列」，
# 意图域关键词只匹配简体；确定性规则层做归一，不引入外部依赖）
_TRAD_TO_SIMP = str.maketrans(
    "任務隊列狀態進度進展情況執行失敗凍結排隊查詢彙報告訴請幫個當前嘗試無"
    "這那說寫複錄鍾時間確認識別錯誤異常處理",
    "任务队列状态进度进展情况执行失败冻结排队查询汇报告诉请帮个当前尝试无"
    "这那说写复录钟时间确认识别错误异常处理",
)


def _normalize(text: str | None) -> str:
    if not isinstance(text, str):
        return ""
    value = unicodedata.normalize("NFKC", text).strip()
    value = value.translate(_TRAD_TO_SIMP)
    return re.sub(r"\s+", "", value)


def _looks_like_quoted_command(text: str) -> bool:
    quoted = re.search(r"[\"'“‘「『](.*?)[\"'”’」』]", text)
    if not quoted:
        return False
    fragment = quoted.group(1)
    return bool(_DOMAIN.search(fragment) and _STATUS_ASPECT.search(fragment))


def _no_match(reason: str) -> IntentResult:
    return IntentResult(False, None, None, False, reason)
