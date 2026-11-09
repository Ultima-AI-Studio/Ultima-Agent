"""wt merge 超时的现场判断 + 合并目标必须显式。

教训来源一（2026-11-09 S7 真跑）：wt merge 在大仓库里超过 180s 被判定超时，
但 wt 其实已经走到第 7 步 cleanup——分支和 worktree 都被删了，主线却没进账，
`def92006` 变成孤儿提交，只能靠 cherry-pick 找回。所以超时后的结论必须查现场，
不能一律写"未变更"。

教训来源二（同日收口）：wt merge 的 TARGET 缺省是 default branch（本仓库为 main），
而施工在 codex/voice-fsmn-new-path 上。上一单其实合进了 main（squash 成 d1e51eb3）、
工作分支没合，被误判成"没合入"；再合第二个分支时 main 已有同名文件，直接 add/add
冲突。target 必须显式给，不能靠 wt 的默认值。
"""
import importlib.util
import pathlib
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
ORCH = ROOT / 'scripts' / 'gorch' / 'batch_orchestrator.py'


@pytest.fixture
def mod():
    spec = importlib.util.spec_from_file_location('batch_orchestrator_merge_timeout', ORCH)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _boom(*a, **k):
    raise subprocess.TimeoutExpired(cmd='wt merge', timeout=600)


def test_merge_timeout_with_branch_gone_says_branch_missing(mod, monkeypatch):
    """分支已被 wt 删掉：必须明说"可能已删分支但没合入"，不许写成未变更。"""
    monkeypatch.setattr(mod, '_branch_exists', lambda b: False)
    monkeypatch.setattr(mod.subprocess, 'run', _boom)
    with pytest.raises(SystemExit) as exc:
        mod.wt_merge('gorch/T1')
    msg = str(exc.value)
    assert '已不存在' in msg
    assert '不要假定无改动' in msg


def test_merge_timeout_with_branch_alive_says_main_untouched(mod, monkeypatch):
    monkeypatch.setattr(mod, '_branch_exists', lambda b: True)
    monkeypatch.setattr(mod.subprocess, 'run', _boom)
    with pytest.raises(SystemExit) as exc:
        mod.wt_merge('gorch/T1')
    msg = str(exc.value)
    assert '仍存在' in msg
    assert '主线应未变更' in msg


def test_merge_timeout_budget_is_larger_than_switch(mod):
    """merge 比 switch 慢一个量级（大仓库 git status 就 90s+），预算必须分开。"""
    assert mod.MERGE_TIMEOUT > mod.WT_TIMEOUT
    assert mod.MERGE_TIMEOUT >= 600


def test_branch_exists_reads_git_branch_list(mod, monkeypatch):
    class _R:
        def __init__(self, out):
            self.stdout = out

    monkeypatch.setattr(mod.subprocess, 'run', lambda *a, **k: _R('  gorch/T1\n'))
    assert mod._branch_exists('gorch/T1') is True
    monkeypatch.setattr(mod.subprocess, 'run', lambda *a, **k: _R('\n'))
    assert mod._branch_exists('gorch/T1') is False


# --- 合并目标必须是"编排所在分支"，不是 wt 默认的 main -----------------------

class _Res:
    def __init__(self, out='', rc=0, err=''):
        self.stdout = out
        self.stderr = err
        self.returncode = rc


def test_current_branch_reads_head(mod, monkeypatch):
    captured = {}

    def fake_run(cmd, **kw):
        captured['cmd'] = cmd
        return _Res('codex/voice-fsmn-new-path\n')

    monkeypatch.setattr(mod.subprocess, 'run', fake_run)
    assert mod._current_branch() == 'codex/voice-fsmn-new-path'
    assert '--abbrev-ref' in captured['cmd']


def test_merge_passes_target_explicitly_to_wt(mod, monkeypatch):
    """merge() 必须把 target 交给 wt，不能靠 wt 的 default branch 缺省。"""
    captured = {}

    def fake_wt_merge(branch, target=None):
        captured['branch'] = branch
        captured['target'] = target
        return _Res('{"branch":"%s"}' % branch)

    monkeypatch.setattr(mod, 'find_done_tasks', lambda d: {'T1': 'run.json'})
    monkeypatch.setattr(mod, '_current_branch',
                        lambda: 'codex/voice-fsmn-new-path')
    monkeypatch.setattr(mod, 'wt_merge', fake_wt_merge)
    monkeypatch.setattr(mod, '_parse_braced_json', lambda s: {'branch': 'T1'})

    mod.merge('batch', tasks=['T1'])
    assert captured == {'branch': 'gorch/T1',
                        'target': 'codex/voice-fsmn-new-path'}


def test_merge_explicit_target_overrides_current(mod, monkeypatch):
    captured = {}

    def fake_wt_merge(branch, target=None):
        captured['target'] = target
        return _Res('{}')

    monkeypatch.setattr(mod, 'find_done_tasks', lambda d: {'T1': 'run.json'})
    monkeypatch.setattr(mod, '_current_branch', lambda: 'codex/voice-fsmn-new-path')
    monkeypatch.setattr(mod, 'wt_merge', fake_wt_merge)
    monkeypatch.setattr(mod, '_parse_braced_json', lambda s: {})

    mod.merge('batch', tasks=['T1'], target='main')
    assert captured['target'] == 'main'


def test_merge_refuses_detached_head(mod, monkeypatch):
    monkeypatch.setattr(mod, 'find_done_tasks', lambda d: {'T1': 'run.json'})
    monkeypatch.setattr(mod, '_current_branch', lambda: 'HEAD')
    with pytest.raises(SystemExit) as exc:
        mod.merge('batch', tasks=['T1'])
    assert 'detached HEAD' in str(exc.value)


def test_wt_merge_puts_target_before_branch_flag(mod, monkeypatch):
    """wt 用法是 `merge [TARGET] --branch <源>`；顺序错了 source/target 会互换。"""
    captured = {}

    def fake_run(cmd, **kw):
        captured['cmd'] = cmd
        return _Res('{}')

    monkeypatch.setattr(mod.subprocess, 'run', fake_run)
    mod.wt_merge('gorch/T1', target='codex/voice-fsmn-new-path')

    cmd = captured['cmd']
    assert cmd[cmd.index('merge') + 1] == 'codex/voice-fsmn-new-path'
    assert cmd[cmd.index('--branch') + 1] == 'gorch/T1'
    assert '--format' in cmd and 'json' in cmd
