"""s5-external-executor 验收测试：ExternalModelExecutor 契约对齐（全 tempfile，无污染）。"""

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.brain.loop.external_executor import (
    DEFAULT_MODEL,
    ENV_KEY_NAME,
    ExternalExecutorError,
    ExternalModelExecutor,
    _parse_trace,
)
from src.brain.loop.params import ExecutionParams


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._raw = json.dumps(payload).encode("utf-8")
        self._status = 200

    def read(self) -> bytes:
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class _FakeOpener:
    """注入桩：open() 返回固定 payload，或抛指定异常。"""

    def __init__(self, payload=None, error=None) -> None:
        self._payload = payload
        self._error = error
        self.calls = []

    def open(self, request, timeout=None):
        self.calls.append((request, timeout))
        if self._error is not None:
            raise self._error
        return _FakeResponse(self._payload)


def _payload(content: str, model: str = DEFAULT_MODEL, prompt_tokens: int = 10,
             completion_tokens: int = 20) -> dict:
    return {
        "model": model,
        "choices": [{"message": {"content": content}}],
        "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
    }


def _params(**overrides) -> ExecutionParams:
    base = {
        "max_turns": 5, "temperature": 0.3, "max_tokens": 8192,
        "output_protocol": "THOUGHT/ACTION/OBSERVE/FINAL", "tools_allowlist": ["exec.run"],
        "permission_scope": {"cap": ["exec.run"], "dev": ["read"], "cred": []},
        "acceptance_gate": {"assert": "run()", "expect": "pass"},
    }
    base.update(overrides)
    return ExecutionParams(**base)


