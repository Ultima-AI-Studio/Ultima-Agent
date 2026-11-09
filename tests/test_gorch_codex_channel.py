"""Codex 执行段验收用例。

被测对象：scripts/gorch/codex_channel.py —— 流水线的执行段。
判据见 docs/plans/gorch-codex-channel-20261109.md §5。

真实 Codex 调用不进用例（一次两分钟以上，且依赖登录态），
真跑证据记在报告里。这里覆盖看板走位、失败分支、幂等、越权与空输入拒绝。
"""
import importlib.util
import hashlib
import json
import os
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
KANBAN = ROOT / 'scripts' / 'gorch' / 'kanban_update.py'
CHANNEL = ROOT / 'scripts' / 'gorch' / 'codex_channel.py'

LEGAL_CHAIN_TO_DOING = ['Taizi', 'Zhongshu', 'Menxia', 'Assigned', 'Doing']


def _env(data_dir):
    env = dict(os.environ)
    env['GORCH_DATA'] = str(data_dir)
    env['PYTHONIOENCODING'] = 'utf-8'
    env.pop('ULTIMA_AGENT_ID', None)
    env.pop('AGENT_ID', None)
    env.pop('OPENCLAW_AGENT_ID', None)
    env.pop('OPENCLAW_AGENT', None)
    return env


def kanban(cmd, data_dir):
    return subprocess.run(
        [sys.executable, str(KANBAN)] + cmd, capture_output=True, text=True,
        encoding='utf-8', errors='replace', env=_env(data_dir))


def channel(cmd, data_dir):
    """起子进程跑 codex_channel。

    r7 起执行端没有 manifest 一律拒，所以这里默认签发一份「宽松」清单
    （no_change_allowed / allow_non_repo 都为真），保持旧用例原本的语义；
    要测拒签的用例在自己的 argv 里显式带 --manifest 覆盖。
    """
    args = list(cmd)
    if '--manifest' not in args and '--task' in args:
        task = args[args.index('--task') + 1]
        mf = data_dir / '_inv.json'
        mf.write_text(json.dumps({
            'manifest_version': 1, 'invocation': 'inv-cli',
            'target': 'test-branch', 'created_at': '2026-11-09T00:00:00+00:00',
            'tasks': {task: {'card': task, 'write_scope': [],
                             'write_scope_source': 'test（未声明写域）',
                             'write_scope_enforced': False,
                             'no_change_allowed': True,
                             'allow_non_repo': True,
                             'requests': {}, 'granted_by': 'test'}},
            'blocked': {}}, ensure_ascii=False), encoding='utf-8')
        args += ['--manifest', str(mf)]
    return subprocess.run(
        [sys.executable, str(CHANNEL)] + args, capture_output=True, text=True,
        encoding='utf-8', errors='replace', env=_env(data_dir))


@pytest.fixture
def board(tmp_path):
    d = tmp_path / 'gorch'
    d.mkdir()
    return d


def seed(board, task='GORCH-T1'):
    """建单并推到 Doing —— Assigned → Doing 是看板认可的接单跳转。"""
    r = kanban(['create', task, '执行段验收任务', 'Pending', '皇上', '主脑'], board)
    assert r.returncode == 0, r.stderr
    for st in LEGAL_CHAIN_TO_DOING:
        r = kanban(['state', task, st, '推进'], board)
        assert r.returncode == 0, r.stderr
    return task


def task_of(board, task):
    data = json.loads((board / 'tasks_source.json').read_text(encoding='utf-8'))
    return [t for t in data if t['id'] == task][0]


def write_prompt(tmp_path, text='# 工单\n\n在当前目录创建 hello.txt。\n'):
    p = tmp_path / 'prompt.md'
    p.write_text(text, encoding='utf-8')
    return p


def test_dry_run_success_lands_in_review(board, tmp_path):
    """成功路径把任务从 Doing 推到 Review，且 todos 全部收口。"""
    task = seed(board)
    prompt = write_prompt(tmp_path)
    r = channel(['--task', task, '--channel', '1', '--prompt', str(prompt),
                 '--run-dir', str(tmp_path / 'run'), '--dry-run'], board)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)['result'] == 'done'

    t = task_of(board, task)
    assert t['state'] == 'Review'
    statuses = [i.get('status') for i in (t.get('todos') or [])]
    assert statuses and all(s == 'completed' for s in statuses)


