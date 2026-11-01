"""Ultima Agent 客户端——薄壳侧调用智能体服务器（agent_server）的标准库 HTTP 客户端。

供文字 CLI 与语音 daemon（interaction 兜底）复用。仅标准库 urllib，
可在任意 Python 3.10+（含 venv-asr）运行。

接口：
- ask_agent(query, max_tokens=None) -> str  调用 Agent 循环，返回最终回答文本
- agent_healthy() -> bool                   服务器是否可达
"""

from __future__ import annotations

import json
import urllib.request

AGENT_SERVER = "http://127.0.0.1:8756"
_ASK_TIMEOUT_SECONDS = 300  # 本地 14B 推理可能耗时（模型加载/长回复）


def ask_agent(query: str, max_tokens: int | None = None) -> str:
    """调用智能体服务器执行一轮自主对话，返回最终回答文本。"""
    payload = {"query": query}
    if max_tokens:
        payload["max_tokens"] = max_tokens
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"{AGENT_SERVER}/ask",
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=_ASK_TIMEOUT_SECONDS) as response:
        result = json.loads(response.read().decode("utf-8"))
    if not result.get("ok"):
        raise RuntimeError(str(result.get("error", "未知错误")))
    return str(result.get("content", ""))


def agent_healthy() -> bool:
    """服务器是否可达（供调用方决定是否走 Agent 兜底）。"""
    try:
        request = urllib.request.Request(f"{AGENT_SERVER}/health", method="GET")
        with urllib.request.urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return bool(payload.get("ok"))
    except Exception:  # 服务未启动/网络异常
        return False


__all__ = ["ask_agent", "agent_healthy"]


def ask_work(query: str, *, request_id: str, session_id: str, context: dict | None = None, max_tokens: int | None = None, server_url: str = AGENT_SERVER) -> dict:
    """Submit structured work only to an explicit loopback service."""
    from urllib.parse import urlparse
    import ipaddress
    url = urlparse(server_url)
    try:
        loopback = url.hostname == 'localhost' or ipaddress.ip_address(url.hostname or '').is_loopback
    except ValueError:
        loopback = False
    if url.scheme != 'http' or not loopback or url.username or url.password or url.path not in ('', '/') or url.query or url.fragment:
        raise ValueError('Work server must be an HTTP loopback origin')
    payload = dict(mode='work', query=query, request_id=request_id, session_id=session_id, context=context, max_tokens=max_tokens)
    request = urllib.request.Request(server_url.rstrip('/') + '/ask', data=json.dumps(payload, ensure_ascii=False).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
    # Never allow proxy environment variables or redirects to forward work remotely.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            raise ValueError('Work redirects are forbidden')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(request, timeout=_ASK_TIMEOUT_SECONDS) as response:
        result = json.loads(response.read().decode('utf-8'))
    if not result.get('ok'):
        raise RuntimeError(str(result.get('error', 'Work transport failed')))
    return result
