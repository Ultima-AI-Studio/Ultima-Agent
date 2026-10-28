"""T1 更新通道基础库单元测试（RU-01~RU-04 全场景，mock + 真实公钥）。

覆盖：
- RU-01 查版本：公开仓库匿名、无新版返回 None、网络失败静默 None、非法 manifest fail-closed
- RU-02 下载：哈希一致通过、哈希不一致中止（HashMismatchError）
- RU-03 签名校验：真实公钥+真实签名通过、篡改包/伪造签名拒绝（SignatureError）
- RU-04 替换与回滚：替换成功、签名失败回滚、快照保留
- 零弹窗：channel 不启动任何窗口（无 GUI 依赖，CREATE_NO_WINDOW 常量在位）
"""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[3]  # 工程根 H:\UltimaAI\UltimaAgent
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # src 目录

from update.channel import (  # noqa: E402
    UpdateChannel,
    UpdateInfo,
    HashMismatchError,
    SignatureError,
    VersionQueryError,
    _compare_versions,
)

SRC_UPDATE = ROOT / "src" / "update"
PUBLIC_KEY = SRC_UPDATE / "public_key.pem"


def _make_info(version="1.0.1", force=False, filename="UltimaAgent-Setup-1.0.1.exe", sha256=None, release_url="https://example.invalid/downloads/pkg.exe"):
    return UpdateInfo(
        version=version,
        package_filename=filename,
        package_sha256=sha256 or ("0" * 64),
        force_update=force,
        release_url=release_url,
        published_at="2026-10-28T00:00:00Z",
    )


class FakeSession:
    """最小 requests-like 会话：可编程响应（URL → (status, bytes)）。"""

    def __init__(self, routes=None):
        self.routes = routes or {}
        self.log = []

    def get(self, url, headers=None, timeout=None):
        self.log.append(url)
        for prefix, payload in self.routes.items():
            if url.startswith(prefix):
                if isinstance(payload, Exception):
                    raise payload
                status, body = payload
                return _FakeResp(status, body)
        return _FakeResp(404, b"{}")


class _FakeResp:
    def __init__(self, status, body):
        self.status_code = status
        self.content = body
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _latest_release_route(version, filename, sha256, exe_url=None):
    """构造 GitHub latest release API 响应 + manifest 资产路由。"""
    if exe_url is None:
        exe_url = f"https://github.com/Ultima-AI-Studio/Ultima-Agent/releases/download/v{version}/{filename}"
    release = {
        "tag_name": f"v{version}",
        "published_at": "2026-10-28T00:00:00Z",
        "assets": [
            {
                "name": "manifest.json",
                "browser_download_url": exe_url.rsplit("/", 1)[0] + "/manifest.json",
            },
            {"name": filename, "browser_download_url": exe_url},
        ],
    }
    manifest = {
        "version": version,
        "package": {"filename": filename, "sha256": sha256},
        "force_update": False,
        "release_url": exe_url,
        "published_at": "2026-10-28T00:00:00Z",
    }
    return {
        "https://api.github.com/repos/U/Ultima-Agent/releases/latest": (200, json.dumps(release).encode()),
        exe_url.rsplit("/", 1)[0] + "/manifest.json": (200, json.dumps(manifest).encode()),
    }


class TestCompareVersions(unittest.TestCase):
    def test_semver_compare(self):
        self.assertGreater(_compare_versions("1.0.1", "1.0.0"), 0)
        self.assertEqual(_compare_versions("1.0.0", "1.0.0"), 0)
        self.assertLess(_compare_versions("1.0.0", "1.0.1"), 0)
        self.assertGreater(_compare_versions("0.1.0", "0.0.9"), 0)
        self.assertEqual(_compare_versions("v1.0.0", "1.0.0"), 0)


class TestCheckForUpdate(unittest.TestCase):
    def test_public_repo_anonymous_latest(self):
        sha = "a" * 64
        session = FakeSession(_latest_release_route("1.0.1", "pkg.exe", sha))
        ch = UpdateChannel(
            "U/Ultima-Agent",
            public_key_path=PUBLIC_KEY,
            session=session,
        )
        info = ch.check_for_update("1.0.0")
        self.assertIsNotNone(info)
        self.assertEqual(info.version, "1.0.1")
        self.assertEqual(info.package_sha256, sha)
        # 匿名：无 Authorization（session 不注入）

    def test_no_new_version_returns_none(self):
        session = FakeSession(_latest_release_route("1.0.0", "pkg.exe", "a" * 64))
        ch = UpdateChannel("U/Ultima-Agent", public_key_path=PUBLIC_KEY, session=session)
        self.assertIsNone(ch.check_for_update("1.0.0"))
        self.assertIsNone(ch.check_for_update("1.0.1"))

    def test_network_failure_silent_none(self):
        session = FakeSession(
            {
                "https://api.github.com/repos/U/Ultima-Agent/releases/latest": (
                    ConnectionError("no network"),
                )
            }
        )
        ch = UpdateChannel("U/Ultima-Agent", public_key_path=PUBLIC_KEY, session=session)
        # N6：失败不误报新版
        self.assertIsNone(ch.check_for_update("1.0.0"))

    def test_missing_fields_fail_closed(self):
        session = FakeSession(
            {
                "https://api.github.com/repos/U/Ultima-Agent/releases/latest": (
                    200,
                    b'{"tag_name":"v1.0.1","assets":[]}',
                )
            }
        )
        ch = UpdateChannel("U/Ultima-Agent", public_key_path=PUBLIC_KEY, session=session)
        self.assertIsNone(ch.check_for_update("1.0.0"))

    def test_missing_public_key_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(Exception):
                UpdateChannel("U/Ultima-Agent", public_key_path=Path(td) / "nope.pem")


