"""写死易变值检测（W_VOLATILE_COUNT_WRITTEN）的正负样本。

0036 元工单多轮卡在「卡面把会变的环境计数当判据」上，当时只有一条文字规矩。
这里把那条规矩固化成可执行判据：正样本必须命中，负样本必须不命中。
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import validate_work_order as vw


POSITIVE = [
    "恰好 560 条脏条目 → 冻结放行",
    "`dispatch-wo-*-now.py`（19 个一次性脚本，归档）",
    "队列状态分布 frozen 112 / blocked 19 / pending 4",
    "写域外脏条目数量 = 546 条",
    "`dispatch-*-prompt.txt`（约 60 个快照，归档）",
]

NEGATIVE = [
    "构造与 T0 实测同量级脏条目后执行冻结 → 放行",
    "用例数 ≥8，全部 PASS",
    "全量 pytest 0 failed",
    "差异条数 ≤2 视为通过",
    "修改 `scripts/validate_work_order.py` 与 `docs/specs/work-order.schema.json`",
    "按 1.2.3 三条逐项落地",
    "T2 总验收：已完成；0003 原专项 51 passed；fresh 全量 731 passed + 120 subtests / 0 failed",
    "R23工作包仍是草案；`finalizer`、`verifier`、`runner` 已加入拒绝检查，Python 11个文件及PowerShell 2个脚本语法PASS。",
]


@pytest.mark.parametrize("line", POSITIVE)
def test_volatile_count_is_flagged(line):
    issues = vw._written_volatile_counts([line])
    assert len(issues) == 1
    assert issues[0]["code"] == vw.W_VOLATILE_COUNT_WRITTEN
    assert issues[0]["line"] == 1


@pytest.mark.parametrize("line", NEGATIVE)
def test_safe_wording_is_not_flagged(line):
    assert vw._written_volatile_counts([line]) == []


def test_line_number_points_at_offending_line():
    lines = ["# 卡面", "", "**验收（Gate T1）**：无", "`dispatch-wo-*-now.py`（19 个一次性脚本，归档）"]
    issues = vw._written_volatile_counts(lines)
    assert [item["line"] for item in issues] == [4]


def test_empty_card_has_no_issues():
    assert vw._written_volatile_counts([]) == []


def test_volatile_warning_stays_a_warning():
    """历史卡保住自己的判定：命中只进 warnings，不进 errors，派发门自行决定拦不拦。"""

    issues = vw._written_volatile_counts(["`dispatch-wo-*-now.py`（19 个一次性脚本，归档）"])
    codes = {item["code"] for item in issues}
    assert codes == {vw.W_VOLATILE_COUNT_WRITTEN}
    assert vw.W_VOLATILE_COUNT_WRITTEN != vw.E_GATE_CONTRADICTION


def test_skip_dor_cannot_bypass_volatile(tmp_path):
    """派发器的 --skip-dor 不得绕过写死易变值的拦截。

    用 0036 卡做真实载荷：它的 L214/L215 是历史病根原文，机检必然命中。
    若这两句哪天被清掉，本用例会失败，提醒同步更新测试样本——那是预期行为。
    """

    import subprocess

    repo = Path(__file__).resolve().parents[2]
    card = repo / 'tasks' / 'queue' / 'wo-ultimaagent-20261110-0036--task-system-rework.md'
    if not card.exists():
        pytest.skip('缺少 0036 卡，跳过派发门回归')

    prompt = tmp_path / 'prompt.txt'
    prompt.write_text('docs/INDEX.md wo-ultimaagent-20261110-0036', encoding='utf-8')

    proc = subprocess.run(
        [sys.executable, str(repo / 'scripts' / 'dispatch-work-order.py'),
         '--order', 'wo-ultimaagent-20261110-0036',
         '--prompt', str(prompt),
         '--card', str(card),
         '--dry-run-dor', '--skip-dor'],
        capture_output=True, text=True, encoding='utf-8', cwd=str(repo),
    )

    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert 'W_VOLATILE_COUNT_WRITTEN' in proc.stdout
    assert 'skip_dor_ignored' in proc.stdout

