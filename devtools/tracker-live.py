"""看板实时数据采集：读 runs 目录 + 进程存活 + final-message，生成 docs/tracker/live-data.js。

判定规则（与 Manager ExecutionBoard 同口径，不人工填写）：
- pid 存活 且 无 final-message           -> 运行中（elapsed 随刷新自动增长）
- pid 不存活 且 有 final-message         -> 已结束（待复审/已交付）
- pid 不存活 且 无 final-message         -> 中断（异常终止）

用法：python -B devtools/tracker-live.py
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes as _wintypes
import json
import re
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(r"H:\UltimaAI\UltimaAgent")
RUNS = ROOT / "tasks" / "queue" / "runs"
GLOBAL_QUEUE = Path(r"H:\UltimaAI\_shared\queue\global-queue-index.md")
OUT = ROOT / "docs" / "tracker" / "live-data.js"
CST = timezone(timedelta(hours=8))

ACTIVITY_RULES = [
    ("apply_patch", "整理补丁"),
    ("exec_command", "运行命令"),
    ("shell", "运行命令"),
    ("token_count", "等待模型响应"),
    ("turn", "等待模型响应"),
    ("task_complete", "收尾"),
]


def process_start(pid: int | None) -> datetime | None:
    """取进程真实启动时间。PID 会被系统复用，单看 pid 存在会把旧单判成在跑。

    直接调 kernel32 读进程创建时间，不起子进程——原来用 subprocess 起 powershell
    查一次，每轮刷 6 条记录就弹 6 个控制台窗口（L78）。
    """
    if not pid:
        return None
    try:
        k32 = ctypes.windll.kernel32
        # PROCESS_QUERY_LIMITED_INFORMATION = 0x1000，够读时间戳且不受更高权限限制
        handle = k32.OpenProcess(0x1000, False, int(pid))
        if not handle:
            return None
        try:
            created = _wintypes.FILETIME()
            exited = _wintypes.FILETIME()
            kernel = _wintypes.FILETIME()
            user = _wintypes.FILETIME()
            ok = k32.GetProcessTimes(
                handle,
                ctypes.byref(created), ctypes.byref(exited),
                ctypes.byref(kernel), ctypes.byref(user),
            )
        finally:
            k32.CloseHandle(handle)
        if not ok:
            return None
        # FILETIME = 自 1601-01-01 起的 100 纳秒数
        ticks = (created.dwHighDateTime << 32) | created.dwLowDateTime
        return datetime.fromtimestamp(ticks / 1e7 - 11644473600, tz=timezone.utc).astimezone(CST)
    except Exception:
        return None


def alive(pid: int | None, dispatch_dt: datetime | None = None, tol_sec: int = 180) -> bool:
    """存活判定 = 进程存在 且 启动时间与派发时间吻合（PID 复用防护）。"""
    if not pid:
        return False
    st = process_start(pid)
    if st is None:
        return False
    if dispatch_dt is None:
        return True
    return abs((st - dispatch_dt).total_seconds()) <= tol_sec


def fmt_minutes(ms: float) -> str:
    m = int(ms // 60000)
    if m < 1:
        return "不到 1 分钟"
    if m < 60:
        return f"{m} 分钟"
    return f"{m // 60} 小时 {m % 60} 分钟"


def tail_activity(log: Path) -> str:
    """从 dispatch.out.log 尾部事件推活动级阶段。仅取最后 200 行，避免读全量。"""
    if not log.exists():
        return ""
    try:
        with log.open("r", encoding="utf-8", errors="ignore") as fh:
            lines = fh.readlines()[-200:]
    except Exception:
        return ""
    last = ""
    for line in reversed(lines):
        low = line.lower()
        for key, label in ACTIVITY_RULES:
            if key in low:
                last = label
                break
        if last:
            break
    return last


def first_line_of_final_message(path: Path) -> str:
    """取收尾消息摘要，截断到 26 字，避免把整段塞进看板焦点框。

    final-message.json 是格式化 JSON，直接取首行会拿到 `"work_order": "wo-…`
    这类 JSON 碎片；所以先按结构化字段取 status + notes，取不到再回退纯文本首行。
    """
    if not path.exists():
        return ""
    STATUS_LABEL = {
        "READY_FOR_REVIEW": "待复审",
        "COMPLETED": "已完成",
        "BLOCKED": "阻塞",
        "FAILED": "失败",
    }
    try:
        text = path.read_text(encoding="utf-8")
        if text.lstrip().startswith("{"):
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                data = None
            if isinstance(data, dict):
                status = str(data.get("status") or "").strip()
                note = str(data.get("notes") or data.get("summary") or "").strip()
                note = re.sub(r"\s+", " ", note)
                label = STATUS_LABEL.get(status, status)
                if note:
                    head = note if len(note) <= 26 else note[:26] + "…"
                    return head
                return label
        for line in text[:400].splitlines():
            s = line.strip().lstrip("#-* ").strip()
            if not s or s.startswith(("{", "[", "|", '"')):
                continue
            s = s.replace("**", "")
            return s if len(s) <= 18 else s[:18] + "…"
    except Exception:
        return ""
    return ""


def collect() -> list[dict]:
    items = []
    for wo_dir in RUNS.glob("wo-*"):
        if not wo_dir.is_dir():
            continue
        for run_dir in wo_dir.iterdir():
            if not run_dir.is_dir():
                continue
            rec = run_dir / "dispatch-record.json"
            if not rec.exists():
                continue
            try:
                r = json.loads(rec.read_text(encoding="utf-8"))
            except Exception:
                continue
            ts_raw = r.get("dispatch_ts")
            try:
                dt = datetime.fromisoformat(str(ts_raw)).replace(tzinfo=CST)
            except Exception:
                continue
            fmsg = Path(r.get("final_message") or (run_dir / "final-message.json"))
            pid = r.get("pid")
            items.append({
                "order": r.get("order") or wo_dir.name,
                "run_dir": str(run_dir),
                "dispatch_dt": dt,
                "pid": pid,
                "has_final": fmsg.exists(),
                "final_path": fmsg,
                "log": run_dir / "dispatch.out.log",
            })
    items.sort(key=lambda x: x["dispatch_dt"], reverse=True)
    # 只对最近 6 条做进程校验（PID 复用防护需要查启动时间，有开销）
    for it in items[:6]:
        it["alive"] = alive(it["pid"], it["dispatch_dt"], tol_sec=180)
    for it in items[6:]:
        it["alive"] = False
    return items


def decide(item: dict, now: datetime) -> dict:
    base = {
        "order": item["order"],
        "pid": item["pid"],
        "running": item["alive"],
    }
    elapsed_ms = (now - item["dispatch_dt"]).total_seconds() * 1000
    if item["alive"]:
        act = tail_activity(item["log"]) or "执行中"
        base.update({
            "stateLabel": "运行中",
            "activity": act,
            "elapsedMs": int(elapsed_ms),
            "elapsedLabel": fmt_minutes(elapsed_ms),
        })
    elif item["has_final"]:
        fin_ms = item["final_path"].stat().st_mtime * 1000
        dur = fin_ms - item["dispatch_dt"].timestamp() * 1000
        base.update({
            "stateLabel": "已结束 · 待独立复审",
            "activity": first_line_of_final_message(item["final_path"]) or "已交付，待复审",
            "elapsedMs": int(max(0, dur)),
            "elapsedLabel": fmt_minutes(max(0, dur)),
        })
    else:
        qs, qdesc = queue_state(item["order"])
        if qs in ("frozen", "completed", "done"):
            # 已冻结/已完成：用最后一条日志的写入时刻当结束时刻，别让 elapsed 从派发一直涨
            end_ms = (item["log"].stat().st_mtime * 1000
                      if item["log"].exists() else item["dispatch_dt"].timestamp() * 1000)
            dur = end_ms - item["dispatch_dt"].timestamp() * 1000
            tag_m = re.search(r"(wo-ultimaagent-[0-9]{8}-[0-9]{4}-frozen-[0-9]{8})", qdesc or "")
            base.update({
                "stateLabel": "已完成 · 已冻结" if qs == "frozen" else "已完成",
                "activity": "已验收冻结（tag 已打，详见主表）" if tag_m else "已验收冻结，见主表",
                "elapsedMs": int(max(0, dur)),
                "elapsedLabel": fmt_minutes(max(0, dur)),
            })
        else:
            base.update({
                "stateLabel": "中断 · 无 final-message",
                "activity": "进程已退出但未产出收尾消息，需核查",
                "elapsedMs": int(elapsed_ms),
                "elapsedLabel": fmt_minutes(elapsed_ms),
            })
    return base


def queue_state(order: str) -> tuple[str, str]:
    """从全局主表取该工单的状态与描述，用于区分「中断」与「已冻结」。

    主表每行形如 `| UltimaAgent | wo-… | frozen | 描述 |`。查不到返回 ("", "")。
    没有这一步时，已冻结但日志里没有 final-message 的工单会被永久误报成「中断」，
    且 elapsed 从派发时刻持续增长，越看越像还在跑。
    """
    if not GLOBAL_QUEUE.exists():
        return "", ""
    try:
        text = GLOBAL_QUEUE.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return "", ""
    for line in text.splitlines():
        if not line.strip().startswith("|") or order not in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        if order in cells[1]:
            return cells[2], cells[3]
    return "", ""


def scan_queue_md(exclude: str) -> dict | None:
    """从全局主表找一条 UltimaAgent 项目的 executing/queued 工单（非当前焦点）。"""
    if not GLOBAL_QUEUE.exists():
        return None
    try:
        text = GLOBAL_QUEUE.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None
    candidates = []
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        if "UltimaAgent" not in line:
            continue
        if "executing" not in line and "queued" not in line:
            continue
        m = re.search(r"(wo-ultimaagent-[0-9]{8}-[0-9]{4})", line)
        if not m:
            continue
        wo = m.group(1)
        if wo == exclude:
            continue
        state = "排队中" if "queued" in line else "执行中"
        candidates.append({"order": wo, "stateLabel": state, "activity": "等待接续"})
    today = datetime.now(CST).date()
    fresh = []
    for c in candidates:
        try:
            d = datetime.strptime(c["order"].split("-")[-2], "%Y%m%d").date()
        except Exception:
            continue
        if (today - d).days <= 7:
            fresh.append(c)
    candidates = fresh
    candidates.sort(key=lambda c: c["order"], reverse=True)
    return candidates[0] if candidates else None


def main() -> int:
    now = datetime.now(CST)
    items = collect()
    if not items:
        print("未找到任何 run 记录")
        return 1

    focus_item = next((i for i in items if i["alive"]), items[0])
    focus = decide(focus_item, now)
    recent = [decide(i, now) for i in items[:5]]
    nxt = scan_queue_md(focus["order"])

    payload = {
        "updatedAt": now.isoformat(timespec="seconds"),
        "updatedAtMs": int(now.timestamp() * 1000),
        "updatedLabel": now.strftime("%Y-%m-%d %H:%M"),
        "focus": focus,
        "recent": [
            {k: v for k, v in r.items() if k in
             ("order", "running", "stateLabel", "activity", "elapsedLabel", "elapsedMs")}
            for r in recent
        ],
        "next": nxt,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    body = "window.ULTIMA_LIVE = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n"
    OUT.write_text(body, encoding="utf-8")

    print(f"[ok] 写入 {OUT} ({len(body)} B)")
    print(f"焦点: {focus['order']} | {focus['stateLabel']} | 用时 {focus['elapsedLabel']} | {focus['activity']}")
    for r in payload["recent"]:
        print(f"  - {r['order']} {r['stateLabel']} {r['elapsedLabel']}")
    if nxt:
        print(f"下一个: {nxt['order']} ({nxt['stateLabel']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
