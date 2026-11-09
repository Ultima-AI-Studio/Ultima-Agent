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


# ============ S6：串行合并与清理 ============

def write_run(runs_root, task, result='done', channel=1):
    """造一条 codex_channel 落盘的 run 记录。"""
    d = runs_root / f'{task}-ch{channel}-20261109T000000000000Z'
    d.mkdir(parents=True)
    (d / 'codex-channel.json').write_text(
        json.dumps({'task': task, 'channel': channel, 'result': result,
                    'exit_code': 0 if result == 'done' else 1}),
        encoding='utf-8')
    return d


def test_parse_braced_json_handles_multiline(mod):
    """wt merge 输出是多行 pretty JSON，必须整体截取，不能只取首行。"""
    text = (
        'some log line\n'
        '{\n'
        '  "merged": true,\n'
        '  "removed": false,\n'
        '  "target": "main"\n'
        '}\n'
        'trailing log\n'
    )
    data = mod._parse_braced_json(text)
    assert data['merged'] is True
    assert data['removed'] is False


def test_parse_braced_json_returns_none_on_garbage(mod):
    assert mod._parse_braced_json('no json here') is None
    assert mod._parse_braced_json('{broken') is None


def test_parse_braced_json_ignores_braces_in_log_text(mod):
    """真实 wt 输出是「日志 + JSON」混合；日志里的花括号不得干扰截取。"""
    text = (
        '◎ Merging 1 commit to main @ 031fd1f\n'
        '  * 031fd1f feat: add func() { return 1; }\n'
        '✓ Merged to main (1 commit, 1 file, +1)\n'
        '{\n'
        '  "branch": "feat1",\n'
        '  "removed": true\n'
        '}\n'
    )
    data = mod._parse_braced_json(text)
    assert data == {'branch': 'feat1', 'removed': True}


def test_parse_braced_json_parses_remove_array(mod):
    """实测 wt remove 输出是 JSON 数组，不能被当成内层单个对象。"""
    text = (
        '◎ Removing feat2 worktree...\n'
        '↳ Branch unmerged; to delete, run wt remove -D feat2\n'
        '[\n'
        '  {\n'
        '    "kind": "worktree",\n'
        '    "branch": "feat2",\n'
        '    "branch_outcome": "retained_unmerged",\n'
        '    "branch_checked_out_at": null\n'
        '  }\n'
        ']\n'
    )
    data = mod._parse_braced_json(text)
    assert isinstance(data, list)
    assert data[0]['branch_outcome'] == 'retained_unmerged'


def test_find_done_tasks_only_counts_done(mod, monkeypatch, tmp_path):
    write_task(tmp_path, 1)
    write_task(tmp_path, 2)
    runs = tmp_path / 'runs'
    write_run(runs, '1', result='done')
    write_run(runs, '2', result='done')
    write_run(runs, '2', result='blocked', channel=2)   # 较新的阻塞记录
    monkeypatch.setattr(mod, 'RUNS', runs)
    done = mod.find_done_tasks(str(tmp_path))
    assert set(done) == {'1', '2'}
    # 取到的是 done 那条，而不是跳过它去信 blocked
    assert done['1'].endswith('codex-channel.json')


def test_find_done_tasks_excludes_blocked_only(mod, monkeypatch, tmp_path):
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    write_run(runs, '1', result='blocked')
    monkeypatch.setattr(mod, 'RUNS', runs)
    assert mod.find_done_tasks(str(tmp_path)) == {}


def test_merge_is_serial_and_stops_on_failure(mod, monkeypatch, tmp_path):
    """两个任务都完成，但第一个合并失败——第二个绝不能被合并。"""
    write_task(tmp_path, 1)
    write_task(tmp_path, 2)
    runs = tmp_path / 'runs'
    write_run(runs, '1')
    write_run(runs, '2')
    monkeypatch.setattr(mod, 'RUNS', runs)

    calls = []

    def fake_wt_merge(branch, target=None):
        calls.append(branch)
        if len(calls) == 1:
            return _FakeResult(1, 'CONFLICT (add/add): Merge conflict in x.py')
        return _FakeResult(0, json.dumps({'merged': True, 'removed': True}))

    monkeypatch.setattr(mod, 'wt_merge', fake_wt_merge)
    done, merged, failed = mod.merge(str(tmp_path))
    assert calls == ['gorch/1']                 # 只调了一次，串行且失败即停
    assert merged == []
    assert failed[0]['task'] == '1'
    assert failed[0]['returncode'] == 1
    assert 'CONFLICT' in failed[0]['stdout']


def test_merge_all_sequential_order(mod, monkeypatch, tmp_path):
    write_task(tmp_path, 1)
    write_task(tmp_path, 2)
    runs = tmp_path / 'runs'
    write_run(runs, '1')
    write_run(runs, '2')
    monkeypatch.setattr(mod, 'RUNS', runs)
    calls = []

    def fake_wt_merge(branch, target=None):
        calls.append(branch)
        return _FakeResult(0, json.dumps({'merged': True, 'removed': True}))

    monkeypatch.setattr(mod, 'wt_merge', fake_wt_merge)
    done, merged, failed = mod.merge(str(tmp_path))
    assert calls == ['gorch/1', 'gorch/2']      # 严格串行，不是并发
    assert [m['task'] for m in merged] == ['1', '2']
    assert failed == []


