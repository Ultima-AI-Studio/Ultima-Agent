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
import os
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


def test_stderr_noise_does_not_reject_intact_verdict(mod, monkeypatch, tmp_path):
    """L77：stderr 有 cygwin 噪声，但 rc=0 且三条标记完整——不能整批拒派。

    git-bash 在 fork 受限时会往 stderr 写 'fork: retry' / 'cygheap ...'，
    此时判定结果本身是好的。把它当失败会把一次偶发噪声放大成整批 fail-closed。
    """
    write_task(tmp_path, 1)

    class _R:
        returncode = 0
        stdout = 'STATUS:open\nUNMET:\nCONFLICTS:\n'
        stderr = '      0 [main] bash 1234 fork: retry: Resource temporarily unavailable'

    monkeypatch.setattr(mod.subprocess, 'run', lambda *a, **k: _R())
    rows = mod.gate_check(str(tmp_path))
    assert rows[0]['verdict'] == '可开工'
    # 噪声不被丢弃，只降级为诊断信息
    assert 'fork: retry' in rows[0]['stderr_diag']


def test_nonzero_exit_still_rejects_and_keeps_stderr(mod, monkeypatch, tmp_path):
    """退出码非 0 仍是硬失败：判定契约收缩到 returncode，但没放弃它。"""
    write_task(tmp_path, 1)

    class _R:
        returncode = 3
        stdout = 'STATUS:open\n'
        stderr = 'ccpm 内部报错'

    monkeypatch.setattr(mod.subprocess, 'run', lambda *a, **k: _R())
    with pytest.raises(SystemExit):
        mod.gate_check(str(tmp_path))


def test_stderr_noise_with_missing_markers_still_fails_closed(mod, monkeypatch, tmp_path):
    """rc=0 但标记缺失仍然拒绝——放宽噪声不等于放宽输出完整性。"""
    write_task(tmp_path, 1)

    class _R:
        returncode = 0
        stdout = 'STATUS:open\n'
        stderr = 'noise'

    monkeypatch.setattr(mod.subprocess, 'run', lambda *a, **k: _R())
    with pytest.raises(SystemExit):
        mod.gate_check(str(tmp_path))


def test_real_stderr_error_with_intact_markers_fails_closed(mod, monkeypatch, tmp_path):
    """第二轮审计的反例：stderr 里是真错误，但三标记齐全、rc=0。

    `printf "$(f)"` 结构下函数内部报错不会传退出码，CONFLICTS 会空成"无冲突"。
    只放行 cygwin 噪声、其余一律拒，才能堵住这条 fail-open。
    """
    write_task(tmp_path, 1, conflicts=['2'])

    class _R:
        returncode = 0
        stdout = 'STATUS:open\nUNMET:\nCONFLICTS:\n'
        stderr = 'grep: 2.md: Permission denied'

    monkeypatch.setattr(mod.subprocess, 'run', lambda *a, **k: _R())
    with pytest.raises(SystemExit) as ei:
        mod.gate_check(str(tmp_path))
    assert 'Permission denied' in str(ei.value)


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


def test_find_done_tasks_trusts_latest_record_only(mod, monkeypatch, tmp_path):
    """第三轮审计 A1：任务重跑失败后，绝不能再按上一次的成功记录合并。

    旧语义（本轮有意变更）：从新到旧扫，命中第一条 done 就算成功 → 任务 2 会被合进去，
    等于把一次失败的执行当成成果。新语义只看最新一条真实记录。
    """
    write_task(tmp_path, 1)
    write_task(tmp_path, 2)
    runs = tmp_path / 'runs'
    d1 = write_run(runs, '1', result='done')
    d2_done = write_run(runs, '2', result='done')
    d2 = write_run(runs, '2', result='blocked', channel=2)   # 较新的阻塞记录
    # 显式拉开 mtime：不给 done 那条也设，它的"刚刚创建"反而会压过 blocked
    for p, ts in ((d1, 1_700_000_000), (d2_done, 1_700_000_000),
                  (d2, 1_700_000_100)):
        os.utime(p / 'codex-channel.json', (ts, ts))
    monkeypatch.setattr(mod, 'RUNS', runs)

    assert mod.find_done_tasks(str(tmp_path)) == {'1': str(d1 / 'codex-channel.json')}
    done, stale = mod.find_done_tasks(str(tmp_path), with_blocked=True)
    assert set(done) == {'1'}
    assert '2' in stale                     # 未进合并池的任务必须显式报出来，不能静默


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
    done, merged, failed, _ = mod.merge(str(tmp_path))
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
    done, merged, failed, _ = mod.merge(str(tmp_path))
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
    done, merged, failed, _ = mod.merge(str(tmp_path))
    assert done == {} and merged == [] and failed == []
    assert called == []


