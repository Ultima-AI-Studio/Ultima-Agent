"""wt merge 超时的现场判断。

教训来源（2026-11-09 S7 真跑）：wt merge 在大仓库里超过 180s 被判定超时，
但 wt 其实已经走到第 7 步 cleanup——分支和 worktree 都被删了，主线却没进账，
`def92006` 变成孤儿提交，只能靠 cherry-pick 找回。所以超时后的结论必须查现场，
不能一律写"未变更"。
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
