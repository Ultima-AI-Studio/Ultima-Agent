# -*- coding: utf-8 -*-
"""
Ultima Agent 看门狗（s3-watchdog / M22）
功能：
  1. LoopGuard 循环防护：重复调用判定、乒乓检测、轮询预算、单回合超时 abort、流式空闲超时；
  2. 进程守护：8756 端口无监听/不健康时自动拉起 agent_server，连续失败 3 次停止并冷却；
  3. 独立进程运行（不内嵌业务进程）；
  4. 总线熔断联动：routing 插件 5 分钟内 >=3 次 error 主动回滚（与 ultima_bus 联动）；
  5. 开机自启：--install 注册计划任务（登录时运行、Hidden、零弹窗，pythonw 无控制台）；
  6. 日志留痕：data/logs/watchdog.log + data/logs/watchdog-events.jsonl。

用法：
  pythonw scripts\\watchdog-loopguard.py            # 守护运行（无窗口）
  python  scripts\\watchdog-loopguard.py --install  # 注册开机自启
  python  scripts\\watchdog-loopguard.py --uninstall
  python  scripts\\watchdog-loopguard.py --selftest # 构造用例自测（ACCEPT-1）
验收钩子（不改变正式行为）：
  --launch-script <path>  覆盖拉起脚本（测试连续失败停止用）
  --bus-log <path>        覆盖总线事件日志路径（测试熔断用）
  --dry-rollback          熔断只记录不执行回滚（测试联动用）
  --loop-events <path>    覆盖循环事件流路径
"""
import argparse
import datetime as _dt
import json
import logging
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = r"H:\UltimaAI\UltimaAgent"
LOG_DIR = os.path.join(ROOT, "data", "logs")
LOG_FILE = os.path.join(LOG_DIR, "watchdog.log")
EVENTS_FILE = os.path.join(LOG_DIR, "watchdog-events.jsonl")
HEALTH_URL = "http://127.0.0.1:8756/health"
AGENT_PORT = 8756
LAUNCH_SCRIPT = os.path.join(ROOT, "scripts", "start-agent-server.ps1")
POWERSHELL = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
BUS_CLI_PY = os.path.join(ROOT, "tools", "venv-openjarvis", "Scripts", "python.exe")
BUS_LOG = os.path.join(ROOT, "logs", "plugin-bus.jsonl")
LOOP_EVENTS = os.path.join(LOG_DIR, "loop-events.jsonl")
BUS_MODULES = ("ultima.domain.skill", "ultima.intent.rule", "ultima.memory.lite")

# ---- 参数（可配置阈值） ----
CHECK_INTERVAL = 20            # 守护检查间隔（秒）
LAUNCH_FAIL_LIMIT = 3          # 连续拉起失败停止阈值
LAUNCH_COOLDOWN = 300          # 停止后冷却（秒），冷却结束允许下一轮
FUSE_WINDOW = 300              # 熔断统计窗口（秒）= 5 分钟
FUSE_ERROR_LIMIT = 3           # 窗口内 error 次数阈值
FUSE_CHECK_INTERVAL = 15       # 熔断检查间隔（秒）
REPEAT_WINDOW = 10.0           # 重复调用判定窗口（秒）
REPEAT_LIMIT = 2               # 窗口内相同调用允许次数
PINGPONG_MIN = 6               # 乒乓交替次数阈值
POLL_BUDGET = 50               # 单会话 60 秒内轮询上限
POLL_WINDOW = 60.0
TURN_TIMEOUT = 300.0           # 单回合超时（秒）
STREAM_IDLE = 30.0             # 流式空闲超时（秒）

logger = logging.getLogger("watchdog")


def _now_iso():
    return _dt.datetime.now().astimezone().isoformat(timespec="milliseconds")


