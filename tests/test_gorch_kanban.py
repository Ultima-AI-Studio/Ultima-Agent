"""gorch 看板状态机验收用例。

被测对象：scripts/gorch/kanban_update.py —— 从 edict（cft0808/edict）原样搬入，
仅改动数据根目录、刷新钩子和身份推断的环境变量三处。

本用例只验证「搬进来之后在我方数据目录下行为正确」，不重新评审 edict 原始实现。
判据全部取自 edict 自带的 _VALID_TRANSITIONS / HIGH_RISK_TRANSITIONS / AGENT_POLICY。
"""
import json
import os
import pathlib
import subprocess
import sys
import threading

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
KANBAN = ROOT / 'scripts' / 'gorch' / 'kanban_update.py'

# 允许的合法推进链（edict _VALID_TRANSITIONS 明文定义）
LEGAL_CHAIN = ['Taizi', 'Zhongshu', 'Menxia', 'Assigned', 'Doing', 'Review']


def run(cmd, data_dir, agent=None):
    env = dict(os.environ)
    env['GORCH_DATA'] = str(data_dir)
    env['PYTHONIOENCODING'] = 'utf-8'
    env.pop('EDICT_HOME', None)
    if agent:
        env['ULTIMA_AGENT_ID'] = agent
    else:
        env.pop('ULTIMA_AGENT_ID', None)
        env.pop('AGENT_ID', None)
        env.pop('OPENCLAW_AGENT_ID', None)
        env.pop('OPENCLAW_AGENT', None)
    return subprocess.run(
        [sys.executable, str(KANBAN)] + cmd,
        capture_output=True, text=True, encoding='utf-8', errors='replace', env=env,
    )


@pytest.fixture
def data_dir(tmp_path):
    d = tmp_path / 'gorch'
    d.mkdir()
    (d / 'tasks_source.json').write_text('[]', encoding='utf-8')
    return d


def board(data_dir):
    return json.loads((data_dir / 'tasks_source.json').read_text(encoding='utf-8'))


def state_of(data_dir, tid):
    for t in board(data_dir):
        if t.get('id') == tid:
            return t.get('state')
    return None


def seed(data_dir, tid='GORCH-T01'):
    r = run(['create', tid, '状态机验收测试任务', 'Pending', '皇上', '主脑'], data_dir)
    assert r.returncode == 0, r.stderr
    assert state_of(data_dir, tid) == 'Pending'
    return tid


def test_legal_chain_all_allowed(data_dir):
    tid = seed(data_dir)
    for st in LEGAL_CHAIN:
        r = run(['state', tid, st, f'推进到{st}'], data_dir)
        assert r.returncode == 0, r.stderr
        assert state_of(data_dir, tid) == st, f'{st} 未落地'


def test_illegal_jump_rejected_and_state_unchanged(data_dir):
    tid = seed(data_dir)
    assert run(['state', tid, 'Taizi', '接旨'], data_dir).returncode == 0
    r = run(['state', tid, 'Doing', '跳步'], data_dir)
    # 拒绝走 log.warning 分支，不改变状态
    assert '非法状态转换' in (r.stdout + r.stderr)
    assert state_of(data_dir, tid) == 'Taizi'


def test_review_to_done_forced_into_pending_confirm(data_dir):
    tid = seed(data_dir)
    for st in LEGAL_CHAIN:
        assert run(['state', tid, st, st], data_dir).returncode == 0
    r = run(['state', tid, 'Done', '尝试完结'], data_dir)
    assert '高风险' in (r.stdout + r.stderr)
    assert state_of(data_dir, tid) == 'PendingConfirm'
    t = next(x for x in board(data_dir) if x['id'] == tid)
    pc = t.get('pending_confirm') or {}
    assert pc.get('target_state') == 'Done'
    assert pc.get('confirm_by') == 'menxia'


def test_confirm_approve_lands_target(data_dir):
    tid = seed(data_dir)
    for st in LEGAL_CHAIN:
        run(['state', tid, st, st], data_dir)
    run(['state', tid, 'Done', '尝试完结'], data_dir)
    r = run(['confirm', tid, 'approve', '确认通过'], data_dir)
    assert r.returncode == 0, r.stderr
    assert state_of(data_dir, tid) == 'Done'


def test_confirm_reject_backs_to_review(data_dir):
    tid = seed(data_dir)
    for st in LEGAL_CHAIN:
        run(['state', tid, st, st], data_dir)
    run(['state', tid, 'Done', '尝试完结'], data_dir)
    r = run(['confirm', tid, 'reject', '驳回'], data_dir)
    assert r.returncode == 0, r.stderr
    assert state_of(data_dir, tid) == 'Review'


def test_confirm_requires_pending_confirm_state(data_dir):
    tid = seed(data_dir)
    r = run(['confirm', tid, 'approve', '不在待确认态'], data_dir)
    assert '不在 PendingConfirm' in (r.stdout + r.stderr)
    assert state_of(data_dir, tid) == 'Pending'


def test_concurrent_create_no_loss(data_dir):
    n = 8
    procs = [
        subprocess.Popen(
            [sys.executable, str(KANBAN), 'create', f'GORCH-C{i:02d}',
             f'并发写入测试任务{i:02d}', 'Pending', '皇上', '主脑'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            env={**os.environ, 'GORCH_DATA': str(data_dir), 'PYTHONIOENCODING': 'utf-8'},
        )
        for i in range(1, n + 1)
    ]
    for p in procs:
        p.wait()
    ids = {t['id'] for t in board(data_dir)}
    expected = {f'GORCH-C{i:02d}' for i in range(1, n + 1)}
    assert expected <= ids, f'并发写入丢失: {sorted(expected - ids)}'


def test_executor_role_cannot_create(data_dir):
    """执行端（六部角色）按 AGENT_POLICY 无权 create，应 exit 1。"""
    r = run(['create', 'GORCH-X01', '越权创建测试任务', 'Pending', '皇上', '主脑'],
            data_dir, agent='bingbu')
    assert r.returncode != 0
    assert '越权' in (r.stdout + r.stderr)
    assert board(data_dir) == []
