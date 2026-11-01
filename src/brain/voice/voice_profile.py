"""Voice-profile loading for the local voice chain.

L1 is the immutable built-in profile below, L2 is ``config/voice-profile.json``,
and L3 is the optional in-memory override passed to :func:`load_profile`.
Configuration loading intentionally uses only the Python standard library.
"""

from __future__ import annotations

import copy
import json
import logging
import re
import subprocess
import wave
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
PROFILE_PATH = ROOT / "config" / "voice-profile.json"
KEYWORDS_PATH = ROOT / "models" / "sherpa" / "kws" / "keywords.txt"
JARVIS_PERSONA_PATH = (
    ROOT
    / "libs"
    / "base"
    / "openjarvis"
    / "configs"
    / "openjarvis"
    / "prompts"
    / "personas"
    / "jarvis.md"
)

DEFAULT_WAKE_WORDS = [
    "j iǎ w éi s ī @贾维斯",
    "j ià w éi s ī @贾维斯",
    "j iā w éi s ī @贾维斯",
    "j iǎ w ei s ī @贾维斯",
    "j iǎ w éi s i @贾维斯",
    "j iǎ w éi s @贾维斯",
]
DEFAULT_WAKE_ECHO_ROOTS = ("贾维斯", "乔维斯")
_ULTIMA_KEYWORD = "AH1 L T IH0 M AH0 @ULTIMA"
_BUILTIN_JARVIS_PROMPT = """You are Jarvis, a loyal, efficient, dry-witted local AI assistant with the calm refinement of a British butler.
Only answer facts present in the provided data or the user's actual question. Never invent.
Never include marketing, promotion, or engagement content.
Keep spoken replies to 2 short sentences maximum. No filler."""

DEFAULT_PROFILE: dict[str, Any] = {
    "persona": {"name": "jarvis", "override": None},
    "wakeword": {"words": DEFAULT_WAKE_WORDS, "custom": None},
    "style": {
        "mode": "efficient-jarvis",
        "banned_phrases": ["关注", "点赞", "订阅", "点个关注"],
        "max_sentences": 2,
    },
    "voice": {
        "engine": "cv3",
        "ref_audio": "data/voice/jarvis-ref/jarvis_voice_ref_pcm16.wav",
        "prompt_text": None,
    },
    "input": {
        "mode": "auto",
        "device_index": None,
        "prefer_wasapi48k": True,
    },
}

_L2_FIELDS = {
    "persona": {"override"},
    "wakeword": {"custom"},
    "style": {"mode", "banned_phrases", "max_sentences"},
    "voice": {"engine", "ref_audio", "prompt_text"},
    "input": {"mode", "device_index", "prefer_wasapi48k"},
}

_AUDIO_SUFFIXES = {".wav", ".flac", ".mp3", ".ogg", ".m4a", ".aac", ".opus"}


def is_usable_reference_audio(path: Path) -> bool:
    """Return whether *path* is a non-empty supported audio reference."""
    try:
        if not path.is_file() or path.stat().st_size <= 0:
            return False
        suffix = path.suffix.lower()
        if suffix not in _AUDIO_SUFFIXES:
            return False
        if suffix != ".wav":
            return True
        with wave.open(str(path), "rb") as reader:
            return (
                reader.getnchannels() > 0
                and reader.getsampwidth() > 0
                and reader.getframerate() > 0
                and reader.getnframes() > 0
            )
    except (EOFError, OSError, wave.Error):
        return False


def _merge_known(target: dict[str, Any], source: dict[str, Any]) -> None:
    """Merge only keys already present in *target*."""
    for key, value in source.items():
        if key not in target:
            continue
        if isinstance(target[key], dict) and isinstance(value, dict):
            _merge_known(target[key], value)
        else:
            target[key] = copy.deepcopy(value)


