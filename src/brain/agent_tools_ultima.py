"""Ultima Agent 自定义工具集（注册进 OpenJarvis ToolRegistry，供本地 8B 自主调用）。

对齐 product-plan v2.3 冻结口径：
- ultima_task_query   ：L2 任务域查询，聚合汇报（结论先行/聚合/异常优先，对齐 L5 汇报三规则）
- ultima_task_adjust  ：L7 队列调整（改优先级/插队），复用冻结队列引擎官方写通道
- ultima_env_snapshot ：L3 环境快照（硬件/磁盘/文件/应用），复用 src.brain.environment

设计约束：
- 仅标准库 + UltimaAgent 自有模块（tasks/queue_engine / src.brain），不引入第三方依赖；
- 写通道只走 QueuePlanner 官方入口（adjust_priority / requeue_before），不绕过冻结引擎；
- 工具返回中文规范文本，供 8B 直接引用进最终回答；
- 本模块运行在 venv-openjarvis 进程（agent_server）内，sys.path 须含 PROJECT_ROOT。
"""

from __future__ import annotations

import json
import os
import re
import sys
import threading
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from openjarvis.core.registry import ToolRegistry  # noqa: E402
from openjarvis.core.types import ToolResult  # noqa: E402
from openjarvis.tools._stubs import BaseTool, ToolSpec  # noqa: E402
from openjarvis.tools.agent_tools import AgentKillTool, AgentSpawnTool  # noqa: E402
from openjarvis.tools.memory_manage import MemoryManageTool  # noqa: E402
from openjarvis.tools.skill_manage import SkillManageTool  # noqa: E402
from openjarvis.tools.web_search import WebSearchTool  # noqa: E402

from tasks.queue_engine import QueuePlanner, QueueStorage  # noqa: E402
from tasks.queue_engine.priority_deps import QueuePlanningError  # noqa: E402
from tasks.queue_engine.storage import StorageError  # noqa: E402

# 中文任务别名（与 src/brain/interaction.py 的 _TASK_ALIASES 保持同步）
_TASK_ALIASES = {
    "一号任务": "voice-01",
    "1号任务": "voice-01",
    "任务一": "voice-01",
    "二号任务": "voice-02",
    "2号任务": "voice-02",
    "任务二": "voice-02",
    "三号任务": "voice-03",
    "3号任务": "voice-03",
    "任务三": "voice-03",
}

_AGENT_TOOL_DATA = PROJECT_ROOT / "data" / "agent_tools"
_SKILL_NAME_RE = re.compile(r"[A-Za-z0-9_-]{1,64}")


class _Utf8SigQueueStorage(QueueStorage):
    """仅兼容 Manager 的 UTF-8 BOM 索引；其余读写规则保持底座原实现。"""

    def load_tasks(self) -> list[dict[str, Any]]:
        try:
            return super().load_tasks()
        except StorageError as exc:
            raw = self.index_path.read_bytes()
            if not raw.startswith(b"\xef\xbb\xbf"):
                raise
            try:
                tasks = json.loads(raw.decode("utf-8-sig"))
            except (UnicodeError, json.JSONDecodeError) as parse_exc:
                raise StorageError(f"invalid task index: {parse_exc}") from parse_exc
            if not isinstance(tasks, list):
                raise StorageError("tasks.json must contain a JSON array") from exc
            for task in tasks:
                self.validate_index_record(task)
            return tasks


def _renamed_result(name: str, result: ToolResult) -> ToolResult:
    """保留底座执行结果，仅把工具名映射为 8B 实际调用的 Ultima 名称。"""
    return ToolResult(
        tool_name=name,
        content=result.content,
        success=result.success,
        usage=result.usage,
        cost_usd=result.cost_usd,
        latency_seconds=result.latency_seconds,
        metadata=result.metadata,
    )


