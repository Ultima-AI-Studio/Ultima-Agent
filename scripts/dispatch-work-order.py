"""One registered engineering order per real Codex process; no automatic approval."""
import argparse
from datetime import datetime, timezone, timedelta
import glob as _glob
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import ctypes
from ctypes import wintypes as W
from contextlib import contextmanager

ROOT = Path(__file__).resolve().parents[1]


def _resolve_shared_queue(root: Path) -> Path:
    """定位共享队列目录，使隔离工作树里也能派发。

    ``root.parent/'_shared/queue'`` 只在主仓布局成立（root=H:\\UltimaAI\\UltimaAgent）。
    在隔离工作树（H:\\UltimaAI\\_worktrees\\gorch\\<task>）下 parent 不是 H:\\UltimaAI，
    会指到不存在的目录，派发直接撞 Errno 2。这里优先环境变量，其次自 root 向上
    逐级探测已存在的 _shared/queue 目录；都没有时退回旧行为，
    保持主仓语义不变。
    """
    override = os.environ.get('GORCH_SHARED_QUEUE')
    if override:
        return Path(override)
    for base in (root, *root.parents):
        candidate = base / '_shared' / 'queue'
        if candidate.is_dir():
            return candidate
    return root.parent / '_shared/queue'


SHARED = _resolve_shared_queue(ROOT)
QUEUE_STATUS = ROOT / 'tasks/queue/queue-status.json'
QUEUE_RENDERER = ROOT / 'scripts/render-queue-views.py'
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
from tasks.queue_engine.dispatcher import DispatchLock, process_identity
from tasks.queue_engine.card_contract import check_version_gates
from tasks.queue_engine.receipt_contract import classify_receipt_path
# The order's card table is parsed once, in ``gorch_contract``, so the dispatcher and
# the freeze gate enumerate the same set and refuse the same malformed rows.
from gorch_contract import order_cards as contract_order_cards
from order_naming import is_valid_order, resolve_card_path
from scripts import validate_work_order

