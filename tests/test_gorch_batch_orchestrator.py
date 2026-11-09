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
def mod(monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location('batch_orchestrator', ORCH)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    # merge 现在会去 git 侧复核合入是否生效（wt 的 JSON 实测没有 merged 字段）。
    # 默认给一个已合入的桩，具体用例要测反例时自己再 setattr 覆盖。
    # merge 的"合入生效"要三条同时成立（第五轮审计 7.2）：target tip 前进、
    # 源分支成为祖先、（预已是祖先时）源 tip 变过。默认桩模拟一次真实合入：
    # 调用前 is-ancestor 失败、调用后成功，SHA 每次都变。
    _anc = {'n': 0}
    # r9（第八轮审计 N9）：proof 现在还比 target 的**前态 tree** 与后态 tree，
    # 默认桩必须让 tree 随每次 rev-parse 变化，否则"内容没变"会把真合入判死。
    _tree = {'n': 0}

    def _fake_git_out(args, *a, **k):
        if isinstance(args, (list, tuple)) and list(args)[:1] == ['merge-base']:
            _anc['n'] += 1
            return (0, '') if _anc['n'] > 1 else (1, '')
        if isinstance(args, (list, tuple)) and list(args)[:1] == ['rev-parse']:
            _tree['n'] += 1
            return (0, 'tree-' + str(_tree['n']))
        return (0, '')

    monkeypatch.setattr(m, '_git_out', _fake_git_out)
    _seq = {'n': 0}

    def _fake_ref_sha(ref):
        _seq['n'] += 1
        return 'sha-' + str(ref) + '-' + str(_seq['n'])

    monkeypatch.setattr(m, '_ref_sha', _fake_ref_sha)
    # 签发 manifest 要记 target；单测里不真去读 git（否则会用真实仓库 + 打到
    # 被 stub 的 Popen 上）。需要看默认 target 的用例自己覆盖。
    monkeypatch.setattr(m, '_current_branch', lambda: 'test-branch')
    # 授权 manifest 落到 RUNS/_invocations：默认隔离到 tmp，避免测试往仓库
    # data/gorch 写运行期文件；需要看真实目录形状的用例自己覆盖 RUNS。
    monkeypatch.setattr(m, 'RUNS', tmp_path / 'runs')
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
    # 签发授权 manifest 会落到 RUNS/_invocations；单测必须隔离到 tmp，
    # 否则每次跑测都在仓库 data/gorch 里堆运行期文件。
    monkeypatch.setattr(mod, 'RUNS', tmp_path / 'runs')
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

def write_run(runs_root, task, result='done', channel=1,
              started_at='2026-11-09T00:00:00Z', invocation='inv-test',
              mergeable=None, run_dir=None, dry_run=False, extra=None):
    """造一条 codex_channel 落盘的 run 记录（按 r8 的真实生产形状）。

    started_at / invocation 是兜底授权的必需字段（第五轮审计 Q3-3）：缺任一即阻断。

    r8（第七轮审计 N1 / B5）：消费端现在要求记录自带
      · run_dir —— 规范化绝对路径必须与请求的 run-dir 相等（不再比 basename）；
      · invocation —— 必须等于本次调用（run_all 会把本次 inv 传下来比对）；
      · mergeable —— 必须是严格 True。
    r7 的 write_run 只写 task/result/invocation，正好掩盖了"生产者写不出可消费的
    记录"这个真问题，所以这里必须按真实形状造，而不是让夹具替生产端补字段。
    """
    slug = started_at.replace(':', '').replace('-', '')
    d = runs_root / f'{task}-ch{channel}-{slug}'
    d.mkdir(parents=True)
    if mergeable is None:
        mergeable = (result == 'done')
    payload = {'task': task, 'channel': channel, 'result': result,
               'invocation': invocation, 'started_at': started_at,
               'mergeable': bool(mergeable), 'dry_run': bool(dry_run),
               'run_dir': str(run_dir or d.resolve()),
               'exit_code': 0 if result == 'done' else 1}
    if extra:
        payload.update(extra)
    (d / 'codex-channel.json').write_text(json.dumps(payload), encoding='utf-8')
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
    # 已不再按 mtime 授权（第五轮 Q3-3）：改用记录里的 started_at 拉开先后
    d2 = write_run(runs, '2', result='blocked', channel=2,
                   started_at='2026-11-09T00:01:40Z')
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
        return _FakeResult(0, json.dumps({'branch': branch, 'target': target or 'main',
                                                  'committed': False, 'removed': False}))

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
        return _FakeResult(0, json.dumps({'branch': branch, 'target': target or 'main',
                                                  'committed': False, 'removed': False}))

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
    """r12（第十一轮审计 E-3）：回执不可解析不再 raise SystemExit——那会绕开
    failed/kind 与结构化 summary，调用方只看到进程退出，拿不到"哪个任务、什么
    类别、现场有没有被动过"。改为 proof_failure 业务失败（wt 已跑，合并可能发生）。
    """
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    write_run(runs, '1')
    monkeypatch.setattr(mod, 'RUNS', runs)
    monkeypatch.setattr(mod, 'wt_merge', lambda *a, **k: _FakeResult(0, 'no json'))
    trace = {}
    done, merged, failed, stale = mod.merge(str(tmp_path), trace=trace)
    assert merged == []
    assert [f['task'] for f in failed] == ['1']
    assert failed[0]['kind'] == 'proof_failure'
    assert trace['attempted'] == ['1']
    assert trace['not_attempted'] == []


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
    assert '目录状态=exists' in skipped[0]['reason']


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
    assert '目录状态=exists' in skipped[0]['reason']


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
    monkeypatch.setattr(mod, 'RUNS', tmp_path / 'runs')
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
    monkeypatch.setattr(mod, 'provision', lambda d, tasks=None: ([], [], []))
    monkeypatch.setattr(mod, 'execute', lambda *a, **k: ([], [
        {'task': '1', 'channel': 1, 'returncode': 0, 'run_dir': str(d1)},
        {'task': '2', 'channel': 2, 'returncode': 0, 'run_dir': str(d2)}]))

    calls = []

    def fake_wt_merge(branch, target=None):
        calls.append(branch)
        if branch == 'gorch/2':
            return _FakeResult(1, 'CONFLICT (content): Merge conflict in x')
        return _FakeResult(0, json.dumps({'branch': branch, 'target': target or 'main',
                                                  'committed': False, 'removed': False}))

    monkeypatch.setattr(mod, 'wt_merge', fake_wt_merge)
    cleaned = []

    def fake_cleanup(batch_dir, tasks=None, force=False, delete_branch=False):
        cleaned.append(list(tasks or []))
        return [], []

    monkeypatch.setattr(mod, 'cleanup', fake_cleanup)
    summary = mod.run_all(str(tmp_path), str(prompts), max_channels=2,
                          invocation='inv-test')
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
    monkeypatch.setattr(mod, 'provision', lambda d, tasks=None: ([], [], []))
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
    monkeypatch.setattr(mod, 'provision', lambda d, tasks=None: ([], [], []))
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


CLEANUP_KEYS = {'removed', 'skipped', 'kept_for_conflict', 'kept_for_evidence',
                'kept_for_proof', 'kept_for_unknown'}


def test_run_all_without_ready_has_merge_key(mod, tmp_path):
    """A8：没有可开工任务时 steps 也要有 merge/cleanup，CLI 不再 KeyError。

    r14（第十三轮审计 E1-4）：只断 `removed` 不够——撤掉 `_stop()` 里补的三个
    `kept_for_*`，用例照样绿。这里改为断言**完整键集**（集合相等）。
    """
    write_task(tmp_path, 1, status='done')
    summary = mod.run_all(str(tmp_path), str(tmp_path))
    assert summary['stopped_at'] == 'gate'
    assert summary['steps']['merge']['failed'] == []
    cleanup = summary['steps']['cleanup']
    assert set(cleanup) == CLEANUP_KEYS
    for k in CLEANUP_KEYS:
        assert cleanup[k] == []


def test_run_all_normal_completion_cleanup_has_all_keepers(mod, monkeypatch, tmp_path):
    """r14（第十三轮审计 E1-4）：正常完成分支的 `steps['cleanup']` 也必须是六键同构。

    此前只有失败四分流路径带完整键集，正常完成只写 kept_for_conflict；撤掉该分支补的
    三个键，本用例的红点是唯一防线（AST 只能证明当前形态，不能防回退）。
    """
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    d1 = write_run(runs, '1')
    prompts = tmp_path / 'prompts'
    prompts.mkdir()
    (prompts / '1.txt').write_text('p', encoding='utf-8')
    monkeypatch.setattr(mod, 'RUNS', runs)
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', tmp_path / 'wt')
    monkeypatch.setattr(mod, 'gate_check', lambda d: [{'task': '1', 'verdict': '可开工'}])
    monkeypatch.setattr(mod, 'provision', lambda d, tasks=None: ([], [], []))
    monkeypatch.setattr(mod, 'execute', lambda *a, **k: ([], [
        {'task': '1', 'channel': 1, 'returncode': 0, 'run_dir': str(d1)}]))
    monkeypatch.setattr(mod, 'find_done_tasks',
                        lambda *a, **k: ({'1': {'task': '1', 'result': 'done'}}, {}))

    def fake_merge(*a, **k):
        k.get('trace', {}).update({'attempted': ['1'], 'not_attempted': []})
        return {}, [{'task': '1'}], [], {}

    monkeypatch.setattr(mod, 'merge', fake_merge)
    monkeypatch.setattr(mod, 'cleanup', lambda *a, **k: ([], []))
    summary = mod.run_all(str(tmp_path), str(prompts), max_channels=1,
                          invocation='inv-test')
    assert summary['stopped_at'] == 'done'
    cleanup = summary['steps']['cleanup']
    assert set(cleanup) == CLEANUP_KEYS
    assert cleanup['removed'] == []
    for k in ('kept_for_conflict', 'kept_for_evidence',
              'kept_for_proof', 'kept_for_unknown'):
        assert cleanup[k] == []


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
        json.dumps({'task': '1', 'result': 'blocked', 'reason': '本轮失败',
                    'invocation': 'inv-test', 'dry_run': False,
                    'mergeable': False, 'run_dir': str(new.resolve())}),
        encoding='utf-8')
    done, stale = mod.find_done_tasks(str(tmp_path), with_blocked=True,
                                      expect_invocation='inv-test', run_dirs={'1': str(new)})
    assert done == {}
    # r9：身份项（dry_run / result / mergeable）前置后，blocked 记录在进候选池之前
    # 就被判否，reason 记的是"不是 done"，不再透传记录里的 reason 文案。
    # r10（第九轮审计）：r9 这里退化成"只要非空就过"，任何理由都能替它作证。
    # 显式 run-dir 模式下 blocked 是**合法执行结果**，不算记录损坏：它必须被
    # 如实回传成 result=blocked + 原样的 reason。两处都钉住，而不是只验非空。
    assert stale['1']['result'] == 'blocked'
    assert stale['1']['reason'] == '本轮失败'


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
                                      expect_invocation='inv-test', run_dirs={'1': str(bad)})
    assert done == {}
    assert '损坏' in stale['1']['reason']


