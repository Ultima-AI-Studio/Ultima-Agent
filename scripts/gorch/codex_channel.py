#!/usr/bin/env python3
"""GORCH 流水线 · Codex 执行段。

流水线只有一个执行段：接单 → 起 Codex → 回写 → 交复检。
不设角色分工、不写角色提示词；通道号 1–6 只用于并发时区分各自的 run-dir 与 flow 标签。

复用（未自研）：
  Codex 可执行体解析 → scripts/dispatch-work-order.py:40-45 / :143
  Codex 调用命令行     → scripts/dispatch-work-order.py:491-494
  看板状态机与并发写锁 → scripts/gorch/kanban_update.py（edict 移植，本轮未改）

用法：
  python codex_channel.py --task GORCH-001 --prompt 工单.md
  python codex_channel.py --task GORCH-001 --channel 3 --prompt - --dry-run
"""
import argparse
import glob as _glob
import hashlib
import json
import os
import pathlib
import re
import shutil
import stat
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
KANBAN = ROOT / 'scripts' / 'gorch' / 'kanban_update.py'
RUNS = ROOT / 'data' / 'gorch' / 'runs'
GIT_EXE = r'C:\Program Files\Git\cmd\git.exe'
# 子进程不建控制台窗口（L78）
_NO_WINDOW = 0x08000000 if sys.platform == 'win32' else 0

# 插槽适配层：S-EXEC 的 exe / model / 参数模板从这里读，换 CLI 不必改本文件。
sys.path.insert(0, str(ROOT))
from src.brain.slot_adapter import exec_settings, render_exec_argv  # noqa: E402

# 与 scripts/dispatch-work-order.py:40-45 逐字一致；Codex 升级会改安装位置且不留 alias
_CODEX_EXE_GLOBS = (
    r'C:\Program Files\WindowsApps\OpenAI.Codex_*\app\resources\codex.exe',
    r'C:\Users\*\AppData\Local\Microsoft\WindowsApps\codex.exe',
    r'C:\Users\*\AppData\Roaming\npm\codex.exe',
    r'C:\Users\*\AppData\Local\Programs\*\codex.exe',
)

# 看板的 AGENT_POLICY 没有给执行位开放 state/flow，只有 progress/todo/done/block。
# 用未注册身份走 _check_permission 的「未注册不拦截」分支，审计日志仍记到通道名。
CHANNEL_AGENT_ID = 'codex-channel'

PLAN_OPEN = '接单✅|调Codex🔄|执行|自检|回写'
PLAN_DONE = '接单✅|调Codex✅|执行✅|自检✅|回写✅'
PLAN_FAIL = '接单✅|调Codex✅|执行|自检|回写🚫'


def _status_rows(workdir):
    """解析 `git status --porcelain -z -uall --ignored`。

    返回 (ok, rows, ignored)。rows 是 [(code, path)]，ignored 是被 .gitignore 命中的
    路径集合。`-z` 不做 C 风格转义：路径原样输出、以 NUL 分隔，带首空格/中文/引号的
    路径不会被拆错（第七轮审计：此前用展示文本 splitlines + strip()，` M docs/x`
    的首空格被吃掉，路径变成 `M docs/x` 从而误判越域）。

    r8（第七轮审计 A⑦ / B3）：rename 与 copy 在 `-z` 下是**两项**——先目标、随后
    一项是源路径（不带状态码）。r7 直接 `i += 1` 把源路径跳过了，于是"域外文件被
    移进域内"时域外那一侧的删除完全不可见。现在源路径也进 rows，用专用码 `SRC`
    标记（展示成 `SRC <path>`）：下游按 rows 建 paths 时源路径自动进指纹集合，
    源已消失则摘要为 ABSENT（与基线里的 sha 不同 → 算本次改动，参与写域校验）。
    """
    rc, out = _git_text(workdir, ['status', '--porcelain', '-z', '-uall', '--ignored'])
    if rc is None or rc != 0:
        return False, [], set()
    parts = (out or '').split('\0')
    rows, ignored = [], set()
    i = 0
    while i < len(parts):
        item = parts[i]
        i += 1
        if not item:
            continue
        code = item[:2]
        path = item[3:]
        if not path:
            continue
        if code == '!!':
            ignored.add(path.replace('\\', '/'))
            continue
        # r10（第九轮审计 A⑦/B3）：porcelain 的 XY 两位都可能是 R/C——
        # 工作区侧未暂存 rename 是 ` R`（X 位空格），只看 code[:1] 会漏掉它，
        # 那条紧随的裸源路径就会被当成下一条状态行、`item[3:]` 截掉前三字符，
        # 于是域外源的删除被伪装成一条域内路径（能把越域写放行）。
        if any(ch in ('R', 'C') for ch in code[:2]) and i < len(parts):
            # -z 下 rename/copy 的**源路径**是紧随其后的独立一项，必须一并保留
            src = parts[i]
            i += 1
            if src:
                rows.append(('SRC', src.replace('\\', '/')))
        rows.append((code, path.replace('\\', '/')))
    return True, rows, ignored



