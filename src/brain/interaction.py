"""L7 交互循环（对话即操作可循环）：征询闭环 + 队列调整 + 异步交付三拍。

对齐 product-plan v2.3 §6 L7 验收口径：
- 征询闭环："你觉得怎么样" → 调整 → 重呈现 → 征询 → 确认 → 待命
- 队列调整：插队（requeue_before）/ 改优先级（adjust_priority）
- 异步交付三拍：告知（"稍等，我整理一下"）→ 进行 → 交付

写通道复用冻结队列引擎官方入口（QueuePlanner.adjust_priority / requeue_before），
不绕过冻结引擎、不写自研状态迁移；调整仅允许 QUEUED 任务（引擎侧校验）。
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from tasks.queue_engine import QueuePlanner, QueueStorage
from tasks.queue_engine.priority_deps import QueuePlanningError

from .queue_source import read_queue_status
from .routing.intent_gate import RouteState, get_intent_gate
from .routing.reply_verifier import ReplySchema, get_reply_verifier

_TASK_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._~-]*$")
_PRIORITY = re.compile(r"^[0-9]{1,3}$")

class _DynamicWakeEchoPattern:
    """Match wakeword-only ASR echoes against the current voice profile."""

    def match(self, text: str):
        from .voice.voice_profile import get_wake_echo_roots

        roots = get_wake_echo_roots()
        if not roots:
            return None
        alternatives = "|".join(re.escape(root) for root in roots)
        return re.match(rf"^(?:{alternatives})[呵啊呀哦呢吧哈。，！？!?.]*$", text)


_WAKE_ECHO_ONLY = _DynamicWakeEchoPattern()

# ── 征询状态机（会话内状态，一次交互会话一个实例）──────────────
_IDLE = "idle"          # 待命：可接受新查询
_PENDING_CONFIRM = "pending_confirm"  # 已交付结果，等待确认/调整指令
_CONFIRMED = "confirmed"  # 确认通过，回到待命


@dataclass(frozen=True, slots=True)
class InteractionState:
    phase: str
    last_summary: str | None
    adjusted: bool


@dataclass(frozen=True, slots=True)
class InteractionResponse:
    handled: bool
    ok: bool
    text: str
    state: InteractionState
    reason: str = ""  # 语义标签（供载体映射：查询完成/征询中/确认通过/调整完成/调整失败…）

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["state"] = asdict(self.state)
        return value


class InteractionLoop:
    """One conversation session's interaction loop state machine."""

    def __init__(
        self,
        queue_root: str | Path,
        *,
        wakeword_change_submitter: Callable[[str], bool] | None = None,
    ) -> None:
        self.queue_root = Path(queue_root).resolve()
        self.phase = _IDLE
        self.last_summary: str | None = None
        self.adjusted = False
        self.storage = QueueStorage(self.queue_root)
        self.planner = QueuePlanner(self.storage)
        self._wakeword_change_submitter = wakeword_change_submitter

    def set_wakeword_change_submitter(
        self, submitter: Callable[[str], bool] | None
    ) -> None:
        """Attach the resident daemon's non-blocking wakeword transaction hook."""
        self._wakeword_change_submitter = submitter

    # ── 对外入口：处理一条交互文本 ─────────────────────────────
    def handle(
        self,
        text: str | None,
        *,
        detail_task_id: str | None = None,
        asr_confidence: float | None = None,
        asr_corrected: bool = False,
    ) -> InteractionResponse:
        """Route one utterance through the interaction state machine."""
        normalized = _normalize_utterance(text)
        if not normalized:
            return self._respond(False, True, "", "空输入", self.phase)

        # 0a. 无实质内容（纯标点/符号，如 ASR 空输出"."）：用户唤醒后未接指令/声音过轻
        #     → 直接引导，不进入 14B 兜底（否则干等 30~50s 后播一句废话，体验=喊了没反应）。
        if not re.search(r"[\u4e00-\u9fffA-Za-z0-9]", normalized):
            return self._respond(True, True, "在呢，请说。", "唤醒确认", self.phase)

        # 0. 纯唤醒词回声引导：ASR 只识别出 profile 中的唤醒称呼及其尾音时，
        #    说明用户喊完唤醒词后未接指令，直接给引导语，
        #    不进入 14B 兜底（否则干等 30s+ 后静默，体验=喊了没反应）。
        if _WAKE_ECHO_ONLY.match(normalized):
            return self._respond(True, True, "在呢，请说。", "唤醒确认", self.phase)

        # 用户设置指令是窄边界、工具执行路径：必须先于通用路由门和队列调整，
        # 否则“改成”会被队列调整吞掉，“以后叫…唤醒我”也可能被误判为听不清。
        wakeword_change = self._try_wakeword_change(normalized)
        if wakeword_change is not None:
            return wakeword_change

        # 已登记且带明确天气上下文的近音可走确定性天气路径；孤立近音片段仍把
        # 原文交给路由门 ABSTAIN，避免未知噪声借纠错绕过入口门。
        route_text = normalized if _is_contextual_weather_correction(text, normalized) else text
        routed = self._route_before_agent(
            route_text,
            asr_confidence=asr_confidence,
            asr_corrected=asr_corrected,
        )
        if routed is not None:
            return routed

        # 1. 具体调整指令优先（插队 / 改优先级）——防被泛意图吞掉
        adjusted = self._try_adjust_command(normalized)
        if adjusted is not None:
            return adjusted

        # 1.5 子智能体调用意图（MVP：识别 + 引导具体任务；业务派发下一阶段接线）
        if _SUBAGENT_INTENT.search(normalized) or _fuzzy_subagent(normalized):
            return self._on_subagent(normalized)

        # 2. 征询/确认/泛调整意图（对话即操作驱动）
        if _CONFIRM_INTENT.search(normalized):
            return self._on_confirm()
        if _CONSULT_INTENT.search(normalized):
            return self._on_consult(normalized)
        if _ADJUST_INTENT.search(normalized):
            return self._on_adjust_request(normalized)

        # 3. 查询意图（复用文本闭环）
        from .reporter import respond_to_text

        response = respond_to_text(text, queue_root=self.queue_root, detail_task_id=detail_task_id)
        if response.handled:
            summary = response.text or "查询无结果输出。"
            self.last_summary = summary
            self.adjusted = False
            self.phase = _PENDING_CONFIRM
            return self._respond(True, response.ok, summary, "查询完成", self.phase)

        # 3.5 模糊意图兜底（ASR 错字/幻觉前缀鲁棒，DEFECT-002 补充）：
        # 精确正则未命中时，按关键词包含 + 编辑距离做语义兜底，
        # 避免「此处理一号任务」（识别错字）等被静默丢弃。
        fuzzy = _fuzzy_intent_fallback(normalized)
        if fuzzy == "adjust":
            return self._on_adjust_request(normalized)
        if fuzzy == "confirm":
            return self._on_confirm()
        if fuzzy == "query":
            response = respond_to_text(text, queue_root=self.queue_root, detail_task_id=detail_task_id)
            if response.handled:
                summary = response.text or "查询无结果输出。"
                self.last_summary = summary
                self.adjusted = False
                self.phase = _PENDING_CONFIRM
                return self._respond(True, response.ok, summary, "查询完成", self.phase)

        # 5.5 天气直达（2026-10-29 新增）：识别天气意图 → 直查天气 → 一句话秒答，
        #     不进入 14B 自由发挥（此前"查天气"被 agent 绕圈 119s 或甩一长串天气网链接，
        #     真机反馈：没直接回答）。仅当天气查询成功才接管；失败/无城市时仍走 14B 兜底。
        weather_reply = self._try_weather_fallback(normalized)
        if weather_reply is not None:
            return weather_reply

        # 6. 规则表全部未命中 → 转本地 Agent 循环（agent_server，14B 自主回答/调工具）。
        #    服务不可达或返回空时降级静默（不语音搭话，保持 L7 验收现状）。
        agent_reply = self._try_agent_fallback(normalized, route_input=False)
        if agent_reply is not None:
            return agent_reply

        # 未命中意图：静默（不语音搭话）。识别成功但语义未命中通常为背景音/无效内容，
        # 频繁语音回应会让用户感到被打扰（真机反馈：总是问我需要做什么）。
        return self._respond(False, True, "", "未命中", self.phase)

    def _try_wakeword_change(self, text: str) -> InteractionResponse | None:
        """Submit an explicit wakeword-setting command without blocking the daemon."""
        if _is_ambiguous_wakeword_change(text):
            return self._respond(
                True,
                False,
                "请明确说，把唤醒词改成某个名字。",
                "唤醒词指令不明确",
                self.phase,
            )
        custom = _extract_wakeword_change(text)
        if custom is None:
            return None
        if self._wakeword_change_submitter is None:
            return self._respond(
                True,
                False,
                "唤醒词修改失败，请稍后再试。",
                "唤醒词修改失败",
                self.phase,
            )
        if not self._wakeword_change_submitter(custom):
            return self._respond(
                True,
                False,
                "已有唤醒词修改正在处理，请稍后再试。",
                "唤醒词修改繁忙",
                self.phase,
            )
        return self._respond(
            True,
            True,
            "",
            "唤醒词修改已提交",
            self.phase,
        )

    # ── Agent 循环兜底（主链路接入底座，P0）─────────────────────
    def _route_before_agent(
        self,
        text: str | None,
        *,
        asr_confidence: float | None = None,
        asr_corrected: bool = False,
    ) -> InteractionResponse | None:
        decision = get_intent_gate().route(
            text,
            asr_confidence=asr_confidence,
            asr_corrected=asr_corrected,
        )
        if decision.state is RouteState.ALLOW:
            return None
        return self._respond(
            True,
            True,
            decision.reply,
            f"routing:{decision.state}:{decision.reason}:{decision.confidence:.4f}",
            self.phase,
        )

    def _try_agent_fallback(
        self,
        text: str,
        *,
        route_input: bool = True,
    ) -> InteractionResponse | None:
        """规则表未命中的输入交给本地 14B 自主对话循环；服务异常返回 None 保持静默。"""
        if route_input:
            routed = self._route_before_agent(text)
            if routed is not None:
                return routed
        try:
            from .agent_client import ask_agent, agent_healthy
            from .voice.voice_profile import (
                compose_agent_query,
                filter_reply,
                load_persona,
                load_profile,
            )

            if not agent_healthy():
                return None
            profile = load_profile()
            persona = load_persona(profile)
            content = ask_agent(compose_agent_query(text, persona))
        except Exception:  # 网络/服务异常：降级静默，不破坏既有链路
            return None
        if not content or not content.strip():
            return None
        style = profile["style"]
        verifier = get_reply_verifier(style["banned_phrases"], style["max_sentences"])
        checked = verifier.verify(ReplySchema(reply_text=content))
        reason = "Agent 回答"
        if not checked.accepted:
            retry_prompt = compose_agent_query(text, persona) + (
                "\n上一回答未通过本地安全校验。只重答一次：不得含营销或诱导话术，"
                "不得超过两句，不确定就明确说不确定。"
            )
            try:
                retried = ask_agent(retry_prompt)
                checked = verifier.verify(ReplySchema(reply_text=retried))
            except Exception:
                checked = verifier.verify(ReplySchema(reply_text=""))
            if checked.accepted:
                reason = "Agent 回答重试"
            else:
                checked = verifier.verify(ReplySchema(reply_text=verifier.config.verifier_fallback_reply))
                reason = "Agent 回答兜底"
        content = filter_reply(checked.text, profile)
        self.last_summary = content
        self.adjusted = False
        self.phase = _PENDING_CONFIRM
        return self._respond(True, True, content, reason, self.phase)

    # ── 天气直达（2026-10-29 新增）─────────────────────────────
    # 识别"查天气"意图 → 直查天气服务 → 一句话秒答。
    # 背景：此前天气指令落 14B 自由发挥 → 绕圈 119s 或甩一长串天气网链接（真机反馈：
    # "让他查天气，查出一大长串让我上天气网看，没直接回答"）。这里窄边界识别
    # 天气意图，直达天气源，绕过 14B；查询失败/无城市信息时返回 None 走原 14B 兜底。
    _WEATHER_INTENT = re.compile(
        r"(?:天气|气温|温度|多少度|几度|下雨|下雪|阴天|晴不晴|冷不冷|热不热|天气预报|天怎么样|天气如何)"
    )

    # 天气查询失败降级话术（2026-10-29 21:1x 加固）：意图命中但查询失败时
    # 快速给一句话反馈，不再静默降级 14B 干等 40s（真机反馈"查天气没回复"）。
    _WEATHER_DEGRADE = "天气服务暂时不可用，请稍后再试。"

    def _try_weather_fallback(self, text: str) -> InteractionResponse | None:
        """天气意图直达：返回一句话天气回答；非天气/查询失败返回 None 走 14B 兜底。"""
        if not self._WEATHER_INTENT.search(text):
            return None
        try:
            from .weather import query_weather  # 天气直达模块（标准库 urllib）
        except Exception:  # 模块缺失等：降级走 14B
            return None
        try:
            answer = query_weather(text)
        except Exception:  # 天气源异常：快速降级话术，不静默
            return self._respond(True, True, self._WEATHER_DEGRADE, "天气查询", self.phase)
        if not answer:
            return self._respond(True, True, self._WEATHER_DEGRADE, "天气查询", self.phase)
        self.last_summary = answer
        self.adjusted = False
        self.phase = _PENDING_CONFIRM
        return self._respond(True, True, answer, "天气查询", self.phase)

    # ── 征询闭环 ──────────────────────────────────────────────
    def _on_confirm(self) -> InteractionResponse:
        """确认通过：回到待命（征询闭环的确认步）。"""
        if self.phase != _PENDING_CONFIRM:
            # 无待确认结果：静默（真机反馈：频繁语音回应打扰）
            return self._respond(False, True, "", "无待确认结果", self.phase)
        self.phase = _IDLE
        return self._respond(True, True, "收到，已确认。随时可以继续。", "确认通过", self.phase)

    # ── 子智能体调用（MVP 入口：识别 + 引导；业务派发走编排引擎下一阶段接线）──
    def _on_subagent(self, text: str) -> InteractionResponse:
        """收到子智能体调用意图：确认入口就绪，引导给出具体任务内容。"""
        return self._respond(
            True,
            True,
            "子智能体调度入口已就绪。请说明要子智能体执行的具体任务内容，我会派发并汇报结果。",
            "子智能体调用",
            self.phase,
        )

    def _on_consult(self, text: str) -> InteractionResponse:
        """征询驱动：当前有结果时，征询是否调整（对话即操作）。"""
        if self.phase != _PENDING_CONFIRM or self.last_summary is None:
            return self._respond(False, True, "", "无已交付结果可征询", self.phase)
        spoken_summary = re.sub(r"[。！？!?]+", "；", self.last_summary).strip("；")
        spoken_summary = re.sub(r"\s+", " ", spoken_summary)
        return self._respond(
            True,
            True,
            f"当前结果：{spoken_summary}。你觉得怎么样，需要调整可以说插队或改优先级，也可以回复确认？",
            "征询中",
            self.phase,
        )

    def _on_adjust_request(self, text: str) -> InteractionResponse:
        """收到调整意图但未带明确指令时，引导给出具体参数。"""
        return self._respond(
            True,
            True,
            "可以调整。请说明要调整的任务 ID，以及是插队到某任务之前，还是修改优先级（0-100）。",
            "等待调整参数",
            self.phase,
        )

    # ── 队列调整（复用冻结引擎官方写通道）────────────────────
    def _try_adjust_command(self, text: str) -> InteractionResponse | None:
        # 中文别名归一：语音口语 ID（一号任务/任务一/1号任务）→ 真实任务 ID
        text = _resolve_task_alias(text)
        # 改优先级：任务ID + 优先级数字（如 "把 X 优先级设为 80" / "X 改成 80"）
        prio = _PRIORITY_COMMAND.search(text)
        if prio:
            task_id = prio.group("task_id")
            priority = int(prio.group("priority"))
            if not _TASK_ID.fullmatch(task_id):
                return self._respond(True, False, "任务 ID 非法。", "调整失败", self.phase)
            return self._adjust_priority(task_id, priority)

        # 插队：把 A 插到 B 之前
        insert = _INSERT_COMMAND.search(text)
        if insert:
            task_id = insert.group("task_id")
            target_id = insert.group("target")
            if not _TASK_ID.fullmatch(task_id) or not _TASK_ID.fullmatch(target_id):
                return self._respond(True, False, "任务 ID 非法。", "调整失败", self.phase)
            return self._requeue_before(task_id, target_id)

        # 含调整关键词但未解析出完整指令：明确报错而非静默回落
        if _ADJUST_KEYWORD.search(text):
            return self._respond(
                True,
                False,
                "调整指令不完整，请提供任务 ID 与参数（如“插队到某任务之前”或“优先级设为 0-100”）。",
                "调整失败",
                self.phase,
            )

        return None

    def _adjust_priority(self, task_id: str, priority: int) -> InteractionResponse:
        try:
            self.planner.adjust_priority(task_id, priority, actor="brain", reason="用户语音/文字调整")
        except (QueuePlanningError, ValueError) as exc:
            return self._respond(True, False, f"调整失败：{exc}", "调整失败", self.phase)
        self.adjusted = True
        return self._respond(
            True,
            True,
            f"已将任务 {task_id} 的优先级调整为 {priority}。",
            "调整完成",
            self.phase,
        )

    def _requeue_before(self, task_id: str, target_id: str) -> InteractionResponse:
        try:
            self.planner.requeue_before(task_id, target_id, actor="brain", reason="用户语音/文字调整")
        except (QueuePlanningError, ValueError) as exc:
            return self._respond(True, False, f"插队失败：{exc}", "调整失败", self.phase)
        self.adjusted = True
        return self._respond(
            True,
            True,
            f"已将任务 {task_id} 插到 {target_id} 之前。",
            "调整完成",
            self.phase,
        )

    # ── 异步交付三拍 ──────────────────────────────────────────
    def acknowledge_delivery(self, summary: str | None = None) -> str:
        """第一拍：告知"稍等，我整理一下"（异步交付默认形态，v2.3 §6 L7）。"""
        self.last_summary = summary or self.last_summary
        self.phase = _PENDING_CONFIRM
        return "稍等，我整理一下。"

    # ── 内部 ──────────────────────────────────────────────────
    def _respond(
        self,
        handled: bool,
        ok: bool,
        text: str,
        reason: str,
        phase: str,
    ) -> InteractionResponse:
        from .voice.voice_profile import filter_reply, load_profile

        filtered_text = filter_reply(text, load_profile())
        if self.last_summary == text:
            self.last_summary = filtered_text
        state = InteractionState(phase=phase, last_summary=self.last_summary, adjusted=self.adjusted)
        return InteractionResponse(handled, ok, filtered_text, state, reason)