def test_done_no_merge_is_not_mergeable(mod, monkeypatch, tmp_path):
    """A6：纯验证卡（done_no_merge）不是可合并成果，不进合并池。"""
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    d = runs / '1-ch1-x'
    d.mkdir(parents=True)
    (d / 'codex-channel.json').write_text(
        json.dumps({'task': '1', 'result': 'done_no_merge',
                    'invocation': 'inv-test', 'dry_run': False,
                    'mergeable': True, 'run_dir': str(d.resolve())}),
        encoding='utf-8')
    monkeypatch.setattr(mod, 'RUNS', runs)
    done, stale = mod.find_done_tasks(str(tmp_path), with_blocked=True,
                                      expect_invocation='inv-test', run_dirs={'1': str(d)})
    assert done == {}
    assert 'done_no_merge' in stale['1']['reason']


def test_merge_rejects_receipt_without_identity(mod, monkeypatch, tmp_path):
    """A8：wt 回执里 branch/target 缺失时不能记成功（此前只要求能解析 JSON）。"""
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    d = write_run(runs, '1')
    monkeypatch.setattr(mod, 'RUNS', runs)
    monkeypatch.setattr(mod, 'wt_merge',
                        lambda *a, **k: _FakeResult(0, json.dumps({'removed': False})))
    done, merged, failed, stale = mod.merge(str(tmp_path), tasks=['1'],
                                            target='main', expect_invocation='inv-test', run_dirs={'1': str(d)})
    assert merged == []
    assert failed[0]['task'] == '1'
    assert 'branch/target' in failed[0]['stderr']


def test_merge_rejects_when_git_shows_no_merge(mod, monkeypatch, tmp_path):
    """A8：wt 说成功、但 git 侧既非祖先又没推进主线 —— 按未合并处理。"""
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    d = write_run(runs, '1')
    monkeypatch.setattr(mod, 'RUNS', runs)
    payload = {'branch': 'gorch/1', 'target': 'main', 'removed': False}
    monkeypatch.setattr(mod, 'wt_merge',
                        lambda *a, **k: _FakeResult(0, json.dumps(payload)))
    def fake_git_out(args, *a, **k):
        # r10：rev-parse 必须给 tree（前态取证失败会提前停），其余一律 rc=1。
        if list(args)[:1] == ['rev-parse']:
            return (0, 'TREE-X')
        return (1, '')

    monkeypatch.setattr(mod, '_git_out', fake_git_out)
    monkeypatch.setattr(mod, '_ref_sha', lambda ref: 'same-sha')
    done, merged, failed, stale = mod.merge(str(tmp_path), tasks=['1'],
                                            target='main', expect_invocation='inv-test', run_dirs={'1': str(d)})
    assert merged == []
    assert '未证明本次合入' in failed[0]['stderr']


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
    payload = {'branch': 'refs/heads/gorch/1', 'target': 'refs/heads/main',
               'removed': False}
    monkeypatch.setattr(mod, 'wt_merge',
                        lambda *a, **k: _FakeResult(0, json.dumps(payload)))
    done, merged, failed, stale = mod.merge(str(tmp_path), tasks=['1'],
                                            target='main', expect_invocation='inv-test', run_dirs={'1': str(d)})
    assert failed == []
    assert merged[0]['task'] == '1'



# ============ 第五轮：7 条最小修复清单的回归验收（r6） ============

def test_find_done_tasks_blocks_broken_record_even_with_older_done(mod, monkeypatch, tmp_path):
    """Q3-1：损坏记录不再只收集而继续扫描——有旧 done 也必须阻断。"""
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    write_run(runs, '1', started_at='2026-11-09T00:00:00Z')
    bad = runs / '1-ch2-20261109T000100Z'
    bad.mkdir(parents=True)
    (bad / 'codex-channel.json').write_text('{ not json', encoding='utf-8')
    monkeypatch.setattr(mod, 'RUNS', runs)
    done, stale = mod.find_done_tasks(str(tmp_path), with_blocked=True)
    assert done == {}
    assert '损坏' in stale['1']['reason']


def test_find_done_tasks_explicit_empty_run_dirs_returns_nothing(mod, monkeypatch, tmp_path):
    """显式给空 run_dirs 时不能退回兜底扫描（否则等于没给）。"""
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    write_run(runs, '1')
    monkeypatch.setattr(mod, 'RUNS', runs)
    done, stale = mod.find_done_tasks(str(tmp_path), with_blocked=True, expect_invocation='inv-test', run_dirs={})
    assert done == {}
    assert '没有该任务的执行记录' in stale['1']['reason']


def test_find_done_tasks_rejects_unparsable_started_at(mod, monkeypatch, tmp_path):
    """Q3-3：started_at 解析不了即阻断，绝不退 mtime。"""
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    d = runs / '1-ch1-badtime'
    d.mkdir(parents=True)
    (d / 'codex-channel.json').write_text(json.dumps(
        {'task': '1', 'result': 'done', 'invocation': 'inv-x',
         'dry_run': False, 'mergeable': True,
         'run_dir': str(d.resolve()),
         'started_at': 'not-a-time'}), encoding='utf-8')
    monkeypatch.setattr(mod, 'RUNS', runs)
    done, stale = mod.find_done_tasks(str(tmp_path), with_blocked=True)
    assert done == {}
    assert 'started_at' in stale['1']['reason']


def test_find_done_tasks_rejects_empty_invocation(mod, monkeypatch, tmp_path):
    """Q3-3：invocation 为空无法唯一确定本次执行，阻断。"""
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    d = runs / '1-ch1-nosinv'
    d.mkdir(parents=True)
    (d / 'codex-channel.json').write_text(json.dumps(
        {'task': '1', 'result': 'done', 'invocation': '',
         'dry_run': False, 'mergeable': True,
         'run_dir': str(d.resolve()),
         'started_at': '2026-11-09T00:00:00Z'}), encoding='utf-8')
    monkeypatch.setattr(mod, 'RUNS', runs)
    done, stale = mod.find_done_tasks(str(tmp_path), with_blocked=True)
    assert done == {}
    assert 'invocation' in stale['1']['reason']


def test_find_done_tasks_rejects_tied_started_at(mod, monkeypatch, tmp_path):
    """Q3-3：并列 started_at（含同一 invocation 多条）一律阻断。"""
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    write_run(runs, '1', channel=1, started_at='2026-11-09T00:00:00Z',
              invocation='inv-1')
    write_run(runs, '1', channel=2, started_at='2026-11-09T00:00:00Z',
              invocation='inv-2')
    monkeypatch.setattr(mod, 'RUNS', runs)
    done, stale = mod.find_done_tasks(str(tmp_path), with_blocked=True)
    assert done == {}
    assert '并列' in stale['1']['reason']


