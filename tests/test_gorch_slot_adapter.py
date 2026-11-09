"""插槽适配层单测：零配置行为不变 + 配置/env 覆盖 + fail-closed。"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.brain.slot_adapter import (  # noqa: E402
    SLOT_NAMES,
    SlotConfigError,
    exec_settings,
    load_config,
    main_settings,
    render_exec_argv,
    require_main,
    review_settings,
    slot,
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """隔离真实环境变量，避免本机已有的 GORCH_* 影响断言。"""
    for name in (
        'GORCH_REVIEW_BASE_URL',
        'GORCH_REVIEW_MODEL',
        'GORCH_REVIEW_KEY_ENV',
        'GORCH_EXEC_EXE',
        'GORCH_EXEC_MODEL',
        'GORCH_MAIN_ENDPOINT',
        'GORCH_MAIN_MODEL',
        'GORCH_SLOT_CONFIG',
        'DEEPSEEK_API_KEY',
    ):
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


def _write(tmp_path, payload):
    target = tmp_path / 'slots.json'
    target.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
    return target


def test_missing_config_falls_back_to_builtin_defaults(tmp_path):
    """没有配置文件时必须是当前已跑通的那一套，不能变。"""
    missing = tmp_path / 'nope.json'
    assert load_config(missing) == {}
    review = review_settings(missing)
    assert review['impl'] == 'deepseek'
    assert review['base_url'] == 'https://api.deepseek.com/chat/completions'
    assert review['model'] == 'deepseek-chat'
    assert review['api_key_env'] == 'DEEPSEEK_API_KEY'
    assert review['max_tokens'] == 4096
    assert review['timeout'] == 60.0


def test_review_config_file_overrides_provider(tmp_path, _clean_env):
    """换供应商只改 base_url + model + key 名，其余不动。"""
    cfg = _write(tmp_path, {
        'S-REVIEW': {
            'impl': 'moonshot',
            'base_url': 'https://api.moonshot.cn/v1/chat/completions',
            'model': 'kimi-k2',
            'api_key_env': 'MOONSHOT_API_KEY',
        }
    })
    _clean_env.setenv('MOONSHOT_API_KEY', 'sk-test')
    review = review_settings(cfg)
    assert review['impl'] == 'moonshot'
    assert review['base_url'].endswith('/v1/chat/completions')
    assert review['model'] == 'kimi-k2'
    assert review['api_key'] == 'sk-test'


def test_env_beats_config_file(tmp_path, _clean_env):
    cfg = _write(tmp_path, {'S-REVIEW': {'model': 'from-file'}})
    _clean_env.setenv('GORCH_REVIEW_MODEL', 'from-env')
    assert review_settings(cfg)['model'] == 'from-env'


def test_blank_env_does_not_override(tmp_path, _clean_env):
    """空字符串不能当成有效覆盖，否则会静默清空配置。"""
    cfg = _write(tmp_path, {'S-REVIEW': {'model': 'from-file'}})
    _clean_env.setenv('GORCH_REVIEW_MODEL', '   ')
    assert review_settings(cfg)['model'] == 'from-file'


def test_broken_json_is_fail_closed(tmp_path):
    target = tmp_path / 'slots.json'
    target.write_text('{ not json', encoding='utf-8')
    with pytest.raises(SlotConfigError):
        load_config(target)
    with pytest.raises(SlotConfigError):
        review_settings(target)


def test_non_object_config_is_fail_closed(tmp_path):
    target = tmp_path / 'slots.json'
    target.write_text('[]', encoding='utf-8')
    with pytest.raises(SlotConfigError):
        load_config(target)


def test_slot_value_must_be_object(tmp_path):
    cfg = _write(tmp_path, {'S-REVIEW': 'deepseek'})
    with pytest.raises(SlotConfigError):
        slot('S-REVIEW', cfg)


def test_unknown_slot_rejected():
    with pytest.raises(SlotConfigError):
        slot('S-NOPE')


def test_main_is_fail_closed_until_enabled(tmp_path):
    """主脑位没起时必须报错，不能让上游以为第 1、4 跳有人在做。"""
    missing = tmp_path / 'nope.json'
    assert main_settings(missing)['enabled'] is False
    with pytest.raises(SlotConfigError):
        require_main(missing)
    cfg = _write(tmp_path, {'S-MAIN': {'enabled': True, 'model': 'qwen3:8b'}})
    assert require_main(cfg)['model'] == 'qwen3:8b'


def test_exec_defaults_keep_current_codex_behaviour(tmp_path):
    settings = exec_settings(tmp_path / 'nope.json')
    assert settings['impl'] == 'codex'
    assert settings['model'] == 'gpt-5.6-sol'
    assert settings['args_template'] == []
    assert settings['exe'] == ''
    assert settings['env'] == {}


def test_exec_template_replaces_argv(tmp_path):
    cfg = _write(tmp_path, {
        'S-EXEC': {
            'impl': 'claude',
            'model': 'claude-sonnet',
            'args_template': ['{exe}', '-p', '{last_msg}', '--cwd', '{workdir}'],
        }
    })
    settings = exec_settings(cfg)
    argv = render_exec_argv(settings, exe='claude.exe', workdir='C:/wt', last_msg='m.txt', effort='high')
    assert argv == ['claude.exe', '-p', 'm.txt', '--cwd', 'C:/wt']


def test_exec_template_rejects_bad_type(tmp_path):
    cfg = _write(tmp_path, {'S-EXEC': {'args_template': 'not-a-list'}})
    with pytest.raises(SlotConfigError):
        exec_settings(cfg)


def test_exec_template_unknown_placeholder_fails(tmp_path):
    cfg = _write(tmp_path, {'S-EXEC': {'args_template': ['{exe}', '{nope}']}})
    settings = exec_settings(cfg)
    with pytest.raises(SlotConfigError):
        render_exec_argv(settings, exe='x', workdir='w', last_msg='m', effort='e')


def test_render_without_template_is_fail_closed(tmp_path):
    settings = exec_settings(tmp_path / 'nope.json')
    with pytest.raises(SlotConfigError):
        render_exec_argv(settings, exe='x', workdir='w', last_msg='m', effort='e')


def test_env_config_path_is_honoured(tmp_path, _clean_env):
    """GORCH_SLOT_CONFIG 指向别的文件时，load_config() 必须读它。"""
    cfg = _write(tmp_path, {'S-REVIEW': {'model': 'via-env-path'}})
    _clean_env.setenv('GORCH_SLOT_CONFIG', str(cfg))
    assert load_config()['S-REVIEW']['model'] == 'via-env-path'


def test_all_slots_resolvable():
    """三个插槽都必须能被解析出来，缺一个就等于该位不可替换。"""
    for name in SLOT_NAMES:
        resolved = slot(name)
        assert resolved['slot'] == name
        assert 'impl' in resolved


# --- 接线层：适配层配了值，真实调用点必须用上（不能只在设置函数里生效） ---


def test_call_deepseek_uses_passed_key_not_env(monkeypatch):
    """回归：曾出现过 base_url/model 换了、Authorization 仍是 DEEPSEEK_API_KEY。"""
    import src.brain.orchestrator as orch

    captured = {}

    class _Resp:
        status_code = 200

        @staticmethod
        def json():
            return {'choices': [{'message': {'content': 'ok'}}], 'usage': {}}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured.update(url=url, headers=headers, model=json['model'])
        return _Resp()

    monkeypatch.setattr(orch.requests, 'post', fake_post)
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'env-key-should-lose')

    orch.call_deepseek(
        'sys', 'usr',
        api_key='slot-key',
        base_url='http://slot.local/v1/chat/completions',
        model='slot-model',
    )

    assert captured['headers']['Authorization'] == 'Bearer slot-key'
    assert captured['url'] == 'http://slot.local/v1/chat/completions'
    assert captured['model'] == 'slot-model'


def test_call_deepseek_falls_back_to_env_key(monkeypatch):
    """不传 key 时仍按历史行为读 DEEPSEEK_API_KEY。"""
    import src.brain.orchestrator as orch

    captured = {}

    class _Resp:
        status_code = 200

        @staticmethod
        def json():
            return {'choices': [{'message': {'content': 'ok'}}], 'usage': {}}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured.update(headers=headers)
        return _Resp()

    monkeypatch.setattr(orch.requests, 'post', fake_post)
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'env-key')
    orch.call_deepseek('sys', 'usr')
    assert captured['headers']['Authorization'] == 'Bearer env-key'


def test_call_deepseek_without_any_key_is_fail_closed(monkeypatch):
    import src.brain.orchestrator as orch

    monkeypatch.delenv('DEEPSEEK_API_KEY', raising=False)
    with pytest.raises(orch.OrchestratorError):
        orch.call_deepseek('sys', 'usr')


def test_run_codex_default_argv_uses_configured_model(tmp_path, monkeypatch):
    """无模板时仍走 codex 那套参数，但 -m 取配置值。"""
    sys.path.insert(0, str(ROOT / 'scripts' / 'gorch'))
    import codex_channel as cc

    cfg = _write(tmp_path, {'S-EXEC': {'model': 'swapped-exec-model'}})
    monkeypatch.setenv('GORCH_SLOT_CONFIG', str(cfg))

    captured = {}

    def fake_run(cmd, **kwargs):
        captured['cmd'] = cmd

        class _P:
            returncode = 0
            stdout = b''
            stderr = b''

        return _P()

    monkeypatch.setattr(cc.subprocess, 'run', fake_run)
    cc.run_codex('codex.exe', b'p', tmp_path, tmp_path / 'm.txt', 'high', 30)

    cmd = captured['cmd']
    assert cmd[0] == 'codex.exe'
    assert cmd[cmd.index('-m') + 1] == 'swapped-exec-model'
    assert '--sandbox' in cmd


def test_run_codex_template_actually_replaces_cli(tmp_path, monkeypatch):
    """模板配好后真起子进程，证明换 CLI 不只停在字符串拼接层面。"""
    sys.path.insert(0, str(ROOT / 'scripts' / 'gorch'))
    import codex_channel as cc

    cfg = _write(tmp_path, {
        'S-EXEC': {
            'impl': 'python-probe',
            'exe': sys.executable,
            'model': 'probe-exec-model',
            'args_template': [
                '{exe}', '-c',
                'import sys; open(sys.argv[1], "w", encoding="utf-8").write("ok:" + sys.argv[2])',
                '{last_msg}', '{model}',
            ],
        }
    })
    monkeypatch.setenv('GORCH_SLOT_CONFIG', str(cfg))

    exe = cc.resolve_codex_exe()
    assert exe == sys.executable

    last_msg = tmp_path / 'last.txt'
    proc, _elapsed = cc.run_codex(exe, b'', tmp_path, last_msg, 'high', 30)
    assert proc.returncode == 0
    assert last_msg.read_text(encoding='utf-8') == 'ok:probe-exec-model'
