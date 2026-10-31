from __future__ import annotations

import json
import subprocess
import sys
import wave
from pathlib import Path

import pytest

from scripts import kws_reconfig


T2_EVIDENCE = kws_reconfig.ROOT / "docs" / "reports" / "evidence" / "kws-reconfig" / "t2-verify"
_TTS_KWS_RESULTS: dict[tuple[str, str], dict[str, object]] = {}


def tts_kws_probe(
    text: str,
    *,
    keywords_path: Path | None = None,
    evidence_stem: str | None = None,
    source_wav: Path | None = None,
) -> dict[str, object]:
    active_keywords = keywords_path or kws_reconfig.KEYWORDS_PATH
    keywords_sha1 = __import__("hashlib").sha1(active_keywords.read_bytes()).hexdigest()
    cache_key = (text, keywords_sha1)
    cached = _TTS_KWS_RESULTS.get(cache_key)
    if cached is not None:
        return cached

    import numpy as np
    import sherpa_onnx

    from src.brain.voice._resample import resample_to_16k
    from src.brain.voice.tts import tts_synthesize

    T2_EVIDENCE.mkdir(parents=True, exist_ok=True)
    stem = evidence_stem or {
        "查天气": "new-word",
        "你好贾维斯": "retained-jarvis",
        "星期五": "replaced-word",
    }.get(text, "probe-" + __import__("hashlib").sha1(text.encode("utf-8")).hexdigest()[:8])
    if source_wav is None:
        wav_path = T2_EVIDENCE / f"{stem}.wav"
        tts_result = tts_synthesize(text, wav_path)
        assert tts_result.get("ok") is True, tts_result
    else:
        wav_path = source_wav
        tts_result = {"ok": True, "reused_wav": str(source_wav)}

    with wave.open(str(wav_path), "rb") as reader:
        assert reader.getsampwidth() == 2
        sample_rate = reader.getframerate()
        channels = reader.getnchannels()
        pcm = np.frombuffer(reader.readframes(reader.getnframes()), dtype=np.int16)
    frames = pcm.reshape(-1, channels).astype(np.float32) / 32768.0
    mono = frames.mean(axis=1, dtype=np.float32)
    samples = resample_to_16k(mono, sample_rate)
    samples = np.concatenate((samples, np.zeros(32000, dtype=np.float32)))

    model = kws_reconfig.MODEL_DIR
    spotter = sherpa_onnx.KeywordSpotter(
        tokens=str(model / "tokens.txt"),
        encoder=str(model / "encoder-epoch-13-avg-2-chunk-8-left-64.int8.onnx"),
        decoder=str(model / "decoder-epoch-13-avg-2-chunk-8-left-64.onnx"),
        joiner=str(model / "joiner-epoch-13-avg-2-chunk-8-left-64.onnx"),
        keywords_file=str(active_keywords),
        num_threads=2,
        sample_rate=16000,
        max_active_paths=8,
        keywords_score=2.0,
        keywords_threshold=0.08,
        num_trailing_blanks=8,
        provider="cpu",
    )
    stream = spotter.create_stream()
    hits: list[str] = []
    for start in range(0, len(samples), 3200):
        block = samples[start : start + 3200]
        if len(block) < 3200:
            block = np.pad(block, (0, 3200 - len(block)))
        stream.accept_waveform(16000, block)
        while spotter.is_ready(stream):
            spotter.decode_stream(stream)
            hit = spotter.get_result(stream)
            if hit:
                hits.append(hit)
                spotter.reset_stream(stream)

    result: dict[str, object] = {
        "text": text,
        "wav": str(wav_path.relative_to(kws_reconfig.ROOT)),
        "tts": tts_result,
        "source_rate": sample_rate,
        "source_channels": channels,
        "source_peak": round(float(np.abs(mono).max()), 6),
        "kws_rate": 16000,
        "keywords_sha1": keywords_sha1,
        "params": {"score": 2.0, "threshold": 0.08, "trailing_blanks": 8},
        "hits": hits,
    }
    (T2_EVIDENCE / f"{stem}.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    _TTS_KWS_RESULTS[cache_key] = result
    return result


def test_direct_script_context_can_import_voice_profile(tmp_path: Path) -> None:
    keywords = tmp_path / "keywords.txt"
    keywords.write_text("AH1 L T IH0 M AH0 @ULTIMA\n", encoding="utf-8")
    code = (
        "import sys; "
        f"sys.path[0] = {str(kws_reconfig.ROOT / 'scripts')!r}; "
        "import kws_reconfig; "
        f"kws_reconfig.KEYWORDS_PATH = __import__('pathlib').Path({str(keywords)!r}); "
        "kws_reconfig._apply_keywords(['ch á t iān q ì :2.0 #0.08 @查天气', "
        "'AH1 L T IH0 M AH0 @ULTIMA'])"
    )
    completed = subprocess.run(
        [sys.executable, "-X", "utf8", "-c", code],
        cwd=kws_reconfig.ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert "@查天气" in keywords.read_text(encoding="utf-8")


def _configure_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    keywords = tmp_path / "keywords.txt"
    raw = tmp_path / "keywords_raw.txt"
    keywords.write_text(
        "j iǎ w éi s ī @贾维斯\nAH1 L T IH0 M AH0 @ULTIMA\n",
        encoding="utf-8",
    )
    raw.write_text("贾维斯 @贾维斯\nULTIMA @ULTIMA\n", encoding="utf-8")
    monkeypatch.setattr(kws_reconfig, "KEYWORDS_PATH", keywords)
    monkeypatch.setattr(kws_reconfig, "KEYWORDS_RAW_PATH", raw)
    return keywords, raw


def test_official_ppinyin_tokenizes_chinese_word() -> None:
    entries = kws_reconfig.tokenize_words(["查天气"], score=2.0, threshold=0.08)
    assert entries == [
        {
            "word": "查天气",
            "token_line": "ch á t iān q ì :2.0 #0.08 @查天气",
            "score": 2.0,
            "threshold": 0.08,
        }
    ]


@pytest.mark.parametrize(
    ("words", "score", "threshold", "message"),
    [
        ([""], 2.0, 0.08, "不能为空"),
        (["查 天气"], 2.0, 0.08, "空格"),
        (["查天气"], -0.1, 0.08, "加分"),
        (["查天气"], 2.0, 1.0, "阈值"),
    ],
)
def test_invalid_input_is_rejected_before_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    words: list[str],
    score: float,
    threshold: float,
    message: str,
) -> None:
    keywords, _ = _configure_paths(tmp_path, monkeypatch)
    before = keywords.read_bytes()
    with pytest.raises(kws_reconfig.KwsReconfigError, match=message):
        kws_reconfig.change_keywords(
            "add", words, score=score, threshold=threshold, wait_for_reload=False
        )
    assert keywords.read_bytes() == before
    assert not list(tmp_path.glob("keywords-bak-*.txt"))


def test_add_preserves_existing_words_and_writes_backup_and_raw(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    keywords, raw = _configure_paths(tmp_path, monkeypatch)
    before = keywords.read_text(encoding="utf-8")

    result = kws_reconfig.change_keywords(
        "add", ["查天气"], score=2.0, threshold=0.08, wait_for_reload=False
    )

    lines = keywords.read_text(encoding="utf-8").splitlines()
    assert lines[:2] == before.splitlines()
    assert lines[-1] == "ch á t iān q ì :2.0 #0.08 @查天气"
    backup = Path(result["backup_path"])
    assert backup.name.startswith("keywords-bak-")
    assert backup.read_text(encoding="utf-8") == before
    assert raw.read_text(encoding="utf-8").splitlines() == [
        "贾维斯 @贾维斯",
        "ULTIMA @ULTIMA",
        "查天气 @查天气",
    ]
    assert result["hot_reload"] == {"requested": False, "success": None}


def test_replace_removes_old_words_but_always_preserves_ultima(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    keywords, _ = _configure_paths(tmp_path, monkeypatch)

    result = kws_reconfig.change_keywords(
        "replace", ["查天气"], score=2.0, threshold=0.08, wait_for_reload=False
    )

    lines = keywords.read_text(encoding="utf-8").splitlines()
    assert lines == [
        "ch á t iān q ì :2.0 #0.08 @查天气",
        "AH1 L T IH0 M AH0 @ULTIMA",
    ]
    assert [item["word"] for item in result["effective_keywords"]] == [
        "查天气",
        "ULTIMA",
    ]
    assert "贾维斯" not in json.dumps(result, ensure_ascii=False)


def test_replace_keeps_all_profile_variants_for_a_requested_retained_word(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    keywords, _ = _configure_paths(tmp_path, monkeypatch)

    kws_reconfig.change_keywords(
        "replace", ["贾维斯", "查天气"], score=2.0, threshold=0.08, wait_for_reload=False
    )

    lines = keywords.read_text(encoding="utf-8").splitlines()
    assert sum(line.endswith("@贾维斯") for line in lines) == 6
    assert "ch á t iān q ì :2.0 #0.08 @查天气" in lines
    assert lines[-1].endswith("@ULTIMA")


def test_replace_applies_requested_settings_to_every_retained_variant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    keywords, _ = _configure_paths(tmp_path, monkeypatch)

    kws_reconfig.change_keywords(
        "replace", ["贾维斯"], score=4.0, threshold=0.2, wait_for_reload=False
    )

    variants = [
        line
        for line in keywords.read_text(encoding="utf-8").splitlines()
        if line.endswith("@贾维斯")
    ]
    assert len(variants) == 6
    assert all(" :4.0 #0.2 @贾维斯" in line for line in variants)


def test_validate_does_not_write_keywords(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    keywords, _ = _configure_paths(tmp_path, monkeypatch)
    before = keywords.read_bytes()

    result = kws_reconfig.validate_words(["查天气"], score=2.0, threshold=0.08)

    assert result["valid"] is True
    assert result["token_lines"] == ["ch á t iān q ì :2.0 #0.08 @查天气"]
    assert keywords.read_bytes() == before
    assert not list(tmp_path.glob("keywords-bak-*.txt"))


def test_daemon_pid_uses_single_instance_lock_when_cross_boundary_probe_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lock = tmp_path / "voice-listen-daemon.lock"
    lock.write_text("14068", encoding="utf-8")
    monkeypatch.setattr(kws_reconfig, "DAEMON_LOCK_PATH", lock)

    def deny_cross_boundary_probe(_pid: int, _signal: int) -> None:
        raise PermissionError("sandbox process boundary")

    monkeypatch.setattr(kws_reconfig.os, "kill", deny_cross_boundary_probe)
    assert kws_reconfig._daemon_pid() == 14068


def test_help_text_is_plain_chinese() -> None:
    help_text = kws_reconfig._parser().format_help()
    assert "用法：" in help_text
    assert "可用参数：" in help_text
    assert "显示这段帮助" in help_text
    assert "usage:" not in help_text
    assert "options:" not in help_text
    assert "show this help" not in help_text


@pytest.mark.parametrize(
    "arguments",
    [
        ["--add", ""],
        ["--add", "查 天气"],
        ["--add", "查天气", "--threshold", "1.0"],
    ],
)
def test_invalid_cli_returns_nonzero_without_writing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arguments: list[str],
) -> None:
    keywords, _ = _configure_paths(tmp_path, monkeypatch)
    before = keywords.read_bytes()
    assert kws_reconfig.main(arguments) != 0
    assert keywords.read_bytes() == before
    assert not list(tmp_path.glob("keywords-bak-*.txt"))


def test_tts_new_wakeword_hits_offline_kws() -> None:
    result = tts_kws_probe("查天气")
    assert "查天气" in result["hits"]


def test_tts_retained_jarvis_hits_offline_kws() -> None:
    result = tts_kws_probe("你好贾维斯")
    assert "贾维斯" in result["hits"]


def test_tts_replaced_word_does_not_hit_offline_kws(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    keywords, _ = _configure_paths(tmp_path, monkeypatch)
    kws_reconfig.change_keywords(
        "add", ["星期五"], score=2.0, threshold=0.08, wait_for_reload=False
    )
    before = tts_kws_probe(
        "今天星期五", keywords_path=keywords, evidence_stem="replaced-word-before"
    )
    assert before["hits"] == ["星期五"]

    kws_reconfig.change_keywords(
        "replace", ["贾维斯", "查天气"], score=2.0, threshold=0.08, wait_for_reload=False
    )
    before_wav = kws_reconfig.ROOT / str(before["wav"])
    after = tts_kws_probe(
        "今天星期五",
        keywords_path=keywords,
        evidence_stem="replaced-word-after",
        source_wav=before_wav,
    )
    assert after["hits"] == []