def test_merge_rejects_preexisting_ancestor_without_source_move(mod, monkeypatch, tmp_path):
    """7.2-②：调用前就已祖先、源 tip 也没变——不认合入（未提交产出没进去）。"""
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    d = write_run(runs, '1')
    monkeypatch.setattr(mod, 'RUNS', runs)
    monkeypatch.setattr(mod, 'wt_merge', lambda *a, **k: _FakeResult(
        0, json.dumps({'branch': 'gorch/1', 'target': 'main'})))
    def fake_git_out(args, *a, **k):
        # r11（第十轮审计 E-5）：这条用例要验"调用前已是祖先且源未移动"这**一个**
        # 条件。若前后态 tree 相同，content_changed=False 也能让它失败，
        # 用例名与实际判据就对不上了。所以按 rev-parse 的实参区分前态/后态。
        if list(args)[:1] == ['rev-parse']:
            spec = list(args)[1]
            if spec.startswith('src-0'):
                return (0, 'TREE-SRC')
            if spec.startswith('main-1'):
                return (0, 'TREE-AFTER')
            return (0, 'TREE-BEFORE')
        return (0, '')

    monkeypatch.setattr(mod, '_git_out', fake_git_out)
    n = {'t': 0}

    def fake_sha(ref):
        if ref == 'main':
            n['t'] += 1
            return 'main-0' if n['t'] == 1 else 'main-1'
        return 'src-0'

    monkeypatch.setattr(mod, '_ref_sha', fake_sha)
    done, merged, failed, stale = mod.merge(str(tmp_path), tasks=['1'],
                                            target='main', expect_invocation='inv-test', run_dirs={'1': str(d)})
    assert merged == []
    assert '调用前已是祖先=True' in failed[0]['stderr']


def test_merge_rejects_unrelated_target_advance(mod, monkeypatch, tmp_path):
    """7.2-③：target 前进了但源分支不是祖先——无关进程推进不能替本任务作证。"""
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    d = write_run(runs, '1')
    monkeypatch.setattr(mod, 'RUNS', runs)
    monkeypatch.setattr(mod, 'wt_merge', lambda *a, **k: _FakeResult(
        0, json.dumps({'branch': 'gorch/1', 'target': 'main'})))
    # r11（第十轮审计 E-5）：显式钉住 SHA 序列，并让前后态 tree **不同**——
    # 否则 content_changed=False 也能让这条用例失败，"target 前进但源不是祖先"
    # 这个判据就没人验了。
    _n = {'main': 0}

    def fake_sha(ref):
        if ref == 'main':
            _n['main'] += 1
            return 'main-0' if _n['main'] == 1 else 'main-1'
        return 'src-0'

    monkeypatch.setattr(mod, '_ref_sha', fake_sha)

    def fake_git_out(args, *a, **k):
        if list(args)[:1] == ['rev-parse']:
            spec = list(args)[1]
            if spec.startswith('src-0'):
                return (0, 'TREE-SRC')
            if spec.startswith('main-1'):
                return (0, 'TREE-AFTER')
            return (0, 'TREE-BEFORE')
        return (1, '')

    monkeypatch.setattr(mod, '_git_out', fake_git_out)
    done, merged, failed, stale = mod.merge(str(tmp_path), tasks=['1'],
                                            target='main', expect_invocation='inv-test', run_dirs={'1': str(d)})
    assert merged == []
    assert 'is-ancestor(src_before) rc=1' in failed[0]['stderr']


def test_cleanup_rejects_invalid_schema_even_when_scene_clean(mod, monkeypatch, tmp_path):
    """7.3-5：回执 schema 不合法（缺 branch_outcome）就不认成功，即使三处已消失。"""
    import shutil

    write_task(tmp_path, 1)
    wt_root = tmp_path / 'wt'
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', wt_root)
    (wt_root / '1').mkdir(parents=True)

    def fake_remove(branch, force=False, delete_branch=False):
        shutil.rmtree(wt_root / '1', ignore_errors=True)
        return _FakeResult(0, json.dumps([{'kind': 'worktree', 'branch': branch}]))

    monkeypatch.setattr(mod, 'wt_remove', fake_remove)
    monkeypatch.setattr(mod, '_branch_state', lambda b: 'absent')
    monkeypatch.setattr(mod, '_worktree_registered', lambda p: False)
    removed, skipped = mod.cleanup(str(tmp_path))
    assert removed == []
    assert 'schema_ok=False' in skipped[0]['reason']


def test_run_all_does_not_accept_reason_text_as_done_no_merge(mod, monkeypatch, tmp_path):
    """第五轮新 fail-open①：blocked 记录 reason 含 done_no_merge 也不能算成功终态。"""
    write_task(tmp_path, 1)
    monkeypatch.setattr(mod, 'RUNS', tmp_path / 'runs')
    monkeypatch.setattr(mod, 'gate_check', lambda d: [{'task': '1', 'verdict': '可开工'}])
    monkeypatch.setattr(mod, 'provision', lambda d, tasks=None: ([], [], []))
    monkeypatch.setattr(mod, 'execute', lambda *a, **k: ([], []))
    monkeypatch.setattr(mod, 'merge', lambda *a, **k: ({}, [], [], {
        '1': {'run_record': 'r1',
              'reason': 'blocked 但文本里写了 done_no_merge 字样'}}))
    monkeypatch.setattr(mod, 'cleanup', lambda *a, **k: ([], []))
    prompts = tmp_path / 'prompts'
    prompts.mkdir()
    summary = mod.run_all(str(tmp_path), str(prompts))
    assert summary['steps']['merge']['verified_only'] == []
    assert summary['stopped_at'] != 'done'


def test_grant_manifest_refuses_contradictory_card(mod, monkeypatch, tmp_path):
    """7.3-6：卡片既声明写域又请求零改动——编排方拒绝签发，不猜哪边是真的。"""
    (tmp_path / '1.md').write_text(
        '---\nname: t1\nstatus: open\ndepends_on: []\nparallel: true\n'
        'conflicts_with: []\nwrites: docs/reports/\n'
        'no_change_allowed: true\n---\n# t1\n', encoding='utf-8')
    monkeypatch.setattr(mod, 'RUNS', tmp_path / 'runs')
    path, blocked = mod.grant_invocation(str(tmp_path), ['1'], 'inv-1', 'test-branch')
    assert path.is_file()
    assert blocked and '1' in blocked
    data = json.loads(path.read_text(encoding='utf-8'))
    assert data['tasks'] == {}
    assert data['granted_by'].startswith('batch_orchestrator')


def test_grant_manifest_records_write_scope_and_requests(mod, monkeypatch, tmp_path):
    """授权清单把卡片声明固化成 write_scope，并标 enforced。"""
    (tmp_path / '1.md').write_text(
        '---\nname: t1\nstatus: open\ndepends_on: []\nparallel: true\n'
        'conflicts_with: []\nwrites: docs/reports/, scripts/gorch/*.py\n---\n# t1\n',
        encoding='utf-8')
    monkeypatch.setattr(mod, 'RUNS', tmp_path / 'runs')
    path, blocked = mod.grant_invocation(str(tmp_path), ['1'], 'inv-2', 'test-branch')
    data = json.loads(path.read_text(encoding='utf-8'))
    g = data['tasks']['1']
    assert g['write_scope'] == ['docs/reports/', 'scripts/gorch/*.py']
    assert g['write_scope_enforced'] is True
    assert blocked == {}

# ============ r7：第六轮审计 4 条 ❌ + 8 条新问题闭环 ============

def test_utc_ts_requires_strict_utc(mod):
    """r7 #5：无时区与任何非零偏移都不算合法时间（此前 replace 成 UTC）。"""
    assert mod._utc_ts('2026-11-09T00:00:00Z')
    assert mod._utc_ts('2026-11-09T00:00:00+00:00')
    assert mod._utc_ts('2026-11-09T00:00:00') is None
    assert mod._utc_ts('2026-11-09T08:00:00+08:00') is None
    assert mod._utc_ts('2026-11-09') is None


def test_run_dirs_rejects_record_of_another_task(mod, monkeypatch, tmp_path):
    """r7 #5：显式 run-dir 必须核到记录身份，B 的 done 不得授权合并 A。"""
    write_task(tmp_path, 1)
    write_task(tmp_path, 2)
    runs = tmp_path / 'runs'
    b = write_run(runs, '2')
    monkeypatch.setattr(mod, 'RUNS', runs)
    done, stale = mod.find_done_tasks(str(tmp_path), with_blocked=True,
                                      expect_invocation='inv-test', run_dirs={'1': str(b)})
    assert done == {}
    assert '身份不符' in stale['1']['reason']


def test_run_dirs_rejects_record_without_invocation(mod, monkeypatch, tmp_path):
    """r7 #5：记录缺 invocation 就无法绑定本次调用，必须阻断。"""
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    d = runs / '1-ch1-x'
    d.mkdir(parents=True)
    (d / 'codex-channel.json').write_text(
        json.dumps({'task': '1', 'result': 'done',
                    'run_dir': str(d.resolve())}), encoding='utf-8')
    monkeypatch.setattr(mod, 'RUNS', runs)
    done, stale = mod.find_done_tasks(str(tmp_path), with_blocked=True,
                                      expect_invocation='inv-test', run_dirs={'1': str(d)})
    assert done == {}
    assert 'invocation' in stale['1']['reason']


def test_run_dirs_rejects_non_dict_root(mod, monkeypatch, tmp_path):
    """r7 #5：合法 JSON 但根节点不是对象，不能 get 崩、也不能当 done。"""
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    d = runs / '1-ch1-x'
    d.mkdir(parents=True)
    (d / 'codex-channel.json').write_text('[1, 2]', encoding='utf-8')
    monkeypatch.setattr(mod, 'RUNS', runs)
    done, stale = mod.find_done_tasks(str(tmp_path), with_blocked=True,
                                      expect_invocation='inv-test', run_dirs={'1': str(d)})
    assert done == {}
    assert '根节点' in stale['1']['reason']