@ToolRegistry.register("ultima_subagent")
class UltimaSubagentTool(BaseTool):
    """通过底座 agent_spawn 登记并真实执行一个受限子智能体任务。"""

    tool_id = "ultima_subagent"

    def __init__(self, child_factory: Callable[[], Any] | None = None) -> None:
        self._child_factory = child_factory or self._create_child

    @staticmethod
    def _create_child() -> Any:
        from openjarvis import Jarvis

        return Jarvis(engine_key="ollama", model="qwen3-8b-uncensored")

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name=self.tool_id,
            description=(
                "派发一个独立的 Ultima 子智能体去执行查询任务并回传真实结果。"
                "当用户说“派个子任务”“让子智能体去查”“交给另一个智能体处理”时调用；"
                "不要只口头声称已派发。"
            ),
            parameters={
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "交给子智能体执行的完整任务。",
                    }
                },
                "required": ["task"],
            },
            category="agents",
        )

    def execute(self, **params: Any) -> ToolResult:
        task = str(params.get("task") or "").strip()
        if not task:
            return ToolResult(
                tool_name=self.tool_id,
                content="子智能体任务不能为空。",
                success=False,
            )

        spawned = AgentSpawnTool().execute(
            agent_type="native_react",
            query=task,
            tools="ultima_task_query,ultima_env_snapshot,ultima_web_search",
        )
        if not spawned.success:
            return _renamed_result(self.tool_id, spawned)
        agent_id = str(json.loads(spawned.content)["agent_id"])
        child = None
        try:
            child = self._child_factory()
            result = child.ask_full(
                task,
                agent="native_react",
                tools=[
                    "ultima_task_query",
                    "ultima_env_snapshot",
                    "ultima_web_search",
                ],
                context=False,
                max_tokens=768,
            )
            content = str(result.get("content") or "").strip()
            tool_results = result.get("tool_results") or []
            if not content and not tool_results:
                return ToolResult(
                    tool_name=self.tool_id,
                    content=f"子智能体 {agent_id} 未返回有效结果。",
                    success=False,
                    metadata={"agent_id": agent_id},
                )
            evidence = json.dumps(tool_results, ensure_ascii=False)
            return ToolResult(
                tool_name=self.tool_id,
                content=(
                    f"子智能体 {agent_id} 执行结果：{content}\n"
                    f"子智能体工具证据：{evidence}"
                ),
                success=True,
                metadata={"agent_id": agent_id, "tool_results": tool_results},
            )
        except Exception as exc:
            return ToolResult(
                tool_name=self.tool_id,
                content=f"子智能体 {agent_id} 执行失败：{exc}",
                success=False,
                metadata={"agent_id": agent_id},
            )
        finally:
            if child is not None:
                child.close()
            AgentKillTool().execute(agent_id=agent_id)


@ToolRegistry.register("ultima_skill_manage")
class UltimaSkillManageTool(BaseTool):
    """把底座 skill_manage 限定到 UltimaAgent 项目内的数据目录。"""

    tool_id = "ultima_skill_manage"

    def __init__(self, skills_dir: Path | str | None = None) -> None:
        self._delegate = SkillManageTool(skills_dir or (_AGENT_TOOL_DATA / "skills"))

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name=self.tool_id,
            description=(
                "管理 Ultima 自主技能：可列出、创建、读取或删除技能。"
                "当用户问“列出你能用的技能”“创建一个技能”“读取某技能”时调用。"
            ),
            parameters=self._delegate.spec.parameters,
            category="skill",
        )

    def execute(self, **params: Any) -> ToolResult:
        action = str(params.get("action") or "list")
        name = str(params.get("name") or "")
        if action in {"create", "load", "delete"} and not _SKILL_NAME_RE.fullmatch(name):
            return ToolResult(
                tool_name=self.tool_id,
                content="技能名仅允许 1-64 位字母、数字、下划线或连字符。",
                success=False,
            )
        return _renamed_result(self.tool_id, self._delegate.execute(**params))