# ── 意图规则（窄边界，与 intent.py 同风格）─────────────────────
_WAKEWORD_LABEL = r"(?:唤醒词|唤新词|花新词|叫醒词)"
_WAKEWORD_CHANGE_PATTERNS = (
    re.compile(
        rf"^(?:把|将)?{_WAKEWORD_LABEL}(?:改|换)(?:成|为)?"
        r"(?P<word>[\u4e00-\u9fff]{1,8}?)(?:吧|啊|呀)?[。！？!?.]*$"
    ),
    re.compile(
        r"^(?:从现在开始|以后)?叫(?P<word>[\u4e00-\u9fff]{1,8}?)"
        r"(?:来)?(?:唤醒|叫醒)我(?:吧|啊|呀)?[。！？!?.]*$"
    ),
)
_AMBIGUOUS_WAKEWORD_CHANGE = (
    re.compile(rf"^(?:把|将)?{_WAKEWORD_LABEL}(?:改|换)(?:成|为)?(?:什么|啥|哪个|哪一个)[。！？!?.]*$"),
    re.compile(rf"^(?:把|将)?{_WAKEWORD_LABEL}(?:改|换)(?:成|为)?[\u4e00-\u9fff]{{1,8}}(?:吗|呢|可不可以|行不行)[。！？!?.]*$"),
    re.compile(r"^星期五(?:可以吗|行吗|好吗)[。！？!?.]*$"),
)


