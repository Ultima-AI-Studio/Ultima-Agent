"""Codex 通道执行器验收用例。

被测对象：scripts/gorch/codex_channel.py —— 六部的执行体替换件。
判据 V1–V6 见 docs/plans/gorch-codex-channel-20261109.md §5。

本用例只验证「通道执行器在我方数据目录下行为正确」：
真实的 Codex 调用不进用例（一次 2 分钟以上，且依赖登录态），
真跑证据见 docs/plans 里记录的手工实测。这里覆盖看板走位、失败分支、
幂等、越权（V4）与空输入拒绝。
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
    """建单并推到 Doing —— Assigned → Doing 是 edict 的合法接单跳转。"""
    r = kanban(['create', task, '通道执行器验收任务', 'Pending', '皇上', '主脑'], board)
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
    """V2：成功路径把任务从 Doing 推到 Review，且 todos 全部收口。"""
    task = seed(board)
    prompt = write_prompt(tmp_path)
    r = channel(['--task', task, '--dept', 'bingbu', '--prompt', str(prompt),
                 '--run-dir', str(tmp_path / 'run'), '--dry-run'], board)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)['result'] == 'done'

    t = task_of(board, task)
    assert t['state'] == 'Review'
    statuses = [i.get('status') for i in (t.get('todos') or [])]
    assert statuses and all(s == 'completed' for s in statuses)


def test_dry_run_failure_blocks_with_reason(board, tmp_path):
    """V3：失败路径落 Blocked，block 字段写明退出码。"""
    task = seed(board)
    prompt = write_prompt(tmp_path)
    r = channel(['--task', task, '--dept', 'hubu', '--prompt', str(prompt),
                 '--run-dir', str(tmp_path / 'run'), '--dry-run', '--simulate-fail'], board)
    assert r.returncode == 1
    assert json.loads(r.stdout)['result'] == 'blocked'

    t = task_of(board, task)
    assert t['state'] == 'Blocked'
    assert '退出码' in (t.get('block') or '')


def test_executor_never_issues_confirm(board, tmp_path):
    """V4：执行器不调 confirm —— 裁决权在门下省与 Owner，执行端无此权。"""
    src = CHANNEL.read_text(encoding='utf-8')
    assert "'confirm'" not in src
    assert '"confirm"' not in src


def test_already_doing_is_idempotent(board, tmp_path):
    """任务已在 Doing 时重复接单不应中断（状态机拒绝 → 记 already_doing 继续）。"""
    task = seed(board)
    prompt = write_prompt(tmp_path)
    r = channel(['--task', task, '--dept', 'libu', '--prompt', str(prompt),
                 '--run-dir', str(tmp_path / 'run'), '--dry-run'], board)
    assert r.returncode == 0, r.stderr
    record = json.loads((tmp_path / 'run' / 'codex-channel.json').read_text(encoding='utf-8'))
    assert record['already_doing'] is True


def test_empty_prompt_rejected(board, tmp_path):
    """空工单必须在任何看板动作之前拒绝 —— 不能把空单推进 Doing。"""
    task = seed(board)
    empty = write_prompt(tmp_path, '   \n\n')
    r = channel(['--task', task, '--dept', 'gongbu', '--prompt', str(empty),
                 '--run-dir', str(tmp_path / 'run'), '--dry-run'], board)
    assert r.returncode == 2

    t = task_of(board, task)
    assert t['state'] == 'Review' or t['state'] == 'Doing'  # 未被 done/block 收口
    assert t['state'] == 'Doing'


def test_run_record_carries_prompt_hash(board, tmp_path):
    """通道记录必须留下 prompt 摘要与工作目录，供事后核对。"""
    task = seed(board)
    prompt = write_prompt(tmp_path, '# 工单\n\n固定内容\n')
    r = channel(['--task', task, '--dept', 'xingbu', '--prompt', str(prompt),
                 '--run-dir', str(tmp_path / 'run'), '--dry-run'], board)
    assert r.returncode == 0, r.stderr
    record = json.loads((tmp_path / 'run' / 'codex-channel.json').read_text(encoding='utf-8'))
    assert len(record['prompt_sha256']) == 64
    assert record['dept'] == 'xingbu'
    assert (tmp_path / 'run' / 'prompt.txt').is_file()


def test_resolve_codex_exe_prefers_env(tmp_path, monkeypatch):
    """V5 前置：可执行体解析必须能被环境变量显式指定。"""
    spec = importlib.util.spec_from_file_location('gorch_codex_channel', CHANNEL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    fake = tmp_path / 'codex.exe'
    fake.write_bytes(b'')
    monkeypatch.setenv('ULTIMA_CODEX_EXE', str(fake))
    assert mod.resolve_codex_exe() == str(fake)

    monkeypatch.delenv('ULTIMA_CODEX_EXE')
    monkeypatch.setenv('PATH', '')  # 断掉 which 与 glob 的常见命中
    assert mod.resolve_codex_exe() is None or mod.resolve_codex_exe().lower().endswith('.exe')