@ToolRegistry.register("ultima_memory")
class UltimaMemoryTool(BaseTool):
    """把底座 memory_manage 限定到 UltimaAgent 项目内的持久记忆。"""

    tool_id = "ultima_memory"

    def __init__(self, memory_path: Path | str | None = None) -> None:
        self._delegate = MemoryManageTool(memory_path or (_AGENT_TOOL_DATA / "MEMORY.md"))

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name=self.tool_id,
            description=(
                "保存和回读 Ultima 的持久记忆。用户说“记住……”时用 action=add；"
                "用户问“你记得什么”“我的偏好是什么”时用 action=read；也支持更新和删除。"
            ),
            parameters=self._delegate.spec.parameters,
            category="memory",
        )

    def execute(self, **params: Any) -> ToolResult:
        return _renamed_result(self.tool_id, self._delegate.execute(**params))


@ToolRegistry.register("ultima_web_search")
class UltimaWebSearchTool(BaseTool):
    """使用底座 web_search 获取带来源 URL 的实时外部信息。"""

    tool_id = "ultima_web_search"
    is_local = False

    def __init__(self) -> None:
        self._delegate = WebSearchTool()

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name=self.tool_id,
            description=(
                "上网检索当前或外部信息并返回真实来源 URL。"
                "当用户说“上网查”“搜索今天的信息”“找最新资料”时调用；"
                "搜索失败必须如实返回错误，禁止编造来源。"
            ),
            parameters=self._delegate.spec.parameters,
            category="web",
        )

    def execute(self, **params: Any) -> ToolResult:
        if not str(params.get("query") or "").strip():
            return ToolResult(
                tool_name=self.tool_id,
                content="缺少搜索关键词，无法执行网络检索。",
                success=False,
            )
        return _renamed_result(self.tool_id, self._delegate.execute(**params))


def _normalize_task_id(raw: str) -> str:
    """任务 ID 归一：中文别名 → 标准 ID；原样保留已标准化的 ID。"""
    key = raw.strip()
    if key in _TASK_ALIASES:
        return _TASK_ALIASES[key]
    return key


@ToolRegistry.register("ultima_task_query")
class UltimaTaskQueryTool(BaseTool):
    """查询 Ultima Agent 任务队列状态（聚合汇报，异常优先）。"""

    tool_id = "ultima_task_query"

    def __init__(self, root: Path | str | None = None) -> None:
        self._root = Path(root) if root is not None else PROJECT_ROOT / "tasks"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="ultima_task_query",
            description=(
                "查询 Ultima Agent 任务队列状态，返回任务总数、各状态计数"
                "（排队中/进行中/已完成/失败/阻塞）与异常任务优先列表。"
                "当用户问'任务状态''任务队列''任务怎么样了''有哪些任务''进度如何'时调用。"
            ),
            parameters={
                "type": "object",
                "properties": {},
            },
            category="task",
        )

    def execute(self, **params: Any) -> ToolResult:
        storage = _Utf8SigQueueStorage(self._root)
        try:
            tasks = storage.load_tasks()
        except Exception as exc:  # 读取失败不崩溃，返回诚实错误
            return ToolResult(
                tool_name="ultima_task_query",
                content=f"任务队列读取失败：{exc}",
                success=False,
            )
        total = len(tasks)
        counts: dict[str, int] = {}
        for item in tasks:
            state = str(item.get("state") or "UNKNOWN").upper()
            counts[state] = counts.get(state, 0) + 1
        # 异常优先（对齐 L5 汇报三规则：结论先行/聚合/异常优先）
        abnormal = [
            f"{item.get('task_id')}({item.get('state')})"
            for item in tasks
            if str(item.get("state") or "").upper() in {"FAILED", "BLOCKED"}
        ]
        parts = [f"当前共 {total} 个任务。"]
        summary = "，".join(
            f"{_CN_STATE.get(s, s.lower())} {n}" for s, n in counts.items()
        )
        if summary:
            parts.append(f"状态汇总：{summary}。")
        if abnormal:
            parts.append("异常任务：" + "；".join(abnormal) + "。")
        else:
            parts.append("无当前异常。")
        return ToolResult(
            tool_name="ultima_task_query",
            content="".join(parts),
            success=True,
        )