spec = importlib.util.spec_from_file_location('native_environment', ROOT / 'scripts/inspect-native-environment.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)

SENTINEL_EXIT_TIMEOUT_S = 210.0

# Where a Codex CLI may live when it is not on PATH. A store update moves the
# payload into a versioned WindowsApps directory and leaves no alias behind,
# so a PATH-only lookup stops dispatching entirely after an upgrade. The
# newest hit wins, because several versioned installs may coexist.
_CODEX_EXE_GLOBS = (
    r'C:\Program Files\WindowsApps\OpenAI.Codex_*\app\resources\codex.exe',
    r'C:\Users\*\AppData\Local\Microsoft\WindowsApps\codex.exe',
    r'C:\Users\*\AppData\Roaming\npm\codex.exe',
    r'C:\Users\*\AppData\Local\Programs\*\codex.exe',
)


def resolve_git_exe() -> str | None:
    """Same class of problem as Codex: `git` is not on PATH in every session."""
    explicit = os.environ.get('ULTIMA_GIT_EXE', '').strip()
    if explicit and os.path.isfile(explicit):
        return explicit
    found = shutil.which('git') or shutil.which('git.exe')
    if found:
        return found
    for candidate in (r'C:\Program Files\Git\cmd\git.exe', r'C:\Program Files\Git\bin\git.exe'):
        if os.path.isfile(candidate):
            return candidate
    return None


def git_snapshot() -> dict:
    """Record enough to prove later which tree content a receipt was earned on.

    An earlier revision recorded the dispatch commit and asked whether it was still
    an ancestor of HEAD. Uncommitted agent edits never move HEAD, so that check
    passed on trees nobody tested.

    Recorded instead: the commit, its tree object, the *whole* set of modified
    tracked files with their hashes, and the declared files with theirs. Content
    identity, not commit identity — an identical-content recommit or rebase is the
    same tree, one edited file is a different one.

    Why the full status set and not just "files that differ from HEAD": on a clean
    working tree that set is empty, so there would be nothing recorded to compare
    against and any later edit would go unnoticed. The entry set is the baseline.

    ``--untracked-files=no`` is deliberate: this tree holds 321k untracked test
    artifacts under data/evidence, and enumerating them costs 50s. With it excluded
    the query takes 0.4s. Newly created untracked files are therefore outside this
    fingerprint — a stated limit, not an oversight, and the declared-file check in
    verification still covers the files an order promises to deliver.
    """
    exe = resolve_git_exe()
    if not exe:
        return {'base_sha': None, 'worktree_dirty': None, 'tree_oid': None,
                'status_entries': None, 'changed_files': None, 'error': 'git not found'}

    def run(*args: str) -> tuple[str, bool]:
        done = subprocess.run([exe, *args], cwd=str(ROOT), capture_output=True, text=True,
                              encoding='utf-8', errors='replace')
        return ((done.stdout or '').strip(), done.returncode == 0)

    head, head_ok = run('rev-parse', 'HEAD')
    tree_oid, tree_ok = run('rev-parse', 'HEAD^{tree}')
    # Kept unstripped on purpose: porcelain's first column is a status code that
    # is a space for an unstaged change. Stripping the output shifts every path by
    # one character and silently reads " M a.txt" as ".txt".
    # NUL-separated output: a rename in line form reads "R  old -> new", which puts
    # the whole expression in the path field, so the file that actually exists is
    # never hashed and later edits to it go unnoticed.
    status = subprocess.run([exe, 'status', '--porcelain=v1', '-z', '--untracked-files=no'],
                            cwd=str(ROOT), capture_output=True, text=True,
                            encoding='utf-8', errors='replace')
    status_ok = status.returncode == 0
    status_parts = (status.stdout or '').split('\0')

    entries: list[dict] | None = None
    manifest: list[dict] | None = None
    if status_ok:
        entries = []
        manifest = []
        index = 0
        while index < len(status_parts):
            item = status_parts[index]
            if not item:
                index += 1
                continue
            code = item[:2]
            name = item[3:]
            origin = None
            if 'R' in code or 'C' in code:
                origin = status_parts[index + 1] if index + 1 < len(status_parts) else None
                index += 2
            else:
                index += 1
            entry = {'code': code, 'path': name}
            if origin:
                entry['orig'] = origin
            entries.append(entry)
            path = ROOT / name
            try:
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError:
                digest = None          # deleted or unreadable: recorded, not guessed
            manifest.append({'path': name, 'code': code, 'sha256': digest, 'orig': origin})
    return {'base_sha': head or None, 'tree_oid': tree_oid or None,
            'worktree_dirty': len(entries) if entries is not None else None,
            'status_entries': entries, 'changed_files': manifest,
            'error': None if (head_ok and tree_ok and status_ok) else 'git query failed'}


def resolve_codex_exe() -> str | None:
    """Find the Codex CLI without relying on PATH alone."""
    explicit = os.environ.get('ULTIMA_CODEX_EXE', '').strip()
    if explicit and Path(explicit).is_file():
        return explicit
    found = shutil.which('codex.exe') or shutil.which('codex')
    if found:
        return found
    hits = [p for pattern in _CODEX_EXE_GLOBS for p in _glob.glob(pattern) if Path(p).is_file()]
    if hits:
        return max(hits, key=lambda p: os.path.getmtime(p))
    return None

# An order that sits in AUDIT blocks every later order from taking the audit
# slot, because the slot test is "is any other order in audit". Without a
# staleness rule a single forgotten order stalls the whole queue forever.
# An order whose audit wait exceeds this many days stops occupying the slot.
# Overridable so the window can be tuned without editing code.
AUDIT_SLOT_MAX_AGE_DAYS = float(os.environ.get('ULTIMA_AUDIT_SLOT_MAX_AGE_DAYS', '7'))
# A reason that already records the order as frozen outside the flow means it
# is no longer waiting on an audit at all, so age does not apply to it.
_AUDIT_FROZEN_MARKERS = ('范围外冻结', '已冻结', 'frozen')
# How many orders may sit in AUDIT at once. This was effectively 1 by accident
# of implementation; a limit that harsh means most work never enters the control
# that is supposed to judge it. Stated here as a decision, with a floor of 1 so
# the gate can never be configured away entirely.
AUDIT_SLOT_LIMIT = max(1, int(os.environ.get('ULTIMA_AUDIT_SLOT_LIMIT', '2')))


def _audit_slot_age_days(order: str, reason: str, now, runs_root: Path | None = None) -> float | None:
    """How long this order has been waiting in audit; None when unknowable.

    Preference order is by reliability: the finished_at of its latest dispatch
    run, then an explicit date in the registry reason, then give up. Returning
    None means "cannot prove it is stale", and the caller must keep treating it
    as occupying — a missing timestamp is not licence to evict an order.
    """
    latest = None
    for done in (runs_root or (ROOT / 'tasks/queue/runs')).glob(order + '-*/done.json'):
        try:
            stamp = json.loads(done.read_text(encoding='utf-8-sig')).get('finished_at')
        except (OSError, ValueError):
            continue
        if not stamp:
            continue
        try:
            at = datetime.fromisoformat(str(stamp).replace('Z', '+00:00'))
        except ValueError:
            continue
        if at.tzinfo is None:
            at = at.replace(tzinfo=timezone.utc)
        if latest is None or at > latest:
            latest = at
    if latest is None:
        # Registry reasons carry hand-written dates such as 2026-10-31 or
        # 20261030; accept either form and take the newest one present.
        dates = []
        for token in re.findall(r'20\d{2}-\d{2}-\d{2}|20\d{6}', reason or ''):
            try:
                dates.append(datetime.strptime(re.sub(r'-', '', token), '%Y%m%d').replace(tzinfo=timezone.utc))
            except ValueError:
                continue
        if dates:
            latest = max(dates)
    if latest is None:
        return None
    return (now - latest).total_seconds() / 86400.0


def _load_queue_status(path: Path | None = None) -> dict:
    source = path or QUEUE_STATUS
    try:
        document = json.loads(source.read_text(encoding='utf-8-sig'))
    except (OSError, ValueError) as exc:
        raise ValueError(f'queue-status.json 不可读，拒绝派发：{exc}') from exc
    records = document.get('records')
    if document.get('schema_version') != 1 or not isinstance(records, list):
        raise ValueError('queue-status.json schema 无效，拒绝派发')
    identities = [(item.get('project'), item.get('work_order')) for item in records
                  if isinstance(item, dict)]
    if len(identities) != len(records) or len(set(identities)) != len(identities):
        raise ValueError('queue-status.json 登记身份缺失或重复，拒绝派发')
    return document


def _registered_record(document: dict, order: str) -> dict:
    matches = [item for item in document['records']
               if item.get('project') == 'UltimaAgent' and item.get('work_order') == order]
    if len(matches) != 1:
        raise ValueError('工单未在 JSON 权威源唯一登记，拒绝派发')
    return matches[0]


def audit_slot_holders(current: dict, order: str, now=None, runs_root: Path | None = None) -> tuple[list[str], list[dict]]:
    """Split the other orders sitting in audit into blocking and disregarded.

    Returns (blocking, disregarded). Disregarded entries carry why they were
    let go so the run records exactly which orders stopped counting.
    """
    now = now or datetime.now(timezone.utc)
    blocking, disregarded = [], []
    for item in current['records']:
        if item.get('state') != 'audit':
            continue
        holder = str(item.get('work_order') or '')
        if holder == order:
            continue
        reason = str(item.get('note') or '')
        if any(m in reason for m in _AUDIT_FROZEN_MARKERS):
            disregarded.append({'order': holder, 'why': 'reason records it as frozen outside the flow'})
            continue
        age = _audit_slot_age_days(holder, reason, now, runs_root)
        if age is None:
            blocking.append(holder)
            disregarded.append({'order': holder, 'why': 'no timestamp; kept as occupant (fail-closed)', 'blocking': True})
            continue
        if age > AUDIT_SLOT_MAX_AGE_DAYS:
            disregarded.append({'order': holder, 'why': f'audit wait {age:.1f}d exceeds {AUDIT_SLOT_MAX_AGE_DAYS}d'})
            continue
        blocking.append(holder)
    return blocking, [d for d in disregarded if not d.get('blocking')]


def receipt_contract_block(order: str) -> str:
    """Append the receipt markers the classifier actually requires.

    The classifier (tasks/queue_engine/receipt_contract.py::_classify_text)
    accepts a text receipt only when it carries the work order id plus both
    markers below. Sending the order without telling the executor about them
    makes a perfectly complete receipt come back as valid=False.

    The markers are described, never spelled out literally: the same block is
    handed to the executor, and a literal marker here would both trip the
    blocked-pattern and let an executor "pass" by copying this text.
    """

    return (
        '\n\n---\n\n'
        '## 回执格式契约（派发器自动附加）\n\n'
        '判读器按字面匹配，同义改写一律不算。最终消息必须包含下面三项：\n\n'
        f'1. 工单号（本单为 {order}）\n'
        '2. 一行「自检」结论：冒号后写通过状态词（全大写 PASS，或中文「通过」）\n'
        '3. 独立一行，交审标记词：全大写、下划线连接，由 READY、FOR、'
        'DEEPSEEK、AUDIT 四个词依次拼成\n\n'
        '三项缺任意一项，回执会被判无效、工单落阻塞，交付内容再好也不计入。\n'
        '确实无法完成时不要写第 2、3 项，改为在消息里写明受阻原因与缺什么。\n'
    )


def start_sentinel(order, run_dir, pid, expected_identity):
    return subprocess.Popen(
        [sys.executable, '-m', 'src.brain.sentinel', order, str(run_dir),
         str(pid), expected_identity],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=0x08000000,
    )


def await_sentinel(process):
    try:
        process.wait(timeout=SENTINEL_EXIT_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        process.terminate()
        process.wait(timeout=5)


def dor_record(order, status, errors, *, skipped=False):
    """Build the auditable DoR fragment stored with a dispatch."""
    if skipped:
        return {'order': order, 'dor_skipped': True, 'dor_errors': list(errors)}
    return {'order': order, 'dor_status': status}


def write_dor_record(path, record):
    Path(path).write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')


class OwnedJob:
    """Bound only this dispatch's worker tree; closing it cannot kill other jobs."""
    def __init__(self, worker):
        class Limits(ctypes.Structure):
            _fields_ = [('process_time', ctypes.c_int64), ('job_time', ctypes.c_int64),
                        ('flags', W.DWORD), ('min_ws', ctypes.c_size_t), ('max_ws', ctypes.c_size_t),
                        ('active', W.DWORD), ('affinity', ctypes.c_size_t), ('priority', W.DWORD), ('scheduling', W.DWORD)]
        class IO(ctypes.Structure):
            _fields_ = [(name, ctypes.c_uint64) for name in ('read_ops', 'write_ops', 'other_ops', 'read_bytes', 'write_bytes', 'other_bytes')]
        class Extended(ctypes.Structure):
            _fields_ = [('basic', Limits), ('io', IO), ('process_memory', ctypes.c_size_t),
                        ('job_memory', ctypes.c_size_t), ('peak_process', ctypes.c_size_t), ('peak_job', ctypes.c_size_t)]
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, W.LPCWSTR]
        self.kernel.CreateJobObjectW.restype = W.HANDLE
        self.kernel.SetInformationJobObject.argtypes = [W.HANDLE, ctypes.c_int, ctypes.c_void_p, W.DWORD]
        self.kernel.AssignProcessToJobObject.argtypes = [W.HANDLE, W.HANDLE]
        self.kernel.CloseHandle.argtypes = [W.HANDLE]
        self.handle = self.kernel.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = Extended()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.kernel.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)) or not self.kernel.AssignProcessToJobObject(self.handle, W.HANDLE(int(worker._handle))):
            error = ctypes.get_last_error()
            self.close()
            worker.kill()
            worker.wait(timeout=5)
            raise ctypes.WinError(error)

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