def _extract_wakeword_change(text: str) -> str | None:
    for pattern in _WAKEWORD_CHANGE_PATTERNS:
        match = pattern.fullmatch(text)
        if match:
            return match.group("word")
    return None


def _is_ambiguous_wakeword_change(text: str) -> bool:
    return any(pattern.fullmatch(text) for pattern in _AMBIGUOUS_WAKEWORD_CHANGE)


_CONFIRM_INTENT = re.compile(r"(?:确认|可以|没问题|好的|就这样|行|收到|嗯好|OK|ok|是的|对|好(?:的|啊|吧)?)")
_ADJUST_INTENT = re.compile(r"(?:调整|改(?:一下)?|重排|挪一下|提前一下)")
_ADJUST_KEYWORD = re.compile(
    r"(?:优先级|优先|插队|插|改成|设为|调到|调整到|改为|调为|调成|重排|挪|提前|放)"
)
_CONSULT_INTENT = re.compile(r"(?:你觉得怎么样|怎么样|如何|行不行|行吗|OK吗|可以吗|感觉如何|是否满意)")
_PRIORITY_COMMAND = re.compile(
    r"(?:^|把|将|让)\s*(?P<task_id>[A-Za-z0-9][A-Za-z0-9._~-]*?)\s*"
    r"(?:优先级|优先|改成|设为|调到|调整到|改为|调为|调成)"
    r"(?:设为|改为|调为|调成|为|成|到|至)?\s*"
    r"(?P<priority>[0-9]{1,3})"
)
_INSERT_COMMAND = re.compile(
    r"(?:把|将|让)\s*(?P<task_id>[A-Za-z0-9][A-Za-z0-9._~-]*?)"
    r"\s*(?:插(?:队|入)?|挪|提前|放)\s*(?:到|至)?\s*"
    r"(?P<target>[A-Za-z0-9][A-Za-z0-9._~-]*?)\s*(?:之前|前面)"
)