def worktree_state(workdir):
    """执行端到底有没有在 worktree 里留下改动。

    退出码 0 只说明 CLI 正常退出，不说明它写过东西：Codex 可以一声不响地跑完、
    什么都不改，回执照样 done 再被 merge 合进主线，等于把"没干活"当成果。
    返回 (kind, detail)：
      changed  有改动（含被 .gitignore 命中的路径），detail 是状态摘要（留作证据）
      clean    干净，一个字节都没动
      not_repo 不是 git 工作树，无从校验（保持只看退出码，记下供审计）
      error    查不动（git 不存在/超时/status 失败），fail-closed
    """
    try:
        probe = subprocess.run(
            [GIT_EXE, '-C', str(workdir), 'rev-parse', '--is-inside-work-tree'],
            capture_output=True, text=True, encoding='utf-8', errors='replace',
            timeout=30, creationflags=_NO_WINDOW)
    except Exception:
        return 'error', 'rev-parse 调用失败'
    if probe.returncode != 0 or probe.stdout.strip() != 'true':
        return 'not_repo', (probe.stderr or '').strip()[:200]
    ok, rows, ignored = _status_rows(workdir)
    if not ok:
        return 'error', 'git status 调用失败'
    if not rows and not ignored:
        return 'clean', ''
    shown = [f'{code} {path}' for code, path in rows]
    shown += [f'!! {path}' for path in sorted(ignored)]
    return 'changed', chr(10).join(shown)


def _status_set(detail):
    """把 git status --porcelain 文本拆成行集合，用于执行前后对比。

    第三轮审计：只有"执行后一次快照"无法区分"本次改的"和"worktree 本来就有"的。
    provision 幂等复用既有 worktree 时，旧改动会被算成本次成果。这里用执行前
    快照做基线，只有**相对基线新增的行**才算本次产出。
    """
    return {ln for ln in (detail or '').splitlines() if ln.strip()}


def _git_text(workdir, args, timeout=180):
    """跑一条只读 git 命令，返回 (rc, stdout)。失败不抛，交给调用方判。"""
    try:
        r = subprocess.run(
            [GIT_EXE, '-C', str(workdir), *args],
            capture_output=True, text=True, encoding='utf-8', errors='replace',
            timeout=timeout, creationflags=_NO_WINDOW)
    except Exception:
        return None, ''
    return r.returncode, (r.stdout or '')


_DIGEST_CHUNK = 1 << 20
_STATUS_IGNORED_LIMIT = 4000



def _digest(workdir, rel):
    """单路径内容指纹：存在→流式 sha256；不存在→ABSENT；读失败→None。

    逐路径而不是全局 diff 哈希：全局哈希只说明"diff 文本变了"，拿不出是哪个路径
    变的，脏基线下同路径继续修改会被判成"无新增"（第七轮审计 #1）。

    r8（第七轮审计 N2）：r7 对超过 8MiB 的文件退化成 `BIG:size:int(mtime)`、读失败
    写成 `ERR:errno`，两者都不是内容摘要——同一秒内等长改写摘要完全不变，脏基线里
    域外大文件被改也无从发现，只要同时有一条域内 fresh 就能拿到 done。现在不论
    大小一律按内容做**流式** sha256（分块读，不整块进内存）。
    读失败返回 None 而不是可比较的哨兵串：两次 `ERR:5` 相等会被判"没变"，等于把
    不可读当成没改。由 worktree_fingerprint 把整份指纹标成不可用，执行前/后统一
    fail-closed。
    """
    p = pathlib.Path(workdir) / rel
    # r9（第八轮审计 N2 复发）：只有"确实不存在"才算 ABSENT。stat 的其它 OSError
    # （权限、I/O、路径组件不可达）说明**读不到**，不是**没改**——两者都记成 ABSENT
    # 时，脏基线里同一路径两次 stat 失败会得到相同摘要，被 fresh_changes 判成"没变"，
    # 域外不可读改动就被漏检。读不到一律 None，由 worktree_fingerprint 整体标 ERR。
    try:
        st = p.stat()
    except FileNotFoundError:
        return 'ABSENT'
    except OSError:
        return None
    # r11（第十轮审计 E-2）：**存在但不是普通文件**（目录 / symlink / 特殊文件）
    # 不能与「不存在」共用 ABSENT——两次采样都 ABSENT 会被判"没变"，而"路径还在、
    # 只是类型不对"本来就是另一个事实。给带类型的摘要：它仍是可比较的（类型一变
    # 摘要就变），既不误判"没改"，也不会把整份指纹打成不可用（untracked 目录是常态）。
    if not stat.S_ISREG(st.st_mode):
        kind = ('dir' if stat.S_ISDIR(st.st_mode)
                else 'link' if stat.S_ISLNK(st.st_mode) else 'other')
        return 'TYPE:' + kind
    h = hashlib.sha256()
    try:
        with open(str(p), 'rb') as fh:
            for chunk in iter(lambda: fh.read(_DIGEST_CHUNK), b''):
                h.update(chunk)
    except OSError:
        return None
    return h.hexdigest()