def test_cleanup_marks_partial_when_dir_gone_but_branch_remains(mod, monkeypatch, tmp_path):
    """第四轮 A7：半清理态（目录没了、分支还在）不能记"已清理"。"""
    write_task(tmp_path, 1)
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', tmp_path / 'wt')
    monkeypatch.setattr(mod, '_branch_state', lambda b: 'exists')
    monkeypatch.setattr(mod, '_worktree_registered', lambda p: False)
    removed, skipped = mod.cleanup(str(tmp_path))
    assert removed == []
    assert skipped[0]['partial'] is True
    assert '半清理态' in skipped[0]['reason']


def test_cleanup_confirms_removed_only_when_all_three_gone(mod, monkeypatch, tmp_path):
    """目录 / worktree 登记 / 分支三处都确认不在，才算已清理。"""
    write_task(tmp_path, 1)
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', tmp_path / 'wt')
    monkeypatch.setattr(mod, '_branch_state', lambda b: 'absent')
    monkeypatch.setattr(mod, '_worktree_registered', lambda p: False)
    removed, skipped = mod.cleanup(str(tmp_path))
    assert skipped == []
    assert removed[0]['task'] == '1'
    assert '三处均已不存在' in removed[0]['note']


def test_cleanup_branch_state_unknown_is_not_success(mod, monkeypatch, tmp_path):
    """分支查询本身失败时不能当成"分支已没了"。"""
    write_task(tmp_path, 1)
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', tmp_path / 'wt')
    monkeypatch.setattr(mod, '_branch_state', lambda b: 'unknown')
    monkeypatch.setattr(mod, '_worktree_registered', lambda p: False)
    removed, skipped = mod.cleanup(str(tmp_path))
    assert removed == []
    assert skipped[0]['partial'] is True


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


def test_cleanup_retained_branch_is_not_counted_as_removed(mod, monkeypatch, tmp_path):
    """rc=0 但分支被保留（retained_unmerged）不算清理完成，回执要如实带出。"""
    write_task(tmp_path, 1)
    wt_root = tmp_path / 'wt'
    (wt_root / '1').mkdir(parents=True)
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', wt_root)
    payload = json.dumps([{'kind': 'worktree', 'branch': 'gorch/1',
                           'branch_outcome': 'retained_unmerged'}])
    monkeypatch.setattr(mod, 'wt_remove', lambda *a, **k: _FakeResult(0, payload))
    removed, skipped = mod.cleanup(str(tmp_path))
    assert removed == []
    assert skipped[0]['partial'] is True
    assert 'retained_unmerged' in skipped[0]['reason']
    assert skipped[0]['result'][0]['branch_outcome'] == 'retained_unmerged'


def test_cleanup_reports_failure_without_force(mod, monkeypatch, tmp_path):
    """脏 worktree 未加 --force 时 wt remove 会失败，必须如实回传而非静默跳过。"""
    write_task(tmp_path, 1)
    wt_root = tmp_path / 'wt'
    (wt_root / '1').mkdir(parents=True)
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', wt_root)
    monkeypatch.setattr(
        mod, 'wt_remove',
        lambda *a, **k: _FakeResult(1, 'worktree contains untracked changes'))
    monkeypatch.setattr(mod, '_branch_state', lambda b: 'exists')
    monkeypatch.setattr(mod, '_worktree_registered', lambda p: True)
    removed, skipped = mod.cleanup(str(tmp_path))
    assert removed == []
    assert 'rc=1' in skipped[0]['reason']
    assert '目录还在=True' in skipped[0]['reason']


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


# ============ 第三轮审计闭环（A1/A3/A7/A8 + 按卡产出策略） ============

def test_gate_rejects_duplicate_marker(mod, monkeypatch, tmp_path):
    """A3：三标记必须各出现且仅一次。重复的 STATUS 会让末行覆盖首行。"""
    write_task(tmp_path, 1)

    class _R:
        returncode = 0
        stdout = 'STATUS:open\nSTATUS:done\nUNMET:\nCONFLICTS:\n'
        stderr = ''

    monkeypatch.setattr(mod.subprocess, 'run', lambda *a, **k: _R())
    with pytest.raises(SystemExit) as ei:
        mod.gate_check(str(tmp_path))
    assert '重复' in str(ei.value)