def validate_profile(profile: object) -> dict[str, Any]:
    """Return a complete profile, replacing invalid fields with L1 defaults."""
    result = copy.deepcopy(DEFAULT_PROFILE)
    if not isinstance(profile, dict):
        return result
    _merge_known(result, profile)

    persona = result["persona"]
    if not isinstance(persona.get("name"), str) or not persona["name"].strip():
        persona["name"] = DEFAULT_PROFILE["persona"]["name"]
    override = persona.get("override")
    if override is not None and (not isinstance(override, str) or not override.strip()):
        persona["override"] = None

    wakeword = result["wakeword"]
    words = wakeword.get("words")
    if not isinstance(words, list) or not words or not all(
        isinstance(word, str) and word.strip() for word in words
    ):
        wakeword["words"] = copy.deepcopy(DEFAULT_WAKE_WORDS)
    else:
        wakeword["words"] = [word.strip() for word in words]
    custom = wakeword.get("custom")
    if custom is not None and (not isinstance(custom, str) or not custom.strip()):
        wakeword["custom"] = None

    style = result["style"]
    if not isinstance(style.get("mode"), str) or not style["mode"].strip():
        style["mode"] = DEFAULT_PROFILE["style"]["mode"]
    banned = style.get("banned_phrases")
    if not isinstance(banned, list) or not all(
        isinstance(phrase, str) and phrase.strip() for phrase in banned
    ):
        style["banned_phrases"] = copy.deepcopy(DEFAULT_PROFILE["style"]["banned_phrases"])
    else:
        style["banned_phrases"] = [phrase.strip() for phrase in banned]
    max_sentences = style.get("max_sentences")
    if isinstance(max_sentences, bool) or not isinstance(max_sentences, int) or not 1 <= max_sentences <= 10:
        style["max_sentences"] = DEFAULT_PROFILE["style"]["max_sentences"]

    voice = result["voice"]
    if not isinstance(voice, dict):
        voice = copy.deepcopy(DEFAULT_PROFILE["voice"])
        result["voice"] = voice
    engine = voice.get("engine")
    # 2026-10-30 声音换回：允许显式本地引擎 sherpa(MeloTTS 44100Hz 女声)/piper，
    # 供"换回以前女声（与 KWS 提示音同源）"配置；cv3=edge 兼容历史冻结。
    if not isinstance(engine, str) or engine not in {"cv3", "edge", "sherpa", "piper"}:
        voice["engine"] = DEFAULT_PROFILE["voice"]["engine"]
    ref_audio = voice.get("ref_audio")
    if not isinstance(ref_audio, str) or not ref_audio.strip():
        voice["ref_audio"] = DEFAULT_PROFILE["voice"]["ref_audio"]
    else:
        ref_audio = ref_audio.strip()
        ref_path = Path(ref_audio).expanduser()
        if not ref_path.is_absolute():
            ref_path = ROOT / ref_path
        if is_usable_reference_audio(ref_path):
            voice["ref_audio"] = ref_audio
        else:
            LOGGER.warning(
                "voice reference audio unavailable or invalid; using L1 Jarvis reference: %s",
                ref_path,
            )
            voice["ref_audio"] = DEFAULT_PROFILE["voice"]["ref_audio"]
    prompt_text = voice.get("prompt_text")
    if prompt_text is not None and (
        not isinstance(prompt_text, str) or not prompt_text.strip()
    ):
        voice["prompt_text"] = None

    input_config = result["input"]
    if input_config.get("mode") not in {"auto", "manual"}:
        input_config["mode"] = DEFAULT_PROFILE["input"]["mode"]
    device_index = input_config.get("device_index")
    if (
        device_index is not None
        and (isinstance(device_index, bool) or not isinstance(device_index, int) or device_index < 0)
    ):
        input_config["device_index"] = None
    if not isinstance(input_config.get("prefer_wasapi48k"), bool):
        input_config["prefer_wasapi48k"] = DEFAULT_PROFILE["input"]["prefer_wasapi48k"]
    return result


def _read_l2() -> dict[str, Any] | None:
    try:
        value = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        LOGGER.warning("voice profile unavailable; using L1 defaults: %s", exc)
        return None
    if not isinstance(value, dict):
        LOGGER.warning("voice profile root is not an object; using L1 defaults")
        return None
    return value


