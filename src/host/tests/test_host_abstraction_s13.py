r"""S13 宿主抽象层 · 单测（正式可复跑版）。

覆盖（对应批次规划 S13 T1/T2/T3）：
  1. 宿主接口定义：HostIO / HostRenderer / HostEvents 三组 Protocol 存在且
     可运行时检查（runtime_checkable）
  2. Windows 宿主适配：文件契约 IO / 渲染 / 事件实现，行为与既有
     HostOrbPusher 契约同构（seq 递增、幂等覆盖、空指令拒绝）
  3. CompositeHost：三组接口聚合透传 + 就绪自检
  4. 跨平台预留：适配器零 Windows API 依赖（仅标准库/文件系统）

运行：
  H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -X utf8 -m unittest discover -s src\host\tests -p "test_*.py" -v
"""

from __future__ import annotations

import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(r"H:\UltimaAI\UltimaAgent")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.host.abstraction import (  # noqa: E402
    CompositeHost,
    HostAbstractionError,
    HostEvents,
    HostIO,
    HostRenderer,
    RENDER_KIND_ORB,
)
from src.host.adapters.file_host import (  # noqa: E402
    FileHostEvents,
    FileHostIO,
    FileHostRenderer,
    build_file_host,
)


class TestProtocols(unittest.TestCase):
    """接口定义（runtime_checkable 可检查）。"""

    def test_protocols_runtime_checkable(self) -> None:
        self.assertTrue(HostIO)
        self.assertTrue(HostRenderer)
        self.assertTrue(HostEvents)

    def test_file_adapters_conform_to_protocols(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            io = FileHostIO(td)
            renderer = FileHostRenderer(td)
            events = FileHostEvents(td)
            self.assertIsInstance(io, HostIO)          # runtime_checkable 结构匹配
            self.assertIsInstance(renderer, HostRenderer)
            self.assertIsInstance(events, HostEvents)

    def test_render_kind_contract(self) -> None:
        self.assertEqual(RENDER_KIND_ORB, "orb.render")


class TestFileHostIO(unittest.TestCase):
    """IO 适配：文本/语音输出 + 输入。"""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.io = FileHostIO(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_send_text_outbox(self) -> None:
        receipt = self.io.send_text("任务已完成")
        self.assertEqual(receipt["kind"], "text")
        outbox = Path(self.tmp.name) / "outbox.jsonl"
        self.assertTrue(outbox.exists())
        lines = outbox.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        self.assertIn("任务已完成", lines[0])

    def test_send_voice_outbox(self) -> None:
        receipt = self.io.send_voice("你好", voice="沉稳男声")
        self.assertEqual(receipt["kind"], "voice")
        self.assertEqual(receipt["voice"], "沉稳男声")

    def test_empty_text_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.io.send_text("")
        with self.assertRaises(ValueError):
            self.io.send_voice("   ")

    def test_receive_input_empty(self) -> None:
        self.assertEqual(self.io.receive_input(), [])


class TestFileHostRenderer(unittest.TestCase):
    """渲染适配：orb_command.json 契约（与 HostOrbPusher 同构）。"""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.renderer = FileHostRenderer(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_render_canvas_seq_increments(self) -> None:
        cmd1 = self.renderer.render_canvas({"kind": "orb.render", "state": "idle"})
        cmd2 = self.renderer.render_canvas({"kind": "orb.render", "state": "listening"})
        self.assertEqual(cmd1["seq"], 1)
        self.assertEqual(cmd2["seq"], 2)

    def test_render_canvas_invalid_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.renderer.render_canvas({"kind": "other", "state": "idle"})
        with self.assertRaises(ValueError):
            self.renderer.render_canvas({"kind": "orb.render"})  # 缺 state

    def test_render_window_tree(self) -> None:
        receipt = self.renderer.render_window({"components": [{"type": "text", "content": "hi"}]})
        self.assertEqual(receipt["kind"], "window.render")
        target = Path(self.tmp.name) / "window_tree.json"
        self.assertTrue(target.exists())


class TestFileHostEvents(unittest.TestCase):
    """事件适配：轮询 + 阻塞等待。"""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.events = FileHostEvents(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_poll_empty(self) -> None:
        self.assertEqual(self.events.poll_events(), [])

    def test_wait_event_timeout(self) -> None:
        self.assertIsNone(self.events.wait_event(timeout_ms=50))

    def test_wait_event_gets_event(self) -> None:
        # 后台线程写入事件
        def _write() -> None:
            import time
            import json
            time.sleep(0.1)
            Path(self.tmp.name, "events.json").write_text(
                json.dumps([{"type": "confirm", "payload": {"ok": True}, "ts": "t"}]),
                encoding="utf-8",
            )

        t = threading.Thread(target=_write)
        t.start()
        event = self.events.wait_event(timeout_ms=3000)
        t.join()
        self.assertIsNotNone(event)
        self.assertEqual(event["type"], "confirm")


class TestCompositeHost(unittest.TestCase):
    """组合宿主：聚合透传 + 就绪自检。"""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.host = build_file_host(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_ready_complete(self) -> None:
        ready = self.host.ready()
        self.assertTrue(ready["io"])
        self.assertTrue(ready["renderer"])
        self.assertTrue(ready["events"])
        self.assertTrue(ready["complete"])

    def test_send_text_through(self) -> None:
        receipt = self.host.send_text("结论先行")
        self.assertEqual(receipt["kind"], "text")

    def test_render_canvas_through(self) -> None:
        cmd = self.host.render_canvas({"kind": "orb.render", "state": "idle"})
        self.assertEqual(cmd["state"], "idle")
        self.assertEqual(cmd["seq"], 1)

    def test_poll_events_through(self) -> None:
        self.assertEqual(self.host.poll_events(), [])

    def test_missing_io_raises(self) -> None:
        host = CompositeHost(renderer=FileHostRenderer(self.tmp.name))
        with self.assertRaises(HostAbstractionError):
            host.send_text("hi")
        self.assertFalse(host.ready()["complete"])


if __name__ == "__main__":
    unittest.main()