_CN_STATE = {
    "QUEUED": "排队中",
    "RUNNING": "进行中",
    "COMPLETED": "已完成",
    "FAILED": "失败",
    "BLOCKED": "阻塞",
}


@ToolRegistry.register("ultima_task_adjust")
class UltimaTaskAdjustTool(BaseTool):
    """调整 Ultima Agent 任务队列（改优先级/插队）。"""

    tool_id = "ultima_task_adjust"

    def __init__(self, root: Path | str | None = None) -> None:
        self._root = Path(root) if root is not None else PROJECT_ROOT / "tasks"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="ultima_task_adjust",
            description=(
                "调整 Ultima Agent 任务队列。action=priority 时把任务的优先级改为"
                " priority（整数）；action=requeue 时把任务插到 target_id 任务之前。"
                "task_id 支持中文别名（一号任务/任务一/1号任务 等）或标准 ID。"
                "仅可调整排队中(QUEUED)的任务。"
                "当用户说'把某任务优先级设为X''把某任务插到某任务前面'时调用。"
            ),
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["priority", "requeue"],
                        "description": "操作类型：priority=改优先级；requeue=插队。",
                    },
                    "task_id": {
                        "type": "string",
                        "description": "目标任务 ID 或中文别名。",
                    },
                    "priority": {
                        "type": "integer",
                        "description": "新优先级（action=priority 时必填）。",
                    },
                    "target_id": {
                        "type": "string",
                        "description": "插队目标任务 ID（action=requeue 时必填）。",
                    },
                },
                "required": ["action", "task_id"],
            },
            category="task",
        )

    def execute(self, **params: Any) -> ToolResult:
        action = params.get("action", "")
        task_id = _normalize_task_id(str(params.get("task_id", "")))
        if not task_id:
            return ToolResult(
                tool_name="ultima_task_adjust",
                content="缺少任务 ID。",
                success=False,
            )
        try:
            storage = _Utf8SigQueueStorage(self._root)
            planner = QueuePlanner(storage)
            if action == "priority":
                priority = params.get("priority")
                if priority is None:
                    return ToolResult(
                        tool_name="ultima_task_adjust",
                        content="改优先级操作缺少 priority 参数。",
                        success=False,
                    )
                planner.adjust_priority(
                    task_id, int(priority), actor="agent", reason="对话/语音指令调整"
                )
                return ToolResult(
                    tool_name="ultima_task_adjust",
                    content=f"已将任务 {task_id} 的优先级调整为 {int(priority)}。",
                    success=True,
                )
            if action == "requeue":
                target_id = _normalize_task_id(str(params.get("target_id", "")))
                if not target_id:
                    return ToolResult(
                        tool_name="ultima_task_adjust",
                        content="插队操作缺少 target_id 参数。",
                        success=False,
                    )
                planner.requeue_before(
                    task_id, target_id, actor="agent", reason="对话/语音指令插队"
                )
                return ToolResult(
                    tool_name="ultima_task_adjust",
                    content=f"已将任务 {task_id} 插到任务 {target_id} 之前。",
                    success=True,
                )
            return ToolResult(
                tool_name="ultima_task_adjust",
                content=f"未知操作类型：{action}（可选 priority / requeue）。",
                success=False,
            )
        except QueuePlanningError as exc:
            return ToolResult(
                tool_name="ultima_task_adjust",
                content=f"调整失败：{exc}",
                success=False,
            )
        except Exception as exc:  # 引擎异常兜底
            return ToolResult(
                tool_name="ultima_task_adjust",
                content=f"调整失败：{exc}",
                success=False,
            )


