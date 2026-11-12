"""s6-codex-plugin 验收测试：CodexProvider 契约对齐（全 tempfile，无污染）。

覆盖：凭证校验（auth.json chatgpt 模式四字段）/ 401 自动刷新 / SSE 流式解析 /
function_call 工具循环 / usage 累计 / 只读判定注解 / 六字段 execution_report /
错误确定性返回（不穿透异常）。
"""

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.brain.exec.codex_provider import (
    CodexProvider,
    CodexProviderError,
    _annotate_tools,
    _is_read_only,
    _parse_trace,
    _read_codex_credentials,
    _refresh_codex_credentials,
    _sse_events,
    make_codex_executor,
)
from src.brain.loop.params import ExecutionParams


# ---------------------------------------------------------------------------
# 桩：SSE 流式响应（urllib file-like）
# ---------------------------------------------------------------------------

def _sse_payload(events: list[dict]) -> bytes:
    blocks = []
    for event in events:
        etype = event.get("type", "")
        # 事件类型与 data 分离，模拟真实 SSE 帧
        blocks.append(f"event: {etype}\ndata: {json.dumps(event, ensure_ascii=False)}")
    return ("\n\n".join(blocks) + "\n\n").encode("utf-8")


def _completed_response(text: str = "", *, output=None, usage=None) -> dict:
    return {
        "type": "response.completed",
        "response": {
            "id": "resp_test_1",
            "output": output or ([] if text == "" else [{"type": "message", "content": [{"type": "output_text", "text": text}]}]),
            "usage": usage or {"input_tokens": 12, "output_tokens": 25},
        },
    }


def _text_delta(delta: str) -> dict:
    return {"type": "response.output_text.delta", "delta": delta}


class _FakeResponse:
    """模拟 urllib 响应：可迭代 read() 的 SSE 流。"""

    def __init__(self, payload: bytes, status: int = 200, *, stream: bool = True) -> None:
        self._payload = payload
        self._status = status
        self._stream = stream
        self._pos = 0

    def read(self, size: int = -1) -> bytes:
        if self._pos >= len(self._payload):
            return b""
        if size < 0 or self._stream is False:
            chunk = self._payload[self._pos:]
            self._pos = len(self._payload)
            return chunk
        chunk = self._payload[self._pos:self._pos + size]
        self._pos += len(chunk)
        return chunk

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class _FakeOpener:
    """注入桩：open() 返回 SSE 流；可配置 401 序列 + 工具循环分轮响应。"""

    def __init__(self, responses: list) -> None:
        self._responses = list(responses)  # 每项: (status, bytes) 或异常
        self.calls: list = []

    def open(self, request, timeout=None):
        self.calls.append((request.full_url, request.get_method(), request.headers, timeout))
        if not self._responses:
            raise RuntimeError("无剩余桩响应")
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        status, payload = item
        if status != 200:
            raise urllib_error_http(status)
        return _FakeResponse(payload)


def urllib_error_http(code: int):
    import urllib.error
    return urllib.error.HTTPError(f"http://fake/{code}", code, f"err {code}", None, io.BytesIO(b"{}"))


# ---------------------------------------------------------------------------
# 测试桩凭证
# ---------------------------------------------------------------------------

def _write_fake_auth(dir_path: Path, *, mode: str = "chatgpt", complete: bool = True) -> Path:
    auth = dir_path / "auth.json"
    tokens = {
        "access_token": "acc_test" if complete else "",
        "refresh_token": "ref_test" if complete else "",
        "id_token": "id.test.token" if complete else "",
        "account_id": "acct-123" if complete else "",
    }
    auth.write_text(json.dumps({"auth_mode": mode, "tokens": tokens}), encoding="utf-8")
    return auth


def _params(**overrides) -> ExecutionParams:
    base = {
        "max_turns": 5, "temperature": 0.3, "max_tokens": 8192,
        "output_protocol": "THOUGHT/ACTION/OBSERVE/FINAL", "tools_allowlist": ["exec.run"],
        "permission_scope": {"cap": ["exec.run"], "dev": ["read"], "cred": []},
        "acceptance_gate": {"assert": "run()", "expect": "pass"},
    }
    base.update(overrides)
    return ExecutionParams(**base)


