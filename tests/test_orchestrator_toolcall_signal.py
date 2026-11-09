"""工具调用信号的判定口径。

背景：work_order 阶段必须产出给执行端照做的命令示例，用 ```bash 代码块标记
当"工具调用"会把整张合法工单误杀（2026-11-09 S7 冒烟单实际踩到）。真正的
工具调用是供应商在 message 里给出的原生 tool_calls 字段，文本标记只留控制
token 泄漏与带引号的键名。
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import src.brain.orchestrator as orch  # noqa: E402


def test_bash_code_block_in_work_order_is_not_tool_call():
    """工单里写 git add / cp 这类命令示例，是合法内容，不许判成工具调用。"""
    text = (
        '## 提交规范\n'
        '命令：\n'
        '```bash\n'
        'git add config/gorch/README.md\n'
        'git commit -m "docs(gorch): ..."\n'
        '```\n'
        'VERDICT: COMPLETED\n'
    )
    assert orch._looks_like_tool_call(text) is False


def test_powershell_block_in_work_order_is_not_tool_call():
    text = '```powershell\nGet-ChildItem\n```\nVERDICT: COMPLETED\n'
    assert orch._looks_like_tool_call(text) is False


def test_control_token_leak_is_tool_call():
    assert orch._looks_like_tool_call('to=func<｜｜tool｜｜>') is True
    assert orch._looks_like_tool_call('<DSML|invoke>') is True


def test_textual_tool_calls_key_is_tool_call():
    assert orch._looks_like_tool_call('{"tool_calls": [{"name": "x"}]}') is True


def _fake_post(payload):
    class _Resp:
        status_code = 200

        def json(self):
            return payload

    return lambda *a, **k: _Resp()


def test_native_tool_calls_payload_is_rejected(monkeypatch):
    """供应商真的返回 tool_calls 字段 → 必须拦，不能当分析结果落盘。"""
    monkeypatch.setattr(
        orch.requests, 'post',
        _fake_post({
            'choices': [{'message': {
                'content': '',
                'tool_calls': [{'id': 'c1', 'function': {'name': 'shell'}}],
            }}],
            'usage': {},
        }),
    )
    with pytest.raises(orch.OrchestratorError) as exc:
        orch.call_deepseek('sys', 'usr', api_key='k')
    assert 'tool_calls' in str(exc.value)


def test_plain_answer_with_usage_still_works(monkeypatch):
    monkeypatch.setattr(
        orch.requests, 'post',
        _fake_post({
            'choices': [{'message': {'content': 'REQUIREMENT UNDERSTANDING...\nVERDICT: COMPLETED'}}],
            'usage': {'prompt_tokens': 5, 'completion_tokens': 3},
        }),
    )
    out = orch.call_deepseek('sys', 'usr', api_key='k')
    assert out['response'].endswith('VERDICT: COMPLETED')
    assert out['tokens'] == {'in': 5, 'out': 3}