def test_gate_rejects_extra_stdout_line(mod, monkeypatch, tmp_path):
    """A3：stdout 只允许那三行。夹带其他行说明判定串被别的东西写过。"""
    write_task(tmp_path, 1)

    class _R:
        returncode = 0
        stdout = 'STATUS:open\nUNMET:\nCONFLICTS:\necho 顺手多打一行\n'
        stderr = ''

    monkeypatch.setattr(mod.subprocess, 'run', lambda *a, **k: _R())
    with pytest.raises(SystemExit) as ei:
        mod.gate_check(str(tmp_path))
    assert '多余行' in str(ei.value)


def test_cleanup_timeout_with_vanished_scene_counts_as_removed(mod, monkeypatch, tmp_path):
    """A7：wt remove 超时（rc!=0）但目录与分支都已消失——按已清理记，不报 fail。

    Windows 上 wt remove 稳定跑不完 180s，而它的内部 cleanup 常在超时点之前做完。
    只看 rc 会把每次清理都报成失败，逼人逐个回读现场。
    """
    write_task(tmp_path, 1)
    wt_root = tmp_path / 'wt'
    (wt_root / '1').mkdir(parents=True)
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', wt_root)
    monkeypatch.setattr(mod, '_branch_state', lambda b: 'absent')
    monkeypatch.setattr(mod, '_worktree_registered', lambda p: False)

    def fake_wt_remove(branch, force=False, delete_branch=False):
        (wt_root / '1').rmdir()          # 模拟 wt 自己已经把目录删掉
        return _FakeResult(1, 'wt remove 超时 gorch/1（180s），未返回结构化结果')

    monkeypatch.setattr(mod, 'wt_remove', fake_wt_remove)
    removed, skipped = mod.cleanup(str(tmp_path))
    assert skipped == []
    assert removed[0]['task'] == '1'
    assert '按已清理处理' in removed[0]['note']


def test_wt_remove_timeout_returns_structured_result(mod, monkeypatch):
    """超时必须作为结构化结果返回，不能再 raise SystemExit（否则 cleanup 拿不到）。"""
    def boom(*a, **k):
        raise mod.subprocess.TimeoutExpired(cmd='wt', timeout=180)

    monkeypatch.setattr(mod.subprocess, 'run', boom)
    r = mod.wt_remove('gorch/1')
    assert r.returncode == -1
    assert '超时' in r.stderr


def test_cleanup_timeout_with_residual_worktree_still_fails(mod, monkeypatch, tmp_path):
    """A7 的反面：超时且目录还在，必须照旧报失败——放宽不能放过真的没清掉。"""
    write_task(tmp_path, 1)
    wt_root = tmp_path / 'wt'
    (wt_root / '1').mkdir(parents=True)
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', wt_root)
    monkeypatch.setattr(mod, 'wt_remove',
                        lambda *a, **k: _FakeResult(1, 'wt remove 超时'))
    monkeypatch.setattr(mod, '_branch_state', lambda b: 'exists')
    monkeypatch.setattr(mod, '_worktree_registered', lambda p: True)
    removed, skipped = mod.cleanup(str(tmp_path))
    assert removed == []
    assert '目录还在=True' in skipped[0]['reason']


def test_task_meta_reads_frontmatter_flags(mod, tmp_path):
    (tmp_path / '1.md').write_text(
        '---\nname: t1\nstatus: open\nno_change_allowed: true\nallow_non_repo: false\n---\n# t1\n',
        encoding='utf-8')
    meta = mod._task_meta(tmp_path / '1.md')
    assert mod._truthy(meta.get('no_change_allowed')) is True
    assert mod._truthy(meta.get('allow_non_repo')) is False
    assert mod._truthy('') is False