def test_dry_run_failure_blocks_with_reason(board, tmp_path):
    """失败路径落 Blocked，block 字段写明退出码。"""
    task = seed(board)
    prompt = write_prompt(tmp_path)
    r = channel(['--task', task, '--channel', '2', '--prompt', str(prompt),
                 '--run-dir', str(tmp_path / 'run'), '--dry-run', '--simulate-fail'], board)
    assert r.returncode == 1
    assert json.loads(r.stdout)['result'] == 'blocked'

    t = task_of(board, task)
    assert t['state'] == 'Blocked'
    assert '退出码' in (t.get('block') or '')


def test_executor_never_issues_confirm(board, tmp_path):
    """执行段不调 confirm —— 裁决权不在执行段。"""
    src = CHANNEL.read_text(encoding='utf-8')
    assert "'confirm'" not in src
    assert '"confirm"' not in src


def test_already_doing_is_idempotent(board, tmp_path):
    """任务已在 Doing 时重复接单不中断（状态机拒绝 → 记 already_doing 继续）。"""
    task = seed(board)
    prompt = write_prompt(tmp_path)
    r = channel(['--task', task, '--channel', '3', '--prompt', str(prompt),
                 '--run-dir', str(tmp_path / 'run'), '--dry-run'], board)
    assert r.returncode == 0, r.stderr
    record = json.loads((tmp_path / 'run' / 'codex-channel.json').read_text(encoding='utf-8'))
    assert record['already_doing'] is True


def test_empty_prompt_rejected(board, tmp_path):
    """空工单必须在任何看板动作之前拒绝 —— 不能把空单推进去。"""
    task = seed(board)
    empty = write_prompt(tmp_path, '   \n\n')
    r = channel(['--task', task, '--channel', '4', '--prompt', str(empty),
                 '--run-dir', str(tmp_path / 'run'), '--dry-run'], board)
    assert r.returncode == 2

    t = task_of(board, task)
    assert t['state'] == 'Doing'


def test_run_record_carries_prompt_hash_and_channel(board, tmp_path):
    """运行记录必须留下 prompt 摘要与通道号，供事后核对。"""
    task = seed(board)
    prompt = write_prompt(tmp_path, '# 工单\n\n固定内容\n')
    r = channel(['--task', task, '--channel', '5', '--prompt', str(prompt),
                 '--run-dir', str(tmp_path / 'run'), '--dry-run'], board)
    assert r.returncode == 0, r.stderr
    record = json.loads((tmp_path / 'run' / 'codex-channel.json').read_text(encoding='utf-8'))
    assert len(record['prompt_sha256']) == 64
    assert record['channel'] == 5
    assert (tmp_path / 'run' / 'prompt.txt').is_file()


def test_default_channel_is_one(board, tmp_path):
    """不传通道号时默认 1。"""
    task = seed(board)
    prompt = write_prompt(tmp_path)
    r = channel(['--task', task, '--prompt', str(prompt),
                 '--run-dir', str(tmp_path / 'run'), '--dry-run'], board)
    assert r.returncode == 0, r.stderr
    record = json.loads((tmp_path / 'run' / 'codex-channel.json').read_text(encoding='utf-8'))
    assert record['channel'] == 1


