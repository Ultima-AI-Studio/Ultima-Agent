"""薄编排（开工前判定）验收用例。

被测对象：scripts/gorch/batch_orchestrator.py 的 gate_check。
判定逻辑本身在 ccpm lib.sh 的原函数内（unmet_deps/active_conflicts/frontmatter_field），
本测试只验证薄编排层把这些现成件的输出正确映射成结构化 verdict，
并保证“可开工”严格对齐 ccpm next.sh 的三条件。

真实调用 git bash + 已复制的 ccpm 脚本（系统固定件），不 mock 判断函数，
否则就失去“照搬逻辑真的可跑”的验证意义。
"""
import importlib.util
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
ORCH = ROOT / 'scripts' / 'gorch' / 'batch_orchestrator.py'


@pytest.fixture
def mod():
    spec = importlib.util.spec_from_file_location('batch_orchestrator', ORCH)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def write_task(d, n, status='open', deps=None, conflicts=None):
    deps = '[]' if deps is None else '[' + ', '.join(deps) + ']'
    conf = '[]' if conflicts is None else '[' + ', '.join(conflicts) + ']'
    (d / f'{n}.md').write_text(
        '---\n'
        f'name: t{n}\n'
        f'status: {status}\n'
        f'depends_on: {deps}\n'
        'parallel: true\n'
        f'conflicts_with: {conf}\n'
        '---\n'
        f'# task {n}\n',
        encoding='utf-8')


def by_id(rows):
    return {r['task']: r for r in rows}


def test_ready_when_open_no_deps_no_conflicts(mod, tmp_path):
    write_task(tmp_path, 1)
    rows = mod.gate_check(str(tmp_path))
    assert by_id(rows)['1']['verdict'] == '可开工'


def test_wait_dependency_when_dep_not_done(mod, tmp_path):
    write_task(tmp_path, 1, status='open')
    write_task(tmp_path, 2, deps=['1'])
    rows = by_id(mod.gate_check(str(tmp_path)))
    assert rows['2']['verdict'] == '等待依赖'
    assert rows['2']['unmet_deps'] == ['1']


def test_dependency_satisfied_when_closed(mod, tmp_path):
    """依赖任务 closed 后，下游应可开工（ccpm is_done_status）。"""
    write_task(tmp_path, 1, status='closed')
    write_task(tmp_path, 2, deps=['1'])
    rows = by_id(mod.gate_check(str(tmp_path)))
    assert rows['1']['verdict'] == '非开放状态'
    assert rows['2']['verdict'] == '可开工'


def test_conflict_blocked_when_other_in_progress(mod, tmp_path):
    write_task(tmp_path, 1, status='in-progress')
    write_task(tmp_path, 3, conflicts=['1'])
    rows = by_id(mod.gate_check(str(tmp_path)))
    assert rows['3']['verdict'] == '等待冲突解除'
    assert rows['3']['active_conflicts'] == ['1']


def test_conflict_not_triggered_when_other_merely_open(mod, tmp_path):
    """冲突对象只是 open（未在执行）时不算活跃冲突，仍可开工。"""
    write_task(tmp_path, 1, status='open')
    write_task(tmp_path, 3, conflicts=['1'])
    rows = by_id(mod.gate_check(str(tmp_path)))
    assert rows['3']['verdict'] == '可开工'
    assert rows['3']['active_conflicts'] == []


def test_non_open_status_never_dispatched(mod, tmp_path):
    write_task(tmp_path, 1, status='in-progress')
    rows = by_id(mod.gate_check(str(tmp_path)))
    assert rows['1']['verdict'] == '非开放状态'


def test_missing_dependency_file_counts_as_unmet(mod, tmp_path):
    write_task(tmp_path, 4, deps=['99'])
    rows = by_id(mod.gate_check(str(tmp_path)))
    assert rows['4']['verdict'] == '等待依赖'
    assert rows['4']['unmet_deps'] == ['99']