def worktree_fingerprint(workdir, status_detail=None):
    """逐路径内容指纹（tracked / untracked / ignored 全覆盖）。

    返回 dict：
      paths     {相对路径: 内容摘要}——仅 git add 不改文件字节，故不会误判"新增"；
      ignored   被 .gitignore 命中的路径集合（此前 status 不带 --ignored，域外
                ignored 写完全不可见，第七轮审计 #2）；
      rows      [(状态码, 路径)]，留作证据；
      diff_sha  全局 diff 哈希，只作证据，判定不再依赖它。
    任一维度取不到时返回带 'ERR:*' 的指纹，由调用方 fail-closed。
    `status_detail` 仅为兼容旧调用签名，解析一律走 -z 结构化输出。
    """
    ok, rows, ignored = _status_rows(workdir)
    if not ok:
        return {'paths': {}, 'ignored': set(), 'rows': [],
                'diff_sha': 'ERR:status'}
    if len(ignored) > _STATUS_IGNORED_LIMIT:
        return {'paths': {}, 'ignored': ignored, 'rows': rows,
                'diff_sha': f'ERR:ignored>{_STATUS_IGNORED_LIMIT}'}
    paths = {}
    for _code, path in rows:
        paths[path] = _digest(workdir, path)
    for path in ignored:
        paths[path] = _digest(workdir, path)
    # r8（N2 后半）：任一路径内容读不出来，整份指纹显式不可用。不能只把该路径记成
    # 某个哨兵串——哨兵与上一次相等就会被判"没变"，那正是 fail-open。
    unreadable = sorted(p for p, d in paths.items() if d is None)
    if unreadable:
        return {'paths': paths, 'ignored': ignored, 'rows': rows,
                'diff_sha': 'ERR:digest:' + unreadable[0]}
    rc, diff_text = _git_text(workdir, ['diff', 'HEAD'])

    diff_sha = (hashlib.sha256(diff_text.encode('utf-8', 'replace')).hexdigest()
                if rc == 0 else f'ERR:{rc}')
    return {'paths': paths, 'ignored': ignored, 'rows': rows, 'diff_sha': diff_sha}


class _BaselineUnusable(Exception):
    """执行前建不出可信基线时用它中止本次执行（fail-closed，不调 Codex）。"""


def fresh_changes(base_fp, after_fp, after_detail=None):
    """本轮新增/变化的**路径集合**（相对执行前基线，内容级）。

    返回 (fresh: set[str], basis: str)，fresh 元素是纯仓库相对路径。
    · 基线 clean  → 执行后所有变化路径都是本次产出；
    · 基线脏      → 只认「基线里没有的路径」与「同路径内容摘要变了」；
                    仅 `git add`（状态码 M → M ）内容摘要不变，不算新增；
                    同路径继续改内容摘要变，算新增（第七轮审计 #1 的堵法）。
    """
    if not after_fp or 'paths' not in after_fp:
        lines = _status_set(after_detail)
        return {ln for ln in lines if ln.strip()}, '基线缺失：按状态行整集判定（弱判据）'
    a_paths = dict(after_fp.get('paths') or {})
    if base_fp is None:
        return set(a_paths), '基线 clean：执行后改动全部属本次'
    b_paths = dict(base_fp.get('paths') or {})
    fresh = {p for p in a_paths if p not in b_paths}
    fresh |= {p for p in a_paths if p in b_paths and a_paths[p] != b_paths[p]}
    # r10（第九轮审计 B4）：执行后**从状态集合里消失**的基线路径同样是本次改动。
    # 基线里有域外脏文件、任务把它恢复成 HEAD，after 里就没有它了；
    # 只遍历 after 差集等于"删掉域外改动"这一动作完全不可见 —— 再顺手改一个
    # 域内文件就能过写域检查落 done。
    fresh |= {p for p in b_paths if p not in a_paths}
    return fresh, '基线脏：逐路径内容指纹差分 + 消失路径回补（ignored 一并纳入）'


def _norm_path(text):
    """统一路径写法：反斜杠转正斜杠，只剥真正的 `./` 前缀，**不改动首尾空格**。

    r7 自查补洞：`lstrip('./')` 会把 `.github/workflows/x.yml` 剥成
    `github/workflows/x.yml`，隐藏目录被吃一层，写域校验就比对错了。

    r8（第七轮审计 N4）：r7 仍保留 `text.strip()`，于是文件名自身的首尾空格被吃掉
    （`docs/a .md` 变成 `docs/a.md`），写域校验比对的是另一个文件。合法文件名里的
    空格必须原样保留；路径合法性（绝对 / drive / UNC / `..`）交给 _repo_relative_safe。
    """
    p = str(text).replace('\\', '/')
    while p.startswith('./'):
        p = p[2:]
    return p



