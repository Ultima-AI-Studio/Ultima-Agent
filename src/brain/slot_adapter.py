"""G-ORCH 三插槽适配层：S-MAIN / S-REVIEW / S-EXEC。

目的：让插槽可以换 API、换 CLI、换模型，而不改调度代码。照搬业界两类成熟形态，
不自研协议：

- 审议位（S-REVIEW）：OpenAI-compatible ``/chat/completions``。DeepSeek、OpenAI、
  Moonshot、Qwen（DashScope compatible-mode）、vLLM、Ollama、LM Studio 都提供这
  同一形态，所以换供应商只是换 ``base_url`` + ``model`` + key，请求体不用改。
- 执行位（S-EXEC）：CLI 参数模板。``args_template`` 一旦配置就整体替换 argv，
  换 Claude / Gemini / Qwen / OpenCode 等 CLI 只换模板，不动通道调度。
- 主脑位（S-MAIN）：本地 8B 的 endpoint + model。

配置优先级：环境变量 > ``config/gorch/slots.json`` > 内置默认值。
内置默认值就是当前已真实跑通的行为，**未配置时行为完全不变**。

不做静默 fallback：某个插槽要换成别的实现必须显式配置；配置本身非法（JSON 坏了、
类型不对、值不认识）一律抛 ``SlotConfigError``，不退回猜测值。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONFIG_REL = Path('config') / 'gorch' / 'slots.json'

SLOT_NAMES = ('S-MAIN', 'S-REVIEW', 'S-EXEC')

# 默认值 = 现有代码里写死的那一套，保证零配置时行为不变。
_DEFAULTS: dict[str, dict[str, Any]] = {
    'S-MAIN': {
        'impl': 'ollama-8b',
        'endpoint': 'http://127.0.0.1:18766',
        'model': 'qwen3:8b',
        'enabled': False,   # 8B 未起时保持 False，调用须报错而非假装可用
    },
    'S-REVIEW': {
        'impl': 'deepseek',
        'base_url': 'https://api.deepseek.com/chat/completions',
        'model': 'deepseek-chat',
        'api_key_env': 'DEEPSEEK_API_KEY',
        'max_tokens': 4096,
        'timeout': 60.0,
    },
    'S-EXEC': {
        'impl': 'codex',
        'exe': '',
        'model': 'gpt-5.6-sol',
        'args_template': [],
        'env': {},
    },
}

# 环境变量覆盖（只开放最常换的那几项；复杂项走 json）。
_ENV_MAP: dict[str, dict[str, str]] = {
    'S-MAIN': {'endpoint': 'GORCH_MAIN_ENDPOINT', 'model': 'GORCH_MAIN_MODEL'},
    'S-REVIEW': {'base_url': 'GORCH_REVIEW_BASE_URL',
                 'model': 'GORCH_REVIEW_MODEL',
                 'api_key_env': 'GORCH_REVIEW_KEY_ENV'},
    'S-EXEC': {'exe': 'GORCH_EXEC_EXE', 'model': 'GORCH_EXEC_MODEL'},
}


class SlotConfigError(RuntimeError):
    """插槽配置非法，或插槽尚未接线却被调用。"""


def config_path(path: str | Path | None = None) -> Path:
    if path is not None:
        return Path(path)
    explicit = os.environ.get('GORCH_SLOT_CONFIG', '').strip()
    return Path(explicit) if explicit else ROOT / CONFIG_REL


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """读插槽配置；文件不存在返回空字典，存在但坏了就报错。"""
    target = config_path(path)
    if not target.is_file():
        return {}
    try:
        data = json.loads(target.read_text(encoding='utf-8-sig'))
    except (OSError, ValueError) as exc:
        raise SlotConfigError(f'插槽配置无法解析 {target}: {exc}') from exc
    if not isinstance(data, dict):
        raise SlotConfigError(f'插槽配置必须是 JSON 对象: {target}')
    return data


def _merge(name: str, raw: Any) -> dict[str, Any]:
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise SlotConfigError(f'{name} 配置必须是 JSON 对象')
    merged = dict(_DEFAULTS[name])
    merged.update(raw)
    for key, env_name in _ENV_MAP[name].items():
        value = os.environ.get(env_name, '').strip()
        if value:
            merged[key] = value
    merged['slot'] = name
    return merged


def slot(name: str, path: str | Path | None = None) -> dict[str, Any]:
    """取某个插槽的生效配置（默认值 + 文件 + 环境变量）。"""
    if name not in SLOT_NAMES:
        raise SlotConfigError(f'未知插槽 {name}，只认 {SLOT_NAMES}')
    return _merge(name, load_config(path).get(name))


def review_settings(path: str | Path | None = None) -> dict[str, Any]:
    """S-REVIEW 生效设置，含解析好的 api_key。"""
    cfg = slot('S-REVIEW', path)
    key_env = str(cfg.get('api_key_env') or 'DEEPSEEK_API_KEY').strip()
    return {
        'slot': 'S-REVIEW',
        'impl': cfg['impl'],
        'base_url': str(cfg['base_url']),
        'model': str(cfg['model']),
        'api_key_env': key_env,
        'api_key': os.environ.get(key_env, '').strip(),
        'max_tokens': int(cfg['max_tokens']),
        'timeout': float(cfg['timeout']),
    }


def exec_settings(path: str | Path | None = None) -> dict[str, Any]:
    """S-EXEC 生效设置。args_template 为空表示沿用内置 codex 命令行。"""
    cfg = slot('S-EXEC', path)
    template = cfg.get('args_template') or []
    if not isinstance(template, list) or not all(isinstance(x, str) for x in template):
        raise SlotConfigError('S-EXEC.args_template 必须是字符串数组')
    extra_env = cfg.get('env') or {}
    if not isinstance(extra_env, dict):
        raise SlotConfigError('S-EXEC.env 必须是 JSON 对象')
    return {
        'slot': 'S-EXEC',
        'impl': cfg['impl'],
        'exe': str(cfg.get('exe') or '').strip(),
        'model': str(cfg['model']),
        'args_template': list(template),
        'env': {str(k): str(v) for k, v in extra_env.items()},
    }


def main_settings(path: str | Path | None = None) -> dict[str, Any]:
    """S-MAIN 生效设置（本地 8B）。"""
    cfg = slot('S-MAIN', path)
    return {
        'slot': 'S-MAIN',
        'impl': cfg['impl'],
        'endpoint': str(cfg['endpoint']),
        'model': str(cfg['model']),
        'enabled': bool(cfg.get('enabled')),
    }


def require_main(path: str | Path | None = None) -> dict[str, Any]:
    """取主脑位；未接线就 fail-closed。

    第 1、4 跳（主脑理解、主脑回传授权条件）当前依赖本地 8B，8B 没起时
    这里必须报错，不能让上游以为"已经有主脑在跑"。
    """
    cfg = main_settings(path)
    if not cfg['enabled']:
        raise SlotConfigError(
            'S-MAIN 未接线（enabled=false）：主脑位尚未启用，'
            '第 1、4 跳不能由适配层代做'
        )
    return cfg


def render_exec_argv(settings: dict[str, Any], *, exe: str, workdir: str,
                     last_msg: str, effort: str) -> list[str]:
    """按模板渲染执行位 argv；模板为空时调用方应走内置 codex 命令行。"""
    template = settings.get('args_template') or []
    if not template:
        raise SlotConfigError('args_template 为空，无模板可渲染')
    values = {
        'exe': exe,
        'model': settings.get('model', ''),
        'workdir': workdir,
        'last_msg': last_msg,
        'effort': effort,
    }
    try:
        return [t.format(**values) for t in template]
    except (KeyError, IndexError, ValueError) as exc:
        raise SlotConfigError(f'args_template 渲染失败: {exc}') from exc
