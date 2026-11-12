"""The environment contract has to catch a missing dependency, and release has to be safe.

The two properties worth locking down:

1. A checkout that has nothing reports its required assets as blocking and exits 2.
   If this regressed to exit 0, a broken checkout would look ready and every order
   would again be diagnosed from scratch.
2. `release()` unlinks only the link. `shutil.rmtree` follows a junction on Windows
   and deletes the real target's contents, so the assertion here is that the source
   tree is untouched after a mount/release round trip.
"""

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

_spec = importlib.util.spec_from_file_location(
    "env_contract", ROOT / "scripts" / "env_contract.py")
env = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(env)


def _fake_repo(base: Path, *, libs: bool = False, runner: bool = False,
               secrets: bool = False) -> Path:
    root = base / "repo"
    root.mkdir(parents=True, exist_ok=True)
    if libs:
        prompt = (root / "libs/base/openjarvis/configs/openjarvis/prompts/"
                  "personas/jarvis.md")
        prompt.parent.mkdir(parents=True, exist_ok=True)
        prompt.write_text("persona", encoding="utf-8")
    if runner:
        exe = root / "tools/venv-openjarvis/Scripts/python.exe"
        exe.parent.mkdir(parents=True, exist_ok=True)
        exe.write_bytes(b"MZ")
    if secrets:
        (root / "config").mkdir(parents=True, exist_ok=True)
        (root / "config/.env").write_text("DEEPSEEK_API_KEY=x", encoding="utf-8")
    return root


class StatusTest(unittest.TestCase):
    def test_empty_checkout_reports_both_required_assets_as_blocking(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = env.status(_fake_repo(Path(tmp)))
        blocking = [r["id"] for r in env.blocking(rows)]
        self.assertEqual(sorted(blocking), ["libs", "runner"],
                         "an empty checkout must block on libs and runner")

    def test_optional_assets_never_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = env.status(_fake_repo(Path(tmp), libs=True, runner=True))
        self.assertEqual(env.blocking(rows), [],
                         "secrets and ollama are optional; their absence is a cost, "
                         "not a blocker")

    def test_probe_is_the_prompt_file_not_merely_the_directory(self):
        """A directory named libs proves only that someone made a directory."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            (root / "libs").mkdir(parents=True)
            rows = env.status(root)
        libs = next(r for r in rows if r["id"] == "libs")
        self.assertFalse(libs["present"],
                         "libs/ without the persona prompt is not usable")

    def test_every_asset_states_what_its_absence_costs(self):
        rows = env.status(ROOT)
        for row in rows:
            if row["required"]:
                self.assertTrue(row["absent_effect"],
                                f"{row['id']} is required but names no cost")

    def test_cli_exit_code_tracks_blocking(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc = env.main(["--check", "--root", str(_fake_repo(Path(tmp))), "--json"])
        self.assertEqual(rc, 2, "a blocking checkout must not exit 0")


class RoundTripTest(unittest.TestCase):
    def _source(self, base: Path) -> Path:
        src = base / "source"
        prompt = (src / "libs/base/openjarvis/configs/openjarvis/prompts/"
                  "personas/jarvis.md")
        prompt.parent.mkdir(parents=True, exist_ok=True)
        prompt.write_text("persona", encoding="utf-8")
        (src / "libs" / "marker.txt").write_text("kept", encoding="utf-8")
        return src

    def test_apply_then_release_leaves_the_source_intact(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            src = self._source(base)
            wt = base / "wt"
            wt.mkdir()
            before = sorted(p.relative_to(src).as_posix()
                            for p in src.rglob("*") if p.is_file())

            applied = env.apply(wt, src)
            self.assertTrue(all(r["ok"] for r in applied), applied)
            self.assertTrue((wt / "libs").is_dir())

            released = env.release(wt)
            self.assertTrue(all(r["ok"] for r in released), released)
            self.assertFalse(os.path.lexists(wt / "libs"),
                             "release must remove the link itself")

            # Computed inside the block: outside it the temporary directory is
            # already gone, and comparing against that would pass no matter what
            # release did to the real target.
            after = sorted(p.relative_to(src).as_posix()
                           for p in src.rglob("*") if p.is_file())

        self.assertEqual(before, after,
                         "release followed the link and touched the real target")

    def test_apply_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            src = self._source(base)
            wt = base / "wt"
            wt.mkdir()
            first = env.apply(wt, src)
            second = env.apply(wt, src)
        self.assertTrue(all(r["ok"] for r in first + second),
                        "a second apply must not fail on an existing link")


class CallerTest(unittest.TestCase):
    def test_mount_names_is_the_single_source_for_verify(self):
        """verify-order.py imports this; it must not restate the list."""
        self.assertIn("libs", env.mount_names())
        spec_text = (ROOT / "scripts" / "verify-order.py").read_text(encoding="utf-8")
        self.assertIn("from env_contract import", spec_text,
                      "verify must read the contract rather than own a second list")
        self.assertNotIn('_MOUNTED_ASSETS = ("libs",)', spec_text,
                         "the hardcoded list is what the contract replaced")


if __name__ == "__main__":
    unittest.main()