def test_merge_refuses_task_without_done_record(mod, monkeypatch, tmp_path):
    write_task(tmp_path, 1)
    write_task(tmp_path, 2)
    runs = tmp_path / 'runs'
    write_run(runs, '1', result='done')
    write_run(runs, '2', result='blocked')
    monkeypatch.setattr(mod, 'RUNS', runs)
    with pytest.raises(SystemExit):
        mod.merge(str(tmp_path), tasks=['1', '2'])


def test_merge_fails_closed_on_unparsable_json(mod, monkeypatch, tmp_path):
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    write_run(runs, '1')
    monkeypatch.setattr(mod, 'RUNS', runs)
    monkeypatch.setattr(mod, 'wt_merge', lambda *a, **k: _FakeResult(0, 'no json'))
    with pytest.raises(SystemExit):
        mod.merge(str(tmp_path))


def test_merge_no_done_tasks_is_noop(mod, monkeypatch, tmp_path):
    write_task(tmp_path, 1)
    monkeypatch.setattr(mod, 'RUNS', tmp_path / 'runs')
    called = []
    monkeypatch.setattr(mod, 'wt_merge', lambda *a, **k: called.append(a))
    done, merged, failed = mod.merge(str(tmp_path))
    assert done == {} and merged == [] and failed == []
    assert called == []


def test_cleanup_skips_when_worktree_missing(mod, monkeypatch, tmp_path):
    write_task(tmp_path, 1)
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', tmp_path / 'wt')
    removed, skipped = mod.cleanup(str(tmp_path))
    assert removed == []
    assert skipped[0]['reason'] == 'worktree 已不存在'


def test_cleanup_force_propagates_to_wt_remove(mod, monkeypatch, tmp_path):
    write_task(tmp_path, 1)
    wt_root = tmp_path / 'wt'
    (wt_root / '1').mkdir(parents=True)
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', wt_root)
    seen = []

    def fake_wt_remove(branch, force=False, delete_branch=False):
        seen.append((branch, force, delete_branch))
        return _FakeResult(0, json.dumps({'removed': True}))

    monkeypatch.setattr(mod, 'wt_remove', fake_wt_remove)
    mod.cleanup(str(tmp_path), force=True)
    assert seen == [('gorch/1', True, False)]


def test_cleanup_delete_branch_propagates(mod, monkeypatch, tmp_path):
    """-D 会丢未合并提交，必须只有显式要求才传下去。"""
    write_task(tmp_path, 1)
    wt_root = tmp_path / 'wt'
    (wt_root / '1').mkdir(parents=True)
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', wt_root)
    seen = []

    def fake_wt_remove(branch, force=False, delete_branch=False):
        seen.append((branch, force, delete_branch))
        return _FakeResult(0, json.dumps([]))

    monkeypatch.setattr(mod, 'wt_remove', fake_wt_remove)
    mod.cleanup(str(tmp_path), force=True, delete_branch=True)
    assert seen == [('gorch/1', True, True)]


def test_cleanup_records_branch_outcome(mod, monkeypatch, tmp_path):
    """未合并分支被保留时，回执要如实写明 retained_unmerged。"""
    write_task(tmp_path, 1)
    wt_root = tmp_path / 'wt'
    (wt_root / '1').mkdir(parents=True)
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', wt_root)
    payload = json.dumps([{'kind': 'worktree', 'branch': 'gorch/1',
                           'branch_outcome': 'retained_unmerged'}])
    monkeypatch.setattr(mod, 'wt_remove', lambda *a, **k: _FakeResult(0, payload))
    removed, skipped = mod.cleanup(str(tmp_path))
    assert removed[0]['branch_outcomes'] == ['retained_unmerged']


def test_cleanup_reports_failure_without_force(mod, monkeypatch, tmp_path):
    """脏 worktree 未加 --force 时 wt remove 会失败，必须如实回传而非静默跳过。"""
    write_task(tmp_path, 1)
    wt_root = tmp_path / 'wt'
    (wt_root / '1').mkdir(parents=True)
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', wt_root)
    monkeypatch.setattr(
        mod, 'wt_remove',
        lambda *a, **k: _FakeResult(1, 'worktree contains untracked changes'))
    removed, skipped = mod.cleanup(str(tmp_path))
    assert removed == []
    assert 'rc=1' in skipped[0]['reason']


def test_next_returns_the_first_ready_task_and_reports_the_rest(mod, tmp_path):
    """接 ccpm next.sh 的 ready 语义：选出一个，其余连同原因一起交出。

    next.sh 在本仓跑不了（list_task_files 只认 .claude/epics/<数字>.md），
    所以接的是判定语义而不是脚本本身——判定仍来自 ccpm 原函数。
    """
    write_task(tmp_path, 1, status='in-progress')
    write_task(tmp_path, 2)
    write_task(tmp_path, 3, deps=['2'])
    write_task(tmp_path, 4, conflicts=['1'])
    out = mod.next_task(str(tmp_path))
    assert out['next'] == '2'
    assert out['ready'] == ['2']
    assert {r['task']: r['verdict'] for r in out['not_ready']} == {
        '1': '非开放状态', '3': '等待依赖', '4': '等待冲突解除'}


def test_next_is_none_when_nothing_is_ready(mod, tmp_path):
    """没有下一单时 next 必须为 null，不能拿一个非开放任务凑数。"""
    write_task(tmp_path, 1, status='in-progress')
    out = mod.next_task(str(tmp_path))
    assert out['next'] is None
    assert out['ready'] == []