def log_event(etype, **payload):
    """写结构化事件到 watchdog-events.jsonl。"""
    try:
        with open(EVENTS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": _now_iso(), "event_type": etype, "payload": payload}, ensure_ascii=False) + "\n")
    except OSError as e:
        logger.error("写事件失败: %s", e)


def health_ok(url=None):
    """检查 agent_server 健康。返回 (ok, detail)。"""
    try:
        with urllib.request.urlopen(url or HEALTH_URL, timeout=8) as r:
            body = r.read().decode("utf-8", "replace")
            data = json.loads(body)
            return True, {"model": data.get("model"), "agent": data.get("agent")}
    except Exception as e:
        return False, str(e)


def port_listening(port):
    """检查端口是否有监听（用 PowerShell 查，避免依赖 netstat 解析）。"""
    try:
        ps = POWERSHELL + " -NoProfile -NonInteractive -Command \"if (Get-NetTCPConnection -LocalPort %d -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }\"" % port
        r = subprocess.run(ps, capture_output=True, timeout=10)
        return r.returncode == 0
    except Exception:
        return False


class LoopGuard:
    """循环防护：对事件流做重复/乒乓/轮询预算/回合超时/流式空闲判定。"""

    def __init__(self, events_path=None):
        self.events_path = events_path or LOOP_EVENTS
        self.pos = 0
        self.seen_calls = {}       # key -> last ts
        self.call_seq = {}         # session -> [keys]
        self.poll_counts = {}      # session -> [ts]
        self.turn_open = {}        # session -> start_ts
        self.stream_last = {}      # session -> last_chunk_ts

    def _read_new(self):
        if not os.path.exists(self.events_path):
            return []
        with open(self.events_path, "r", encoding="utf-8") as f:
            f.seek(self.pos)
            lines = f.readlines()
            self.pos = f.tell()
        out = []
        for ln in lines:
            ln = ln.strip()
            if not ln:
                continue
            try:
                out.append(json.loads(ln))
            except json.JSONDecodeError:
                logger.warning("事件行解析失败: %r", ln[:120])
        return out

    def _prune(self, now, window):
        for k in list(self.poll_counts.keys()):
            self.poll_counts[k] = [t for t in self.poll_counts[k] if now - t <= window]
            if not self.poll_counts[k]:
                del self.poll_counts[k]

    def check(self):
        """增量读事件流，返回违规列表 [(type, session, detail)]。"""
        violations = []
        now = time.time()
        for ev in self._read_new():
            et = ev.get("type")
            session = ev.get("session") or "default"
            key = ev.get("key") or ""
            ts = ev.get("ts")
            t = ts if isinstance(ts, (int, float)) else now
            if et == "call_start":
                k = (session, key)
                if k in self.seen_calls and t - self.seen_calls[k] <= REPEAT_WINDOW:
                    violations.append(("repeat_call", session, "key=%s 窗口%.0fs内重复" % (key, REPEAT_WINDOW)))
                self.seen_calls[k] = t
                seq = self.call_seq.setdefault(session, [])
                seq.append(key)
                if len(seq) >= PINGPONG_MIN:
                    tail = seq[-PINGPONG_MIN:]
                    adjacent_alt = all(tail[i] != tail[i + 1] for i in range(PINGPONG_MIN - 1))
                    two_values = len(set(tail)) <= 2
                    if adjacent_alt and two_values:
                        violations.append(("pingpong", session, "交替序列=%s" % ",".join(tail)))
            elif et == "poll":
                self._prune(t, POLL_WINDOW)
                lst = self.poll_counts.setdefault(session, [])
                lst.append(t)
                if len(lst) > POLL_BUDGET:
                    violations.append(("poll_budget", session, "60s内轮询>%d次" % POLL_BUDGET))
            elif et == "turn_start":
                self.turn_open[session] = t
            elif et == "turn_end":
                self.turn_open.pop(session, None)
            elif et == "stream_chunk":
                last = self.stream_last.get(session)
                if last is not None and t - last > STREAM_IDLE and session in self.turn_open:
                    violations.append(("stream_idle", session, "流式空闲%.0fs>上限%.0fs" % (t - last, STREAM_IDLE)))
                self.stream_last[session] = t
            # 回合超时即时判定：任何事件到来时检查该会话开启的回合
            st = self.turn_open.get(session)
            if st is not None and t - st > TURN_TIMEOUT:
                violations.append(("turn_timeout", session, "回合%.0fs>上限%.0fs" % (t - st, TURN_TIMEOUT)))
                self.turn_open.pop(session, None)
        return violations

    def reset(self):
        self.pos = 0
        self.seen_calls.clear()
        self.call_seq.clear()
        self.poll_counts.clear()
        self.turn_open.clear()
        self.stream_last.clear()


def loopguard_cycle(guard):
    """执行一轮 LoopGuard 判定并记录违规。"""
    try:
        for vtype, session, detail in guard.check():
            msg = "LoopGuard违规 type=%s session=%s detail=%s" % (vtype, session, detail)
            logger.warning(msg)
            log_event("loopguard_violation", type=vtype, session=session, detail=detail,
                      abort_file=os.path.join(LOG_DIR, "loop-abort.%s" % session))
    except Exception as e:
        logger.error("LoopGuard 判定异常: %s", e)


def ensure_agent_server(health_url=None):
    """检查并拉起 agent_server。返回 ("ok"|"up"|"fail", detail)。"""
    ok, detail = health_ok(health_url)
    if ok:
        return "up", detail
    if port_listening(AGENT_PORT):
        # 端口在但健康接口失败：视为不健康，仍尝试拉起（脚本内部会先停旧进程）
        logger.warning("端口%d有监听但健康检查失败: %s", AGENT_PORT, detail)
    logger.info("agent_server 不健康，尝试拉起")
    log_event("agent_start_attempt", reason=str(detail)[:200])
    try:
        r = subprocess.run(
            [POWERSHELL, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
             "-File", LAUNCH_SCRIPT],
            capture_output=True, timeout=120)
        if r.returncode == 0:
            time.sleep(3)
            ok2, detail2 = health_ok(health_url)
            if ok2:
                log_event("agent_started", detail=detail2)
                return "ok", detail2
            logger.warning("拉起命令成功但健康未就绪: %s", r.stdout.decode("utf-8", "replace")[-300:])
            return "fail", "health not ready"
        err = r.stderr.decode("utf-8", "replace")[-300:]
        logger.warning("拉起失败 rc=%d: %s", r.returncode, err)
        return "fail", err
    except Exception as e:
        logger.error("拉起执行异常: %s", e)
        return "fail", str(e)


def fuse_check(bus_log=None, dry=False):
    """总线熔断：routing 插件 5 分钟内 >=3 error 触发回滚。"""
    path = bus_log or BUS_LOG
    if not os.path.exists(path):
        return
    now = time.time()
    since = now - FUSE_WINDOW
    counts = {}
    with open(path, "r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                ev = json.loads(ln)
            except json.JSONDecodeError:
                continue
            source = ev.get("source", "")
            if source not in BUS_MODULES:
                continue
            et = (ev.get("event_type") or "").lower()
            payload = ev.get("payload") or {}
            is_err = ("error" in et) or (str(payload.get("status", "")).lower() == "error") or (payload.get("error") is not None)
            if not is_err:
                continue
            try:
                ts = _dt.datetime.fromisoformat(ev["ts"]).timestamp()
            except Exception:
                continue
            if ts >= since:
                counts[source] = counts.get(source, 0) + 1
    for mod, cnt in counts.items():
        if cnt >= FUSE_ERROR_LIMIT:
            logger.warning("熔断触发 module=%s 窗口%.0fs内error=%d次", mod, FUSE_WINDOW, cnt)
            log_event("fuse_triggered", module_id=mod, error_count=cnt, window_sec=FUSE_WINDOW)
            if dry:
                log_event("fuse_rollback_dryrun", module_id=mod, would_exec="python -m ultima_bus bus rollback %s" % mod)
                continue
            try:
                r = subprocess.run(
                    [BUS_CLI_PY, "-m", "ultima_bus", "bus", "rollback", mod],
                    cwd=ROOT, capture_output=True, timeout=60)
                log_event("fuse_rollback_exec", module_id=mod, rc=r.returncode,
                          out=(r.stdout.decode("utf-8", "replace")[-200:] if r.stdout else None))
            except Exception as e:
                logger.error("回滚执行异常: %s", e)


def install_autostart():
    """注册开机自启计划任务（登录时运行、Hidden、零弹窗）。"""
    pyw = sys.executable if sys.executable.lower().endswith("pythonw.exe") else os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.exists(pyw):
        pyw = r"C:\Windows\py.exe"
    task_name = "UltimaAgent-Watchdog"
    tr = '"%s" "%s"' % (pyw, os.path.abspath(__file__))
    cmd = ['schtasks', '/Create', '/TN', task_name, '/TR', tr, '/SC', 'ONLOGON',
           '/RL', 'HIGHEST', '/F']
    r = subprocess.run(cmd, capture_output=True, timeout=30)
    if r.returncode == 0:
        log_event("autostart_installed", task=task_name, command=" ".join(cmd))
        logger.info("自启已注册: %s", task_name)
        return True
    logger.error("自启注册失败 rc=%d: %s", r.returncode, r.stderr.decode("utf-8", "replace"))
    return False


def uninstall_autostart():
    r = subprocess.run(["schtasks", "/Delete", "/TN", "UltimaAgent-Watchdog", "/F"],
                       capture_output=True, timeout=30)
    log_event("autostart_removed", rc=r.returncode)
    return r.returncode == 0


def selftest():
    """ACCEPT-1 构造用例自测：逐项构造违规事件验证判定。"""
    import tempfile
    tmp = os.path.join(tempfile.gettempdir(), "watchdog_selftest_%d.jsonl" % int(time.time()))
    guard = LoopGuard(events_path=tmp)
    base = time.time()

    def feed(etype, session="s1", key="", ts=None, path=tmp):
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"type": etype, "session": session, "key": key,
                                "ts": ts if ts is not None else time.time()}, ensure_ascii=False) + "\n")

    results = {}
    # 1) 重复调用：窗口内同 key 两次 call_start
    feed("call_start", key="k1", ts=base)
    feed("call_start", key="k1", ts=base + 1)
    v = guard.check()
    results["repeat_call"] = any(x[0] == "repeat_call" for x in v)

    # 2) 乒乓：A,B 交替 6 次
    guard.reset()
    for i in range(3):
        feed("call_start", session="sp", key="A", ts=base + i)
        feed("call_start", session="sp", key="B", ts=base + i + 0.1)
    v = guard.check()
    results["pingpong"] = any(x[0] == "pingpong" for x in v)

    # 3) 轮询预算：51 次 poll
    guard.reset()
    for i in range(POLL_BUDGET + 1):
        feed("poll", session="po", ts=base + i * 0.5)
    v = guard.check()
    results["poll_budget"] = any(x[0] == "poll_budget" for x in v)

    # 4) 回合超时：turn_start 后 301s 无 turn_end
    guard.reset()
    feed("turn_start", session="tt", ts=base)
    feed("poll", session="tt", ts=base + TURN_TIMEOUT + 1)
    v = guard.check()
    results["turn_timeout"] = any(x[0] == "turn_timeout" for x in v)

    # 5) 流式空闲：turn 内 chunk 间隔 31s
    guard.reset()
    feed("turn_start", session="si", ts=base)
    feed("stream_chunk", session="si", ts=base)
    feed("stream_chunk", session="si", ts=base + STREAM_IDLE + 1)
    v = guard.check()
    results["stream_idle"] = any(x[0] == "stream_idle" for x in v)

    os.remove(tmp)
    return results


