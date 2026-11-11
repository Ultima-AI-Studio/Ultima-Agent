#!/usr/bin/env python3
"""用官方 sherpa-onnx text2token 安全修改本地 KWS 唤醒词。"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
KWS_DIR = ROOT / "models" / "sherpa" / "kws"
MODEL_DIR = KWS_DIR / "sherpa-onnx-kws-zipformer-zh-en-3M-2025-12-20"
TOKENS_PATH = MODEL_DIR / "tokens.txt"
KEYWORDS_PATH = KWS_DIR / "keywords.txt"
KEYWORDS_RAW_PATH = KWS_DIR / "keywords_raw.txt"
TEXT2TOKEN_PATH = ROOT / "tools" / "venv-asr" / "Scripts" / "sherpa-onnx-cli.exe"
DAEMON_LOG_PATH = ROOT / "data" / "logs" / "voice-listen.log"
DAEMON_LOCK_PATH = ROOT / "data" / "logs" / "voice-listen-daemon.lock"
ULTIMA_FALLBACK = "AH1 L T IH0 M AH0 @ULTIMA"


class KwsReconfigError(ValueError):
    """可直接展示给使用者的改词错误。"""


class ChineseArgumentParser(argparse.ArgumentParser):
    def format_help(self) -> str:
        return (
            super()
            .format_help()
            .replace("usage:", "用法：", 1)
            .replace("options:", "可用参数：", 1)
        )


def _number_text(value: float) -> str:
    return str(value)


def _validate_settings(words: list[str], score: float, threshold: float) -> None:
    if not math.isfinite(score) or score < 0:
        raise KwsReconfigError("灵敏度加分必须是不小于 0 的有限数值")
    if not math.isfinite(threshold) or not 0 < threshold < 1:
        raise KwsReconfigError("触发阈值必须大于 0 且小于 1")
    if not words:
        raise KwsReconfigError("至少要提供一个唤醒词")
    for word in words:
        if not isinstance(word, str) or not word.strip():
            raise KwsReconfigError("唤醒词不能为空")
        if word != word.strip() or any(character.isspace() for character in word):
            raise KwsReconfigError("唤醒词不能含空格；需要分隔时请使用下划线 _")
        if "@" in word:
            raise KwsReconfigError("唤醒词中不能含 @，原文标记会由工具自动补上")


def tokenize_words(
    words: list[str], *, score: float, threshold: float
) -> list[dict[str, Any]]:
    """调用官方 text2token(ppinyin)，不提供任何备用音素化路径。"""
    _validate_settings(words, score, threshold)
    if not TEXT2TOKEN_PATH.is_file():
        raise KwsReconfigError(f"找不到官方转写工具：{TEXT2TOKEN_PATH}")
    if not TOKENS_PATH.is_file():
        raise KwsReconfigError(f"找不到模型词元表：{TOKENS_PATH}")

    score_text = _number_text(score)
    threshold_text = _number_text(threshold)
    with tempfile.TemporaryDirectory(prefix="ultima-kws-token-") as temporary_dir:
        input_path = Path(temporary_dir) / "input.txt"
        output_path = Path(temporary_dir) / "output.txt"
        input_path.write_text(
            "".join(
                f"{word} :{score_text} #{threshold_text} @{word}\n" for word in words
            ),
            encoding="utf-8",
        )
        command = [
            str(TEXT2TOKEN_PATH),
            "text2token",
            "--tokens",
            str(TOKENS_PATH),
            "--tokens-type",
            "ppinyin",
            str(input_path),
            str(output_path),
        ]
        try:
            completed = subprocess.run(
                command,
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise KwsReconfigError(f"官方唤醒词转写工具无法运行：{exc}") from exc
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout).strip()
            raise KwsReconfigError(
                f"官方唤醒词转写失败（退出码 {completed.returncode}）：{detail}"
            )
        try:
            lines = [
                line.strip()
                for line in output_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        except OSError as exc:
            raise KwsReconfigError(f"官方唤醒词转写没有生成可读结果：{exc}") from exc

    by_word: dict[str, str] = {}
    for line in lines:
        if "@" not in line:
            continue
        label = line.rsplit("@", 1)[1].strip()
        if label:
            by_word[label] = line
    missing = [word for word in words if word not in by_word]
    if missing:
        detail = completed.stderr.strip()
        suffix = f"；工具提示：{detail}" if detail else ""
        raise KwsReconfigError(f"以下唤醒词无法用官方词元表转写：{', '.join(missing)}{suffix}")
    return [
        {
            "word": word,
            "token_line": by_word[word],
            "score": score,
            "threshold": threshold,
        }
        for word in words
    ]


def parse_keyword_line(line: str) -> dict[str, Any]:
    stripped = line.strip()
    label = stripped.rsplit("@", 1)[1].strip() if "@" in stripped else ""
    score_match = re.search(r"(?:^|\s):([+-]?(?:\d+(?:\.\d*)?|\.\d+))(?=\s|$)", stripped)
    threshold_match = re.search(
        r"(?:^|\s)#([+-]?(?:\d+(?:\.\d*)?|\.\d+))(?=\s|$)", stripped
    )
    return {
        "word": label,
        "token_line": stripped,
        "score": float(score_match.group(1)) if score_match else None,
        "threshold": float(threshold_match.group(1)) if threshold_match else None,
    }


def list_keywords() -> dict[str, Any]:
    try:
        lines = [
            line.strip()
            for line in KEYWORDS_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except OSError as exc:
        raise KwsReconfigError(f"无法读取当前唤醒词表：{exc}") from exc
    return {
        "action": "list",
        "effective_keywords": [parse_keyword_line(line) for line in lines],
        "backup_path": None,
        "hot_reload": None,
    }


def validate_words(words: list[str], *, score: float, threshold: float) -> dict[str, Any]:
    entries = tokenize_words(words, score=score, threshold=threshold)
    return {
        "action": "validate",
        "valid": True,
        "token_lines": [entry["token_line"] for entry in entries],
        "effective_keywords": entries,
        "backup_path": None,
        "hot_reload": None,
    }


def _next_backup_path() -> Path:
    stamp = datetime.now()
    for _ in range(120):
        candidate = KEYWORDS_PATH.with_name(
            f"keywords-bak-{stamp.strftime('%Y%m%d%H%M%S')}.txt"
        )
        if not candidate.exists():
            return candidate
        stamp += timedelta(seconds=1)
    raise KwsReconfigError("无法生成不重复的唤醒词备份名称")


def _backup_keywords() -> Path:
    try:
        content = KEYWORDS_PATH.read_bytes()
        backup_path = _next_backup_path()
        with backup_path.open("xb") as backup_file:
            backup_file.write(content)
        return backup_path
    except OSError as exc:
        raise KwsReconfigError(f"备份当前唤醒词表失败：{exc}") from exc


def _atomic_write_text(path: Path, content: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_text(content, encoding="utf-8")
        os.replace(temporary, path)
    except OSError as exc:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise KwsReconfigError(f"原子更新 {path.name} 失败：{exc}") from exc


def _daemon_pid() -> int | None:
    try:
        value = int(DAEMON_LOCK_PATH.read_text(encoding="utf-8").strip())
        return value if value > 0 else None
    except (OSError, ValueError):
        return None


def _wait_for_hot_reload(
    *, mtime_ns: int, pid_before: int | None, log_offset: int, timeout: float = 20.0
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    success_pattern = re.compile(
        rf"KWS keywords 热重载成功 pid=(\d+) mtime_ns={mtime_ns}(?:\D|$)"
    )
    failure_marker = "KWS keywords 热重载失败"
    observed = ""
    while time.monotonic() < deadline:
        try:
            with DAEMON_LOG_PATH.open("rb") as log_file:
                log_file.seek(log_offset)
                observed = log_file.read().decode("utf-8", errors="replace")
        except OSError:
            observed = ""
        match = success_pattern.search(observed)
        if match:
            log_pid = int(match.group(1))
            pid_after = _daemon_pid()
            return {
                "requested": True,
                "success": pid_before is not None
                and pid_before == log_pid
                and pid_after == pid_before,
                "pid_before": pid_before,
                "pid_after": pid_after,
                "log_pid": log_pid,
                "same_pid": pid_before == log_pid == pid_after,
                "mtime_ns": mtime_ns,
                "log_line": match.group(0).strip(),
            }
        if failure_marker in observed:
            break
        time.sleep(0.1)
    return {
        "requested": True,
        "success": False,
        "pid_before": pid_before,
        "pid_after": _daemon_pid(),
        "log_pid": None,
        "same_pid": False,
        "mtime_ns": mtime_ns,
        "error": "等待同进程热重载成功日志超时或 daemon 报告重载失败",
    }


def _apply_keywords(lines: list[str]) -> None:
    """经冻结模块的公开接口完成原子替换，不改其实现。"""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from src.brain.voice import voice_profile

    original_path = voice_profile.KEYWORDS_PATH
    voice_profile.KEYWORDS_PATH = KEYWORDS_PATH
    try:
        profile = voice_profile.load_profile(
            {"wakeword": {"words": lines, "custom": None}}
        )
        if not voice_profile.apply_to_daemon(profile):
            raise KwsReconfigError("voice_profile.apply_to_daemon 未能更新唤醒词表")
    finally:
        voice_profile.KEYWORDS_PATH = original_path


def _profile_variants(word: str) -> list[str]:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from src.brain.voice.voice_profile import load_profile

    return [
        line.strip()
        for line in load_profile()["wakeword"]["words"]
        if line.strip().rsplit("@", 1)[-1].strip() == word
    ]


def _with_settings(line: str, *, score: float, threshold: float) -> str:
    tokens_and_settings, label = line.rsplit("@", 1)
    tokens = [
        item
        for item in tokens_and_settings.split()
        if not item.startswith(":") and not item.startswith("#")
    ]
    return (
        f"{' '.join(tokens)} :{_number_text(score)} #{_number_text(threshold)} "
        f"@{label.strip()}"
    )


def change_keywords(
    action: str,
    words: list[str],
    *,
    score: float,
    threshold: float,
    wait_for_reload: bool = True,
) -> dict[str, Any]:
    if action not in {"add", "replace"}:
        raise KwsReconfigError(f"不支持的改词动作：{action}")
    entries = tokenize_words(words, score=score, threshold=threshold)
    current = list_keywords()["effective_keywords"]
    current_lines = [item["token_line"] for item in current]
    ultima_line = next(
        (line for line in current_lines if line.rsplit("@", 1)[-1].strip() == "ULTIMA"),
        ULTIMA_FALLBACK,
    )
    if action == "add":
        final_lines = list(current_lines)
        existing_labels = {item["word"] for item in current}
        final_lines.extend(
            entry["token_line"] for entry in entries if entry["word"] not in existing_labels
        )
    else:
        final_lines = []
        for entry in entries:
            variants = _profile_variants(entry["word"])
            final_lines.extend(
                [
                    _with_settings(line, score=score, threshold=threshold)
                    for line in variants
                ]
                or [entry["token_line"]]
            )
        if not any(line.rsplit("@", 1)[-1].strip() == "ULTIMA" for line in final_lines):
            final_lines.append(ultima_line)

    backup_path = _backup_keywords()
    pid_before = _daemon_pid() if wait_for_reload else None
    try:
        log_offset = DAEMON_LOG_PATH.stat().st_size if wait_for_reload else 0
    except OSError:
        log_offset = 0
    _apply_keywords(final_lines)
    actual_lines = list_keywords()["effective_keywords"]
    raw_content = "".join(
        f"{item['word']} @{item['word']}\n" for item in actual_lines if item["word"]
    )
    _atomic_write_text(KEYWORDS_RAW_PATH, raw_content)
    mtime_ns = KEYWORDS_PATH.stat().st_mtime_ns
    hot_reload = (
        _wait_for_hot_reload(
            mtime_ns=mtime_ns, pid_before=pid_before, log_offset=log_offset
        )
        if wait_for_reload
        else {"requested": False, "success": None}
    )
    return {
        "action": action,
        "effective_keywords": actual_lines,
        "backup_path": str(backup_path.resolve()),
        "hot_reload": hot_reload,
        "token_lines": [entry["token_line"] for entry in entries],
    }


def _parser() -> argparse.ArgumentParser:
    parser = ChineseArgumentParser(
        description="安全查看、校验或修改本机语音唤醒词；改词前会自动备份。",
        add_help=False,
    )
    parser._optionals.title = "options"
    parser.add_argument("-h", "--help", action="help", help="显示这段帮助后退出")
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--add", nargs="+", metavar="唤醒词", help="保留现有词并追加新词")
    actions.add_argument("--replace", nargs="+", metavar="唤醒词", help="用新词整体替换，始终保留 ULTIMA")
    actions.add_argument("--list", action="store_true", help="查看当前生效词表")
    actions.add_argument("--validate", nargs="+", metavar="唤醒词", help="只检查能否转写，不改文件")
    parser.add_argument(
        "--score",
        type=float,
        default=2.0,
        metavar="加分值",
        help="新词灵敏度加分，默认 2.0，必须不小于 0",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.08,
        metavar="阈值",
        help="新词触发阈值，默认 0.08，必须在 0 和 1 之间",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    arguments = parser.parse_args(argv)
    try:
        if arguments.list:
            result = list_keywords()
        elif arguments.validate is not None:
            result = validate_words(
                arguments.validate,
                score=arguments.score,
                threshold=arguments.threshold,
            )
        else:
            action = "add" if arguments.add is not None else "replace"
            words = arguments.add if arguments.add is not None else arguments.replace
            result = change_keywords(
                action,
                words,
                score=arguments.score,
                threshold=arguments.threshold,
            )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result.get("hot_reload") and result["hot_reload"].get("success") is False:
            return 3
        return 0
    except KwsReconfigError as exc:
        print(
            json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