class TestKeyMissing(unittest.TestCase):
    """ACCEPT-1：key 缺失明确报错、不崩溃。"""

    def test_missing_key_raises_deterministic_error(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop(ENV_KEY_NAME, None)
            executor = ExternalModelExecutor(transport=_FakeOpener())
            report = executor.run({"title": "t", "goal": "g"}, _params())
        self.assertEqual(report["self_check"]["gate"], "fail")
        self.assertEqual(report["over_limits"]["error_code"], "credential_missing")
        self.assertIn("未配置", report["trace"][0]["content"])


class TestStubTransport(unittest.TestCase):
    """ACCEPT-2：桩 transport 下 run() 返回六字段 execution_report。"""

    def test_six_field_contract(self):
        opener = _FakeOpener(payload=_payload(
            "THOUGHT：拆解目标\nACTION：exec.run\nOBSERVE：成功\nFINAL：完成"
        ))
        executor = ExternalModelExecutor(transport=opener)
        with mock.patch.dict(os.environ, {ENV_KEY_NAME: "sk-test"}):
            report = executor.run({"title": "t", "goal": "g"}, _params())
        for field in ("model", "actual_turns", "tokens", "trace", "self_check", "over_limits"):
            self.assertIn(field, report)
        self.assertEqual(report["self_check"]["gate"], "pass")
        self.assertEqual(report["actual_turns"], 1)
        self.assertEqual(report["tokens"], 30)  # 10+20

    def test_request_payload_carries_params(self):
        opener = _FakeOpener(payload=_payload("FINAL：ok"))
        executor = ExternalModelExecutor(transport=opener)
        with mock.patch.dict(os.environ, {ENV_KEY_NAME: "sk-test"}):
            executor.run({"title": "t", "goal": "g"}, _params(max_tokens=2048, temperature=0.7))
        request, _ = opener.calls[0]
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(body["model"], DEFAULT_MODEL)
        self.assertEqual(body["max_tokens"], 2048)
        self.assertAlmostEqual(body["temperature"], 0.7)
        self.assertIn("任务目标", body["messages"][1]["content"])
        self.assertEqual(request.headers["Authorization"], "Bearer sk-test")


class TestTraceParsing(unittest.TestCase):
    """ACCEPT-3：四段 trace 结构化解析。"""

    def test_full_four_segments(self):
        trace = _parse_trace(
            "THOUGHT：拆解\nACTION：exec.run\nOBSERVE：返回\nFINAL：结论"
        )
        names = [t["segment"] for t in trace]
        self.assertEqual(names, ["THOUGHT", "ACTION", "OBSERVE", "FINAL"])

    def test_missing_segment_declared_not_fabricated(self):
        trace = _parse_trace("FINAL：只有结论")
        names = [t["segment"] for t in trace]
        self.assertIn("FINAL", names)
        self.assertNotIn("THOUGHT", names)
        # 缺段显式占位声明，不编造内容
        self.assertTrue(any("未按四段协议完整输出" in t["content"] for t in trace))


class TestFailureSemantics(unittest.TestCase):
    """ACCEPT-4：鉴权/限流/上游/网络/超时 → 确定性错误码，不穿透异常。"""

    def test_auth_failed(self):
        from urllib.error import HTTPError
        err = HTTPError("https://api.deepseek.com/chat/completions", 401, "Unauthorized",
                        {}, io.BytesIO(b'{"error":"bad key"}'))
        executor = ExternalModelExecutor(transport=_FakeOpener(error=err))
        with mock.patch.dict(os.environ, {ENV_KEY_NAME: "sk-bad"}):
            report = executor.run({"title": "t", "goal": "g"}, _params())
        self.assertEqual(report["over_limits"]["error_code"], "auth_failed")
        self.assertEqual(report["self_check"]["gate"], "fail")

    def test_rate_limited(self):
        from urllib.error import HTTPError
        err = HTTPError("u", 429, "Too Many Requests", {}, io.BytesIO(b""))
        executor = ExternalModelExecutor(transport=_FakeOpener(error=err))
        with mock.patch.dict(os.environ, {ENV_KEY_NAME: "sk-test"}):
            report = executor.run({"title": "t", "goal": "g"}, _params())
        self.assertEqual(report["over_limits"]["error_code"], "rate_limited")

    def test_network_failed(self):
        from urllib.error import URLError
        executor = ExternalModelExecutor(transport=_FakeOpener(error=URLError("no route")))
        with mock.patch.dict(os.environ, {ENV_KEY_NAME: "sk-test"}):
            report = executor.run({"title": "t", "goal": "g"}, _params())
        self.assertEqual(report["over_limits"]["error_code"], "network_failed")

    def test_max_tokens_declared(self):
        opener = _FakeOpener(payload=_payload("FINAL：ok", completion_tokens=9000))
        executor = ExternalModelExecutor(transport=opener)
        with mock.patch.dict(os.environ, {ENV_KEY_NAME: "sk-test"}):
            report = executor.run({"title": "t", "goal": "g"}, _params(max_tokens=8192))
        self.assertEqual(report["over_limits"]["kind"], "max_tokens")
        self.assertTrue(report["over_limits"]["declared"])


class TestBrainLoopInjection(unittest.TestCase):
    """ACCEPT-6：BrainLoop 注入真实执行器全链通过（tempfile，不污染真实库）。"""

    def test_inject_executor_full_loop(self):
        from src.brain.loop.brain_loop import BrainLoop
        opener = _FakeOpener(payload=_payload(
            "THOUGHT：任务拆解\nACTION：exec.run\nOBSERVE：执行成功\nFINAL：任务完成"
        ))
        executor = ExternalModelExecutor(transport=opener)
        with tempfile.TemporaryDirectory() as tmp:
            loop = BrainLoop(Path(tmp), executor=executor.run)
            with mock.patch.dict(os.environ, {ENV_KEY_NAME: "sk-test"}):
                result = loop.run(
                    "执行一个测试任务：生成 hello 输出",
                    params=_params(),  # 显式下发执行参数（契约：下发必带参数）
                )
        self.assertEqual(result.status, "approved")
        self.assertEqual(result.report["self_check"]["gate"], "pass")
        self.assertTrue(result.memory_archived)
        self.assertTrue(result.audit_ids)


if __name__ == "__main__":
    unittest.main()