def test_fallback_rejects_duplicate_invocation(mod, monkeypatch, tmp_path):
    """r7 #5：同一 invocation 多条记录 = 本次结果不唯一，兜底路径必须阻断。"""
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    write_run(runs, '1', channel=1, invocation='inv-1')
    write_run(runs, '1', channel=2, started_at='2026-11-09T00:00:01Z',
              invocation='inv-1')
    monkeypatch.setattr(mod, 'RUNS', runs)
    done, stale = mod.find_done_tasks(str(tmp_path), with_blocked=True)
    assert done == {}
    assert '多条' in stale['1']['reason']


def test_merge_rejects_when_pre_state_probe_fails(mod, monkeypatch, tmp_path):
    """r7 #4：前态取证失败（rc=128）不能折叠成「前态不是祖先」而放行。"""
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    d = write_run(runs, '1')
    monkeypatch.setattr(mod, 'RUNS', runs)
    monkeypatch.setattr(mod, 'wt_merge', lambda *a, **k: _FakeResult(
        0, json.dumps({'branch': 'gorch/1', 'target': 'main'})))
    monkeypatch.setattr(mod, '_git_out', lambda *a, **k: (128, ''))
    done, merged, failed, stale = mod.merge(str(tmp_path), tasks=['1'],
                                            target='main', expect_invocation='inv-test', run_dirs={'1': str(d)})
    assert merged == []
    assert '合并前取证失败' in failed[0]['stderr']


def test_merge_cli_requires_run_dir(mod, tmp_path):
    """r7：独立 merge 不给 --run-dir 直接拒（不再按历史 glob 授权）。"""
    write_task(tmp_path, 1)
    rc = mod.main(['merge', str(tmp_path), '--target', 'main',
                   '--invocation', 'inv-test'])
    assert rc == 2


def test_run_all_returns_gate_when_all_grants_refused(mod, monkeypatch, tmp_path):
    """r7 #8a：全部拒签时 _stop 必须在定义之后调用，不能抛 UnboundLocalError。"""
    write_task(tmp_path, 1)
    monkeypatch.setattr(mod, 'gate_check',
                        lambda d: [{'task': '1', 'verdict': '可开工'}])
    monkeypatch.setattr(mod, 'provision', lambda d, tasks=None: ([], [], []))
    mpath = tmp_path / 'inv.json'
    mpath.write_text(json.dumps({'manifest_version': 1, 'invocation': 'inv-x',
                                 'tasks': {}, 'blocked': {}}), encoding='utf-8')
    monkeypatch.setattr(mod, 'grant_invocation',
                        lambda *a, **k: (str(mpath), {'1'}))
    summary = mod.run_all(str(tmp_path), str(tmp_path))
    assert summary['stopped_at'] == 'gate'
    assert summary['steps']['merge']['failed'] == []
    assert '拒不签发' in summary['note'] or '拒绝签发' in summary['note']


def test_execute_does_not_restore_refused_tasks(mod, monkeypatch, tmp_path):
    """r7 #8b：编排方已剔除拒签任务时，execute 不能从 gate 重建全量 ready。"""
    for n in (1, 2):
        (tmp_path / f'{n}.md').write_text(
            f'---\nname: t{n}\nstatus: open\ndepends_on: []\nparallel: true\n'
            f'conflicts_with: []\n---\n# t{n}\n', encoding='utf-8')
    wt_root = tmp_path / 'wt'
    for n in (1, 2):
        (wt_root / str(n)).mkdir(parents=True)
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', wt_root)
    monkeypatch.setattr(mod, 'RUNS', tmp_path / 'runs')
    prompts = tmp_path / 'prompts'
    prompts.mkdir()
    for n in (1, 2):
        (prompts / f'{n}.txt').write_text('p', encoding='utf-8')
    seen = []

    class _P:
        returncode = 0

        def communicate(self):
            return ('', '')

    monkeypatch.setattr(mod.subprocess, 'Popen',
                        lambda cmd, **kw: (seen.append(cmd) or _P()))
    monkeypatch.setattr(mod, 'gate_check', lambda d: [
        {'task': '1', 'verdict': '可开工'}, {'task': '2', 'verdict': '可开工'}])
    manifest, blocked = mod.grant_invocation(str(tmp_path), ['1'], 'inv-x',
                                             'test-branch')
    assert not blocked
    results_rows, results = mod.execute(str(tmp_path), str(prompts),
                                        max_channels=2, manifest=manifest,
                                        tasks=['1'])
    tasks_run = [c[c.index('--task') + 1] for c in seen]
    assert tasks_run == ['1']
    assert results[0]['task'] == '1'

def test_cleanup_pre_absent_three_way_records_evidence(mod, monkeypatch, tmp_path):
    """r7 口径③：目录/登记/分支 三处都已不存在时，豁免要带独立回读证据。"""
    write_task(tmp_path, 1)
    wt_root = tmp_path / 'wt'
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', wt_root)
    monkeypatch.setattr(mod, '_branch_state', lambda b: 'absent')
    monkeypatch.setattr(mod, '_worktree_registered', lambda p: False)
    removed, skipped = mod.cleanup(str(tmp_path))
    assert skipped == []
    ev = removed[0]['evidence']
    assert ev['dir_state'] == 'absent'
    assert ev['branch_state'] == 'absent'
    assert ev['worktree_registered'] is False
    assert ev['exemption'] == 'pre_absent'
    assert set(ev) == {'dir_state', 'branch_state', 'worktree_registered',
                       'wt_returncode', 'exemption', 'readback'}


def test_cleanup_timeout_exemption_records_evidence(mod, monkeypatch, tmp_path):
    """r7 口径③：wt remove 超时但现场已空，豁免条目必须留下 rc 与三处回读值。"""
    write_task(tmp_path, 1)
    wt_root = tmp_path / 'wt'
    (wt_root / '1').mkdir(parents=True)
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', wt_root)
    def fake_remove(*a, **k):
        # 超时点之前内部已经删掉了目录，rc 却仍是非 0 —— 这正是要被豁免的形态
        (wt_root / '1').rmdir()
        return _FakeResult(-1, 'wt remove 超时')

    monkeypatch.setattr(mod, 'wt_remove', fake_remove)
    monkeypatch.setattr(mod, '_branch_state', lambda b: 'absent')
    monkeypatch.setattr(mod, '_worktree_registered', lambda p: False)
    removed, skipped = mod.cleanup(str(tmp_path))
    ev = removed[0]['evidence']
    assert ev['wt_returncode'] == -1
    assert ev['dir_state'] == 'absent'    # r11：目录已被 rmdir，三态不能反写
    assert ev['branch_state'] == 'absent'
    assert ev['worktree_registered'] is False
    assert ev['exemption'] == 'rc_zero_not_required'
    assert set(ev) == {'dir_state', 'branch_state', 'worktree_registered',
                       'wt_returncode', 'exemption', 'readback'}
# --- r8：授权收窄 / 记录身份 / 合并因果证明 / 生产者-消费者 ---

class _ChanProc:
    returncode = 0
    stdout = b''
    stderr = b''


class _ChanRes:
    returncode = 0
    stdout = ''
    stderr = ''


def test_provision_tasks_narrows_out_unauthorized(mod, monkeypatch, tmp_path):
    """N5：run_all 剔除拒签任务后，provision 不能再按 gate 全量为它们建现场。"""
    write_task(tmp_path, 1)
    write_task(tmp_path, 2)
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', tmp_path / 'wt')
    real_wt = tmp_path / 'real-wt'
    real_wt.mkdir()
    calls = []

    def fake_switch(branch, wt_path, create):
        calls.append(branch)
        return _FakeResult(0, json.dumps({'action': 'created', 'path': str(real_wt)}))

    monkeypatch.setattr(mod, 'wt_switch', fake_switch)
    rows, provisioned, skipped = mod.provision(str(tmp_path), tasks=['1'])
    assert [p['task'] for p in provisioned] == ['1']
    assert skipped == ['2']
    assert len(calls) == 1


def test_run_dirs_rejects_record_without_run_dir(mod, monkeypatch, tmp_path):
    """B5：run_dir 缺失不能再放行（r7 只在非空时才比对）。"""
    write_task(tmp_path, 1)
    d = write_run(tmp_path / 'runs', '1', extra={'run_dir': ''})
    monkeypatch.setattr(mod, 'RUNS', tmp_path / 'runs')
    with pytest.raises(SystemExit):
        mod.merge(str(tmp_path), tasks=['1'], expect_invocation='inv-test', run_dirs={'1': str(d)},
                  only_tasks=['1'], target='test-branch')


def test_run_dirs_rejects_run_dir_pointing_elsewhere(mod, monkeypatch, tmp_path):
    """B5：记录 run_dir 指向别的目录（同名基名）时必须判 stale。"""
    write_task(tmp_path, 1)
    other = tmp_path / 'other' / 'x'
    other.mkdir(parents=True)
    d = write_run(tmp_path / 'runs', '1', run_dir=str(other))
    monkeypatch.setattr(mod, 'RUNS', tmp_path / 'runs')
    done, stale = mod.find_done_tasks(str(tmp_path), with_blocked=True,
                                      expect_invocation='inv-test', run_dirs={'1': str(d)})
    assert done == {}
    assert 'run_dir' in stale['1']['reason']