# 中文任务别名 → 真实任务 ID（语音场景：英文 ID 经 ASR 识别不稳，如 voice-02→VALS02）
# 用户口语说「一号任务」，归一为真实 ID 后走既有调整正则（voice-01 满足 [A-Za-z0-9] 校验）
_TASK_ALIASES = {
    "一号任务": "voice-01",
    "二号任务": "voice-02",
    "三号任务": "voice-03",
    "1号任务": "voice-01",
    "2号任务": "voice-02",
    "3号任务": "voice-03",
    "任务一": "voice-01",
    "任务二": "voice-02",
    "任务三": "voice-03",
}


def _resolve_task_alias(text: str) -> str:
    """把文本中的中文任务别名替换为真实任务 ID（长别名优先，防部分替换）。"""
    for alias in sorted(_TASK_ALIASES, key=len, reverse=True):
        text = text.replace(alias, _TASK_ALIASES[alias])
    return text


# 子智能体调用意图（MVP 窄边界）
# 精确：子智能体/子代理/subagent；模糊兜底：含「智能体」且带调用动作词
# （ASR 错字场景：「帮我调用指智能体」→「子」误识为「指」，靠模糊兜底命中）
_SUBAGENT_INTENT = re.compile(r"(?:子智能体|子代理|subagent)")
_SUBAGENT_ACTION_WORDS = ("调用", "派", "让", "叫", "交给", "启动", "唤醒", "问问")