@ToolRegistry.register("ultima_env_snapshot")
class UltimaEnvSnapshotTool(BaseTool):
    """获取本机环境快照（硬件/磁盘/文件/应用）。"""

    tool_id = "ultima_env_snapshot"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="ultima_env_snapshot",
            description=(
                "获取本机环境快照：CPU/内存/GPU/操作系统、磁盘空间、指定文件状态、"
                "运行中的应用窗口。当用户问'系统环境''硬件配置''磁盘空间'"
                "'这台电脑什么配置''有哪些程序在运行'时调用。"
            ),
            parameters={
                "type": "object",
                "properties": {
                    "files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "可选：要检查状态的文件路径列表。",
                    },
                },
            },
            category="env",
            # 工具本体约 2-3s；显式放宽到 90s，避免进程级共享
            # _BoundedToolRunner(8 workers) 排队或慢盘时被默认 30s 硬限误杀。
            timeout_seconds=90.0,
        )

    def execute(self, **params: Any) -> ToolResult:
        from src.brain.environment import capture_snapshot

        files: list[str] = list(params.get("files") or [])
        try:
            snap = capture_snapshot(file_targets=files or None)
        except Exception as exc:
            return ToolResult(
                tool_name="ultima_env_snapshot",
                content=f"环境快照采集失败：{exc}",
                success=False,
            )
        hw = snap.hardware
        lines = [
            f"操作系统：{hw.os_name} {hw.os_version}（{hw.arch}）",
            f"CPU：{hw.cpu_model or '未知'}（{hw.cpu_cores} 核 / {hw.cpu_logical} 线程）",
            f"内存：{hw.memory_total_gb:.1f} GB（可用 {hw.memory_available_gb:.1f} GB）",
        ]
        if hw.gpu:
            lines.append("GPU：" + "；".join(hw.gpu))
        disks = snap.disks
        if disks:
            for d in disks:
                lines.append(
                    f"磁盘 {d.mount}：共 {d.total_gb:.1f} GB，剩余 {d.free_gb:.1f} GB"
                )
        apps = snap.apps
        if apps:
            names = "、".join(a.name for a in apps[:10])
            lines.append(f"运行中应用：{names}")
        return ToolResult(
            tool_name="ultima_env_snapshot",
            content="\n".join(lines),
            success=True,
        )


# --------------------------------------------------------------- 派单编排
# 主脑的职责是「接单 → 派给外脑 → 逐环节回报」，不是把活推回用户。
# 本组工具给主脑一条真正能派出去的通道：派单立即返回，外脑（DeepSeek）
# 出方案在后台线程异步完成，主脑靠 dispatch_status 逐环节汇报。
# 只有本工具返回成功，主脑才算真派了；规则第 11 条据此禁止空口声称已派。

_DISPATCH_DIR = PROJECT_ROOT / "data" / "mainbrain" / "dispatches"
_DEEPSEEK_CHAT_URL = "https://api.deepseek.com/chat/completions"
_DEEPSEEK_MODEL = "deepseek-chat"
_DEEPSEEK_TIMEOUT = 120.0

DISPATCH_PLANNER_PROMPT = """你是 Ultima 的审计外脑（DeepSeek）。主脑 8B 已接单，把用户诉求派给你。
三方分工：主脑只做查询与编排；你是审计外脑，负责拆工单/出方案/定验收/审计监管并向下派 Codex；
Codex 是代码外脑，是唯一执行代码的一方。你不写代码、不改文件、不声称已改动。
本轮请给出：
1) 工单拆解（每条含范围、涉及文件、验收门、禁止项）；
2) 技术方案要点、关键风险与回退方式；
3) 可机检的验收标准；
4) 是否需要向 Codex 派单，以及首张工单草案。
不要编造不存在的文件路径。"""

_DISPATCH_STATE_CN = {
    "DISPATCHED": "已派出",
    "PLANNING": "外脑出方案中",
    "PLANNED": "方案已回",
    "FAILED": "外脑调用失败",
}


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _notify_event(text: str) -> None:
    """把派单进展推到事件总线（语音/面板消费）。推送失败不影响派单结果落盘。"""
    try:
        from src.brain.events import get_event_bus

        get_event_bus().emit_event("message", {"text": text, "role": "jarvis"})
    except Exception:  # noqa: BLE001 - 事件总线不可用不是派单失败
        pass