def test_merge_proves_tree_equivalence_when_source_ref_gone(mod, monkeypatch, tmp_path):
    """N3 + 口径②：wt squash 后源分支被删，仍要能证明本次合入（B 级证据）。

    r7 用分支名查 merge-base、强制 src_moved，分支一被 wt 清掉就把真成功判 failed。
    """
    write_task(tmp_path, 1)
    d = write_run(tmp_path / 'runs', '1')
    monkeypatch.setattr(mod, 'RUNS', tmp_path / 'runs')
    seq = {'target': 0, 'branch': 0, 'tree': 0}

    def fake_ref(ref):
        if ref == 'gorch/1':
            seq['branch'] += 1
            return 'srcsha1' if seq['branch'] == 1 else ''
        seq['target'] += 1
        return 'target-a' if seq['target'] == 1 else 'target-b'

    monkeypatch.setattr(mod, '_ref_sha', fake_ref)

    def fake_git_out(args, *a, **k):
        if list(args)[:1] == ['merge-base']:
            return (0, '')                 # 调用前已是祖先 → ff 证据不成立
        if list(args)[:1] == ['rev-parse']:
            seq['tree'] += 1
            # r9：rev-parse 顺序是 ①源 tree ②target **前态** tree ③target 后态 tree。
            # 让前态与后态不同（内容真变了），源 tree 与后态相同 → 只有 tree 档成立。
            return (0, 'OTHER-TREE\n' if seq['tree'] == 2 else 'SAME-TREE\n')
        return (0, '')

    monkeypatch.setattr(mod, '_git_out', fake_git_out)
    monkeypatch.setattr(mod, 'wt_merge', lambda *a, **k: _FakeResult(
        0, json.dumps({'branch': 'gorch/1', 'target': 'test-branch',
                       'committed': True, 'squashed': True,
                       'rebased': False, 'removed': True})))
    done, merged, failed, stale = mod.merge(
        str(tmp_path), tasks=['1'], target='test-branch',
        expect_invocation='inv-test', run_dirs={'1': str(d)}, only_tasks=['1'])
    assert failed == []
    assert merged[0]['task'] == '1'
    assert merged[0]['proof'] == 'tree'
    assert merged[0]['source_ref_alive'] is False


def test_merge_falls_back_to_wt_receipt_after_uncommitted_squash(mod, monkeypatch, tmp_path):
    """口径② 的 C 级：未提交产出经 wt squash 后源码树与结果树本就不同，不能判死。"""
    write_task(tmp_path, 1)
    d = write_run(tmp_path / 'runs', '1')
    monkeypatch.setattr(mod, 'RUNS', tmp_path / 'runs')
    seq = {'target': 0, 'branch': 0, 'tree': 0}

    def fake_ref(ref):
        if ref == 'gorch/1':
            seq['branch'] += 1
            return 'srcsha1' if seq['branch'] == 1 else ''
        seq['target'] += 1
        return 'target-a' if seq['target'] == 1 else 'target-b'

    monkeypatch.setattr(mod, '_ref_sha', fake_ref)

    def fake_git_out(args, *a, **k):
        if list(args)[:1] == ['merge-base']:
            return (0, '')
        if list(args)[:1] == ['rev-parse']:
            seq['tree'] += 1
            # r9：前态 tree 与后态不同（内容变了），但源 tree 与后态 tree 不同，
            # 才能保证不误命中 tree 档、只剩 wt_receipt 兜底。
            if seq['tree'] == 1:
                return (0, 'TREE-A\n')
            return (0, 'TREE-SRC\n' if seq['tree'] == 2 else 'TREE-TOP\n')
        return (0, '')

    monkeypatch.setattr(mod, '_git_out', fake_git_out)
    monkeypatch.setattr(mod, 'wt_merge', lambda *a, **k: _FakeResult(
        0, json.dumps({'branch': 'gorch/1', 'target': 'test-branch',
                       'committed': True, 'squashed': True,
                       'rebased': False, 'removed': True})))
    done, merged, failed, stale = mod.merge(
        str(tmp_path), tasks=['1'], target='test-branch',
        expect_invocation='inv-test', run_dirs={'1': str(d)}, only_tasks=['1'])
    assert failed == []
    assert merged[0]['proof'] == 'wt_receipt'


def test_find_done_tasks_consumes_real_producer_record(mod, monkeypatch, tmp_path):
    """N1 的生产者-消费者闭环：真跑 channel 的 main()，其落盘记录必须可被消费。

    r7 的 write_run 由夹具人工补 invocation/run_dir，正好掩盖了生产端不写这些字段。
    这条用例只让 channel 走真实落盘逻辑，外部 Codex 与看板仍用桩。
    """
    ch_path = ROOT / 'scripts' / 'gorch' / 'codex_channel.py'
    spec = importlib.util.spec_from_file_location('codex_channel_consume', ch_path)
    ch = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ch)

    write_task(tmp_path, 1)
    inv = tmp_path / 'inv.json'
    inv.write_text(json.dumps({
        'manifest_version': 1, 'invocation': 'inv-prod', 'target': 'test-branch',
        'tasks': {'1': {'card': '1', 'write_scope': [], 'write_scope_source': 'test',
                        'write_scope_enforced': False, 'no_change_allowed': False,
                        'allow_non_repo': False, 'requests': {}, 'granted_by': 'test'}},
    }, ensure_ascii=False), encoding='utf-8')

    fake_exe = tmp_path / 'codex.exe'
    fake_exe.write_bytes(b'')
    monkeypatch.setattr(ch, 'resolve_codex_exe', lambda: str(fake_exe))
    monkeypatch.setattr(ch, 'run_codex', lambda *a, **k: (_ChanProc(), 1.0))
    monkeypatch.setattr(ch, 'kanban', lambda *a, **k: _ChanRes())
    state = {'n': 0}

    def fake_state(wd):
        state['n'] += 1
        return ('changed', ' M old.txt') if state['n'] == 1 else ('changed', ' M new.txt')

    monkeypatch.setattr(ch, 'worktree_state', fake_state)

    def fake_fp(wd, detail=None):
        body = str(detail or '').strip()
        if not body:
            return {'paths': {}, 'ignored': set(), 'rows': [], 'diff_sha': 'sha'}
        return {'paths': {body[2:]: 'sha-' + body[2:]}, 'ignored': set(),
                'rows': [], 'diff_sha': 'sha'}

    monkeypatch.setattr(ch, 'worktree_fingerprint', fake_fp)

    prompt = tmp_path / 'p.md'
    prompt.write_text('# 工单\n', encoding='utf-8')
    run_dir = tmp_path / 'run-prod'
    rc = ch.main(['--task', '1', '--prompt', str(prompt), '--workdir', str(tmp_path),
                  '--run-dir', str(run_dir), '--manifest', str(inv)])
    assert rc == 0

    monkeypatch.setattr(mod, 'RUNS', tmp_path / 'runs')
    # r9（N12）：生产者—消费者必须真的传本次 invocation，且值要与生产侧一致。
    done, stale = mod.find_done_tasks(str(tmp_path), with_blocked=True,
                                      expect_invocation='inv-prod',
                                      run_dirs={'1': str(run_dir)})
    assert done == {'1': str(run_dir / 'codex-channel.json')}
    assert '1' not in stale


# --- r9：run-record 身份严格化 / 锁互斥 / 三档 proof 负例（第八轮审计 N8–N12）---

def test_run_dirs_mode_requires_expected_invocation(mod, monkeypatch, tmp_path):
    """r9（N10）：显式 run-dir 模式不给本次 invocation 必须拒绝。

    r8 写成 `if expect_invocation and ...`：不给期望时退化成"只验非空"，
    任何历史 invocation 的 done 记录都能拿到合并授权。
    """
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    d = write_run(runs, '1')
    monkeypatch.setattr(mod, 'RUNS', runs)
    with pytest.raises(SystemExit) as ei:
        mod.find_done_tasks(str(tmp_path), with_blocked=True,
                            run_dirs={'1': str(d)})
    assert 'invocation' in str(ei.value)


def test_run_dirs_rejects_foreign_invocation(mod, monkeypatch, tmp_path):
    """r9：记录 invocation 不等于本次 → stale，不授权合并。"""
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    d = write_run(runs, '1', invocation='inv-other')
    monkeypatch.setattr(mod, 'RUNS', runs)
    with pytest.raises(SystemExit) as ei:
        mod.merge(str(tmp_path), tasks=['1'], target='main',
                  expect_invocation='inv-test', run_dirs={'1': str(d)})
    assert 'invocation' in str(ei.value)


def test_merge_rejects_record_without_strict_dry_run(mod, monkeypatch, tmp_path):
    """r9（N10）：dry_run 缺字段 / None / 0 都不等于 False，必须判 stale。"""
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    d = write_run(runs, '1', extra={'dry_run': None})
    monkeypatch.setattr(mod, 'RUNS', runs)
    with pytest.raises(SystemExit) as ei:
        mod.merge(str(tmp_path), tasks=['1'], target='main',
                  expect_invocation='inv-test', run_dirs={'1': str(d)})
    assert 'dry_run' in str(ei.value)


def test_merge_lock_is_exclusive(mod, monkeypatch, tmp_path):
    """r9（N8 / N12）：同一 target 的第二把锁必须 fail-closed。

    "锁不住就跑"会让两个 gorch 同时在取证窗口里推进同一个 target；这里直接验
    占用即 SystemExit，不是只测路径算得对不对。
    """
    monkeypatch.setattr(mod, 'RUNS', tmp_path / 'runs')
    first = mod._MergeLock('main')
    first.__enter__()
    try:
        with pytest.raises(SystemExit):
            mod._MergeLock('main').__enter__()
    finally:
        first.__exit__()


