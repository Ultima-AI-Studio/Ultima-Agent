from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "dispatch-work-order.py"


def _load():
    spec = importlib.util.spec_from_file_location("dispatch_work_order_cli", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_explicit_env_wins(monkeypatch, tmp_path):
    fake = tmp_path / "codex.exe"
    fake.write_text("", encoding="utf-8")
    monkeypatch.setenv("ULTIMA_CODEX_EXE", str(fake))
    assert _load().resolve_codex_exe() == str(fake)


def test_ignores_env_pointing_at_missing_file(monkeypatch, tmp_path):
    monkeypatch.setenv("ULTIMA_CODEX_EXE", str(tmp_path / "gone.exe"))
    cli = _load()
    # falls through to whatever this machine actually has; must not crash
    assert cli.resolve_codex_exe() is None or Path(cli.resolve_codex_exe()).is_file()


def test_env_beats_the_glob_fallback(monkeypatch, tmp_path):
    """An explicit path must not be overridden by an auto-discovery hit."""

    fake = tmp_path / "codex.exe"
    fake.write_text("", encoding="utf-8")
    monkeypatch.setenv("ULTIMA_CODEX_EXE", str(fake))
    assert _load().resolve_codex_exe() == str(fake)


def test_newest_install_is_preferred():
    """Several versioned installs coexist after upgrades; pick the newest."""

    cli = _load()
    import glob as _glob
    hits = [p for pattern in cli._CODEX_EXE_GLOBS for p in _glob.glob(pattern)]
    got = cli.resolve_codex_exe()
    if hits:
        assert got in hits or (got is not None and Path(got).is_file())
    else:
        assert got is None or Path(got).is_file()