def _fuzzy_subagent(text: str) -> bool:
    """模糊子智能体判定：文本含「智能体」且带调用动作词（ASR 错字容忍）。"""
    if "智能体" not in text.lower():
        return False
    return any(word in text for word in _SUBAGENT_ACTION_WORDS)


_DEFAULT_ASR_NEAR_HOMOPHONE = (
    ("水量天听", "天气"),
    ("水平听听清", "天气"),
    ("水平听", "天气"),
    ("明天上海的这", "明天上海的天气"),
)
_ASR_NORMALIZE_PATH = Path(__file__).resolve().parents[2] / "config" / "asr-normalize.json"
_ASR_WEATHER_CONTEXT = re.compile(r"(?:查|看|问|今天|明天|后天|大后天|气温|温度|下雨|下雪)")


def _load_asr_near_homophones(path: Path = _ASR_NORMALIZE_PATH) -> tuple[tuple[str, str], ...]:
    """Load literal phrase mappings; any missing/invalid config falls back safely."""
    try:
        import json as _json

        payload = _json.loads(path.read_text(encoding="utf-8"))
        rows = payload["mappings"]
        if not isinstance(rows, list) or not rows:
            raise ValueError("mappings must be a non-empty list")
        mappings = []
        for row in rows:
            wrong, right = row["from"], row["to"]
            if not isinstance(wrong, str) or not isinstance(right, str):
                raise ValueError("mapping values must be strings")
            if len(wrong) < 2 or not wrong or not right:
                raise ValueError("single-character or empty mappings are forbidden")
            mappings.append((wrong, right))
        return tuple(sorted(mappings, key=lambda item: len(item[0]), reverse=True))
    except (OSError, KeyError, TypeError, ValueError, _json.JSONDecodeError):
        return _DEFAULT_ASR_NEAR_HOMOPHONE