def test_resolve_codex_exe_prefers_env(tmp_path, monkeypatch):
    """可执行体解析必须能被环境变量显式指定。"""
    spec = importlib.util.spec_from_file_location('gorch_codex_channel', CHANNEL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    fake = tmp_path / 'codex.exe'
    fake.write_bytes(b'')
    monkeypatch.setenv('ULTIMA_CODEX_EXE', str(fake))
    assert mod.resolve_codex_exe() == str(fake)


# --- 产出校验（退出码 0 不等于干过活，§七-8）---

def _load():
    spec = importlib.util.spec_from_file_location('gorch_codex_channel_wt', CHANNEL)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_worktree_state_clean_then_changed(tmp_path):
    """判据源本身：干净仓库判 clean，写过文件判 changed 并带出文件名。"""
    m = _load()
    repo = tmp_path / 'wt'
    repo.mkdir()

    def git(*a):
        return subprocess.run(
            [m.GIT_EXE, '-C', str(repo)] + list(a),
            capture_output=True, text=True, encoding='utf-8', errors='replace')

    assert git('init').returncode == 0
    # 先落一个已跟踪文件再提交，避免 clean 分支被"全未跟踪"的初始态混淆
    (repo / 'base.txt').write_text('base\n', encoding='utf-8')
    assert git('add', 'base.txt').returncode == 0
    assert git('-c', 'user.name=t', '-c', 'user.email=t@t',
               'commit', '-m', 'base').returncode == 0

    assert m.worktree_state(repo) == ('clean', '')

    (repo / 'new.txt').write_text('x\n', encoding='utf-8')
    kind, detail = m.worktree_state(repo)
    assert kind == 'changed'
    assert 'new.txt' in detail


def test_worktree_state_not_a_repo(tmp_path):
    """非 git 目录如实返回 not_repo —— 不能当成 clean 去误判空产出。"""
    m = _load()
    plain = tmp_path / 'plain'
    plain.mkdir()
    assert m.worktree_state(plain)[0] == 'not_repo'


# --- 产出校验的挂载点（主流程级，不是只测 helper）---

class _Proc:
    returncode = 0
    stdout = b''
    stderr = b''


class _Res:
    returncode = 0
    stdout = ''
    stderr = ''


def _run_main(m, monkeypatch, tmp_path, wt_kind, wt_detail='', extra=None,
              baseline=None, grants=None):
    """走完整执行段，只替换外部 Codex、产出判定与看板 CLI。

    ``baseline`` 是执行前快照（None 表示与执行后同值）。A4 之后 worktree_state
    会被调两次（执行前基线 + 执行后），所以这里用队列模拟先后两次读数。
    """
    fake = tmp_path / 'codex.exe'
    fake.write_bytes(b'')
    monkeypatch.setattr(m, 'resolve_codex_exe', lambda: str(fake))
    monkeypatch.setattr(m, 'run_codex', lambda *a, **k: (_Proc(), 1.0))
    queue = list(baseline or [])

    def fake_state(wd):
        return queue.pop(0) if queue else (wt_kind, wt_detail)

    monkeypatch.setattr(m, 'worktree_state', fake_state)

    # 指纹也用桩：tmp_path 不是 git 仓库，真去跑 git diff 会返回 ERR:*，
    # 而 ERR 现在按"读取失败即阻断"处理（不在这个桩里就每条用例都 blocked）。
    def fake_fp(wd, detail=None):
        d = str(detail or '')
        rows = [x for x in d.splitlines() if x.strip()]
        paths = {}
        for ln in rows:
            body = ln[3:] if len(ln) > 3 else ln
            paths[body.strip()] = hashlib.sha256(ln.encode('utf-8')).hexdigest()[:16]
        return {'paths': paths, 'ignored': set(), 'rows': [],
                'diff_sha': hashlib.sha256(d.encode('utf-8')).hexdigest()[:16]}

    monkeypatch.setattr(m, 'worktree_fingerprint', fake_fp)
    monkeypatch.setattr(m, 'kanban', lambda *a, **k: _Res())

    extra = list(extra or [])
    if '--manifest' not in extra:
        g = dict(grants or {})
        g.setdefault('no_change_allowed', '--no-change-allowed' in extra)
        g.setdefault('allow_non_repo', '--allow-non-repo' in extra)
        scope = list(g.get('write_scope') or [])
        inv = tmp_path / 'inv-auto.json'
        inv.write_text(json.dumps({
            'manifest_version': 1, 'invocation': 'inv-auto',
            'target': 'test-branch', 'created_at': '2026-11-09T00:00:00+00:00',
            'tasks': {'T1': {'card': 'T1', 'write_scope': scope,
                             'write_scope_source': 'test',
                             'write_scope_enforced': bool(scope),
                             'no_change_allowed': bool(g.get('no_change_allowed')),
                             'allow_non_repo': bool(g.get('allow_non_repo')),
                             'requests': {}, 'granted_by': 'test'}},
            'blocked': {}}, ensure_ascii=False), encoding='utf-8')
        extra += ['--manifest', str(inv)]

    prompt = tmp_path / 'p.md'
    prompt.write_text('# 工单\n', encoding='utf-8')
    run_dir = tmp_path / 'run'
    argv = ['--task', 'T1', '--prompt', str(prompt), '--run-dir', str(run_dir),
            '--workdir', str(tmp_path)] + extra
    rc = m.main(argv)
    record = json.loads((run_dir / 'codex-channel.json').read_text(encoding='utf-8'))
    return rc, record


def test_clean_worktree_blocks_even_with_exit_zero(tmp_path, monkeypatch):
    """退出码 0 但 worktree 没动过——必须 blocked，不能写 done。"""
    m = _load()
    rc, record = _run_main(m, monkeypatch, tmp_path, 'clean')
    assert rc == 1
    assert record['result'] == 'blocked'
    assert record['worktree_state'] == 'clean'
    assert '无任何改动' in (record.get('reason') or '')


def test_changed_worktree_lands_done(tmp_path, monkeypatch):
    """有真实改动时正常 done，并把改动摘要落进 record。

    基线是干净的、执行后才出现 `?? docs/x.md`——这才是"本次产出"。
    """
    m = _load()
    rc, record = _run_main(m, monkeypatch, tmp_path, 'changed', '?? docs/x.md',
                           baseline=[('clean', '')])
    assert rc == 0
    assert record['result'] == 'done'
    assert record['worktree_state'] == 'changed'
    assert 'docs/x.md' in record['worktree_changes']
    assert 'docs/x.md' in record['worktree_new_changes']


def test_not_repo_blocks_by_default(tmp_path, monkeypatch):
    """不是 git 工作树时默认 fail-closed —— 否则批量路径能绕过产出闸。"""
    m = _load()
    rc, record = _run_main(m, monkeypatch, tmp_path, 'not_repo')
    assert rc == 1
    assert record['result'] == 'blocked'
    assert '不是 git 工作树' in (record.get('reason') or '')


def test_not_repo_allowed_only_with_explicit_flag(tmp_path, monkeypatch):
    """手工场景显式声明后放行，并留下放行标记供审计。"""
    m = _load()
    rc, record = _run_main(m, monkeypatch, tmp_path, 'not_repo',
                           extra=['--allow-non-repo'])
    assert rc == 0
    assert record['result'] == 'done'
    assert 'allow-non-repo' in record.get('worktree_state_note', '')


# --- A2/A4：零改动协议与执行前基线 ---

def test_clean_worktree_allowed_when_flag_declared(tmp_path, monkeypatch):
    """A2：纯验证卡 / 只回 last-message.md 的卡按约定不改仓库，显式开关后放行。

    默认仍严格（见 test_clean_worktree_blocks_even_with_exit_zero）——只开一道
    有名字的门，不是把 clean 一律当成功。
    """
    m = _load()
    rc, record = _run_main(m, monkeypatch, tmp_path, 'clean',
                           extra=['--no-change-allowed'])
    assert rc == 0
    # 第四轮口径：零改动卡可以判「执行完成」，但不是可合并成果（done_no_merge）。
    assert record['result'] == 'done_no_merge'
    assert record['mergeable'] is False
    assert '--no-change-allowed' in record['worktree_state_note']


def test_dirty_baseline_without_new_changes_blocks(tmp_path, monkeypatch):
    """A4：复用脏 worktree 时，旧改动不能算本次成果。

    执行前后都是同一堆脏文件（行集合相同）→ 本次没新增任何东西 → blocked。
    """
    m = _load()
    dirty = ' M docs/old.md\n?? docs/junk.md'
    rc, record = _run_main(m, monkeypatch, tmp_path, 'changed', dirty,
                           baseline=[('changed', dirty)])
    assert rc == 1
    assert record['result'] == 'blocked'
    assert '无新增' in (record.get('reason') or '')
    assert record['worktree_baseline'] == 'changed'
    assert record['worktree_new_changes'] == ''


def test_dirty_baseline_with_new_change_lands_done(tmp_path, monkeypatch):
    """A4 的正面：脏基线之上确实多了一个文件，那才叫本次产出。"""
    m = _load()
    before = ' M docs/old.md'
    after = ' M docs/old.md\n?? docs/new.md'
    rc, record = _run_main(m, monkeypatch, tmp_path, 'changed', after,
                           baseline=[('changed', before)])
    assert rc == 0
    assert record['result'] == 'done'
    assert 'docs/new.md' in record['worktree_new_changes']
    assert 'docs/old.md' not in record['worktree_new_changes']

# --- 第四轮：基线 fail-open 闭环与内容级判据 ---

def test_baseline_error_blocks_before_running_codex(tmp_path, monkeypatch):
    """A4：执行前读不到 worktree 状态就不许开工（此前 before 取空集 → fail-open）。"""
    m = _load()
    called = []
    fake = tmp_path / 'codex.exe'
    fake.write_bytes(b'')
    monkeypatch.setattr(m, 'resolve_codex_exe', lambda: str(fake))
    monkeypatch.setattr(m, 'run_codex', lambda *a, **k: called.append(1))
    monkeypatch.setattr(m, 'worktree_state', lambda wd: ('error', 'git status 失败'))
    monkeypatch.setattr(m, 'kanban', lambda *a, **k: _Res())
    prompt = tmp_path / 'p.md'
    prompt.write_text('# 工单\n', encoding='utf-8')
    run_dir = tmp_path / 'run'
    rc = m.main(['--task', 'T1', '--prompt', str(prompt),
                 '--run-dir', str(run_dir), '--workdir', str(tmp_path), '--manifest', str(_manifest(tmp_path, []))])
    record = json.loads((run_dir / 'codex-channel.json').read_text(encoding='utf-8'))
    assert rc == 1
    assert record['result'] == 'blocked'
    assert 'fail-closed' in record['reason']
    assert called == []


def test_non_repo_baseline_blocks_without_flag(tmp_path, monkeypatch):
    """A4：非 git 目录默认阻断，只有显式 --allow-non-repo 才放行。"""
    m = _load()
    called = []
    fake = tmp_path / 'codex.exe'
    fake.write_bytes(b'')
    monkeypatch.setattr(m, 'resolve_codex_exe', lambda: str(fake))
    monkeypatch.setattr(m, 'run_codex', lambda *a, **k: called.append(1))
    monkeypatch.setattr(m, 'worktree_state', lambda wd: ('not_repo', '不是 git 目录'))
    monkeypatch.setattr(m, 'kanban', lambda *a, **k: _Res())
    prompt = tmp_path / 'p.md'
    prompt.write_text('# 工单\n', encoding='utf-8')
    run_dir = tmp_path / 'run'
    rc = m.main(['--task', 'T1', '--prompt', str(prompt),
                 '--run-dir', str(run_dir), '--workdir', str(tmp_path), '--manifest', str(_manifest(tmp_path, []))])
    record = json.loads((run_dir / 'codex-channel.json').read_text(encoding='utf-8'))
    assert rc == 1
    assert record['result'] == 'blocked'
    assert called == []


def test_empty_prompt_still_writes_blocked_record(tmp_path):
    """A1a：空工单也落 blocked 记录（否则旧 done 仍是目录里唯一真实记录）。"""
    m = _load()
    prompt = tmp_path / 'empty.md'
    prompt.write_text('   \n', encoding='utf-8')
    run_dir = tmp_path / 'run'
    rc = m.main(['--task', 'T1', '--prompt', str(prompt),
                 '--run-dir', str(run_dir), '--workdir', str(tmp_path), '--manifest', str(_manifest(tmp_path, []))])
    record = json.loads((run_dir / 'codex-channel.json').read_text(encoding='utf-8'))
    assert rc == 2
    assert record['result'] == 'blocked'
    assert record['mergeable'] is False


def test_fresh_changes_detects_content_change_with_same_lines():
    """A4：前后都是同一行「M a.txt」，但内容变了 → 必须判本次有新增（此前误杀）。"""
    m = _load()
    base = {'paths': {'a.txt': 'aa'}, 'ignored': set(), 'diff_sha': 'aa'}
    after = {'paths': {'a.txt': 'bb'}, 'ignored': set(), 'diff_sha': 'bb'}
    fresh, basis = m.fresh_changes(base, after)
    assert fresh == {'a.txt'}
    assert '内容' in basis


def test_fresh_changes_sees_untracked_dir_files():
    """A4：未跟踪目录下的新增文件也要看得见（行集合只有 ?? out/，看不见内部）。"""
    m = _load()
    base = {'paths': {'out/': 'x'}, 'ignored': set(), 'diff_sha': 'aa'}
    after = {'paths': {'out/': 'x', 'out/new.txt': 'y'}, 'ignored': set(),
             'diff_sha': 'aa'}
    fresh, _ = m.fresh_changes(base, after)
    assert fresh == {'out/new.txt'}

def test_fingerprint_read_failure_blocks(tmp_path, monkeypatch):
    """A4：执行后 diff 指纹读不出来（ERR:*）时不能退化判定，必须 blocked。"""
    m = _load()
    fake = tmp_path / 'codex.exe'
    fake.write_bytes(b'')
    monkeypatch.setattr(m, 'resolve_codex_exe', lambda: str(fake))
    monkeypatch.setattr(m, 'run_codex', lambda *a, **k: (_Proc(), 1.0))
    monkeypatch.setattr(m, 'worktree_state',
                        lambda wd: ('changed', ' M docs/x.md'))
    monkeypatch.setattr(m, 'worktree_fingerprint',
                        lambda wd, detail=None: {'paths': {'docs/x.md': 'd'},
                                                 'ignored': set(), 'rows': [],
                                                 'diff_sha': 'ERR:128'})
    monkeypatch.setattr(m, 'kanban', lambda *a, **k: _Res())
    prompt = tmp_path / 'p.md'
    prompt.write_text('# 工单\n', encoding='utf-8')
    run_dir = tmp_path / 'run'
    inv = _manifest(tmp_path, [])
    rc = m.main(['--task', 'T1', '--prompt', str(prompt), '--run-dir', str(run_dir),
                 '--workdir', str(tmp_path), '--manifest', str(inv)])
    record = json.loads((run_dir / 'codex-channel.json').read_text(encoding='utf-8'))
    assert rc == 1
    assert record['result'] == 'blocked'
    assert '指纹' in (record.get('reason') or '')



# ============ r6：脏基线阻断 + 授权写域（第五轮 7.3 最小清单） ============

def test_baseline_fingerprint_error_blocks_before_codex(tmp_path, monkeypatch):
    """Q3-6：执行前内容指纹读不出来（diff_sha=ERR:*）时，调 Codex 前就 blocked。"""
    m = _load()
    fake = tmp_path / 'codex.exe'
    fake.write_bytes(b'')
    monkeypatch.setattr(m, 'resolve_codex_exe', lambda: str(fake))
    called = {'n': 0}

    def fake_run(*a, **k):
        called['n'] += 1
        return _Proc(), 1.0

    monkeypatch.setattr(m, 'run_codex', fake_run)
    monkeypatch.setattr(m, 'worktree_state', lambda wd: ('changed', ' M docs/x.md'))
    monkeypatch.setattr(m, 'worktree_fingerprint', lambda wd, detail=None: {
        'paths': {'docs/x.md': 'd'}, 'ignored': set(), 'rows': [],
        'diff_sha': 'ERR:git diff failed'})
    monkeypatch.setattr(m, 'kanban', lambda *a, **k: _Res())
    prompt = tmp_path / 'p.md'
    prompt.write_text('# work order\n', encoding='utf-8')
    run_dir = tmp_path / 'run'
    inv = _manifest(tmp_path, [])
    rc = m.main(['--task', 'T1', '--prompt', str(prompt),
                 '--run-dir', str(run_dir), '--workdir', str(tmp_path),
                 '--manifest', str(inv)])
    record = json.loads((run_dir / 'codex-channel.json').read_text(encoding='utf-8'))
    assert rc == 1
    assert called['n'] == 0
    assert record['result'] == 'blocked'
    assert '基线' in (record.get('reason') or '')


def _manifest(tmp_path, write_scope):
    p = tmp_path / 'inv.json'
    p.write_text(json.dumps({
        'manifest_version': 1, 'invocation': 'inv1',
        'tasks': {'T1': {'write_scope': write_scope,
                         'write_scope_enforced': bool(write_scope),
                         'no_change_allowed': False,
                         'allow_non_repo': False,
                         'granted_by': 'orchestrator'}}}), encoding='utf-8')
    return p


def test_write_scope_violation_blocks(tmp_path, monkeypatch):
    """7.3-4：产出路径越出授权写域即 blocked，不写 done。"""
    m = _load()
    rc, record = _run_main(m, monkeypatch, tmp_path, 'changed',
                           '?? scripts/hack.py', baseline=[('clean', '')],
                           extra=['--manifest',
                                  str(_manifest(tmp_path, ['docs/reports/']))])
    assert rc == 1
    assert record['result'] == 'blocked'
    assert '超出授权写域' in (record.get('reason') or '')
    assert record['write_scope_check']['outside'] == ['scripts/hack.py']


def test_write_scope_inside_allows_done(tmp_path, monkeypatch):
    """正面：产出全部落在授权写域内时正常 done。"""
    m = _load()
    rc, record = _run_main(m, monkeypatch, tmp_path, 'changed',
                           '?? docs/reports/x.md', baseline=[('clean', '')],
                           extra=['--manifest',
                                  str(_manifest(tmp_path, ['docs/reports/']))])
    assert rc == 0
    assert record['result'] == 'done'
    assert record['write_scope_check']['outside'] == []


def test_manifest_missing_task_blocks(tmp_path, monkeypatch):
    """授权清单里没有本任务条目——fail-closed，不起 Codex。"""
    m = _load()
    p = tmp_path / 'inv-empty.json'
    p.write_text(json.dumps({'manifest_version': 1, 'tasks': {}}), encoding='utf-8')
    rc, record = _run_main(m, monkeypatch, tmp_path, 'clean', '',
                          extra=['--manifest', str(p)])
    assert rc == 2
    assert record['result'] == 'blocked'
    assert '未包含任务' in (record.get('reason') or '')

# ============ r7：第六轮审计 4 条 ❌ + 新问题闭环 ============

def test_no_manifest_rejects_cli_self_authorization(tmp_path, monkeypatch):
    """r7 口径①：没有 manifest 一律拒，命令行开关不构成授权。"""
    m = _load()
    monkeypatch.setattr(m, 'kanban', lambda *a, **k: _Res())
    fake = tmp_path / 'codex.exe'
    fake.write_bytes(b'')
    monkeypatch.setattr(m, 'resolve_codex_exe', lambda: str(fake))
    called = {'n': 0}

    def fake_run(*a, **k):
        called['n'] += 1
        return _Proc(), 1.0

    monkeypatch.setattr(m, 'run_codex', fake_run)
    prompt = tmp_path / 'p.md'
    prompt.write_text('# work order\n', encoding='utf-8')
    run_dir = tmp_path / 'run'
    rc = m.main(['--task', 'T1', '--prompt', str(prompt), '--run-dir', str(run_dir),
                 '--workdir', str(tmp_path), '--no-change-allowed'])
    record = json.loads((run_dir / 'codex-channel.json').read_text(encoding='utf-8'))
    assert rc == 2
    assert record['result'] == 'blocked'
    assert 'manifest' in (record.get('reason') or '')
    assert called['n'] == 0


def test_cli_flag_without_grant_still_blocks(tmp_path, monkeypatch):
    """r7 口径①：清单明说 no_change_allowed=false 时，传开关也不放行。"""
    m = _load()
    rc, record = _run_main(m, monkeypatch, tmp_path, 'clean',
                           extra=['--no-change-allowed'],
                           grants={'no_change_allowed': False})
    assert rc == 1
    assert record['result'] == 'blocked'
    assert '无任何改动' in (record.get('reason') or '')
    assert record['ignored_cli_flags']['no_change_allowed'] is True


def test_ignored_path_outside_scope_blocks(tmp_path, monkeypatch):
    """r7 新问题 #2：被 .gitignore 命中的域外产物也必须被写域校验看见。"""
    m = _load()
    fake = tmp_path / 'codex.exe'
    fake.write_bytes(b'')
    monkeypatch.setattr(m, 'resolve_codex_exe', lambda: str(fake))
    monkeypatch.setattr(m, 'run_codex', lambda *a, **k: (_Proc(), 1.0))
    states = [('clean', ''), ('changed', '!! data/gorch/x.log')]
    monkeypatch.setattr(m, 'worktree_state',
                        lambda wd: states.pop(0) if states else ('changed', '!! data/gorch/x.log'))

    def fake_fp(wd, detail=None):
        return {'paths': {'data/gorch/x.log': 'd1'},
                'ignored': {'data/gorch/x.log'}, 'rows': [],
                'diff_sha': 'ok'}

    monkeypatch.setattr(m, 'worktree_fingerprint', fake_fp)
    monkeypatch.setattr(m, 'kanban', lambda *a, **k: _Res())
    prompt = tmp_path / 'p.md'
    prompt.write_text('# work order\n', encoding='utf-8')
    run_dir = tmp_path / 'run'
    inv = _manifest(tmp_path, ['docs/reports/'])
    rc = m.main(['--task', 'T1', '--prompt', str(prompt), '--run-dir', str(run_dir),
                 '--workdir', str(tmp_path), '--manifest', str(inv)])
    record = json.loads((run_dir / 'codex-channel.json').read_text(encoding='utf-8'))
    assert rc == 1
    assert '超出授权写域' in (record.get('reason') or '')
    assert record['write_scope_check']['outside'] == ['data/gorch/x.log']


def test_scope_star_does_not_cross_separator():
    """r7 新问题：fnmatch 的 `*` 会跨 `/`，等于写域比声明的宽一层。"""
    m = _load()
    assert m._scope_match('scripts/gorch/a.py', 'scripts/gorch/*.py')
    assert not m._scope_match('scripts/gorch/sub/a.py', 'scripts/gorch/*.py')
    assert m._scope_match('scripts/gorch/sub/a.py', 'scripts/gorch/**/*.py')
    assert m._outside_scope(['scripts/gorch/sub/a.py'],
                            ['scripts/gorch/*.py']) == ['scripts/gorch/sub/a.py']


def test_rename_checks_both_ends():
    """r7 新问题 #3：域外文件移进域内时，域外的删除也要参与写域校验。"""
    m = _load()
    paths = m._fresh_paths({'scripts/secret.py -> docs/reports/x.md'})
    assert set(paths) == {'scripts/secret.py', 'docs/reports/x.md'}
    assert m._outside_scope(paths, ['docs/reports/']) == ['scripts/secret.py']


def test_state_prefix_keeps_leading_space_path():
    """r7 新问题 #7：` M docs/x.md` 的首空格不得吃掉，路径不能被读成 `M docs/x.md`。"""
    m = _load()
    assert m._fresh_paths({' M docs/reports/x.md'}) == ['docs/reports/x.md']
    assert m._fresh_paths({'?? docs/reports/x.md'}) == ['docs/reports/x.md']


def test_same_path_content_change_is_fresh():
    """r7 新问题 #1：脏基线下同路径内容摘要变了，必须判本次有新增。"""
    m = _load()
    base = {'paths': {'docs/x.md': 'd1'}, 'ignored': set(), 'diff_sha': 'h1'}
    after = {'paths': {'docs/x.md': 'd2'}, 'ignored': set(), 'diff_sha': 'h2'}
    fresh, _ = m.fresh_changes(base, after)
    assert fresh == {'docs/x.md'}


def test_staging_only_is_not_fresh():
    """r7：只 git add（文件字节没变）不算本次新增。"""
    m = _load()
    base = {'paths': {'docs/x.md': 'd1'}, 'ignored': set(), 'diff_sha': 'h1'}
    after = {'paths': {'docs/x.md': 'd1'}, 'ignored': set(), 'diff_sha': 'h2'}
    fresh, _ = m.fresh_changes(base, after)
    assert fresh == set()

def test_hidden_dir_path_is_not_truncated():
    """r7 自查：`lstrip('./')` 会把 `.github/...` 剥成 `github/...`，写域比对会错位。"""
    m = _load()
    assert m._fresh_paths({'?? .github/workflows/x.yml'}) == ['.github/workflows/x.yml']
    assert m._fresh_paths({'./docs/a.md'}) == ['docs/a.md']
    assert m._fresh_paths({'docs\\win.md'}) == ['docs/win.md']