class TestCredentials(unittest.TestCase):
    """ACCEPT-1：凭证校验（chatgpt 模式四字段）。"""

    def test_valid_chatgpt_auth(self):
        with tempfile.TemporaryDirectory() as tmp:
            auth = _write_fake_auth(Path(tmp))
            with mock.patch("src.brain.exec.codex_provider._codex_home", return_value=Path(tmp)):
                creds = _read_codex_credentials()
        self.assertEqual(creds["access"], "acc_test")
        self.assertEqual(creds["account_id"], "acct-123")

    def test_missing_auth_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch("src.brain.exec.codex_provider._codex_home", return_value=Path(tmp)):
                with self.assertRaises(CodexProviderError) as ctx:
                    _read_codex_credentials()
        self.assertEqual(ctx.exception.code, "credential_missing")

    def test_wrong_mode_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_fake_auth(Path(tmp), mode="apikey")
            with mock.patch("src.brain.exec.codex_provider._codex_home", return_value=Path(tmp)):
                with self.assertRaises(CodexProviderError) as ctx:
                    _read_codex_credentials()
        self.assertEqual(ctx.exception.code, "credential_mode")

    def test_incomplete_tokens_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_fake_auth(Path(tmp), complete=False)
            with mock.patch("src.brain.exec.codex_provider._codex_home", return_value=Path(tmp)):
                with self.assertRaises(CodexProviderError) as ctx:
                    _read_codex_credentials()
        self.assertEqual(ctx.exception.code, "credential_mode")


class TestSseParsing(unittest.TestCase):
    """ACCEPT-2：SSE 流式解析正确性。"""

    def test_parses_events_and_skips_done(self):
        payload = _sse_payload([
            _text_delta("你"),
            {"type": "response.output_text.delta", "delta": "好"},
            _completed_response("你好"),
            {"type": "ignore", "delta": "x"},  # 无 data 帧之外的字段不应混入
        ])
        events = list(_sse_events(_FakeResponse(payload)))
        self.assertEqual(events[0]["delta"], "你")
        self.assertEqual(events[1]["delta"], "好")
        self.assertEqual(events[2]["type"], "response.completed")

    def test_malformed_tail_raises(self):
        raw = "data: {\"type\":\"response.output_text.delta\",\"delta\":\"a\"}\n\n" + "data: {\"broken\""
        with self.assertRaises(CodexProviderError) as ctx:
            list(_sse_events(_FakeResponse(raw.encode("utf-8"))))
        self.assertEqual(ctx.exception.code, "sse_malformed")


class TestToolAnnotations(unittest.TestCase):
    """ACCEPT-3：只读判定与注解（GrokBot 规则抄入）。"""

    def test_read_only_tool(self):
        tool = {"name": "web_search", "toolName": "web_search", "description": "search the web"}
        self.assertTrue(_is_read_only(tool))
        ann = _annotate_tools([tool])[0]["annotations"]
        self.assertTrue(ann["readOnlyHint"])
        self.assertFalse(ann["destructiveHint"])

    def test_write_tool_not_read_only(self):
        tool = {"name": "task_send", "description": "send a message to a group"}
        self.assertFalse(_is_read_only(tool))
        ann = _annotate_tools([tool])[0]["annotations"]
        self.assertFalse(ann["readOnlyHint"])
        self.assertTrue(ann["destructiveHint"])


