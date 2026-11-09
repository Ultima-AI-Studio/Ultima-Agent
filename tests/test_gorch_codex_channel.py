"""Codex 执行段验收用例。

被测对象：scripts/gorch/codex_channel.py —— 流水线的执行段。
判据见 docs/plans/gorch-codex-channel-20261109.md §5。

真实 Codex 调用不进用例（一次两分钟以上，且依赖登录态），
真跑证据记在报告里。这里覆盖看板走位、失败分支、幂等、越权与空输入拒绝。
"""
import importlib.util
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
    return subprocess.run(
        [sys.executable, str(CHANNEL)] + cmd, capture_output=True, text=True,
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