def test_execute_passes_output_policy_per_card(mod, monkeypatch, tmp_path):
    """A2/A5：产出策略按卡透传。一张卡声明零改动，不能把整批都放开。"""
    for n, extra in ((1, 'no_change_allowed: true\n'), (2, '')):
        (tmp_path / f'{n}.md').write_text(
            f'---\nname: t{n}\nstatus: open\ndepends_on: []\nparallel: true\n'
            f'conflicts_with: []\n{extra}---\n# t{n}\n', encoding='utf-8')
    wt_root = tmp_path / 'wt'
    for n in (1, 2):
        (wt_root / str(n)).mkdir(parents=True)
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', wt_root)
    prompts = tmp_path / 'prompts'
    prompts.mkdir()
    for n in (1, 2):
        (prompts / f'{n}.txt').write_text('p', encoding='utf-8')

    seen = []

    class _P:
        returncode = 0

        def communicate(self):
            return ('', '')

    monkeypatch.setattr(mod.subprocess, 'Popen', lambda cmd, **kw: (seen.append(cmd) or _P()))
    monkeypatch.setattr(mod, 'gate_check', lambda d: [
        {'task': '1', 'verdict': '可开工'}, {'task': '2', 'verdict': '可开工'}])
    mod.execute(str(tmp_path), str(prompts), max_channels=2)
    flagged = [c[c.index('--task') + 1] for c in seen if '--no-change-allowed' in c]
    assert flagged == ['1']        # 只有声明了的那张卡带上开关


def test_run_all_stops_at_conflict_and_keeps_scene(mod, monkeypatch, tmp_path):
    """A8：一条命令串完五步；merge 冲突时停在那里，冲突任务的 worktree 不清。"""
    write_task(tmp_path, 1)
    write_task(tmp_path, 2)
    runs = tmp_path / 'runs'
    d1 = write_run(runs, '1')
    d2 = write_run(runs, '2')
    monkeypatch.setattr(mod, 'RUNS', runs)
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', tmp_path / 'wt')
    prompts = tmp_path / 'prompts'
    prompts.mkdir()
    for n in (1, 2):
        (prompts / f'{n}.txt').write_text('p', encoding='utf-8')

    monkeypatch.setattr(mod, 'gate_check', lambda d: [
        {'task': '1', 'verdict': '可开工'}, {'task': '2', 'verdict': '可开工'}])
    monkeypatch.setattr(mod, 'provision', lambda d: ([], [], []))
    monkeypatch.setattr(mod, 'execute', lambda *a, **k: ([], [
        {'task': '1', 'channel': 1, 'returncode': 0, 'run_dir': str(d1)},
        {'task': '2', 'channel': 2, 'returncode': 0, 'run_dir': str(d2)}]))

    calls = []

    def fake_wt_merge(branch, target=None):
        calls.append(branch)
        if branch == 'gorch/2':
            return _FakeResult(1, 'CONFLICT (content): Merge conflict in x')
        return _FakeResult(0, json.dumps({'merged': True, 'removed': True}))

    monkeypatch.setattr(mod, 'wt_merge', fake_wt_merge)
    cleaned = []

    def fake_cleanup(batch_dir, tasks=None, force=False, delete_branch=False):
        cleaned.append(list(tasks or []))
        return [], []

    monkeypatch.setattr(mod, 'cleanup', fake_cleanup)
    summary = mod.run_all(str(tmp_path), str(prompts), max_channels=2)
    assert calls == ['gorch/1', 'gorch/2']
    assert summary['stopped_at'] == 'merge'
    assert [f['task'] for f in summary['steps']['merge']['failed']] == ['2']
    # 第四轮口径：冲突时一律不 cleanup，冲突任务与其余任务的现场全保留
    # （审计明确不建议"冲突后自动清理所有非冲突任务"）。
    assert cleaned == []
    assert summary['steps']['cleanup']['kept_for_conflict'] == ['2']

# ============ 第四轮：第三轮审计 10 条的闭环验收 ============

def test_run_all_stops_at_execute_when_any_task_fails(mod, monkeypatch, tmp_path):
    """A8：execute 任一非 0 即停，不进 merge（此前只看 merge 的失败）。"""
    for n in (1, 2):
        write_task(tmp_path, n)
    monkeypatch.setattr(mod, 'gate_check', lambda d: [
        {'task': '1', 'verdict': '可开工'}, {'task': '2', 'verdict': '可开工'}])
    monkeypatch.setattr(mod, 'provision', lambda d: ([], [], []))
    monkeypatch.setattr(mod, 'execute', lambda *a, **k: ([], [
        {'task': '1', 'channel': 1, 'returncode': 0, 'run_dir': 'R1'},
        {'task': '2', 'channel': 2, 'returncode': 1, 'run_dir': 'R2'}]))
    called = []
    monkeypatch.setattr(mod, 'wt_merge',
                        lambda *a, **k: called.append('merge') or _FakeResult(0, '{}'))
    monkeypatch.setattr(mod, 'cleanup',
                        lambda *a, **k: called.append('cleanup') or ([], []))
    summary = mod.run_all(str(tmp_path), str(tmp_path))
    assert summary['stopped_at'] == 'execute'
    assert summary['steps']['execute']['failed'] == ['2']
    assert called == []            # 既没合也没清