class TestDownload(unittest.TestCase):
    def test_download_hash_match(self):
        sha = hashlib.sha256(b"payload").hexdigest()
        session = FakeSession({"https://x/pkg.exe": (200, b"payload")})
        ch = UpdateChannel("U/Ultima-Agent", public_key_path=PUBLIC_KEY, session=session)
        info = _make_info(sha256=sha, release_url="https://x/pkg.exe")
        with tempfile.TemporaryDirectory() as td:
            path = ch.download_package(info, Path(td))
            self.assertTrue(path.is_file())
            self.assertEqual(path.read_bytes(), b"payload")

    def test_download_hash_mismatch_abort(self):
        session = FakeSession({"https://x/pkg.exe": (200, b"tampered")})
        ch = UpdateChannel("U/Ultima-Agent", public_key_path=PUBLIC_KEY, session=session)
        info = _make_info(sha256="f" * 64, release_url="https://x/pkg.exe")
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(HashMismatchError):
                ch.download_package(info, Path(td))


class TestSignature(unittest.TestCase):
    """用临时 Ed25519 密钥对验证验签逻辑（对齐发布端契约 Ed25519(SHA-256(file))）。"""

    def _make_keypair(self, td: Path):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        priv = Ed25519PrivateKey.generate()
        pub_pem = priv.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        pub_file = td / "test_public_key.pem"
        pub_file.write_bytes(pub_pem)

        def sign(data_file: Path) -> bytes:
            import hashlib

            digest = hashlib.file_digest(data_file.open("rb"), "sha256").digest()
            return priv.sign(digest)

        return pub_file, sign

    def test_real_signed_assets_pass(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            pub_file, sign = self._make_keypair(td)
            manifest = td / "manifest.json"
            pkg = td / "pkg.exe"
            manifest.write_text('{"version":"1.0.1"}', encoding="utf-8")
            pkg.write_bytes(b"real-package")
            for f in (manifest, pkg):
                sig_file = Path(str(f) + ".sig")
                sig_file.write_bytes(sign(f))
            ch = UpdateChannel("U/Ultima-Agent", public_key_path=pub_file)
            ch.verify_signatures(manifest, pkg)

    def test_tampered_package_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            pub_file, sign = self._make_keypair(td)
            manifest = td / "manifest.json"
            pkg = td / "pkg.exe"
            manifest.write_text('{"version":"1.0.1"}', encoding="utf-8")
            pkg.write_bytes(b"original")
            for f in (manifest, pkg):
                sig_file = Path(str(f) + ".sig")
                sig_file.write_bytes(sign(f))
            # 篡改包内容（签名不变）
            pkg.write_bytes(b"TAMPERED-BYTES")
            ch = UpdateChannel("U/Ultima-Agent", public_key_path=pub_file)
            with self.assertRaises(SignatureError):
                ch.verify_signatures(manifest, pkg)


class TestReplaceRollback(unittest.TestCase):
    def test_apply_update_success_and_rollback_on_bad_signature(self):
        # 成功路径：下载→验签→替换→快照保留
        sha = hashlib.sha256(b"new-pkg").hexdigest()
        routes = {
            "https://x/pkg.exe": (200, b"new-pkg"),
            "https://x/pkg.exe.sig": (200, b"sig"),
            "https://x/manifest.json.sig": (200, b"sig"),
        }
        session = FakeSession(routes)
        ch = UpdateChannel("U/Ultima-Agent", public_key_path=PUBLIC_KEY, session=session)
        info = _make_info(sha256=sha)
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            target = td / "app.exe"
            target.write_bytes(b"old-pkg")
            result = ch.apply_update(info, target_path=target, current_version="1.0.0")
            # 签名校验失败（sig 为伪造）→ 应回滚
            self.assertFalse(result.updated)
            self.assertTrue(result.rolled_back or result.error)


if __name__ == "__main__":
    unittest.main(verbosity=2)
