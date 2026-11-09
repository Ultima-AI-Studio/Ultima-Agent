"""S7 交接点（bridge）验收用例。

bridge 的职责边界是「只搬不解析」：把审议链的 stages 产物登记成交接单，
不反解自然语言工单。本测试锁住这条边界，防止有人后来偷偷加回启发式解析。
"""
import importlib.util
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
ORCH = ROOT / 'scripts' / 'gorch' / 'batch_orchestrator.py'


@pytest.fixture
def mod():
    spec = importlib.util.spec_from_file_location('batch_orchestrator_bridge', ORCH)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def write_stage(run_dir, name, verdict='completed', model='deepseek-chat'):
    stages = pathlib.Path(run_dir) / 'stages'
    stages.mkdir(parents=True, exist_ok=True)
    payload = {'stage': name, 'verdict': verdict, 'model': model,
               'response': f'{name} output'}
    (stages / f'{name}.json').write_text(
        json.dumps(payload, ensure_ascii=False), encoding='utf-8')


def test_bridge_copies_evidence_and_writes_manifest(mod, tmp_path):
    run_dir = tmp_path / 'run'
    batch_dir = tmp_path / 'batch'
    write_stage(run_dir, 'decompose')
    write_stage(run_dir, 'work_order')

    manifest = mod.bridge(run_dir, batch_dir)

    handoff = batch_dir / mod.HANDOFF_DIRNAME
    assert (handoff / 'decompose.json').is_file()
    assert (handoff / 'work_order.json').is_file()
    assert (handoff / 'manifest.json').is_file()
    assert set(manifest['stages']) == {'decompose', 'work_order'}
    assert manifest['stages']['work_order']['verdict'] == 'completed'
    assert manifest['stages']['work_order']['model'] == 'deepseek-chat'
    # 没有工单 md 时如实说还不能开工，而不是假装交接成功。
    assert manifest['ready_to_gate'] is False


def test_bridge_sees_task_files_when_owner_puts_them(mod, tmp_path):
    run_dir = tmp_path / 'run'
    batch_dir = tmp_path / 'batch'
    write_stage(run_dir, 'work_order')
    batch_dir.mkdir(parents=True)
    (batch_dir / 'T1.md').write_text(
        'name: T1\nstatus: open\ndepends_on: []\nparallel: true\n'
        'conflicts_with: []\n---\n# T1\n', encoding='utf-8')

    manifest = mod.bridge(run_dir, batch_dir)
    assert manifest['ready_to_gate'] is True
    assert manifest['task_files'] == ['T1.md']


def test_bridge_blocks_incomplete_stage(mod, tmp_path):
    """审议没跑完就交接 = 执行端拿半成品开工，必须拦住。"""
    run_dir = tmp_path / 'run'
    write_stage(run_dir, 'decompose', verdict='blocked')
    with pytest.raises(SystemExit) as exc:
        mod.bridge(run_dir, tmp_path / 'batch')
    assert 'blocked' in str(exc.value)


def test_bridge_blocks_missing_stage_verdict(mod, tmp_path):
    run_dir = tmp_path / 'run'
    stages = run_dir / 'stages'
    stages.mkdir(parents=True)
    (stages / 'work_order.json').write_text('{"stage": "work_order"}', encoding='utf-8')
    with pytest.raises(SystemExit) as exc:
        mod.bridge(run_dir, tmp_path / 'batch')
    assert '缺失' in str(exc.value)


def test_bridge_without_stages_dir_fails(mod, tmp_path):
    with pytest.raises(SystemExit):
        mod.bridge(tmp_path / 'nope', tmp_path / 'batch')


def test_bridge_rejects_broken_json(mod, tmp_path):
    run_dir = tmp_path / 'run'
    stages = run_dir / 'stages'
    stages.mkdir(parents=True)
    (stages / 'work_order.json').write_text('{ oops', encoding='utf-8')
    with pytest.raises(SystemExit):
        mod.bridge(run_dir, tmp_path / 'batch')