def load_profile(runtime_overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Load L1, overlay L2, then overlay L3; never raise for bad config files."""
    profile = copy.deepcopy(DEFAULT_PROFILE)
    l2 = _read_l2()
    if l2 is not None:
        _merge_known(profile, l2)
    profile = validate_profile(profile)
    if isinstance(runtime_overrides, dict):
        _merge_known(profile, runtime_overrides)
        profile = validate_profile(profile)
    return profile


def save_user_override(overrides: dict[str, Any]) -> bool:
    """Persist declared L2 fields atomically, preserving all other profile data."""
    if not isinstance(overrides, dict):
        return False
    raw = _read_l2()
    profile = validate_profile(raw if raw is not None else DEFAULT_PROFILE)
    for section, allowed in _L2_FIELDS.items():
        incoming = overrides.get(section)
        if not isinstance(incoming, dict):
            continue
        for key in allowed:
            if key in incoming:
                profile[section][key] = copy.deepcopy(incoming[key])
    profile = validate_profile(profile)
    temporary = PROFILE_PATH.with_suffix(PROFILE_PATH.suffix + ".tmp")
    try:
        PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_text(
            json.dumps(profile, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(PROFILE_PATH)
    except OSError as exc:
        LOGGER.warning("failed to save voice profile override: %s", exc)
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        return False
    if isinstance(overrides.get("wakeword"), dict) and "custom" in overrides["wakeword"]:
        return apply_to_daemon(profile)
    return True


def _custom_keyword_line(custom: str) -> str | None:
    custom = custom.strip()
    if not custom:
        return None
    if "@" in custom:
        tokens, label = custom.rsplit("@", 1)
        if tokens.strip() and label.strip():
            return f"{tokens.strip()} @{label.strip()}"
        return None
    if re.fullmatch(r"[\u4e00-\u9fff]+", custom):
        try:
            from pypinyin import Style, pinyin  # KWS/ASR environment dependency

            initials = pinyin(custom, style=Style.INITIALS, strict=False)
            finals = pinyin(custom, style=Style.FINALS_TONE, strict=False)
            pairs = [[initial[0], final[0]] for initial, final in zip(initials, finals)]
        except ImportError:
            pairs = _phonemize_with_asr_runtime(custom)
        except ValueError as exc:
            LOGGER.warning("cannot phonemize custom wakeword %r: %s", custom, exc)
            return None
        if pairs is None:
            return None
        tokens: list[str] = []
        for initial, final in pairs:
            if initial:
                tokens.append(initial)
            if final:
                tokens.append(final)
        if tokens:
            return f"{' '.join(tokens)} @{custom}"
        return None
    LOGGER.warning("custom wakeword must be Chinese text or a token line ending in @label")
    return None


def _phonemize_with_asr_runtime(text: str) -> list[list[str]] | None:
    """Use the pinned ASR interpreter when the Agent environment lacks pypinyin."""
    interpreter = ROOT / "tools" / "venv-asr" / "Scripts" / "python.exe"
    script = (
        "import json,sys; from pypinyin import Style,pinyin; t=sys.argv[1]; "
        "a=pinyin(t,style=Style.INITIALS,strict=False); "
        "b=pinyin(t,style=Style.FINALS_TONE,strict=False); "
        "print(json.dumps([[x[0],y[0]] for x,y in zip(a,b)],ensure_ascii=False))"
    )
    try:
        completed = subprocess.run(
            [str(interpreter), "-X", "utf8", "-c", script, text],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=15,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or f"exit {completed.returncode}")
        value = json.loads(completed.stdout)
        if not isinstance(value, list) or not all(
            isinstance(pair, list)
            and len(pair) == 2
            and all(isinstance(item, str) for item in pair)
            for pair in value
        ):
            raise ValueError("invalid pinyin payload")
        return value
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, RuntimeError, ValueError) as exc:
        LOGGER.warning("ASR runtime cannot phonemize custom wakeword %r: %s", text, exc)
        return None


def _keyword_lines(profile: dict[str, Any]) -> list[str] | None:
    lines = list(profile["wakeword"]["words"])
    custom = profile["wakeword"].get("custom")
    if custom:
        custom_line = _custom_keyword_line(custom)
        if custom_line is None:
            return None
        if custom_line not in lines:
            lines.append(custom_line)
    ultima_line = _ULTIMA_KEYWORD
    try:
        for line in KEYWORDS_PATH.read_text(encoding="utf-8").splitlines():
            if line.strip().endswith("@ULTIMA"):
                ultima_line = line.strip()
                break
    except OSError:
        pass
    if ultima_line not in lines:
        lines.append(ultima_line)
    return lines


def apply_to_daemon(
    profile: dict[str, Any] | None = None,
    *,
    listener: object | None = None,
) -> bool:
    """Sync keywords atomically and optionally request an in-process reload.

    The resident daemon watches ``keywords.txt`` mtime, so replacing this file
    is the cross-process reload signal; no process restart is involved.
    """
    validated = validate_profile(profile if profile is not None else load_profile())
    lines = _keyword_lines(validated)
    if lines is None:
        return False
    temporary = KEYWORDS_PATH.with_suffix(KEYWORDS_PATH.suffix + ".tmp")
    try:
        KEYWORDS_PATH.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
        temporary.replace(KEYWORDS_PATH)
    except OSError as exc:
        LOGGER.warning("failed to sync wakeword keywords: %s", exc)
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        return False
    if listener is not None:
        reload_keywords = getattr(listener, "reload_keywords", None)
        if not callable(reload_keywords):
            return False
        try:
            return bool(reload_keywords())
        except Exception as exc:  # caller's live listener must remain usable
            LOGGER.warning("live keyword reload failed: %s", exc)
            return False
    return True


def get_wake_echo_roots(profile: dict[str, Any] | None = None) -> tuple[str, ...]:
    """Return ASR wakeword roots, including the current L2 custom label."""
    loaded = validate_profile(profile if profile is not None else load_profile())
    roots: list[str] = list(DEFAULT_WAKE_ECHO_ROOTS)
    for keyword in loaded["wakeword"]["words"]:
        if "@" in keyword:
            roots.append(keyword.rsplit("@", 1)[1].strip())
    custom = loaded["wakeword"].get("custom")
    if custom:
        roots.append(custom.rsplit("@", 1)[-1].strip())
    return tuple(dict.fromkeys(root for root in roots if root))


def _persona_override_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else ROOT / path


def load_persona(profile: dict[str, Any] | None = None) -> str:
    """Load the L2 persona when valid; otherwise fail closed to L1 Jarvis."""
    loaded = validate_profile(profile if profile is not None else load_profile())
    override = loaded["persona"].get("override")
    if override:
        path = _persona_override_path(override)
        try:
            content = path.read_text(encoding="utf-8").strip()
            if content:
                return content
            LOGGER.warning("persona override is empty; falling back to Jarvis: %s", path)
        except OSError as exc:
            LOGGER.warning("persona override unavailable; falling back to Jarvis: %s", exc)
    try:
        content = JARVIS_PERSONA_PATH.read_text(encoding="utf-8").strip()
        if content:
            return content
        LOGGER.warning("Jarvis persona file is empty; using built-in Jarvis template")
    except OSError as exc:
        LOGGER.warning("Jarvis persona file unavailable; using built-in template: %s", exc)
    return _BUILTIN_JARVIS_PROMPT


def compose_agent_query(question: str, persona: str) -> str:
    """Carry the selected persona into the local agent request."""
    return (
        f"{persona}\n\nUSER QUESTION:\n{question}\n\n"
        "Answer under the persona constraints above.\n"
        "回答规则（必须遵守）：\n"
        "1. 直接回答用户问的问题本身，禁止反问用户或让用户换一种问法；\n"
        "2. 不知道、不确定或没有把握的事实，明确回答'我不确定/我无法确认'，禁止编造数字与事实，"
        "也禁止用'没有/不存在/请提供更多信息'一类话术回避问题；\n"
        "3. 口语化，控制在三句以内。"
    )


def _has_marketing_phrase(text: str, phrases: list[str]) -> bool:
    for phrase in phrases:
        if phrase not in text:
            continue
        if phrase not in {"关注", "点赞", "订阅"}:
            return True
        escaped = re.escape(phrase)
        if re.search(
            rf"(?:请|记得|欢迎|别忘了|点击|点个|求|帮忙).{{0,4}}{escaped}|"
            rf"{escaped}(?:我|我们|账号|频道|主播|作者|支持)",
            text,
        ):
            return True
    return False


def filter_reply(text: str, profile: dict[str, Any] | None = None) -> str:
    """Apply marketing safety and the spoken sentence limit."""
    if not text:
        return text
    loaded = validate_profile(profile if profile is not None else load_profile())
    if _has_marketing_phrase(text, loaded["style"]["banned_phrases"]):
        return "收到。"
    limit = loaded["style"]["max_sentences"]
    sentences = re.findall(r"[^。！？!?]+[。！？!?]?", text)
    if len(sentences) <= limit:
        return text
    return "".join(sentences[:limit]).strip()


__all__ = [
    "DEFAULT_PROFILE",
    "DEFAULT_WAKE_ECHO_ROOTS",
    "JARVIS_PERSONA_PATH",
    "KEYWORDS_PATH",
    "PROFILE_PATH",
    "ROOT",
    "apply_to_daemon",
    "compose_agent_query",
    "filter_reply",
    "get_wake_echo_roots",
    "load_profile",
    "load_persona",
    "save_user_override",
    "validate_profile",
]