def _deepseek_api_key() -> str:
    """环境变量优先，其次读 config/.env；两处都没有则视为未配置。"""
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if key:
        return key
    env_file = PROJECT_ROOT / "config" / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if stripped.startswith("DEEPSEEK_API_KEY"):
                return stripped.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _dispatch_path(dispatch_id: str) -> Path:
    return _DISPATCH_DIR / f"{dispatch_id}.json"


def _write_dispatch(record: dict[str, Any]) -> None:
    """原子写：先落临时文件再 replace，避免半截 JSON 被读到。"""
    _DISPATCH_DIR.mkdir(parents=True, exist_ok=True)
    target = _dispatch_path(str(record["dispatch_id"]))
    tmp = target.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    tmp.replace(target)


def _read_dispatch(dispatch_id: str) -> dict[str, Any] | None:
    path = _dispatch_path(dispatch_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _call_deepseek_planner(task: str) -> str:
    """纯标准库直调 DeepSeek，不引第三方依赖、不经过 Jarvis 引擎。"""
    key = _deepseek_api_key()
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY 未配置，无法派给外脑")
    payload = {
        "model": _DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": DISPATCH_PLANNER_PROMPT},
            {"role": "user", "content": task},
        ],
        "temperature": 0.2,
        "max_tokens": 2048,
        "stream": False,
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        _DEEPSEEK_CHAT_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
    )
    with urllib.request.urlopen(request, timeout=_DEEPSEEK_TIMEOUT) as response:
        data = json.loads(response.read().decode("utf-8"))
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("外脑返回空结果")
    return str((choices[0].get("message") or {}).get("content") or "").strip()


def _run_dispatch_worker(dispatch_id: str, task: str) -> None:
    """后台线程：标记 PLANNING → 调外脑 → 落方案或失败原因。"""
    record = _read_dispatch(dispatch_id) or {"dispatch_id": dispatch_id, "task": task}
    record["state"] = "PLANNING"
    record["updated_at"] = _now_iso()
    try:
        _write_dispatch(record)
    except OSError:
        pass
    try:
        proposal = _call_deepseek_planner(task)
        record = _read_dispatch(dispatch_id) or record
        record["state"] = "PLANNED"
        record["proposal"] = proposal
        record.pop("error", None)
    except Exception as exc:  # 外脑侧任何失败都要如实落盘，不能吞
        record = _read_dispatch(dispatch_id) or record
        record["state"] = "FAILED"
        record["error"] = f"{type(exc).__name__}: {exc}"
    record["updated_at"] = _now_iso()
    try:
        _write_dispatch(record)
    except OSError:
        pass
    # 关键环节主动汇报：方案回来或失败都要说，不能让用户干等、也不知道断没断。
    if record.get("state") == "PLANNED":
        _notify_event(f"派单 {dispatch_id} 的方案回来了，要我讲给你听吗？")
    elif record.get("state") == "FAILED":
        _notify_event(f"派单 {dispatch_id} 外脑调用失败：{record.get('error')}")