def test_full_batch_ready_blocked_summary(mod, tmp_path):
    """复刻受控实测：1 进行中时，整批无一个可开工。"""
    write_task(tmp_path, 1, status='in-progress')
    write_task(tmp_path, 2, deps=['1'])
    write_task(tmp_path, 3, conflicts=['1'])
    write_task(tmp_path, 4, deps=['99'])
    rows = mod.gate_check(str(tmp_path))
    ready = [r['task'] for r in rows if r['verdict'] == '可开工']
    blocked = [r['task'] for r in rows if r['verdict'] != '可开工']
    assert ready == []
    assert sorted(blocked) == ['1', '2', '3', '4']


def test_missing_dir_raises(mod, tmp_path):
    with pytest.raises(SystemExit):
        mod.gate_check(str(tmp_path / 'nope'))


def test_empty_dir_raises(mod, tmp_path):
    with pytest.raises(SystemExit):
        mod.gate_check(str(tmp_path))


def test_unknown_status_fails_closed(mod, tmp_path):
    """非法状态值必须 fail-closed 报错，不能当成可开工放行。"""
    write_task(tmp_path, 1, status='weird')
    with pytest.raises(SystemExit):
        mod.gate_check(str(tmp_path))


def test_missing_frontmatter_fails_closed(mod, tmp_path):
    """读不到 status（无 frontmatter）必须 fail-closed，不能默认当 open。"""
    (tmp_path / '1.md').write_text('# no frontmatter\n', encoding='utf-8')
    with pytest.raises(SystemExit):
        mod.gate_check(str(tmp_path))


# --- provision 子命令（判断仍真实走 gate/ccpm；只 mock 外部 wt 命令）---

class _FakeResult:
    def __init__(self, returncode, stdout=''):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = ''


def test_parse_first_json_extracts_object(mod):
    d = mod._parse_first_json('noise line\n{"action":"created","x":1}\nmore')
    assert d == {'action': 'created', 'x': 1}


def test_parse_first_json_none_when_absent(mod):
    assert mod._parse_first_json('no json at all') is None


def test_provision_creates_only_ready_tasks(mod, monkeypatch, tmp_path):
    write_task(tmp_path, 1)                       # 可开工
    write_task(tmp_path, 2, deps=['1'])           # 等待依赖
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', tmp_path / 'wt')
    real_wt = tmp_path / 'real-wt'
    real_wt.mkdir()
    calls = []

    def fake_switch(branch, wt_path, create):
        calls.append((branch, create))
        return _FakeResult(0, json.dumps({'action': 'created', 'path': str(real_wt)}))

    monkeypatch.setattr(mod, 'wt_switch', fake_switch)
    rows, provisioned, skipped = mod.provision(str(tmp_path))
    assert [p['task'] for p in provisioned] == ['1']
    assert skipped == ['2']
    assert len(calls) == 1                         # 只对可开工任务调 wt
    assert provisioned[0]['worktree'] == str(real_wt)


def test_provision_fails_closed_when_wt_errors(mod, monkeypatch, tmp_path):
    write_task(tmp_path, 1)
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', tmp_path / 'wt')
    monkeypatch.setattr(mod, 'wt_switch',
                        lambda *a, **k: _FakeResult(1, 'boom'))
    with pytest.raises(SystemExit):
        mod.provision(str(tmp_path))


def test_provision_fails_closed_when_reported_path_missing(mod, monkeypatch, tmp_path):
    """wt 报成功但 worktree 路径不存在，必须 fail-closed，不假装就绪。"""
    write_task(tmp_path, 1)
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', tmp_path / 'wt')
    ghost = tmp_path / 'does-not-exist'
    monkeypatch.setattr(
        mod, 'wt_switch',
        lambda *a, **k: _FakeResult(0, json.dumps({'action': 'created', 'path': str(ghost)})))
    with pytest.raises(SystemExit):
        mod.provision(str(tmp_path))


# --- execute 子命令（判断仍真实走 gate/ccpm；只 mock 外部进程 Popen）---

class _FakeProc:
    def __init__(self, returncode=0, out=''):
        self.returncode = returncode
        self._out = out

    def communicate(self):
        return self._out, ''