def test_merge_rejects_when_only_stale_proof_candidates(mod, monkeypatch, tmp_path):
    """r9（N9）：pre_anc 为真、源 tip 未动、tree 不同、wt 无动作 → 三档全不成立。

    r8 的 ff 档在 pre_anc=True 时只要求 src_moved（本用例不成立）；tree 档要求
    target tree == 旧 source tree（本用例刻意给不同 tree）；wt_receipt 要求回执
    里有 committed/squashed/rebased（本用例回执里没有）。三者都不成立时不能记合并。
    """
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    d = write_run(runs, '1')
    monkeypatch.setattr(mod, 'RUNS', runs)
    state = {'main': 'm0', 'gorch/1': 's0'}
    monkeypatch.setattr(mod, '_ref_sha', lambda ref: state.get(ref, ''))
    trees = iter(['tree-src', 'tree-top'])

    def fake_git(args, **kwargs):
        if list(args)[:1] == ['rev-parse']:
            return (0, next(trees, 'tree-third'))
        if list(args)[:1] == ['merge-base']:
            return (0, '')          # 调用前源已是祖先
        return (0, '')

    monkeypatch.setattr(mod, '_git_out', fake_git)

    def fake_merge(*a, **k):
        state['main'] = 'm1'        # 只有 target 前进，源 tip 不动
        return _FakeResult(0, json.dumps({'branch': 'gorch/1', 'target': 'main'}))

    monkeypatch.setattr(mod, 'wt_merge', fake_merge)
    done, merged, failed, stale = mod.merge(str(tmp_path), tasks=['1'], target='main',
                                            expect_invocation='inv-test',
                                            run_dirs={'1': str(d)})
    assert merged == []
    assert '未证明本次合入' in failed[0]['stderr']


def test_merge_cli_requires_invocation(mod, tmp_path):
    """r9（N10）：独立 merge 不给 --invocation 直接拒（argparse 必填）。

    argparse 的 required 是在 parse 阶段就 SystemExit(2)，不经过 main 的返回路径，
    所以这里断言退出码，而不是 `rc == 2`。
    """
    write_task(tmp_path, 1)
    with pytest.raises(SystemExit) as ei:
        mod.main(['merge', str(tmp_path), '--target', 'main'])
    assert ei.value.code == 2


# --- r10：跨进程锁 / 锁键归一 / 前态 tree 前置 / 宽松 JSON 类型（第九轮审计 E 段）---

def test_merge_lock_is_exclusive_across_processes(mod, monkeypatch, tmp_path):
    """r10（第九轮审计 E-7）：锁必须是**跨进程**互斥。

    r9 那条只证明"同进程第二个对象也被拒"——两句 `__enter__` 跑在同一句柄环境里，
    即使锁实现坏掉也可能碰巧通过。这里起真子进程持锁，父进程再抢必须 fail-closed。
    """
    monkeypatch.setattr(mod, 'RUNS', tmp_path / 'runs')
    orch_dir = str(pathlib.Path(mod.__file__).resolve().parent)
    runs_dir = str(tmp_path / 'runs')
    script = tmp_path / 'hold.py'
    script.write_text(
        'import sys, time, pathlib\n'
        'sys.path.insert(0, r"' + orch_dir + '")\n'
        'import batch_orchestrator as b\n'
        'b.RUNS = pathlib.Path(r"' + runs_dir + '")\n'
        'lk = b._MergeLock("main")\n'
        'lk.__enter__()\n'
        'print("HOLDING", flush=True)\n'
        'time.sleep(30)\n',
        encoding='utf-8')
    p = mod.subprocess.Popen([mod.sys.executable, str(script)],
                             stdout=mod.subprocess.PIPE, text=True)
    try:
        line = p.stdout.readline()
        assert 'HOLDING' in line, f'子进程没拿到锁：{line!r}'
        with pytest.raises(SystemExit):
            mod._MergeLock('main').__enter__()
    finally:
        p.kill()
        p.wait(timeout=10)


def test_merge_lock_key_normalizes_ref_prefix(mod, monkeypatch, tmp_path):
    """r10（第九轮审计）：`main` 与 `refs/heads/main` 是同一个 ref，必须是同一把锁。

    未归一化时两把锁文件名不同，两个 gorch 就能同时进入同一 target 的取证窗口。
    """
    monkeypatch.setattr(mod, 'RUNS', tmp_path / 'runs')
    short = mod._MergeLock('main')
    full = mod._MergeLock('refs/heads/main')
    assert short.path == full.path
    short.__enter__()
    try:
        with pytest.raises(SystemExit):
            full.__enter__()
    finally:
        short.__exit__()


def test_merge_does_not_run_wt_when_target_tree_unavailable(mod, monkeypatch, tmp_path):
    """r10（第九轮审计 E-5）：前态 tree 取不到必须在调 wt_merge **之前**停。

    否则真实合并已经发生（wt 还可能顺手清掉 source 分支），却因 content_changed
    恒假落进"未证明合入"的通用出口，把"取证失败"和"确实没合进去"混成一个结论。
    """
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    d = write_run(runs, '1')
    monkeypatch.setattr(mod, 'RUNS', runs)
    state = {'main': 'm0', 'gorch/1': 's0'}
    monkeypatch.setattr(mod, '_ref_sha', lambda ref: state.get(ref, ''))
    calls = {'wt': 0}

    def fake_git(args, **kwargs):
        if list(args)[:1] == ['rev-parse']:
            return (1, '')                  # tree 取不到
        if list(args)[:1] == ['merge-base']:
            return (0, '')
        return (0, '')

    monkeypatch.setattr(mod, '_git_out', fake_git)

    def fake_merge(*a, **k):
        calls['wt'] += 1
        state['main'] = 'm1'
        return _FakeResult(0, json.dumps({'branch': 'gorch/1', 'target': 'main'}))

    monkeypatch.setattr(mod, 'wt_merge', fake_merge)
    done, merged, failed, stale = mod.merge(str(tmp_path), tasks=['1'], target='main',
                                            expect_invocation='inv-test',
                                            run_dirs={'1': str(d)})
    assert merged == []
    assert calls['wt'] == 0
    assert '前态 tree 取不到' in failed[0]['stderr']
    assert failed[0]['kind'] == 'evidence_failure'


@pytest.mark.parametrize('field,value', [
    ('dry_run', None), ('dry_run', 0), ('dry_run', 1), ('dry_run', 'true'),
    ('mergeable', 0), ('mergeable', 1), ('mergeable', 'true'),
])
def test_merge_rejects_loose_json_types(mod, monkeypatch, tmp_path, field, value):
    """r10（第九轮审计 E-7）：`is not False` / `is not True` 必须挡住 0/1/"true"。

    只测 dry_run=None 证明不了这个判据——`0`、`1`、"true" 都是常见的手写值，
    一旦被 `==` 式比较放进来，等于把"严格布尔"降级成真值判断。
    """
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    d = write_run(runs, '1', extra={field: value})
    monkeypatch.setattr(mod, 'RUNS', runs)
    with pytest.raises(SystemExit) as ei:
        mod.merge(str(tmp_path), tasks=['1'], target='main',
                  expect_invocation='inv-test', run_dirs={'1': str(d)})
    assert field in str(ei.value)


# --- r11：第十轮审计可直改 1 / 3 / 4 / 5 / 6（E-1 E-3 E-4 E-5 E-6）---

def test_path_state_distinguishes_regular_file_and_unknown(mod, tmp_path, monkeypatch):
    """r11（第十轮审计 E-1）+ r12（第十一轮审计 E-1）：存在的**普通文件**不是
    absent；读不到才是 unknown；**link 对象**（含 dangling）一律 wrong_type。

    r10 用 `is_dir()` 两态，普通文件被记成 absent——worktree 路径被一个文件占据、
    branch 又已删、登记又已清时，cleanup 会把它记成"已清理"，尽管路径还在。
    r11 用 `os.stat` 仍跟随 symlink：dangling symlink 的目标不存在 → absent，而
    link 本体还在。r12 改用 lstat，link 一律 wrong_type。
    """
    import stat as _stat
    d = tmp_path / 'dir'
    d.mkdir()
    f = tmp_path / 'plain.txt'
    f.write_text('x', encoding='utf-8')
    assert mod._path_state(d) == 'exists'
    assert mod._path_state(f) == 'wrong_type'
    assert mod._path_state(tmp_path / 'nope') == 'absent'

    # 本机实测无 symlink 权限（`os.symlink` 抛 WinError 183/87），故 lstat 桩化。
    real_lstat = mod.os.lstat

    def link_only(p, *a, **k):
        if str(p) == str(f):
            return mod.os.stat_result((_stat.S_IFLNK | 0o777,) + (0,) * 9)
        return real_lstat(p, *a, **k)

    monkeypatch.setattr(mod.os, 'lstat', link_only)
    assert mod._path_state(f) == 'wrong_type'
    monkeypatch.undo()

    def boom(p, *a, **k):
        raise PermissionError(13, 'denied', str(p))

    monkeypatch.setattr(mod.os, 'lstat', boom)
    assert mod._path_state(f) == 'unknown'


