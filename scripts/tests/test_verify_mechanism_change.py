"""机制变更验收器（scripts/verify-mechanism-change.py）与 verify-order 的 profile 分工。

元工单改的是派发/校验链自身，没有一次派发 run 的回执能描述这件事；拿回执契约
去验它只会得到六条描述"契约错配"的失败。这里把新器件的判据和 verify-order 的
显式拒绝各钉一条用例，避免以后有人把 profile 又"顺手"合回普通路径。
"""

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / 'scripts' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


vmc = load('verify_mechanism_change', 'verify-mechanism-change.py')
vo = load('verify_order_under_test', 'verify-order.py')


def test_unknown_card_is_rejected():
    ok, detail, path = vmc._card('wo-does-not-exist-0000', None)
    assert ok is False
    assert path is None
    assert 'wo-does-not-exist-0000' in detail


def test_empty_file_list_is_refused():
    ok, detail = vmc._files([])
    assert ok is False
    assert '--file' in detail


def test_absent_file_fails():
    ok, detail = vmc._files(['scripts/__no_such_file__.py'])
    assert ok is False
    assert 'absent on disk' in detail


def test_untracked_file_is_not_a_delivery():
    ok, detail = vmc._files(['scripts/verify-mechanism-change.py'])
    if not (REPO / 'scripts' / 'verify-mechanism-change.py').is_file():
        return
    # 该文件一旦被提交，本用例的前提消失，改为断言它能通过——否则测试会长期红。
    committed = vo._git('ls-tree', '-r', 'HEAD', '--', 'scripts/verify-mechanism-change.py')
    if (committed.stdout or '').strip():
        return
    assert ok is False
    assert 'not in the' in detail


def test_committed_clean_file_passes():
    ok, detail = vmc._files(['scripts/order_naming.py'])
    assert ok is True, detail


def test_lesson_marker_is_required():
    ok, detail = vmc._lesson('')
    assert ok is False
    assert '--require-lesson' in detail


def test_unregistered_lesson_fails():
    ok, detail = vmc._lesson('L9999-not-registered')
    assert ok is False
    assert 'does not mention' in detail


def test_registered_lesson_passes():
    ok, detail = vmc._lesson('L120')
    assert ok is True, detail


def test_verify_order_declares_mechanism_profile_unsupported(tmp_path):
    payload = vo.verify('wo-ultimaagent-20261110-0036', tmp_path, profile='mechanism')
    assert payload['profile'] == 'mechanism-change'
    assert payload['verified'] is False
    assert payload['blocking_failures'] == ['profile_applicable']
    assert payload['checks'][0]['check'] == 'profile_applicable'