def _setup_ready(mod, monkeypatch, tmp_path, nums):
    """建可开工任务 + 对应 worktree 目录 + prompt 文件，返回 prompts 目录。"""
    for n in nums:
        write_task(tmp_path, n)
    wt_root = tmp_path / 'wt'
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', wt_root)
    prompts = tmp_path / 'prompts'
    prompts.mkdir()
    for n in nums:
        (wt_root / str(n)).mkdir(parents=True)
        (prompts / f'{n}.txt').write_text('p', encoding='utf-8')
    return prompts


def test_find_prompt_prefers_md(mod, tmp_path):
    (tmp_path / '1.md').write_text('a', encoding='utf-8')
    (tmp_path / '1.txt').write_text('b', encoding='utf-8')
    assert mod._find_prompt(tmp_path, '1').name == '1.md'


def test_find_prompt_falls_back_to_txt(mod, tmp_path):
    (tmp_path / '1.txt').write_text('b', encoding='utf-8')
    assert mod._find_prompt(tmp_path, '1').name == '1.txt'


def test_find_prompt_none(mod, tmp_path):
    assert mod._find_prompt(tmp_path, '1') is None


def test_execute_fans_out_one_process_per_task(mod, monkeypatch, tmp_path):
    prompts = _setup_ready(mod, monkeypatch, tmp_path, (1, 2, 3))
    real_popen = mod.subprocess.Popen               # 先留真实 Popen 给 gate 的 bash 用
    popen_cmds = []

    def fake_popen(cmd, **kw):
        if cmd and cmd[0] == mod.BASH:             # gate_check 内部 run→Popen，走真实
            return real_popen(cmd, **kw)
        popen_cmds.append(cmd)
        return _FakeProc(0, json.dumps({'result': 'done'}))

    monkeypatch.setattr(mod.subprocess, 'Popen', fake_popen)
    rows, results = mod.execute(str(tmp_path), str(prompts), max_channels=3)
    assert len(popen_cmds) == 3                       # 每个任务一个进程
    assert [r['task'] for r in results] == ['1', '2', '3']
    assert [r['channel'] for r in results] == [1, 2, 3]
    # 每个进程的 --workdir 指向各自 worktree
    for cmd in popen_cmds:
        wd = cmd[cmd.index('--workdir') + 1]
        assert wd.startswith(str(tmp_path / 'wt'))


def test_execute_batches_and_reuses_channel_numbers(mod, monkeypatch, tmp_path):
    prompts = _setup_ready(mod, monkeypatch, tmp_path, (1, 2, 3, 4))
    real_popen = mod.subprocess.Popen
    channels_seen = []

    def fake_popen(cmd, **kw):
        if cmd and cmd[0] == mod.BASH:             # gate 的 bash 调用走真实
            return real_popen(cmd, **kw)
        channels_seen.append(int(cmd[cmd.index('--channel') + 1]))
        return _FakeProc(0, '{}')

    monkeypatch.setattr(mod.subprocess, 'Popen', fake_popen)
    rows, results = mod.execute(str(tmp_path), str(prompts), max_channels=2)
    assert len(results) == 4
    # 每批 2 个，通道号在批内复用：[1,2] 然后 [1,2]
    assert channels_seen == [1, 2, 1, 2]


def test_execute_fails_closed_when_worktree_missing(mod, monkeypatch, tmp_path):
    write_task(tmp_path, 1)
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', tmp_path / 'wt')
    prompts = tmp_path / 'prompts'
    prompts.mkdir()
    (prompts / '1.txt').write_text('p', encoding='utf-8')
    with pytest.raises(SystemExit):
        mod.execute(str(tmp_path), str(prompts))


def test_execute_fails_closed_when_prompt_missing(mod, monkeypatch, tmp_path):
    write_task(tmp_path, 1)
    wt_root = tmp_path / 'wt'
    (wt_root / '1').mkdir(parents=True)
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', wt_root)
    prompts = tmp_path / 'prompts'
    prompts.mkdir()
    with pytest.raises(SystemExit):
        mod.execute(str(tmp_path), str(prompts))