def test_cleanup_rejects_regular_file_at_worktree_path(mod, monkeypatch, tmp_path):
    """r11（第十轮审计 E-1）：worktree 路径被普通文件占据时不得记 removed。"""
    write_task(tmp_path, 1)
    wt_root = tmp_path / 'wt'
    wt_root.mkdir()
    (wt_root / '1').write_text('not a worktree', encoding='utf-8')
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', wt_root)
    monkeypatch.setattr(mod, '_branch_state', lambda b: 'absent')
    monkeypatch.setattr(mod, '_worktree_registered', lambda p: False)
    removed, skipped = mod.cleanup(str(tmp_path))
    assert removed == []
    assert skipped and skipped[0]['partial'] is True


def test_cleanup_evidence_schema_is_uniform(mod, monkeypatch, tmp_path):
    """r11（第十轮审计 E-4/B7）：三个 removed 出口的 evidence key 集必须完全一致。"""
    wt_root = tmp_path / 'wt'
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', wt_root)
    monkeypatch.setattr(mod, '_branch_state', lambda b: 'absent')
    monkeypatch.setattr(mod, '_worktree_registered', lambda p: False)
    keys, outers = [], []

    b1 = tmp_path / 'b1'
    b1.mkdir()
    write_task(b1, 1)
    removed, _s = mod.cleanup(str(b1))
    assert removed and removed[0]['evidence']['exemption'] == 'pre_absent'
    keys.append(set(removed[0]['evidence']))
    outers.append(set(removed[0]))

    b2 = tmp_path / 'b2'
    b2.mkdir()
    write_task(b2, 1)
    (wt_root / '1').mkdir(parents=True)

    def fake_timeout(*a, **k):
        (wt_root / '1').rmdir()
        return _FakeResult(-1, 'wt remove 超时')

    monkeypatch.setattr(mod, 'wt_remove', fake_timeout)
    removed, _s = mod.cleanup(str(b2))
    assert removed and removed[0]['evidence']['exemption'] == 'rc_zero_not_required'
    keys.append(set(removed[0]['evidence']))
    outers.append(set(removed[0]))

    b3 = tmp_path / 'b3'
    b3.mkdir()
    write_task(b3, 1)
    (wt_root / '1').mkdir(parents=True)

    def fake_ok(*a, **k):
        (wt_root / '1').rmdir()
        return _FakeResult(0, json.dumps([{'kind': 'worktree', 'branch': 'gorch/1',
                                          'path': str(wt_root / '1'),
                                          'branch_outcome': 'deleted'}]))

    monkeypatch.setattr(mod, 'wt_remove', fake_ok)
    removed, _s = mod.cleanup(str(b3))
    assert removed and removed[0]['evidence']['exemption'] == 'rc_zero_confirmed'
    keys.append(set(removed[0]['evidence']))
    outers.append(set(removed[0]))

    assert keys[0] == keys[1] == keys[2]
    assert all('dir_state' in k and 'dir_exists' not in k for k in keys)
    # r12（第十一轮审计 E-6，中）：r11 只统一了 evidence 内层。按
    # `removed[0]['schema_ok']` 读的 consumer 在 pre_absent / rc 非零两个出口会
    # KeyError——removed 条目**外层**也必须同 key 集，缺值显式 None / 空串。
    assert outers[0] == outers[1] == outers[2]
    need = {'result', 'schema_ok', 'wt_remove_rc', 'raw_tail'}
    assert all(need <= k for k in outers)


def test_merge_lock_keys_do_not_collide_for_distinct_refs(mod, monkeypatch, tmp_path):
    """r11（第十轮审计 E-3/C-3）：`re.sub` 会把 `feature/a` 与 `feature_a` 压成同一
    个锁文件名 → 两个不同 target 互相阻塞（假互斥）。摘要必须让它们分开。
    """
    monkeypatch.setattr(mod, 'RUNS', tmp_path / 'runs')
    a = mod._MergeLock('feature/a')
    b = mod._MergeLock('feature_a')
    assert a.path != b.path
    assert mod._MergeLock('main').path == mod._MergeLock('refs/heads/main').path


def test_merge_lock_distinct_targets_do_not_block(mod, monkeypatch, tmp_path):
    """r11（第十轮审计 E-3）：不同 target 的两把锁必须能同时持有（不假互斥）。"""
    monkeypatch.setattr(mod, 'RUNS', tmp_path / 'runs')
    l1 = mod._MergeLock('feature/a')
    l2 = mod._MergeLock('feature_a')
    l1.__enter__()
    try:
        l2.__enter__()
        l2.__exit__()
    finally:
        l1.__exit__()


def test_run_all_keeps_evidence_failure_out_of_conflict(mod, monkeypatch, tmp_path):
    """r11（第十轮审计 E-6）：前态 tree 取不到 = 取证失败、未执行合并，不能写进
    kept_for_conflict——那会让调用方按冲突流程去 abort/solve rebase。
    """
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    d1 = write_run(runs, '1')
    monkeypatch.setattr(mod, 'RUNS', runs)
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', tmp_path / 'wt')
    prompts = tmp_path / 'prompts'
    prompts.mkdir()
    (prompts / '1.txt').write_text('p', encoding='utf-8')
    monkeypatch.setattr(mod, 'gate_check', lambda d: [{'task': '1', 'verdict': '可开工'}])
    monkeypatch.setattr(mod, 'provision', lambda d, tasks=None: ([], [], []))
    monkeypatch.setattr(mod, 'execute', lambda *a, **k: ([], [
        {'task': '1', 'channel': 1, 'returncode': 0, 'run_dir': str(d1)}]))
    monkeypatch.setattr(mod, '_git_out', lambda args, *a, **k: (
        (1, '') if list(args)[:1] == ['rev-parse'] else (0, '')))
    cleaned = []
    monkeypatch.setattr(mod, 'cleanup', lambda *a, **k: (cleaned.append(1) or ([], [])))
    summary = mod.run_all(str(tmp_path), str(prompts), max_channels=1,
                          invocation='inv-test')
    assert summary['stopped_at'] == 'merge'
    assert summary['steps']['cleanup']['kept_for_conflict'] == []
    assert summary['steps']['cleanup']['kept_for_evidence'] == ['1']
    assert cleaned == []


def test_cleanup_treats_any_symlink_as_wrong_type(mod, monkeypatch, tmp_path):
    """r12（第十一轮审计 E-1，高）：`os.stat` 跟随 symlink，dangling symlink 的
    目标不存在 → FileNotFoundError → 落 absent，而 link 对象本身还在，于是
    "worktree 路径被 dangling symlink 占据 + branch absent + registration false"
    仍会被记 removed。改用 lstat 后，任何 link 都必须落 wrong_type。

    本机实测无 symlink 权限（`os.symlink` 抛 WinError 183/87），故 lstat 桩化；
    link→file / link→dir / dangling 在 lstat 层是同一种 st_mode，行为一致。
    """
    import stat as _stat
    write_task(tmp_path, 1)
    wt_root = tmp_path / 'wt'
    wt_root.mkdir()
    placeholder = wt_root / '1'
    placeholder.write_text('not a worktree', encoding='utf-8')
    real_lstat = mod.os.lstat

    def fake_lstat(p, *a, **k):
        if str(p) == str(placeholder):
            return mod.os.stat_result((_stat.S_IFLNK | 0o777,) + (0,) * 9)
        return real_lstat(p, *a, **k)

    monkeypatch.setattr(mod.os, 'lstat', fake_lstat)
    # r13（第十二轮审计 C 段：本用例原可假通过）：只把 lstat 桩成 S_IFLNK 时，
    # 若实现退回 r11 的 `os.stat`，普通文件同样得 wrong_type，用例照样绿。
    # 这里把 `os.stat` 也桩成"dangling 会抛 FileNotFoundError"——真实 dangling
    # link 走 stat 就是这个行为；实现若回退，`_path_state` 会得到 absent，
    # cleanup 就会把该路径记 removed，两条断言立刻变红。
    real_stat = mod.os.stat

    def dangling_stat(p, *a, **k):
        if str(p) == str(placeholder):
            raise FileNotFoundError(2, 'no such file', str(p))
        return real_stat(p, *a, **k)

    monkeypatch.setattr(mod.os, 'stat', dangling_stat)
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', wt_root)
    monkeypatch.setattr(mod, '_branch_state', lambda b: 'absent')
    monkeypatch.setattr(mod, '_worktree_registered', lambda p: False)
    removed, skipped = mod.cleanup(str(tmp_path))
    assert removed == []
    assert skipped and skipped[0]['partial'] is True
    # 桩下 `os.stat` 抛 FileNotFoundError（dangling link 的真实行为）。若实现退回
    # r11 的 `os.stat`，这里会得到 absent —— cleanup 就会把该路径记 removed，
    # 上面两条断言立刻变红；因此本用例不再能"改不改探针都绿"。
    assert mod._path_state(str(placeholder)) == 'wrong_type'