def main():
    ap = argparse.ArgumentParser(description="Ultima Agent 看门狗")
    ap.add_argument("--install", action="store_true")
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--launch-script", default=None)
    ap.add_argument("--bus-log", default=None)
    ap.add_argument("--dry-rollback", action="store_true")
    ap.add_argument("--loop-events", default=None)
    ap.add_argument("--health-url", default=None)
    args = ap.parse_args()

    global LAUNCH_SCRIPT
    if args.launch_script:
        LAUNCH_SCRIPT = args.launch_script

    os.makedirs(LOG_DIR, exist_ok=True)
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s",
                        encoding="utf-8")
    logger.info("watchdog 启动 pid=%d", os.getpid())

    if args.selftest:
        res = selftest()
        ok = all(res.values())
        print(json.dumps({"selftest": res, "pass": ok}, ensure_ascii=False, indent=1))
        log_event("watchdog_selftest", results=res, pass_=ok)
        return 0 if ok else 1
    if args.install:
        return 0 if install_autostart() else 1
    if args.uninstall:
        return 0 if uninstall_autostart() else 1

    # 单实例守卫（2026-10-27 性能修复）：无锁时每次开机/测试都拉一个 watchdog，
    # 多个看门狗可能同时拉起多个 agent_server → 进程累积吃满机器。
    import ctypes
    import tempfile

    _wd_lock = Path(tempfile.gettempdir()) / "ultima-watchdog.pid"

    def _wd_holder_alive() -> bool:
        try:
            old = int(_wd_lock.read_text().strip())
            h = ctypes.windll.kernel32.OpenProcess(0x1000, False, old)
            if h:
                ctypes.windll.kernel32.CloseHandle(h)
                return True
        except Exception:
            pass
        return False

    if _wd_holder_alive():
        logger.info("watchdog 已有实例在运行（pid 锁存活），本实例退出")
        print(json.dumps({"exit": "already-running"}, ensure_ascii=False))
        return 0
    try:
        _wd_lock.write_text(str(os.getpid()), encoding="utf-8")
    except Exception:
        pass

    import atexit as _atexit

    def _wd_cleanup() -> None:
        try:
            if _wd_lock.read_text().strip() == str(os.getpid()):
                _wd_lock.unlink(missing_ok=True)
        except Exception:
            pass

    _atexit.register(_wd_cleanup)
    log_event("watchdog_started", pid=os.getpid())

    guard = LoopGuard(events_path=args.loop_events)
    fail_count = 0
    fail_since = 0.0
    fuse_last = 0.0
    while True:
        # 进程守护
        if fail_count >= LAUNCH_FAIL_LIMIT:
            if time.time() - fail_since >= LAUNCH_COOLDOWN:
                logger.info("冷却结束，重置拉起失败计数")
                fail_count = 0
            else:
                pass
        else:
            st, det = ensure_agent_server(health_url=args.health_url)
            if st in ("ok", "up"):
                fail_count = 0
            else:
                fail_count += 1
                if fail_count == 1:
                    fail_since = time.time()
                if fail_count >= LAUNCH_FAIL_LIMIT:
                    fail_since = time.time()
                    logger.error("连续%d次拉起失败，停止本轮重试，冷却%d秒", LAUNCH_FAIL_LIMIT, LAUNCH_COOLDOWN)
                    log_event("agent_start_stopped", fail_count=fail_count, cooldown_sec=LAUNCH_COOLDOWN)
        # 熔断联动
        if time.time() - fuse_last >= FUSE_CHECK_INTERVAL:
            try:
                fuse_check(bus_log=args.bus_log, dry=args.dry_rollback)
            except Exception as e:
                logger.error("熔断检查异常: %s", e)
            fuse_last = time.time()
        # LoopGuard
        try:
            loopguard_cycle(guard)
        except Exception as e:
            logger.error("LoopGuard 循环异常: %s", e)
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    sys.exit(main())