@ToolRegistry.register("ultima_dispatch")
class UltimaDispatchTool(BaseTool):
    """主脑接单后的派单通道：把动手类任务交给外脑出方案。"""

    tool_id = "ultima_dispatch"
    is_local = False

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="ultima_dispatch",
            description=(
                "把非查询类诉求派给 DeepSeek（审计外脑），立即返回派单号和状态，工单与方案由它异步产出。"
                "凡是修改、开发、制作、设计、修复、接入这类诉求，先用一句话接单，再调用本工具派出去。"
                "DeepSeek 负责拆工单/出方案/定验收/审计，代码执行只由 Codex 承担。"
                "只有本工具返回成功才算真的派出去了；没调用它就不许声称已派单。"
            ),
            parameters={
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "用户要求做什么，用用户原话，不要改写或补全。",
                    },
                },
                "required": ["task"],
            },
            category="dispatch",
            # 只做落盘 + 起线程，正常远小于 1s；给 30s 足够容错
            timeout_seconds=30.0,
        )

    def execute(self, **params: Any) -> ToolResult:
        task = str(params.get("task") or "").strip()
        if not task:
            return ToolResult(
                tool_name=self.tool_id,
                content="没有收到要派的任务内容，无法派单。",
                success=False,
            )
        dispatch_id = "D" + datetime.now().strftime("%Y%m%d-%H%M%S")
        record: dict[str, Any] = {
            "dispatch_id": dispatch_id,
            "task": task,
            "state": "DISPATCHED",
            "proposal": None,
            "error": None,
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        }
        try:
            _write_dispatch(record)
        except OSError as exc:
            return ToolResult(
                tool_name=self.tool_id,
                content=f"派单记录落盘失败，本轮没有派出：{exc}",
                success=False,
            )
        threading.Thread(
            target=_run_dispatch_worker,
            args=(dispatch_id, task),
            name=f"dispatch-{dispatch_id}",
            daemon=True,
        ).start()
        return ToolResult(
            tool_name=self.tool_id,
            content=(
                f"已派给外脑 DeepSeek，派单号 {dispatch_id}。"
                "方案生成中，回来我汇报给你。"
            ),
            success=True,
            metadata={"dispatch_id": dispatch_id, "state": "DISPATCHED"},
        )


@ToolRegistry.register("ultima_dispatch_status")
class UltimaDispatchStatusTool(BaseTool):
    """查派单进度，供主脑逐环节回报。"""

    tool_id = "ultima_dispatch_status"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name=self.tool_id,
            description=(
                "查派单进度与 DeepSeek（审计外脑）的工单/方案产出。"
                "用户问「那个修好了没」「方案出来了吗」「进展如何」时调用。"
                "省略 dispatch_id 时返回最近几单的概览。"
            ),
            parameters={
                "type": "object",
                "properties": {
                    "dispatch_id": {
                        "type": "string",
                        "description": "可选，派单号；省略则列出最近派单。",
                    },
                },
            },
            category="dispatch",
        )

    def execute(self, **params: Any) -> ToolResult:
        dispatch_id = str(params.get("dispatch_id") or "").strip()
        if dispatch_id:
            record = _read_dispatch(dispatch_id)
            if not record:
                return ToolResult(
                    tool_name=self.tool_id,
                    content=f"没找到派单 {dispatch_id}。",
                    success=False,
                )
            state = str(record.get("state") or "")
            parts = [f"派单 {dispatch_id}：{_DISPATCH_STATE_CN.get(state, state)}。"]
            proposal = str(record.get("proposal") or "").strip()
            if proposal:
                parts.append("外脑方案：" + proposal[:800])
            error = str(record.get("error") or "").strip()
            if error:
                parts.append("失败原因：" + error)
            return ToolResult(
                tool_name=self.tool_id,
                content="".join(parts),
                success=True,
                metadata={"dispatch_id": dispatch_id, "state": state},
            )

        if not _DISPATCH_DIR.exists():
            return ToolResult(
                tool_name=self.tool_id,
                content="还没有任何派单记录。",
                success=True,
            )
        files = sorted(_DISPATCH_DIR.glob("D*.json"), reverse=True)[:5]
        if not files:
            return ToolResult(
                tool_name=self.tool_id,
                content="还没有任何派单记录。",
                success=True,
            )
        lines = []
        for path in files:
            record = _read_dispatch(path.stem)
            if not record:
                continue
            state = str(record.get("state") or "")
            task = str(record.get("task") or "")[:40]
            lines.append(f"{path.stem}：{_DISPATCH_STATE_CN.get(state, state)}｜{task}")
        return ToolResult(
            tool_name=self.tool_id,
            content="最近派单：" + "；".join(lines) + "。",
            success=True,
        )


__all__ = [
    "UltimaSubagentTool",
    "UltimaSkillManageTool",
    "UltimaMemoryTool",
    "UltimaWebSearchTool",
    "UltimaTaskQueryTool",
    "UltimaTaskAdjustTool",
    "UltimaEnvSnapshotTool",
    "UltimaDispatchTool",
    "UltimaDispatchStatusTool",
]