def _fresh_paths(fresh):
    """从 fresh 证据集里抽出真实路径（用于写域校验）：**只接受纯路径**。

    r9（第八轮审计 N11）：r8 保留了「按字符串开头猜展示格式」的兼容——`SRC ` 前缀
    剥 4 字符、`<XY> ` 状态前缀剥 3 字符。但合法文件名本身就可以以 `SRC ` 或 ` M `
    开头，那不是展示行，是真实路径：`SRC docs/in-scope.md` 被改写成
    `docs/in-scope.md` 后，一个域外文件就骗过了写域校验（新的 fail-open）。

    rename / copy 的两端已由 `_status_rows` 结构化产出（目标进 rows、源进
    `('SRC', src)`），并直接进入 `worktree_fingerprint.paths`，因此写域校验侧不需要
    任何形态推断。这里遇到不像纯路径的串，只会原样交给 `_repo_relative_safe` 判非法
    （fail-closed），不会再把字符剥掉。
    """
    out = []
    for raw in fresh or ():
        text = str(raw)
        if not text:
            continue
        out.append(_norm_path(text))
    return [p for p in out if p]



_DRIVE_PREFIX = re.compile(r'^[A-Za-z]:')


def _repo_relative_safe(path):
    """是不是一个合法的 repo-relative 路径（拒绝绝对 / drive / UNC / `..` / 空段）。

    r8（第七轮审计 N4）：此前写域校验只做裸字符串前缀命中，`docs/../outside/x`
    因为以 `docs/` 开头就被当成域内——实际写到仓库外或另一个目录。这里在写域
    校验前统一拦下：绝对路径、Windows 盘符、UNC、任何 `..` 段、空段（`a//b`）、
    `.` 段都算不合法，一律按"域外"处理（fail-closed）。
    """
    p = str(path or '').replace('\\', '/')
    if not p:
        return False
    if p.startswith('/'):          # 同时覆盖 UNC 的 `//server/share`
        return False
    if _DRIVE_PREFIX.match(p):
        return False
    if any(seg in ('', '.', '..') for seg in p.split('/')):
        return False
    return True


def _scope_match(path, pat):
    """按路径段匹配：`*` 不跨 `/`，`?` 匹配单个非分隔符字符，`**` 跨段。

    第七轮审计 #2：fnmatch 的 `*` 会跨目录，`scripts/gorch/*.py` 能命中
    `scripts/gorch/sub/x.py`，等于写域比声明的宽一层。

    r8（N4）：path 与 pattern 两侧都先过 _repo_relative_safe——含 `..` 的
    `docs/../outside` 不再因为字符串前缀命中而被接受；pattern 自身不合法时
    直接判不匹配（不猜它想指哪）。
    """
    p = str(pat).replace('\\', '/').strip().rstrip('/')
    if not p or not _repo_relative_safe(p):
        return False
    if not _repo_relative_safe(path):
        return False

    if path == p or path.startswith(p + '/'):
        return True
    rx, i = '', 0
    while i < len(p):
        c = p[i]
        if c == '*':
            if i + 1 < len(p) and p[i + 1] == '*':
                rx += '.*'
                i += 2
                continue
            rx += '[^/]*'
        elif c == '?':
            rx += '[^/]'
        else:
            rx += re.escape(c)
        i += 1
    return (re.fullmatch(rx, path) is not None
            or re.fullmatch(rx + '/.*', path) is not None)


def _outside_scope(paths, scope):
    """返回不在授权写域内的路径；scope 为空表示不校验（调用方已标注 undeclared）。

    写域写法与卡片一致：目录前缀（``docs/reports/``）或通配（``scripts/*.py``）。

    r8（N4）：每条路径先验 repo-relative 合法性——绝对路径 / drive / UNC /
    含 `..` 的一律直接判越域，不再进入前缀或正则匹配（否则 `docs/../outside/x`
    会因 `docs/` 前缀命中而被放行）。
    """
    if not scope:
        return []
    pats = [_norm_path(x).rstrip('/') for x in scope if str(x).strip()]
    bad = []
    for p in paths:
        if not _repo_relative_safe(p):
            bad.append(p)
            continue
        if not any(_scope_match(p, pat) for pat in pats):
            bad.append(p)
    return bad