_ASR_NEAR_HOMOPHONE = _load_asr_near_homophones()


def _is_contextual_weather_correction(text: str | None, normalized: str) -> bool:
    if not isinstance(text, str) or "天气" not in normalized:
        return False
    compact = re.sub(r"\s+", "", text)
    corrected = any(wrong in compact for wrong, _ in _ASR_NEAR_HOMOPHONE)
    return corrected and bool(_ASR_WEATHER_CONTEXT.search(compact))


def _normalize_utterance(text: str | None) -> str:
    """NFKC + 繁体→简体（复用 intent.py 的映射，独立实现避免循环依赖）。"""
    if not isinstance(text, str):
        return ""
    import unicodedata

    _TRAD_TO_SIMP = str.maketrans(
        "任務隊列狀態進度進展情況執行失敗凍結排隊查詢彙報告訴請幫個當前嘗試無插隊優先級調整確認識別錯誤異常處理將級為調於",
        "任务队列状态进度进展情况执行失败冻结排队查询汇报告诉请帮个当前尝试无插队优先级调整确认识别错误异常处理将级为调于",
    )
    value = unicodedata.normalize("NFKC", text).strip()
    value = value.translate(_TRAD_TO_SIMP)
    value = re.sub(r"\s+", "", value)
    # 只做配置登记的整词/短语字面替换，禁止单字映射；配置异常时使用内置默认表。
    for wrong, right in _ASR_NEAR_HOMOPHONE:
        # “水天”也可出现在“水天一色”中；仅在明确天气上下文纠正该短词。
        if wrong == "水天" and (
            "水天一色" in value or not _ASR_WEATHER_CONTEXT.search(value)
        ):
            continue
        if wrong in value:
            value = value.replace(wrong, right)
    return value