def test_run_all_dry_run_does_not_merge_or_cleanup(mod, monkeypatch, tmp_path):
    """A1e：--dry-run 只空转执行段，此前照样真 merge + 真 cleanup。"""
    write_task(tmp_path, 1)
    monkeypatch.setattr(mod, 'gate_check', lambda d: [{'task': '1', 'verdict': '可开工'}])
    monkeypatch.setattr(mod, 'provision', lambda d: ([], [], []))
    monkeypatch.setattr(mod, 'execute', lambda *a, **k: ([], [
        {'task': '1', 'channel': 1, 'returncode': 0, 'run_dir': 'R1'}]))
    called = []
    monkeypatch.setattr(mod, 'wt_merge',
                        lambda *a, **k: called.append('merge') or _FakeResult(0, '{}'))
    monkeypatch.setattr(mod, 'cleanup',
                        lambda *a, **k: called.append('cleanup') or ([], []))
    summary = mod.run_all(str(tmp_path), str(tmp_path), dry_run=True)
    assert summary['stopped_at'] == 'dry_run'
    assert called == []


def test_run_all_without_ready_has_merge_key(mod, tmp_path):
    """A8：没有可开工任务时 steps 也要有 merge/cleanup，CLI 不再 KeyError。"""
    write_task(tmp_path, 1, status='done')
    summary = mod.run_all(str(tmp_path), str(tmp_path))
    assert summary['stopped_at'] == 'gate'
    assert summary['steps']['merge']['failed'] == []
    assert summary['steps']['cleanup']['removed'] == []


def test_run_all_carries_invocation_and_target(mod, monkeypatch, tmp_path):
    """A8：target 在 run 开始就固定，不再到 merge 才动态读当前分支。"""
    write_task(tmp_path, 1, status='done')
    summary = mod.run_all(str(tmp_path), str(tmp_path), target='gorch/base')
    assert summary['target'] == 'gorch/base'
    assert len(summary['invocation']) >= 14


def test_find_done_tasks_only_reads_this_invocation(mod, monkeypatch, tmp_path):
    """A1：run 模式只认本次 invocation 的 run-dir，历史 done 不得顶上来。"""
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    write_run(runs, '1')                           # 上一次的成功记录
    monkeypatch.setattr(mod, 'RUNS', runs)
    new = runs / 'new'
    new.mkdir()
    (new / 'codex-channel.json').write_text(
        json.dumps({'result': 'blocked', 'reason': '本轮失败'}), encoding='utf-8')
    done, stale = mod.find_done_tasks(str(tmp_path), with_blocked=True,
                                      run_dirs={'1': str(new)})
    assert done == {}
    assert '本轮失败' in stale['1']['reason']


def test_find_done_tasks_corrupt_record_blocks_instead_of_fallback(mod, monkeypatch, tmp_path):
    """A1b：本次记录损坏必须阻断，不能静默跳过回退到旧 done。"""
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    write_run(runs, '1')
    monkeypatch.setattr(mod, 'RUNS', runs)
    bad = runs / 'bad'
    bad.mkdir()
    (bad / 'codex-channel.json').write_text('{not json', encoding='utf-8')
    done, stale = mod.find_done_tasks(str(tmp_path), with_blocked=True,
                                      run_dirs={'1': str(bad)})
    assert done == {}
    assert '损坏' in stale['1']['reason']


def test_done_no_merge_is_not_mergeable(mod, monkeypatch, tmp_path):
    """A6：纯验证卡（done_no_merge）不是可合并成果，不进合并池。"""
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    d = runs / '1-ch1-x'
    d.mkdir(parents=True)
    (d / 'codex-channel.json').write_text(
        json.dumps({'result': 'done_no_merge'}), encoding='utf-8')
    monkeypatch.setattr(mod, 'RUNS', runs)
    done, stale = mod.find_done_tasks(str(tmp_path), with_blocked=True,
                                      run_dirs={'1': str(d)})
    assert done == {}
    assert 'done_no_merge' in stale['1']['reason']