@contextmanager
def completion_lock():
    lock = DispatchLock(SHARED / '.engineering-dispatch.lock')
    deadline = time.monotonic()+10
    while not lock.acquire():
        if time.monotonic() >= deadline:
            raise RuntimeError('执行已退出，等待共享锁回写；保留execution-exit.json，不重复派发')
        time.sleep(.1)
    try:
        yield
    finally:
        lock.release()


def registered(order):
    document = _load_queue_status()
    return document, _registered_record(document, order)

def check_recovery_fence(record,expected_state,expected_run,reservation):
    if expected_state is None and expected_run is None and reservation is None:
        return
    if not expected_state or not expected_run or not reservation:
        raise RuntimeError('恢复必须同时绑定状态、原运行和预约标识')
    note = str(record.get('note') or '')
    if record.get('state') != expected_state or expected_run not in note or reservation not in note:
        raise RuntimeError('恢复预约已过期或登记被其他裁决改变，拒绝启动')


def state(order, target, reason, run, *, expected=None, expected_run=None):
    path = QUEUE_STATUS
    original = path.read_bytes()
    document = _load_queue_status(path)
    record = _registered_record(document, order)
    if expected is not None and record.get('state') != expected:
        raise RuntimeError('工单状态已变化，拒绝覆盖其他裁决')
    if expected_run is not None and expected_run not in str(record.get('note') or ''):
        raise RuntimeError('运行轮次已变化，拒绝旧执行回写')
    (run / ('queue-status-before-' + target + '.json')).write_bytes(original)
    record['state'] = target
    record['note'] = reason
    if target == 'executing':
        record['dispatched_at'] = datetime.now(timezone.utc).isoformat()
    if target == 'audit':
        record['audit_run'] = run.name
    updated = (json.dumps(document, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    if path.read_bytes() != original:
        raise RuntimeError('全局登记已并发变化，拒绝覆盖')
    temporary = path.with_name('queue-status.' + run.name + '.tmp')
    temporary.write_bytes(updated)
    try:
        temporary.replace(path)
    except PermissionError:
        # Some Windows readers allow WRITE but deny DELETE sharing. Stay under
        # the dispatch lock, recheck exact bytes, and retain the durable backup.
        with path.open('r+b') as stream:
            if stream.read() != original:
                raise RuntimeError('全局登记已并发变化，拒绝覆盖')
            stream.seek(0)
            stream.write(updated)
            stream.truncate()
            stream.flush()
            os.fsync(stream.fileno())
        temporary.unlink()
    if path.read_bytes() != updated:
        raise RuntimeError('全局登记写入后核对失败')
    subprocess.run([sys.executable, str(QUEUE_RENDERER)], check=True,
                   capture_output=True, timeout=20, creationflags=0x08000000)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--order', required=True)
    parser.add_argument('--prompt', required=True, type=Path)
    parser.add_argument('--card', type=Path)
    parser.add_argument('--skip-dor', action='store_true')
    parser.add_argument('--dry-run-dor', action='store_true')
    parser.add_argument('--dor-record', type=Path, help=argparse.SUPPRESS)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--repair', action='store_true')
    parser.add_argument('--max-runtime-seconds', type=int, default=1800)
    parser.add_argument('--expected-run')
    parser.add_argument('--expected-state')
    parser.add_argument('--expected-reservation')
    parser.add_argument('--reasoning-effort',choices=['high','ultra'],default='high')
    args = parser.parse_args()
    if not 60 <= args.max_runtime_seconds <= 14400:
        raise ValueError('执行时限必须在60至14400秒之间')
    if not is_valid_order(args.order):
        raise ValueError(f'工单号不符合命名契约：{args.order!r}')
    order_path = resolve_card_path(args.order, ROOT / 'tasks/queue')
    if args.card is not None and args.card.resolve() != order_path.resolve():
        raise ValueError(
            f'--card 与权威解析结果不一致：传入 {args.card}，实际为 {order_path}'
        )
    dor_report = validate_work_order.validate(order_path)
    # 写死易变值只在校验器里作为 warning 登记，由派发门在此处升级为拒派：
    # 历史已冻结卡保持它自己的判定，新卡则在真正派出去之前被拦下。
    volatile = [
        item for item in dor_report.warnings
        if item['code'] == validate_work_order.W_VOLATILE_COUNT_WRITTEN
    ]
    blocking = list(dor_report.errors) + volatile
    if (dor_report.status != 'PASS' or volatile) and not args.skip_dor:
        print(json.dumps({'dor_status': 'FAIL', 'order': args.order, 'card': str(order_path),
                          'errors': blocking}, ensure_ascii=False))
        return 2
    record = dor_record(args.order, dor_report.status, blocking,
                        skipped=dor_report.status != 'PASS' and args.skip_dor)
    record['card'] = str(order_path)
    if args.dry_run_dor:
        if args.dor_record is not None:
            write_dor_record(args.dor_record, record)
        print(json.dumps({'ready': True, 'would_dispatch': True, **record}, ensure_ascii=False))
        return 0
    if args.dor_record is not None:
        raise ValueError('--dor-record 仅供 --dry-run-dor 测试使用')
    queue, record = registered(args.order)
    if record.get('state') not in ({'pending', 'blocked', 'audit'} if args.repair else {'pending'}):
        raise ValueError('当前状态不允许派发；修复续行须显式 --repair')
    prompt = args.prompt.read_text(encoding='utf-8-sig')
    if 'docs/INDEX.md' not in prompt or args.order not in prompt:
        raise ValueError('派发载荷必须引用 INDEX 及当前唯一工单')
    try:
        cards = contract_order_cards(order_path.read_text(encoding='utf-8'))
    except UnicodeError:
        raise ValueError('工单文件无法按 UTF-8 读取')
    except ValueError as exc:
        raise ValueError(f'工单任务卡表不可解析：{exc}')
    # 卡引用是可选形态：s1/orb 系列用 `| T1 <card-id> |` 指名 tasks/cards/<id>，
    # ultimaagent 系列的任务表只写文件路径、不引用卡。空集不代表工单不合格，
    # 只表示卡固化机制对该工单不适用；一旦引用了卡，下面的逐卡校验与固化照旧从严。
    versions = set()
    for card_id in cards:
        card = ROOT / 'tasks/cards' / card_id / 'task.md'
        if not card.is_file():
            raise ValueError('工单引用的任务卡缺失')
        version = re.search(r'^-\s*\*\*stage\*\*[^\n]*\b(v\d+\.\d+)', card.read_text(encoding='utf-8-sig'), re.M)
        if not version:
            raise ValueError('任务卡阶段不可核对')
        versions.add(version.group(1))
    if cards and len(versions) != 1:
        raise ValueError('工单引用任务阶段不一致')
    if cards:
        check_version_gates({'card_path': str(ROOT / 'tasks/cards' / cards[0] / 'task.md')}, ROOT / 'tasks')
    # Every card the order names is fixed at dispatch time, not just the first one.
    # An order may reference several cards (`wo-s1-host-shell` names five), and a
    # single hash covered only the one that happened to be used for the audit.
    card_records = []
    for cid in cards:
        path = ROOT / 'tasks/cards' / cid / 'task.md'
        card_records.append({'path': str(path),
                             'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    card_path = card_sha256 = None
    if cards:
        card_path = ROOT / 'tasks/cards' / cards[0] / 'task.md'
        card_sha256 = hashlib.sha256(card_path.read_bytes()).hexdigest()
    if (ROOT / 'tasks/.pause-dispatch').exists() or (SHARED / '.pause-dispatch').exists():
        raise ValueError('派发暂停标记存在')
    codex = resolve_codex_exe()
    if not codex:
        raise ValueError('Codex 执行器不存在（PATH 与常见安装路径均未找到；可用 ULTIMA_CODEX_EXE 显式指定）')
    admission = DispatchLock(SHARED / '.engineering-dispatch.lock')
    with admission:
        queue, record = registered(args.order)
        check_recovery_fence(record,args.expected_state,args.expected_run,args.expected_reservation)
        if record.get('state') not in ({'pending', 'blocked', 'audit'} if args.repair else {'pending'}):
            raise ValueError('锁内复核：工单状态不再允许派发')
        if cards:
            check_version_gates({'card_path': str(ROOT / 'tasks/cards' / cards[0] / 'task.md')}, ROOT / 'tasks')
            if any(not (ROOT / 'tasks/cards' / card_id / 'task.md').is_file() for card_id in cards):
                raise ValueError('锁内复核：任务卡缺失')
        if (ROOT / 'tasks/.pause-dispatch').exists() or (SHARED / '.pause-dispatch').exists():
            raise ValueError('锁内复核：派发已暂停')
        processes = native.codex_processes()
        active = [item for item in processes if item['role'] == 'exec']
        if any(item['role'] == 'unknown' for item in processes):
            raise ValueError('Codex 进程用途不明，按忙处理')
        if len(active) >= 3 or any(not item['project'] or Path(item['project']).resolve() == ROOT for item in active):
            raise ValueError('全局或项目实际执行 WIP 闸门未通过')
        if any(item.get('project') == 'UltimaAgent' and item.get('state') == 'executing'
               for item in queue['records']):
            raise ValueError('本项目登记仍有执行中工单，须先核查回执')
        if not args.execute:
            print(json.dumps({'ready': True, 'order': args.order, 'codex_roles': processes}, ensure_ascii=False))
            return 0
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        run = ROOT / 'tasks/queue/runs' / (args.order + '-' + stamp)
        run.mkdir(parents=True, exist_ok=False)
        write_dor_record(run / 'dispatch-record.json', record)
        prompt = prompt + receipt_contract_block(args.order)
        (run / 'prompt.txt').write_text(prompt, encoding='utf-8')
        base = git_snapshot()
        (run / 'before.json').write_text(json.dumps({'order': args.order, 'processes': processes, 'tree': base}, indent=2, ensure_ascii=False), encoding='utf-8')
        parent = os.getppid()
        parent_identity = process_identity(parent)
        if parent_identity is None:
            raise ValueError('父进程已失联，拒绝自治派发')
        final = run / 'final.json'
        command = [codex, '-a', 'never', '-c', f'model_reasoning_effort="{args.reasoning_effort}"', 'exec',
                   '-m', 'gpt-5.6-sol', '-C', str(ROOT), '--sandbox', 'danger-full-access',
                   '--skip-git-repo-check', '--json', '--color', 'never',
                   '--output-last-message', str(final), '-']
        reservation_note=('；reservation='+args.expected_reservation) if args.expected_reservation else ''
        state(args.order, 'executing', f'真实工单派发 {run.name}，一单一进程；尚未验收'+reservation_note, run, expected=record.get('state'))
        worker = None
        guardian = None
        sentinel_process = None
        job = None
        try:
            guardian = subprocess.Popen([sys.executable, str(ROOT / 'tasks/queue_engine/guardian.py'),
                str(os.getpid()), str(process_identity(os.getpid())), str(ROOT / 'tasks/.pause-dispatch'), str(run / 'done.json')],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=0x08000000)
            if (ROOT / 'tasks/.pause-dispatch').exists() or (SHARED / '.pause-dispatch').exists():
                raise ValueError('启动前复核：派发已暂停')
            with (run / 'out.jsonl').open('wb') as out, (run / 'err.log').open('wb') as err:
                worker = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.PIPE, stdout=out,
                                          stderr=err, creationflags=0x08000000)
                # Attach before sending any task input so tool children inherit
                # this job and cannot survive a timeout/supervisor exit.
                job = OwnedJob(worker)
                worker_identity = process_identity(worker.pid)
                if worker_identity is None:
                    raise ValueError('执行进程身份不可核对，拒绝启动监工')
                sentinel_process = start_sentinel(
                    args.order, run, worker.pid, worker_identity)
                (run / 'session.json').write_text(json.dumps({'pid': worker.pid,
                    'identity': worker_identity, 'parent_pid': parent,
                    'adapter_pid': os.getpid(), 'adapter_identity': process_identity(os.getpid()),
                    'engineering_reservation':args.expected_reservation,
                    'max_runtime_seconds': args.max_runtime_seconds,
                    'guardian_pid': guardian.pid, 'sentinel_pid': sentinel_process.pid,
                    'parent_identity': parent_identity, 'started_at': datetime.now(timezone.utc).isoformat()}), encoding='utf-8')
                worker.stdin.write(prompt.encode('utf-8'))
                worker.stdin.close()
                # EXECUTING and session identity are durable before releasing
                # admission. Other projects may now use the remaining WIP slots.
                admission.release()
                parent_lost = False
                deadline = time.monotonic()+args.max_runtime_seconds
                while worker.poll() is None:
                    if (ROOT/'tasks/.pause-dispatch').exists() or (SHARED/'.pause-dispatch').exists():
                        (run/'pause-stop.json').write_text(json.dumps({'at':datetime.now(timezone.utc).isoformat(),'status':'BLOCKED','reason':'Explicit dispatch pause; closing only this worker job'}),encoding='utf-8')
                        job.close()
                        worker.wait(timeout=5)
                        break
                    parent_lost = parent_lost or process_identity(parent) != parent_identity
                    if parent_lost and not (ROOT / 'tasks/.pause-dispatch').exists():
                        try:
                            with (ROOT / 'tasks/.pause-dispatch').open('x', encoding='utf-8') as stream:
                                json.dump({'mode': 'read-only', 'action': 'no-further-dispatch', 'run': run.name}, stream)
                        except FileExistsError:
                            pass
                    if time.monotonic() >= deadline:
                        (run / 'runtime-limit.json').write_text(json.dumps({
                            'at': datetime.now(timezone.utc).isoformat(), 'limit_seconds': args.max_runtime_seconds,
                            'reason': 'Bounded execution deadline; not a claim of deadlock', 'status': 'BLOCKED'}), encoding='utf-8')
                        job.close()
                        worker.wait(timeout=5)
                        break
                    time.sleep(0.25)
                code = worker.wait()
                job.close()
            await_sentinel(sentinel_process)
            sentinel_process = None
            (run / 'execution-exit.json').write_text(json.dumps({'exit_code': code,
                'finished_at': datetime.now(timezone.utc).isoformat(), 'worker_identity': None}), encoding='utf-8')
            receipt_decision = classify_receipt_path(
                final, work_order=args.order, exit_code=code)
            valid = receipt_decision.valid
            target = receipt_decision.state
            if (run / 'runtime-limit.json').exists() or (run/'pause-stop.json').exists():
                target = 'blocked'
            if parent_lost:
                target = 'blocked'
            # Completion is a second short critical section. Never decide the
            # audit slot from an unlocked snapshot or overwrite a newer run.
            with completion_lock():
                current, _ = registered(args.order)
                blocking, disregarded = audit_slot_holders(current, args.order)
                # The slot count used to be an implicit 1, which made the control
                # unreachable in practice: ordinary work orders queued outside it
                # rather than being judged. It is now a stated limit, so the number
                # is a decision someone made and can defend, not a side effect.
                slot_limit = AUDIT_SLOT_LIMIT
                audit_busy = target == 'audit' and len(blocking) >= slot_limit
                if audit_busy:
                    target = 'blocked'
                if disregarded:
                    (run / 'audit-slot.json').write_text(json.dumps({
                        'max_age_days': AUDIT_SLOT_MAX_AGE_DAYS,
                        'disregarded': disregarded,
                        'blocking': blocking,
                        'at': datetime.now(timezone.utc).isoformat()}, ensure_ascii=False), encoding='utf-8')
                # The snapshot that matters is the one taken *after* the worker
                # finished: base was captured before dispatch and says nothing
                # about the tree the receipt is actually claiming.
                after = git_snapshot()
                (run / 'done.json').write_text(json.dumps({
                    # The receipt names its own run and work order. Without these,
                    # a receipt from order A could be read under order B's run
                    # directory and every downstream check would agree with itself.
                    'work_order': args.order, 'run_id': run.name,
                    'card': str(card_path), 'card_sha256': card_sha256,
                    'cards': card_records,
                    'exit_code': code, 'receipt_valid': valid,
                    'state': target, 'audit_slot_busy': audit_busy, 'parent_lost': parent_lost,
                    'audit_slot_blocking': blocking, 'audit_slot_disregarded': disregarded,
                    'base_sha': base.get('base_sha'), 'worktree_dirty': base.get('worktree_dirty'),
                    'tree_oid': after.get('tree_oid'), 'changed_files': after.get('changed_files'),
                    'status_entries': after.get('status_entries'),
                    'end_sha': after.get('base_sha'),
                    'finished_at': datetime.now(timezone.utc).isoformat()}, ensure_ascii=False), encoding='utf-8')
                if not parent_lost:
                    reason = '等待审计名额（同身份模型二轮复核）；' if audit_busy else ''
                    if disregarded:
                        reason += (f'审计名额时限清点：{len(disregarded)} 单超 {AUDIT_SLOT_MAX_AGE_DAYS:g}d '
                                   f'或已标冻结，不再占位（{", ".join(d["order"] for d in disregarded)}）；')
                    state(args.order, target, reason+f'真实执行结束 exit={code}；{run.name}；待二轮复核，不自动批准或续派'+reservation_note, run,
                          expected='executing', expected_run=run.name)
            guardian.wait(timeout=5)
            print(json.dumps({'order': args.order, 'state': target, 'run': str(run)}, ensure_ascii=False))
            return 0 if target == 'audit' else 2
        except Exception as exc:
            (run / 'dispatch-error.json').write_text(json.dumps({'error': type(exc).__name__}), encoding='utf-8')
            if worker is not None and worker.poll() is not None and not (run / 'done.json').exists():
                after = git_snapshot()
                (run / 'done.json').write_text(json.dumps({'exit_code': worker.returncode,
                    'state': 'blocked', 'finalization_pending': True,
                    'card': str(card_path), 'card_sha256': card_sha256,
                    'cards': card_records,
                    'base_sha': base.get('base_sha'), 'worktree_dirty': base.get('worktree_dirty'),
                    'tree_oid': after.get('tree_oid'), 'changed_files': after.get('changed_files'),
                    'status_entries': after.get('status_entries'),
                    'end_sha': after.get('base_sha'),
                    'finished_at': datetime.now(timezone.utc).isoformat()}), encoding='utf-8')
            if worker is None:
                (run / 'done.json').write_text(json.dumps({'exit_code': None, 'launched': False,
                    'card': str(card_path), 'card_sha256': card_sha256,
                    'cards': card_records,
                    'base_sha': base.get('base_sha'), 'worktree_dirty': base.get('worktree_dirty'),
                    'tree_oid': base.get('tree_oid'), 'changed_files': base.get('changed_files'),
                    'status_entries': base.get('status_entries'),
                    'end_sha': base.get('base_sha'),
                    'error': type(exc).__name__}), encoding='utf-8')
                if guardian:
                    guardian.wait(timeout=5)
                state(args.order, 'blocked', f'执行器未启动，派发失败：{run.name}', run, expected='executing', expected_run=run.name)
            # Keep EXECUTING if a launched process might still be alive.
            raise
        finally:
            if job is not None:
                job.close()
            if sentinel_process is not None:
                await_sentinel(sentinel_process)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(json.dumps({'blocked': True, 'reason': str(exc)}, ensure_ascii=False))
        raise SystemExit(2)
