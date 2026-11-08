"""L7 语音入口接线：音频 → ASR → 桥接 → 悬浮球推送 → TTS 回放 闭环。

对齐 product-alignment-20261025（⑤ L7 语音入口接线）与 product-plan L7：
- 语音输入（麦克风 WAV）→ faster-whisper medium（daemon 常驻热缓存）转写；
- 转写文本 → InteractionOrbBridge.handle()（交互循环：查询/征询/调整/确认）；
- 桥接结果 → orb_command()（orb.render + prompt）→ HostOrbPusher 落盘
  → 壳常驻循环推送悬浮球（L4 A2 链路）；
- 响应文本 → tts_synthesize 合成回放 WAV（DEFECT-001 三层修复出口）；
- 各段结果结构化返回（asr/response/pushed/tts），失败分段留痕不静默。

写域：仅 H:\\UltimaAI\\UltimaAgent\\ 内。
"""

from __future__ import annotations

import json
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.brain.interaction_orb import InteractionOrbBridge
from src.brain.display.host_pusher import HostOrbPusher
from src.brain.voice.asr import asr_transcribe
from src.brain.voice.tts import tts_synthesize
from src.brain.voice.voice_profile import load_profile, save_user_override

_run_process = subprocess.run


class WakewordChangeCoordinator:
    """Run the frozen CLI off-thread and wait for daemon-side reload events."""

    def __init__(
        self,
        reply_dir: str | Path,
        *,
        profile_wait_timeout: float = 10.0,
        cli_timeout: float = 45.0,
    ) -> None:
        self.reply_dir = Path(reply_dir)
        self.reply_dir.mkdir(parents=True, exist_ok=True)
        self.profile_wait_timeout = profile_wait_timeout
        self.cli_timeout = cli_timeout
        self._state_lock = threading.Lock()
        self._active = False
        self._profile_event = threading.Event()
        self._profile_result: bool | None = None
        self._expected_profile_custom: str | None = None
        self._completions: queue.Queue[dict[str, Any]] = queue.Queue()

    def submit(self, custom: str) -> bool:
        """Start one transaction and return immediately; reject overlapping changes."""
        with self._state_lock:
            if self._active:
                return False
            self._active = True
        threading.Thread(
            target=self._run_transaction,
            args=(custom,),
            name="wakeword-change",
            daemon=True,
        ).start()
        return True

    def notify_daemon_reload(self, event: dict[str, Any]) -> None:
        """Receive reload/watcher completion emitted by the resident daemon thread."""
        if event.get("type") != "profile_applied":
            return
        with self._state_lock:
            if event.get("custom") != self._expected_profile_custom:
                return
            self._profile_result = event.get("success") is True
            self._profile_event.set()

    def poll_completion(self) -> dict[str, Any] | None:
        try:
            return self._completions.get_nowait()
        except queue.Empty:
            return None

    def _reset_profile_wait(self, expected_custom: str | None) -> None:
        with self._state_lock:
            self._expected_profile_custom = expected_custom
            self._profile_result = None
            self._profile_event.clear()

    def _wait_for_profile_apply(self) -> bool:
        if not self._profile_event.wait(self.profile_wait_timeout):
            return False
        with self._state_lock:
            return self._profile_result is True

    @staticmethod
    def _custom_label(custom: str | None) -> str | None:
        if not custom:
            return None
        return custom.rsplit("@", 1)[-1].strip() or None

    def _run_cli(self, custom: str | None) -> tuple[bool, str]:
        project_root = Path(__file__).resolve().parents[2]
        words = ["贾维斯"]
        label = self._custom_label(custom)
        if label and label != "贾维斯":
            words.append(label)
        command = [
            sys.executable,
            "-X",
            "utf8",
            str(project_root / "scripts" / "kws_reconfig.py"),
            "--replace",
            *words,
        ]
        try:
            completed = _run_process(
                command,
                cwd=project_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.cli_timeout,
                check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            result = json.loads(completed.stdout)
            reload_result = result.get("hot_reload")
            success = (
                completed.returncode == 0
                and isinstance(reload_result, dict)
                and reload_result.get("success") is True
                and reload_result.get("same_pid") is True
            )
            error = "" if success else str(
                (reload_result or {}).get("error")
                or result.get("error")
                or completed.stderr
                or f"CLI exit {completed.returncode}"
            )
            return success, error
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
            return False, str(exc)

    def _rollback(self, old_custom: str | None) -> bool:
        self._reset_profile_wait(old_custom)
        saved = save_user_override({"wakeword": {"custom": old_custom}})
        watcher_applied = self._wait_for_profile_apply()
        cli_ok, _ = self._run_cli(old_custom)
        restored = load_profile()["wakeword"].get("custom") == old_custom
        return bool(saved and watcher_applied and cli_ok and restored)

    def _run_transaction(self, custom: str) -> None:
        old_custom = load_profile()["wakeword"].get("custom")
        ok = False
        error = ""
        rollback_ok: bool | None = None
        try:
            first_ok, error = self._run_cli(custom)
            if not first_ok:
                rollback_ok = self._rollback(old_custom)
                return

            self._reset_profile_wait(custom)
            persisted = save_user_override({"wakeword": {"custom": custom}})
            if not persisted or load_profile()["wakeword"].get("custom") != custom:
                error = "profile save/apply failed"
                rollback_ok = self._rollback(old_custom)
                return
            if not self._wait_for_profile_apply():
                error = "daemon profile watcher confirmation timed out or failed"
                rollback_ok = self._rollback(old_custom)
                return

            second_ok, error = self._run_cli(custom)
            if not second_ok:
                rollback_ok = self._rollback(old_custom)
                return
            if load_profile()["wakeword"].get("custom") != custom:
                error = "profile verification failed after final reload"
                rollback_ok = self._rollback(old_custom)
                return
            ok = True
        except Exception as exc:
            error = str(exc)
            try:
                rollback_ok = self._rollback(old_custom)
            except Exception:
                rollback_ok = False
        finally:
            text = f"唤醒词已改为{custom}。" if ok else "唤醒词修改失败，请稍后再试。"
            output = self.reply_dir / f"wakeword-change-{time.time_ns()}.wav"
            try:
                tts = tts_synthesize(text, output, timeout=300)
                reply_wav = str(output) if tts.get("ok") else None
            except Exception as exc:
                tts = {"ok": False, "error": str(exc)}
                reply_wav = None
            self._completions.put(
                {
                    "ok": ok,
                    "custom": custom,
                    "text": text,
                    "error": error,
                    "rollback_ok": rollback_ok,
                    "tts": tts,
                    "reply_wav": reply_wav,
                }
            )
            with self._state_lock:
                self._active = False


class VoiceInteractionLoop:
    """语音入口闭环编排：ASR → 桥接 → 悬浮球推送 → TTS 回放。"""

    def __init__(
        self,
        queue_root: str | Path,
        command_file: str | Path,
        reply_dir: str | Path,
    ) -> None:
        self.reply_dir = Path(reply_dir)
        self.reply_dir.mkdir(parents=True, exist_ok=True)
        self.wakeword_changes = WakewordChangeCoordinator(self.reply_dir)
        self.bridge = InteractionOrbBridge(queue_root)
        self.bridge.loop.set_wakeword_change_submitter(self.wakeword_changes.submit)
        self.pusher = HostOrbPusher(command_file)

    def notify_wakeword_reload(self, event: dict[str, Any]) -> None:
        self.wakeword_changes.notify_daemon_reload(event)

    def poll_wakeword_completion(self) -> dict[str, Any] | None:
        return self.wakeword_changes.poll_completion()

    def handle_audio(
        self,
        wav_path: str | Path,
        *,
        detail_task_id: str | None = None,
        reply_timeout: int = 300,
    ) -> Dict[str, Any]:
        """处理一段语音输入，返回结构化结果。

        Returns
        -------
        dict:
            {
              ok, stage（asr/bridge/tts）, asr, response, pushed, tts,
              reply_wav, error（失败段）
            }
        """
        # 1. ASR 转写（daemon 常驻优先，冷启动兜底）
        wav = Path(wav_path)
        if not wav.is_file():
            return {"ok": False, "stage": "input", "error": f"音频不存在: {wav}"}
        try:
            asr = asr_transcribe(wav)
        except Exception as exc:
            return {"ok": False, "stage": "asr", "error": f"ASR 失败: {exc}"}
        text = (asr.get("text") or "").strip() if asr.get("ok") else ""
        if not text:
            return {"ok": False, "stage": "asr", "error": "ASR 无有效文本", "asr": asr}

        # 2. 桥接（交互循环语义映射）
        response = self.bridge.handle(text, detail_task_id=detail_task_id)
        # 空输入语义（桥接不迁移）也视作成功处理
        bridge_ok = response.ok or response.reason == "空输入"

        # 3. 悬浮球推送（L4 A2 链路）
        pushed = self.pusher.push(self.bridge.orb_command())

        # 4. TTS 回放（响应文本；空则不合成）
        tts: Dict[str, Any] | None = None
        reply_wav: str | None = None
        reply_text = response.text or ""
        if reply_text:
            out = self.reply_dir / f"reply-{pushed['seq']}.wav"
            try:
                tts = tts_synthesize(reply_text, out, timeout=reply_timeout)
                reply_wav = str(out) if tts.get("ok") else None
                tts_ok = bool(tts.get("ok"))
            except Exception as exc:
                tts = {"ok": False, "error": str(exc)}
                tts_ok = False
        else:
            tts_ok = True  # 无回放需求视为通过

        return {
            "ok": bridge_ok and tts_ok,
            "stage": "tts" if reply_text else "bridge",
            "asr": asr,
            "text": text,
            "response": response.to_dict() if hasattr(response, "to_dict") else {
                "handled": response.handled, "ok": response.ok,
                "text": response.text, "reason": response.reason,
                "state": response.state,
            },
            "pushed": pushed,
            "tts": tts,
            "reply_wav": reply_wav,
        }


__all__ = ["VoiceInteractionLoop", "WakewordChangeCoordinator"]