def test_merge_requires_merged_true(mod, monkeypatch, tmp_path):
    """A8：wt 报 merged=false 时不能记成功（此前只要求能解析 JSON）。"""
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    d = write_run(runs, '1')
    monkeypatch.setattr(mod, 'RUNS', runs)
    monkeypatch.setattr(mod, 'wt_merge',
                        lambda *a, **k: _FakeResult(0, json.dumps({'merged': False})))
    done, merged, failed, stale = mod.merge(str(tmp_path), tasks=['1'],
                                            target='main', run_dirs={'1': str(d)})
    assert merged == []
    assert failed[0]['task'] == '1'
    assert 'merged=False' in failed[0]['stderr']


def test_gate_check_rejects_error_after_200_chars(mod, monkeypatch, tmp_path):
    """A2：真错误排在前 200 字符之后也必须被看见。"""
    write_task(tmp_path, 1)
    noise = '      3 [main] bash 1234 fork: retry: Resource temporarily unavailable\n'
    pad = 'x' * 250 + '\n'
    err = noise + pad + 'fatal: Permission denied\n'

    class _R:
        returncode = 0
        stdout = 'STATUS:open\nUNMET:\nCONFLICTS:\n'
        stderr = err

    monkeypatch.setattr(mod.subprocess, 'run', lambda *a, **k: _R())
    with pytest.raises(SystemExit) as ei:
        mod.gate_check(str(tmp_path))
    assert 'Permission denied' in str(ei.value)
    assert '共 2 行真错误' in str(ei.value)


def test_cygwin_noise_is_anchored_not_substring(mod, monkeypatch, tmp_path):
    """A2：真实错误行里含 cygheap 关键词时，不能被当噪声吞掉。"""
    write_task(tmp_path, 1)

    class _R:
        returncode = 0
        stdout = 'STATUS:open\nUNMET:\nCONFLICTS:\n'
        stderr = 'error: could not read cygheap header of index file\n'

    monkeypatch.setattr(mod.subprocess, 'run', lambda *a, **k: _R())
    with pytest.raises(SystemExit) as ei:
        mod.gate_check(str(tmp_path))
    assert 'cygheap' in str(ei.value)


def test_cygwin_noise_lines_still_pass(mod, monkeypatch, tmp_path):
    """A2 的反面：整行 fork 噪声仍应放行，不把一次噪声放大成整批拒派。"""
    write_task(tmp_path, 1)

    class _R:
        returncode = 0
        stdout = 'STATUS:open\nUNMET:\nCONFLICTS:\n'
        stderr = ('      3 [main] bash 1234 fork: retry: Resource temporarily unavailable\n'
                  'bash: child_copy: cygheap read copy failed, 0x2EF8\n')

    monkeypatch.setattr(mod.subprocess, 'run', lambda *a, **k: _R())
    rows = mod.gate_check(str(tmp_path))
    assert by_id(rows)['1']['verdict'] == '可开工'


def test_branch_state_distinguishes_absent_from_unknown(mod, monkeypatch):
    """A7：git rc 不是 0/1 时是 unknown，不能读成"分支不存在"。"""
    class _R128:
        returncode = 128
        stdout = ''

    monkeypatch.setattr(mod.subprocess, 'run', lambda *a, **k: _R128())
    assert mod._branch_state('gorch/1') == 'unknown'

    class _R1:
        returncode = 1
        stdout = ''

    monkeypatch.setattr(mod.subprocess, 'run', lambda *a, **k: _R1())
    assert mod._branch_state('gorch/1') == 'absent'

    class _R0:
        returncode = 0
        stdout = 'abc123 refs/heads/gorch/1\n'

    monkeypatch.setattr(mod.subprocess, 'run', lambda *a, **k: _R0())
    assert mod._branch_state('gorch/1') == 'exists'

def test_merge_tolerates_refs_heads_prefix(mod, monkeypatch, tmp_path):
    """自查补充：wt 把 branch/target 写成 refs/heads/x 时不能判成"不一致"误杀。"""
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    d = write_run(runs, '1')
    monkeypatch.setattr(mod, 'RUNS', runs)
    payload = {'merged': True, 'branch': 'refs/heads/gorch/1',
               'target': 'refs/heads/main'}
    monkeypatch.setattr(mod, 'wt_merge',
                        lambda *a, **k: _FakeResult(0, json.dumps(payload)))
    done, merged, failed, stale = mod.merge(str(tmp_path), tasks=['1'],
                                            target='main', run_dirs={'1': str(d)})
    assert failed == []
    assert merged[0]['task'] == '1'