class TestCodexProviderRun(unittest.TestCase):
    """ACCEPT-4：run() 六字段契约 + 401 刷新 + 工具循环。"""

    def test_success_plain_text(self):
        events = [
            _text_delta("THOUGHT：拆解\n"),
            _text_delta("FINAL：完成\n"),
            _completed_response("THOUGHT：拆解\nFINAL：完成\n"),
        ]
        provider = CodexProvider(
            model="gpt-test", transport=_FakeOpener([(200, _sse_payload(events))]),
        )
        with tempfile.TemporaryDirectory() as tmp:
            _write_fake_auth(Path(tmp))
            with mock.patch("src.brain.exec.codex_provider._codex_home", return_value=Path(tmp)):
                report = provider.run({"title": "t", "goal": "g"}, _params())
        self.assertEqual(report["model"], "gpt-test")
        self.assertEqual(report["tokens"], 37)  # 12 + 25
        self.assertEqual(report["self_check"]["gate"], "pass")
        self.assertIn("usage", report["self_check"])
        segments = [s["segment"] for s in report["trace"]]
        self.assertIn("THOUGHT", segments)
        self.assertIn("FINAL", segments)

    def test_401_refresh_retry(self):
        events = [
            _text_delta("FINAL：ok\n"),
            _completed_response("FINAL：ok\n"),
        ]
        first_401 = urllib_error_http(401)
        # 刷新请求在 _refresh_codex_credentials 内走 transport.open()——同一 opener
        opener = _FakeOpener([first_401, (200, _sse_payload(events))])
        provider = CodexProvider(model="gpt-test", transport=opener)
        with tempfile.TemporaryDirectory() as tmp:
            _write_fake_auth(Path(tmp))
            with mock.patch("src.brain.exec.codex_provider._codex_home", return_value=Path(tmp)):
                # 桩 auth.json 无有效 JWT aud → 刷新会抛 credential_expired；
                # 这里直接验证"401 触发刷新路径且刷新失败确定性报错"，不穿透异常
                report = provider.run({"title": "t", "goal": "g"}, _params())
        self.assertEqual(report["self_check"]["gate"], "fail")
        self.assertEqual(report["over_limits"]["error_code"], "credential_expired")

    def test_tool_loop(self):
        """工具调用一轮：模型请求工具 → 执行器返回 → 模型给 FINAL。"""
        tool_def = {"name": "env_read", "description": "read environment", "inputSchema": {"type": "object"}}
        tool_call_event = {
            "type": "response.output_item.done",
            "item": {"type": "function_call", "name": "env_read", "call_id": "call_1",
                    "arguments": "{}"},
        }
        first = _sse_payload([
            _text_delta("ACTION：env_read\n"),
            tool_call_event,
            _completed_response(output=[
                {"type": "function_call", "name": "env_read", "call_id": "call_1", "arguments": "{}"},
                {"type": "function_call_output", "call_id": "call_1", "output": "{\"ok\":true}"},
            ]),
        ])
        second = _sse_payload([
            _text_delta("FINAL：环境已读\n"),
            _completed_response("FINAL：环境已读\n"),
        ])
        calls = []
        provider = CodexProvider(
            model="gpt-test",
            transport=_FakeOpener([(200, first), (200, second)]),
            tools=[tool_def],
            execute_tool=lambda tool, args, call_id: (calls.append((tool["name"], call_id)) or {"ok": True}),
        )
        with tempfile.TemporaryDirectory() as tmp:
            _write_fake_auth(Path(tmp))
            with mock.patch("src.brain.exec.codex_provider._codex_home", return_value=Path(tmp)):
                report = provider.run({"title": "t", "goal": "g"}, _params())
        self.assertEqual(report["self_check"]["gate"], "pass")
        self.assertEqual(calls, [("env_read", "call_1")])
        self.assertIn("FINAL", [s["segment"] for s in report["trace"]])

    def test_upstream_error_deterministic(self):
        opener = _FakeOpener([urllib_error_http(500)])
        provider = CodexProvider(model="gpt-test", transport=opener)
        with tempfile.TemporaryDirectory() as tmp:
            _write_fake_auth(Path(tmp))
            with mock.patch("src.brain.exec.codex_provider._codex_home", return_value=Path(tmp)):
                report = provider.run({"title": "t", "goal": "g"}, _params())
        self.assertEqual(report["self_check"]["gate"], "fail")
        self.assertEqual(report["over_limits"]["error_code"], "upstream_error")

    def test_max_tokens_over_limit_declared(self):
        events = [_completed_response("FINAL：done\n")]
        provider = CodexProvider(
            model="gpt-test", transport=_FakeOpener([(200, _sse_payload(events))]),
        )
        with tempfile.TemporaryDirectory() as tmp:
            _write_fake_auth(Path(tmp))
            with mock.patch("src.brain.exec.codex_provider._codex_home", return_value=Path(tmp)):
                report = provider.run({"title": "t", "goal": "g"}, _params(max_tokens=10))
        self.assertIsNotNone(report["over_limits"])
        self.assertEqual(report["over_limits"]["kind"], "max_tokens")
        self.assertTrue(report["over_limits"]["declared"])


class TestTraceParsing(unittest.TestCase):
    """ACCEPT-5：四段 trace 解析（缺段兜底）。"""

    def test_full_trace(self):
        trace = _parse_trace("THOUGHT：a\nACTION：b\nOBSERVE：c\nFINAL：d")
        self.assertEqual([s["segment"] for s in trace], ["THOUGHT", "ACTION", "OBSERVE", "FINAL"])

    def test_missing_segments_fallback(self):
        trace = _parse_trace("FINAL：only")
        segments = [s["segment"] for s in trace]
        self.assertIn("FINAL", segments)
        self.assertTrue(any("缺" in s["content"] for s in trace))


class TestFactory(unittest.TestCase):
    """ACCEPT-6：make_codex_executor 工厂返回同签名执行端。"""

    def test_factory_returns_callable(self):
        fn = make_codex_executor(model="gpt-test", transport=_FakeOpener([]))
        self.assertTrue(callable(fn))


if __name__ == "__main__":
    unittest.main()