def test_merge_records_not_attempted_after_failure(mod, monkeypatch, tmp_path):
    """r12（第十一轮审计 E-5，中）：首条失败即 break，后续任务既不在 merged 也不在
    failed，现场归属不明。attempted / not_attempted 必须由 merge 如实回传。
    """
    runs = tmp_path / 'runs'
    runs.mkdir()
    monkeypatch.setattr(mod, 'RUNS', runs)
    done = {t: {'task': t, 'result': 'done'} for t in ('1', '2', '3')}
    monkeypatch.setattr(mod, 'find_done_tasks', lambda *a, **k: (done, {}))
    monkeypatch.setattr(mod, '_ref_sha', lambda ref: 'a' * 40)

    def fake_git(args, *a, **k):
        if list(args)[:1] == ['rev-parse']:
            return 1, ''
        return 0, ''

    monkeypatch.setattr(mod, '_git_out', fake_git)
    trace = {}
    _done, merged, failed, stale = mod.merge(str(tmp_path), tasks=['1', '2', '3'],
                                             target='main', trace=trace)
    assert merged == []
    assert [f['task'] for f in failed] == ['1']
    assert failed[0]['kind'] == 'evidence_failure'
    assert trace['attempted'] == ['1']
    assert trace['not_attempted'] == ['2', '3']


def _run_all_with_merge_failure(mod, monkeypatch, tmp_path, entry):
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    d1 = write_run(runs, '1')
    monkeypatch.setattr(mod, 'RUNS', runs)
    monkeypatch.setattr(mod, 'WORKTREE_ROOT', tmp_path / 'wt')
    prompts = tmp_path / 'prompts'
    prompts.mkdir()
    (prompts / '1.txt').write_text('p', encoding='utf-8')
    monkeypatch.setattr(mod, 'gate_check', lambda d: [{'task': '1', 'verdict': '可开工'}])
    monkeypatch.setattr(mod, 'provision', lambda d, tasks=None: ([], [], []))
    monkeypatch.setattr(mod, 'execute', lambda *a, **k: ([], [
        {'task': '1', 'channel': 1, 'returncode': 0, 'run_dir': str(d1)}]))
    monkeypatch.setattr(mod, 'find_done_tasks',
                        lambda *a, **k: ({'1': {'task': '1', 'result': 'done'}}, {}))

    def fake_merge(*a, **k):
        k.get('trace', {}).update({'attempted': ['1'], 'not_attempted': []})
        return {}, [], [entry], {}

    monkeypatch.setattr(mod, 'merge', fake_merge)
    cleaned = []
    monkeypatch.setattr(mod, 'cleanup', lambda *a, **k: (cleaned.append(1) or ([], [])))
    summary = mod.run_all(str(tmp_path), str(prompts), max_channels=1,
                          invocation='inv-test')
    assert summary['stopped_at'] == 'merge'
    assert cleaned == []
    return summary


def test_run_all_keeps_proof_failure_out_of_conflict(mod, monkeypatch, tmp_path):
    """r12（第十一轮审计 E-4，中）：proof_failure 的现场通常没有 rebase 可 abort，
    不能并进 kept_for_conflict 把下游引去解决不存在的冲突。
    """
    summary = _run_all_with_merge_failure(
        mod, monkeypatch, tmp_path, {'task': '1', 'kind': 'proof_failure'})
    cleanup = summary['steps']['cleanup']
    assert cleanup['kept_for_proof'] == ['1']
    assert cleanup['kept_for_conflict'] == []
    assert cleanup['kept_for_evidence'] == []
    assert cleanup['kept_for_unknown'] == []


def test_run_all_keeps_unknown_kind_separate(mod, monkeypatch, tmp_path):
    """r12：未知 kind（failed 里缺 kind）必须单列并 fail-closed，不得默认归冲突。"""
    summary = _run_all_with_merge_failure(
        mod, monkeypatch, tmp_path, {'task': '1'})
    cleanup = summary['steps']['cleanup']
    assert cleanup['kept_for_unknown'] == ['1']
    assert cleanup['kept_for_conflict'] == []
    assert cleanup['kept_for_proof'] == []


def test_merge_receipt_identity_mismatch_is_proof_failure(mod, monkeypatch, tmp_path):
    """r12（第十一轮审计 E-3，高）：回执里的 branch/target 与请求不一致同样是**业务
    失败**，不再 raise SystemExit——否则调用方只看到进程退出码，拿不到"哪个任务、
    哪种类别、现场有没有被动过"，也无法区分"编程错误"与"回执不成立"。
    """
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    d = write_run(runs, '1')
    monkeypatch.setattr(mod, 'RUNS', runs)
    monkeypatch.setattr(mod, '_ref_sha', lambda ref: 'a' * 40)

    def fake_git(args, *a, **k):
        if list(args)[:1] == ['rev-parse']:
            return 0, 't0'
        if list(args)[:1] == ['merge-base']:
            return 1, ''
        return 0, ''

    monkeypatch.setattr(mod, '_git_out', fake_git)
    monkeypatch.setattr(mod, 'wt_merge', lambda *a, **k: _FakeResult(
        0, json.dumps({'branch': 'other/branch', 'target': 'main'})))
    _done, merged, failed, stale = mod.merge(
        str(tmp_path), tasks=['1'], target='main', expect_invocation='inv-test',
        run_dirs={'1': str(d)})
    assert merged == []
    assert [f['task'] for f in failed] == ['1']
    assert failed[0]['kind'] == 'proof_failure'
    assert '不一致' in failed[0]['stderr']


def test_merge_target_sha_missing_is_evidence_failure(mod, monkeypatch, tmp_path):
    """r13（第十二轮审计 C 段：五个结构化出口里 3 个没有回归用例）：target 的
    commit sha 取不到时，必须在调 `wt_merge` **之前**结构化停（evidence_failure），
    且 trace 仍记为"尝试过"— 现场没动过，可直接重试。
    """
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    d = write_run(runs, '1')
    monkeypatch.setattr(mod, 'RUNS', runs)
    monkeypatch.setattr(mod, '_ref_sha', lambda ref: '')
    calls = []
    monkeypatch.setattr(mod, 'wt_merge', lambda *a, **k: calls.append(a))
    trace = {}
    _done, merged, failed, _stale = mod.merge(
        str(tmp_path), tasks=['1'], target='main', expect_invocation='inv-test',
        run_dirs={'1': str(d)}, trace=trace)
    assert calls == []                       # 未执行合并
    assert merged == []
    assert failed[0]['kind'] == 'evidence_failure'
    assert '未执行合并' in failed[0]['stderr']
    assert trace['attempted'] == ['1']
    assert trace['not_attempted'] == []


def test_merge_receipt_not_object_is_proof_failure(mod, monkeypatch, tmp_path):
    """r13（第十二轮审计 C 段）：回执解析出的是标量/无 dict 的数组 → `proof_failure`
    （wt 已跑、现场可能已动），不能被当成"没合并"放过。
    """
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    d = write_run(runs, '1')
    monkeypatch.setattr(mod, 'RUNS', runs)
    monkeypatch.setattr(mod, '_ref_sha', lambda ref: 'a' * 40)

    def fake_git(args, *a, **k):
        if list(args)[:1] == ['rev-parse']:
            return 0, 't0'
        if list(args)[:1] == ['merge-base']:
            return 1, ''
        return 0, ''

    monkeypatch.setattr(mod, '_git_out', fake_git)
    monkeypatch.setattr(mod, 'wt_merge', lambda *a, **k: _FakeResult(0, '[1, 2, 3]'))
    _done, merged, failed, _stale = mod.merge(
        str(tmp_path), tasks=['1'], target='main', expect_invocation='inv-test',
        run_dirs={'1': str(d)})
    assert merged == []
    assert failed[0]['kind'] == 'proof_failure'
    assert '不是对象' in failed[0]['stderr']


def test_merge_receipt_target_mismatch_is_proof_failure(mod, monkeypatch, tmp_path):
    """r13（第十二轮审计 C 段）：回执 target 与请求不一致（branch 一致）也必须
    `proof_failure`——此前只测了 branch 不一致那一支。
    """
    write_task(tmp_path, 1)
    runs = tmp_path / 'runs'
    d = write_run(runs, '1')
    monkeypatch.setattr(mod, 'RUNS', runs)
    monkeypatch.setattr(mod, '_ref_sha', lambda ref: 'a' * 40)

    def fake_git(args, *a, **k):
        if list(args)[:1] == ['rev-parse']:
            return 0, 't0'
        if list(args)[:1] == ['merge-base']:
            return 1, ''
        return 0, ''

    monkeypatch.setattr(mod, '_git_out', fake_git)
    monkeypatch.setattr(mod, 'wt_merge', lambda *a, **k: _FakeResult(
        0, json.dumps({'branch': 'gorch/1', 'target': 'other'})))
    _done, merged, failed, _stale = mod.merge(
        str(tmp_path), tasks=['1'], target='main', expect_invocation='inv-test',
        run_dirs={'1': str(d)})
    assert merged == []
    assert failed[0]['kind'] == 'proof_failure'
    assert '目标与请求不一致' in failed[0]['stderr']


def test_merge_empty_targets_resets_trace(mod, monkeypatch, tmp_path):
    """r13（第十二轮审计 E1-3）：空批次早退时 trace 必须归零。调用方复用同一个
    dict 时，上一轮的 attempted / not_attempted 不能被当成本轮结果读走。
    """
    runs = tmp_path / 'runs'
    runs.mkdir()
    monkeypatch.setattr(mod, 'RUNS', runs)
    monkeypatch.setattr(mod, 'find_done_tasks', lambda *a, **k: ({}, {}))
    trace = {'attempted': ['old'], 'not_attempted': ['old2']}
    _done, merged, failed, _stale = mod.merge(str(tmp_path), tasks=[], trace=trace)
    assert merged == [] and failed == []
    assert trace['attempted'] == []
    assert trace['not_attempted'] == []