def load_authorizations(manifest_path, task):
    """读编排方签发的授权清单（第五轮审计 7.3-6）。

    返回 dict；结构不合法或没有本任务条目时 ``problem`` 非空，由调用方 fail-closed。

    r8（第七轮审计 N1 / N6）：
    · 没有 manifest 一律 problem——命令行开关不构成授权，也不再存在"手工回退"分支；
    · 解析后先验**根节点必须是对象**再 `.get()`：此前合法 JSON 数组会抛未捕获的
      AttributeError，既不是 blocked 也不是 SystemExit，审计记录直接缺失；
    · manifest 必须带 `invocation`：执行记录要能绑定"这一次"调用，否则 merge 端
      无法确认归属（生产端与消费端共用这一个字段）。
      manifest 级的 `invocation` / `target` / `manifest` 一并回传，由 main() 写进记录。
    """
    out = {'source': 'cli', 'write_scope': [], 'write_scope_enforced': False,
           'no_change_allowed': False, 'allow_non_repo': False,
           'granted_by': None, 'problem': '',
           'manifest': '', 'invocation': '', 'target': ''}
    if not manifest_path:
        out['problem'] = ('未提供 invocation manifest：授权只由编排方在派发时签发，'
                          '执行端不读卡片字段、也不接受命令行自授权；'
                          '确需手工验证请由编排方签发清单后传 --manifest')
        return out
    p = pathlib.Path(manifest_path)
    if not p.is_file():
        out['problem'] = f'invocation manifest 不存在：{p}'
        return out
    try:
        data = json.loads(p.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
        out['problem'] = f'invocation manifest 不可解析：{p}（{exc}）'
        return out
    if not isinstance(data, dict):
        out['problem'] = (f'invocation manifest 根节点不是对象（{type(data).__name__}）：'
                          f'{p}')
        return out
    inv = str(data.get('invocation') or '').strip()
    if not inv:
        out['problem'] = ('invocation manifest 缺少 invocation：执行记录无法绑定本次调用，'
                          'merge 端会把它判成 stale（清单应由编排方 grant_invocation 签发）')
        return out
    tasks = data.get('tasks')
    if not isinstance(tasks, dict):
        out['problem'] = f'invocation manifest 结构不对（tasks 不是对象）：{p}'
        return out
    g = tasks.get(task)
    if not isinstance(g, dict):
        out['problem'] = f'invocation manifest 未包含任务 {task} 的授权'
        return out
    scope = g.get('write_scope')
    if not isinstance(scope, list):
        out['problem'] = f'{task} 的 write_scope 不是数组：{scope!r}'
        return out
    for flag in ('no_change_allowed', 'allow_non_repo'):
        if not isinstance(g.get(flag), bool):
            out['problem'] = f'{task} 的 {flag} 不是严格布尔：{g.get(flag)!r}'
            return out
    out.update({
        'source': 'manifest',
        'write_scope': [str(s) for s in scope],
        'write_scope_enforced': bool(g.get('write_scope_enforced')),
        'no_change_allowed': g['no_change_allowed'],
        'allow_non_repo': g['allow_non_repo'],
        'granted_by': g.get('granted_by'),
        'manifest': str(p.resolve()),
        'invocation': inv,
        'target': str(data.get('target') or ''),
    })
    return out



def resolve_codex_exe():
    """解析执行体路径：适配层配置 → env → PATH → 四组 glob（按 mtime 取最新）。

    前两者是插槽替换入口：配 config/gorch/slots.json 的 S-EXEC.exe 或设
    GORCH_EXEC_EXE / ULTIMA_CODEX_EXE，就能换成另一个 CLI，不改本文件。
    后两者沿用 scripts/dispatch-work-order.py:143 的原逻辑，保证零配置行为不变。
    """
    configured = exec_settings()['exe']
    if configured and pathlib.Path(configured).is_file():
        return configured
    explicit = os.environ.get('ULTIMA_CODEX_EXE', '').strip()
    if explicit and pathlib.Path(explicit).is_file():
        return explicit
    found = shutil.which('codex.exe') or shutil.which('codex')
    if found:
        return found
    hits = [p for pattern in _CODEX_EXE_GLOBS
            for p in _glob.glob(pattern) if pathlib.Path(p).is_file()]
    return max(hits, key=lambda p: os.path.getmtime(p)) if hits else None


def now_stamp():
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')


def kanban(*args, check=True):
    """看板操作一律走 CLI，不直接读写 JSON。"""
    env = dict(os.environ)
    env['ULTIMA_AGENT_ID'] = CHANNEL_AGENT_ID
    env['PYTHONIOENCODING'] = 'utf-8'
    r = subprocess.run(
        [sys.executable, str(KANBAN), *[str(a) for a in args]],
        capture_output=True, text=True, encoding='utf-8', errors='replace', env=env,
    )
    if check and r.returncode != 0:
        raise RuntimeError(
            f'看板命令失败 {args[:2]}: rc={r.returncode} '
            f'{(r.stdout + r.stderr).strip()[-400:]}')
    return r


def run_codex(codex, prompt_bytes, workdir, last_msg, effort, timeout):
    """命令行默认为 codex（与 scripts/dispatch-work-order.py:491-494 一致，去掉 --json 流式事件）。

    适配层配了 S-EXEC.args_template 时，整体改用模板渲染的 argv——这是换
    Claude / Gemini / Qwen / OpenCode 等 CLI 的唯一入口，调度逻辑不参与。
    """
    settings = exec_settings()
    template = settings['args_template']
    if template:
        rendered = render_exec_argv(settings, exe=codex, workdir=str(workdir),
                                    last_msg=str(last_msg), effort=effort)
        cmd = rendered if rendered and rendered[0] == codex else [codex, *rendered]
    else:
        cmd = [
            codex, '-a', 'never', '-c', f'model_reasoning_effort="{effort}"', 'exec',
            '-m', settings['model'], '-C', str(workdir),
            '--sandbox', 'danger-full-access', '--skip-git-repo-check',
            '--color', 'never', '--output-last-message', str(last_msg), '-',
        ]
    env = None
    if settings['env']:
        env = dict(os.environ)
        env.update(settings['env'])
    started = time.monotonic()
    proc = subprocess.run(
        cmd, input=prompt_bytes, capture_output=True, timeout=timeout,
        creationflags=0x08000000,  # CREATE_NO_WINDOW
        env=env,
    )
    return proc, time.monotonic() - started


def main(argv=None):
    ap = argparse.ArgumentParser(description='GORCH 流水线 Codex 执行段')
    ap.add_argument('--task', required=True, help='看板任务号')
    ap.add_argument('--channel', type=int, default=1, choices=range(1, 7),
                    help='通道号 1–6，并发时区分 run-dir 与 flow 标签')
    ap.add_argument('--prompt', required=True, help='工单文件路径，- 表示从 stdin 读')
    ap.add_argument('--workdir', default=str(ROOT), help='Codex 工作目录（并发时传各自 worktree）')
    ap.add_argument('--run-dir', default='', help='运行目录，默认 data/gorch/runs/<task>-ch<N>-<ts>')
    ap.add_argument('--effort', default='high', choices=('low', 'medium', 'high'))
    ap.add_argument('--timeout', type=int, default=3600)
    ap.add_argument('--dry-run', action='store_true', help='只走看板流程，不真起 Codex')
    ap.add_argument('--simulate-fail', action='store_true', help='演练失败路径')
    ap.add_argument('--allow-non-repo', action='store_true',
                    help=('仅留痕：本开关不构成授权，取值一律以 manifest 的 '
                          'allow_non_repo 为准（命令行传了也只写进记录的 ignored_cli_flags）'))
    ap.add_argument('--no-change-allowed', action='store_true',
                    help=('仅留痕：本开关不构成授权，取值一律以 manifest 的 '
                          'no_change_allowed 为准；未授权时 worktree 零改动仍判 blocked'))
    ap.add_argument('--manifest', default='',
                    help='编排方签发的 invocation manifest（必填；须含 invocation）。'
                         '授权（写域与 no_change_allowed/allow_non_repo）只从此清单读，'
                         '命令行开关不构成授权')
    args = ap.parse_args(argv)

    if not KANBAN.is_file():
        print(f'看板脚本不存在: {KANBAN}', file=sys.stderr)
        return 2

    label = f'通道{args.channel}'
    run_dir = (pathlib.Path(args.run_dir) if args.run_dir
               else RUNS / f'{args.task}-ch{args.channel}-{now_stamp()}')
    run_dir.mkdir(parents=True, exist_ok=True)

    # 记录在任何前置校验之前建好（第四轮审计）：此前"空工单"与"找不到执行体"都在建记录
    # 之前直接 return，观测目录里不会留下失败记录，合并池仍可能取到更旧的那条 done。
    record = {
        'task': args.task, 'channel': args.channel, 'run_dir': str(run_dir),
        'workdir': args.workdir, 'dry_run': args.dry_run,
        'started_at': datetime.now(timezone.utc).isoformat(),
        # r8：先占位，拿到 manifest 后覆盖（前置失败也留这三项，便于回溯）
        'manifest': '', 'invocation': '', 'target': '',
    }

    def _fail_early(code, reason, kanban_reason=None):
        """前置失败也落一条 blocked 记录，别让更旧的 done 顶上来。"""
        record['exit_code'] = code
        record['reason'] = reason
        record['mergeable'] = False
        record['result'] = 'blocked'
        record['finished_at'] = datetime.now(timezone.utc).isoformat()
        (run_dir / 'codex-channel.json').write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
        if kanban_reason:
            kanban('block', args.task, kanban_reason, check=False)
        print(json.dumps({'task': args.task, 'channel': args.channel,
                          'result': 'blocked', 'run_dir': str(run_dir)},
                         ensure_ascii=False))
        print(reason, file=sys.stderr)
        return 2 if code == 2 else 3

    # 授权只认编排方签发的那份清单（第五轮审计 Q3-9 / 7.3-6）：卡片自己写的字段
    # 只能算"请求"，执行端不读；清单缺失/结构不对/没有本任务条目一律 fail-closed。
    auth = load_authorizations(args.manifest, args.task)
    record['authorizations'] = {k: v for k, v in auth.items() if k != 'problem'}
    # r8（第七轮审计 N1）：manifest 级身份必须写进生产记录——merge 端要靠它绑定
    # 本次调用；r7 只写确认了授权文件在不在，记录里没有 invocation 可绑定。
    record['manifest'] = auth.get('manifest') or ''
    record['invocation'] = auth.get('invocation') or ''
    record['target'] = auth.get('target') or ''
    if auth['problem']:
        return _fail_early(2, f'授权清单不可用：{auth["problem"]}')
    # 第七轮审计 #6：命令行开关不再具备授权能力——没有 manifest 的调用在上一步
    # 已被 problem 阻断。这里把两个 flag 记进记录，留证"传了但没生效"。
    if args.no_change_allowed or args.allow_non_repo:
        record['ignored_cli_flags'] = {
            'no_change_allowed': bool(args.no_change_allowed),
            'allow_non_repo': bool(args.allow_non_repo),
            'note': '命令行开关不构成授权，实际取值以 manifest 为准',
        }
    no_change_allowed = bool(auth['no_change_allowed'])
    allow_non_repo = auth['allow_non_repo']

    if args.prompt == '-':
        prompt_bytes = sys.stdin.buffer.read()
    else:
        prompt_bytes = pathlib.Path(args.prompt).read_bytes()
    if not prompt_bytes.strip():
        return _fail_early(2, '工单为空，拒绝执行')
    (run_dir / 'prompt.txt').write_bytes(prompt_bytes)
    record['prompt_sha256'] = hashlib.sha256(prompt_bytes).hexdigest()

    codex = None if args.dry_run else resolve_codex_exe()
    record['codex'] = codex
    if not args.dry_run and not codex:
        return _fail_early(3, 'Codex 执行段未找到（检查 ULTIMA_CODEX_EXE / PATH）',
                           kanban_reason='Codex 执行段未找到')

    # 1) 接单（任务已在 Doing 时这次 state 会被状态机拒绝，幂等处理不中断）
    enter = kanban('state', args.task, 'Doing', f'{label} 开始执行', check=False)
    record['already_doing'] = '非法状态转换' in (enter.stdout + enter.stderr)
    kanban('flow', args.task, label, label, '▶️ 开始执行')
    kanban('progress', args.task, f'{label} 接单，准备调用 Codex', PLAN_OPEN)

    # 2) 执行
    ok = False
    mergeable = True
    summary = ''
    guard_reason = ''
    if args.dry_run:
        record['exit_code'] = 0 if not args.simulate_fail else 1
        ok = not args.simulate_fail
        summary = '[dry-run] 未真实执行 Codex'
        (run_dir / 'out.log').write_text(summary, encoding='utf-8')
    else:
        last_msg = run_dir / 'last-message.md'
        # 执行前基线（第三轮审计 A4）：只认相对基线**新增**的改动，
        # 复用脏 worktree 时不把旧文件当成本次产出。
        base_kind, base_detail = worktree_state(args.workdir)
        record['worktree_baseline'] = base_kind
        base_fp = None
        if base_kind == 'changed':
            record['worktree_baseline_dirty'] = base_detail[:2000]
            base_fp = worktree_fingerprint(args.workdir, base_detail)
            record['worktree_baseline_fingerprint'] = {
                'paths': len(base_fp.get('paths') or {}),
                'ignored': len(base_fp.get('ignored') or ()),
                'diff_sha': base_fp.get('diff_sha'),
            }
        try:
            # 基线建不出来就不开工（第四轮审计）：此前 error / not_repo 时 before 取空集，
            # 执行后一读到 changed，worktree 里所有既有脏项都会被当成本轮新增——纯 fail-open。
            if base_kind == 'error':
                raise _BaselineUnusable(
                    f'执行前无法读取 worktree 状态，fail-closed：{base_detail}')
            # 脏基线但**内容指纹读不出来**时同样不许开工（第五轮审计 Q3-6）：
            # 此前只有"执行后指纹 ERR"被阻断，基线 ERR 会被 fresh_changes 退化成
            # 状态行差集去判产出——那是被点名的弱判据，等于在不可判定的基线上放行。
            if base_fp and str(base_fp.get('diff_sha') or '').startswith('ERR:'):
                raise _BaselineUnusable(
                    '执行前 worktree 内容指纹读取失败（diff_sha='
                    f'{base_fp.get("diff_sha")}），无法建立产出基线，fail-closed')
            if base_kind == 'not_repo' and not allow_non_repo:
                raise _BaselineUnusable(
                    '执行前 workdir 不是 git 工作树，无法建立产出基线，'
                    '批量路径 fail-closed（确需在无仓库目录执行时加 --allow-non-repo）')
            proc, elapsed = run_codex(codex, prompt_bytes, args.workdir,
                                      last_msg, args.effort, args.timeout)
            record['exit_code'] = proc.returncode
            record['elapsed_sec'] = round(elapsed, 1)
            (run_dir / 'stdout.log').write_bytes(proc.stdout or b'')
            (run_dir / 'stderr.log').write_bytes(proc.stderr or b'')
            ok = proc.returncode == 0
            if last_msg.is_file():
                summary = last_msg.read_text(encoding='utf-8', errors='replace').strip()[:300]
            # 产出校验：done 不能只凭退出码（§七-8）。只在退出码已为 0 时追加判定，
            # 退出码非 0 的失败原因仍以原生错误为准，不被这里的结论覆盖。
            if ok:
                kind, detail = worktree_state(args.workdir)
                record['worktree_state'] = kind
                record['worktree_changes'] = (detail or '')[:2000]
                # 本次产出 = 相对执行前基线**新增**的改动（第三轮审计 A4）。
                # 第四轮：改用内容级指纹，porcelain 行集合只作为其中一维——
                # 同一文件内容继续变化时行文本不变（此前误杀），只 `git add` 改状态码时
                # 会凭空多一行（此前 fail-open），两种都要靠 diff 指纹与未跟踪清单兜住。
                after_fp = None
                fresh = set()
                basis = ''
                if kind == 'changed':
                    after_fp = worktree_fingerprint(args.workdir, detail)
                    record['worktree_after_fingerprint'] = {
                        'paths': len(after_fp.get('paths') or {}),
                        'ignored': len(after_fp.get('ignored') or ()),
                        'diff_sha': after_fp.get('diff_sha'),
                    }
                    # 指纹读失败不能退化判定（第四轮审计 #4）：`ERR:*` 说明 git diff
                    # 本身没跑通，此时任何"有/无产出"的结论都没有依据，直接阻断。
                    if str(after_fp.get('diff_sha') or '').startswith('ERR:'):
                        ok = False
                        guard_reason = (
                            '执行后 worktree 指纹读取失败'
                            f'（diff_sha={after_fp.get("diff_sha")}），'
                            '无法判定本次产出，fail-closed 不写 done')
                    else:
                        fresh, basis = fresh_changes(base_fp, after_fp, detail)
                        record['worktree_new_changes'] = '\n'.join(sorted(fresh))[:2000]
                        record['worktree_fresh_basis'] = basis
                        # 授权写域校验（第五轮审计 7.3-4/6）：所有新增路径必须落在
                        # 编排方授权的写域内，越域即 blocked；未声明写域的卡在记录里
                        # 标 enforced=False，交由编排侧决定是否补卡（不静默当已授权）。
                        scope = auth.get('write_scope') or []
                        if auth.get('write_scope_enforced') and scope and fresh:
                            outside = _outside_scope(_fresh_paths(fresh), scope)
                            record['write_scope_check'] = {
                                'scope': scope, 'outside': outside}
                            if outside:
                                ok = False
                                guard_reason = (
                                    f'产出路径超出授权写域 {len(outside)} 个：'
                                    f'{outside[:5]}（授权 {scope}），fail-closed 不写 done')
                if kind == 'clean':
                    if no_change_allowed:
                        # 纯验证卡 / 纯报告卡：可以判「执行完成」，但**不签发合并授权**。
                        # 「验证成功」与「有可合并成果」是两个状态，混成一个会让零产出的卡
                        # 进合并池（第四轮审计）。
                        record['worktree_state_note'] = (
                            'clean，按 --no-change-allowed 放行（本次约定不产生仓库改动）')
                        mergeable = False
                    else:
                        ok = False
                        guard_reason = ('Codex 退出码 0，但 worktree 无任何改动——'
                                        '判空产出，不写 done（执行端没留下任何可合并内容）。'
                                        '若本次本就约定不改仓库，须显式加 --no-change-allowed')
                elif kind == 'changed' and not fresh:
                    ok = False
                    guard_reason = ('Codex 退出码 0，worktree 有改动但相对执行前基线无新增——'
                                    '改动全部来自复用前既有的脏状态（状态行与内容指纹都未变），'
                                    '判空产出，不写 done')
                elif kind == 'error':
                    ok = False
                    guard_reason = f'无法确认 worktree 改动，fail-closed：{detail}'
                elif kind == 'not_repo':
                    # 批量路径下"不是 git 工作树"等于无法确认产出：get worktree 的编排
                    # 一定给的是 worktree，落到 not_repo 说明接线错了或 workdir 指错。
                    # 只有明确声明无仓库（手工验证场景）才放行（第二轮审计）。
                    if allow_non_repo:
                        record['worktree_state_note'] = 'not_repo，已按 --allow-non-repo 放行'
                    else:
                        ok = False
                        guard_reason = ('workdir 不是 git 工作树，无法确认产出，'
                                        '批量路径 fail-closed（确需在无仓库目录执行时加 '
                                        '--allow-non-repo）')
        except _BaselineUnusable as exc:
            record['exit_code'] = None
            ok = False
            guard_reason = str(exc)
        except subprocess.TimeoutExpired:
            record['exit_code'] = 124
            record['elapsed_sec'] = args.timeout
            summary = f'Codex 超时（>{args.timeout}s）'
            ok = False

    # 3) 回写（done 自身已写一条 →复检 的 flow，这里不再重复）
    if ok:
        kanban('progress', args.task, f'{label} 已产出，交复检', PLAN_DONE)
        kanban('done', args.task, str(run_dir), summary or '完成，无末段消息')
    else:
        err_tail = ''
        for name in ('stderr.log', 'out.log'):
            f = run_dir / name
            if f.is_file():
                err_tail = f.read_bytes().decode('utf-8', 'replace').strip()[-200:]
                if err_tail:
                    break
        reason = guard_reason or (
            f'Codex 退出码 {record.get("exit_code")}：{err_tail or summary or "无输出"}')
        record['reason'] = reason
        kanban('progress', args.task, f'{label} 执行失败，已上报', PLAN_FAIL)
        kanban('block', args.task, reason)
        kanban('flow', args.task, label, '派发', f'🚫 阻塞：{reason[:100]}')

    record['finished_at'] = datetime.now(timezone.utc).isoformat()
    if ok:
        record['result'] = 'done' if mergeable else 'done_no_merge'
        record['mergeable'] = bool(mergeable)
    else:
        record['result'] = 'blocked'
        record['mergeable'] = False
    (run_dir / 'codex-channel.json').write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')

    print(json.dumps({'task': args.task, 'channel': args.channel,
                      'result': record['result'], 'run_dir': str(run_dir)},
                     ensure_ascii=False))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