def _levenshtein(a: str, b: str) -> int:
    """编辑距离（模糊匹配用，短文本场景 O(mn) 足够）。"""
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cur[j] = min(
                prev[j] + 1,          # 删除
                cur[j - 1] + 1,       # 插入
                prev[j - 1] + (0 if ca == cb else 1),  # 替换
            )
        prev = cur
    return prev[-1]


# 模糊兜底意图词（ASR 错字容忍）：
# 调整类优先判定（"一号任务/插队/优先级"语义更具体，防被查询类"任务"吞掉）
_FUZZY_ADJUST_KEYWORDS = ("插队", "优先级", "一号任务", "二号任务", "三号任务", "优先处理", "重排", "提前", "调整")
_FUZZY_CONFIRM_KEYWORDS = ("确认", "没问题", "就这样", "收到", "可以了", "就这个", "不改了")
_FUZZY_QUERY_KEYWORDS = ("任务状态", "任务进度", "查询", "看看", "进展", "执行情况", "汇报", "当前任务", "在做什么")
# 编辑距离短语库（≤12 字，错 1-2 字仍命中）
_FUZZY_PHRASES = {
    "adjust": ("优先处理一号任务", "插队到前面", "调整优先级", "改优先级", "重排任务"),
    "confirm": ("确认通过", "可以了", "就这样吧", "没问题"),
    "query": ("查询任务状态", "任务状态", "查询任务进度", "当前任务", "任务进展"),
}


def _fuzzy_intent_fallback(text: str) -> str | None:
    """模糊意图兜底：ASR 错字/幻觉前缀时按关键词与编辑距离归类。

    Returns
    -------
    "adjust" | "confirm" | "query" | None（不命中）
    """
    # 1. 关键词包含（幻觉前缀如"此外，"不影响核心词命中）
    if any(k in text for k in _FUZZY_ADJUST_KEYWORDS):
        return "adjust"
    if any(k in text for k in _FUZZY_CONFIRM_KEYWORDS):
        return "confirm"
    if any(k in text for k in _FUZZY_QUERY_KEYWORDS):
        return "query"
    # 2. 编辑距离（仅短文本，避免长句误配）
    if len(text) <= 14:
        for intent, phrases in _FUZZY_PHRASES.items():
            for phrase in phrases:
                dist = _levenshtein(text, phrase)
                threshold = 1 if len(phrase) <= 6 else 2
                if dist <= threshold:
                    return intent
    return None


__all__ = [
    "InteractionLoop",
    "InteractionResponse",
    "InteractionState",
    "InteractionLoopError",
]


class InteractionLoopError(ValueError):
    """Raised when the interaction loop cannot be constructed safely."""
