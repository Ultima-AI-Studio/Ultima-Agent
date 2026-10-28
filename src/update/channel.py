"""s1-remote-update-channel 更新通道基础库（T1 · RU-01~RU-04）。

职责：GitHub Releases API 查版本 → 下载资产（哈希校验）→ 内置公钥验签
（manifest + 包，篡改拒绝）→ 替换 + 失败自动回滚。全程零弹窗（N7），
查询失败/无网络静默降级（N6，不打扰、记日志、不误报新版）。

对齐单一权威：docs/specs/update-manifest-schema.md v1.0（N5）。
客户端公钥：src/update/public_key.pem（与发布端 publisher-public.pem 成对）。
"""
from __future__ import annotations

import hashlib
import json
import logging
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import urllib.request
import urllib.error

logger = logging.getLogger("ultima.update.channel")

MANIFEST_SCHEMA_AUTHORITY = "docs/specs/update-manifest-schema.md"
MANIFEST_FIELDS = {"version", "package", "force_update", "release_url", "published_at"}
PACKAGE_FIELDS = {"filename", "sha256"}

# 零弹窗：子进程/启动一律 CREATE_NO_WINDOW
CREATE_NO_WINDOW = 0x08000000


class UpdateChannelError(Exception):
    """通道错误基类：查询失败/下载失败/校验失败/回滚失败统一归类。"""


class VersionQueryError(UpdateChannelError):
    """查版本失败（无网络/API 错误）。"""


class DownloadError(UpdateChannelError):
    """下载失败。"""


class HashMismatchError(UpdateChannelError):
    """哈希校验不一致（中止，RU-02）。"""


class SignatureError(UpdateChannelError):
    """签名校验失败（篡改/伪造 → 拒绝执行，硬性要求 RU-03）。"""


class ReplaceError(UpdateChannelError):
    """替换/回滚失败。"""


@dataclass
class UpdateInfo:
    """一次更新所需的全部信息（从 manifest 解析，字段以 schema 为准）。"""

    version: str
    package_filename: str
    package_sha256: str
    force_update: bool
    release_url: str
    published_at: str


@dataclass
class UpdateResult:
    """更新执行结果。"""

    checked: bool = False
    updated: bool = False
    rolled_back: bool = False
    error: str | None = None
    old_version: str | None = None
    new_version: str | None = None
    detail: list[str] = field(default_factory=list)


def _noop(_msg: str) -> None:
    """默认静默回调：不打扰（N6）。"""


class UpdateChannel:
    """客户端更新通道。

    - check_for_update()：查版本（公开仓库匿名 API），无新版/失败静默返回 None。
    - apply_update(info, target_dir, current_version)：下载→验签→替换→回滚闭环。
    """

    def __init__(
        self,
        repository: str,
        *,
        public_key_path: Path | None = None,
        api_base: str = "https://api.github.com",
        download_base: str | None = None,
        http_timeout: float = 20.0,
        on_progress: Callable[[str], None] = _noop,
        session: Any = None,
    ) -> None:
        self.repository = repository
        self.api_base = api_base.rstrip("/")
        self.download_base = (download_base or api_base).rstrip("/")
        self.http_timeout = http_timeout
        self.on_progress = on_progress
        self._session = session
        public_key_path = public_key_path or (
            Path(__file__).resolve().parent / "public_key.pem"
        )
        self.public_key_path = public_key_path
        if not self.public_key_path.is_file():
            # 无公钥 fail-closed（B1）：签名校验不可用则整个通道不可用
            raise UpdateChannelError(
                f"client public key missing: {self.public_key_path} (fail-closed)"
            )

    # ---------- RU-01 查版本 ----------
    def check_for_update(
        self, current_version: str, *, force_fetch: bool = False
    ) -> UpdateInfo | None:
        """查最新 Release + manifest；无新版/失败 → None（静默降级）。

        公开仓库匿名可用（任务卡 RU-01）；404/超时/网络错误不误报新版（N6）。
        """
        try:
            manifest = self._fetch_latest_manifest()
        except UpdateChannelError as exc:
            logger.info("update check skipped: %s", exc)
            return None

        info = _parse_manifest(manifest, self.repository)
        if _compare_versions(info.version, current_version) <= 0:
            # 服务端版本不高于当前 → 无新版
            return None
        return info

    def _fetch_latest_manifest(self) -> dict[str, Any]:
        # 优先直接取 manifest 资产；不存在则取 release 元数据（fail-closed）
        release_url = f"{self.api_base}/repos/{self.repository}/releases/latest"
        try:
            body = self._get_json(release_url)
        except UpdateChannelError as exc:
            raise VersionQueryError(f"latest release query failed: {exc}") from exc

        tag = body.get("tag_name")
        if not tag:
            raise VersionQueryError("latest release has no tag_name")

        # manifest 资产：browser_download_url 优先（与 T3 上传资产同名）
        manifest_url = None
        for asset in body.get("assets", []) or []:
            if asset.get("name") == "manifest.json":
                manifest_url = asset.get("browser_download_url")
                break
        if manifest_url:
            try:
                return self._get_json(manifest_url)
            except UpdateChannelError:
                logger.info("manifest asset fetch failed, fall back to release meta")
        # 兜底：用 release 元数据构造最小 manifest（仍校验必填字段）
        return _release_meta_to_manifest(body)

    def _get_json(self, url: str) -> dict[str, Any]:
        data = self._http_get(url)
        try:
            return json.loads(data)
        except json.JSONDecodeError as exc:
            raise VersionQueryError(f"invalid JSON from {url}") from exc

    def _http_get(self, url: str) -> bytes:
        headers = {
            "User-Agent": "UltimaAgent-Update/0.1",
            "Accept": "application/vnd.github+json",
        }
        try:
            if self._session is not None:
                with self._session.get(
                    url, headers=headers, timeout=self.http_timeout
                ) as resp:
                    if resp.status_code >= 400:
                        raise DownloadError(f"HTTP {resp.status_code}: {url}")
                    return resp.content
            with urllib.request.urlopen(
                urllib.request.Request(url, headers=headers), timeout=self.http_timeout
            ) as resp:
                if resp.status >= 400:
                    raise DownloadError(f"HTTP {resp.status}: {url}")
                return resp.read()
        except urllib.error.URLError as exc:
            raise VersionQueryError(f"network error: {exc}") from exc
        except UpdateChannelError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise VersionQueryError(f"fetch failed: {exc}") from exc

    # ---------- RU-02 下载 ----------
    def download_package(self, info: UpdateInfo, target_dir: Path) -> Path:
        """下载更新包到目标目录，SHA256 校验一致才返回（不一致 → 中止）。"""
        target_dir.mkdir(parents=True, exist_ok=True)
        dest = target_dir / info.package_filename
        url = info.release_url
        self.on_progress(f"download {info.package_filename}")
        data = self._http_get(url)
        digest = hashlib.sha256(data).hexdigest()
        if digest.lower() != info.package_sha256.lower():
            raise HashMismatchError(
                f"sha256 mismatch: {digest} != {info.package_sha256} (abort)"
            )
        # 先写临时文件再原子 rename，避免半包残留
        tmp = dest.with_name(dest.name + ".part")
        tmp.write_bytes(data)
        tmp.replace(dest)
        return dest

    # ---------- RU-03 签名校验 ----------
    def verify_signatures(self, manifest_path: Path, package_path: Path) -> None:
        """内置公钥验证 manifest.sig 与包 .sig（伪造/篡改 → 拒绝执行）。"""
        manifest_sig = manifest_path.with_name(manifest_path.name + ".sig")
        package_sig = Path(str(package_path) + ".sig")
        for sig_file in (manifest_sig, package_sig):
            if not sig_file.is_file():
                raise SignatureError(f"missing signature: {sig_file.name}")
        if not _verify_signature(
            self.public_key_path, manifest_path, manifest_sig
        ):
            raise SignatureError("manifest signature invalid (reject)")
        if not _verify_signature(self.public_key_path, package_path, package_sig):
            raise SignatureError("package signature invalid (reject)")

    # ---------- RU-04 替换与回滚 ----------
    def apply_update(
        self,
        info: UpdateInfo,
        *,
        target_path: Path,
        current_version: str,
        launcher_args: list[str] | None = None,
    ) -> UpdateResult:
        """完整更新闭环：下载→验签→替换（保留快照）→失败回滚。

        target_path：当前安装文件路径（如 host.exe / 安装包路径）。
        替换前将旧文件复制为 .bak 快照；签名/替换/启动失败 → 回滚上一版本。
        """
        result = UpdateResult(
            old_version=current_version, new_version=info.version
        )
        tmp_root = Path(tempfile.mkdtemp(prefix="ultima-update-"))
        try:
            result.checked = True
            package = self.download_package(info, tmp_root)
            manifest_path = tmp_root / "manifest.json"
            manifest_path.write_text(
                json.dumps(_manifest_to_dict(info), ensure_ascii=False),
                encoding="utf-8",
            )
            # 拉取真实 .sig（下载 manifest.sig + 包.sig 与包同源）
            self._download_signatures(info, tmp_root, package)
            self.verify_signatures(manifest_path, package)

            backup = target_path.with_name(target_path.name + ".bak")
            if target_path.is_file():
                shutil.copy2(target_path, backup)
                self.on_progress("snapshot created")

            # 替换（跨卷原子性不足时先复制再替换）
            try:
                package.replace(target_path)
            except OSError:
                shutil.copy2(package, target_path)
            self.on_progress("package replaced")

            # 启动自检（可选：校验替换后可执行；失败 → 回滚）
            if launcher_args and not _smoke_launch(target_path, launcher_args):
                result.rolled_back = True
                self._rollback(target_path, backup)
                result.error = "smoke launch failed; rolled back"
                return result

            result.updated = True
            self.on_progress(f"updated to {info.version}")
            return result
        except UpdateChannelError as exc:
            result.error = str(exc)
            backup = target_path.with_name(target_path.name + ".bak")
            if backup.is_file() and target_path.is_file():
                self._rollback(target_path, backup)
                result.rolled_back = True
            return result
        finally:
            shutil.rmtree(tmp_root, ignore_errors=True)

    def _download_signatures(
        self, info: UpdateInfo, tmp_root: Path, package: Path
    ) -> None:
        manifest_sig = tmp_root / "manifest.json.sig"
        package_sig = Path(str(package) + ".sig")
        for sig_file, base in (
            (manifest_sig, info.release_url.rsplit("/", 1)[0]),
            (package_sig, info.release_url),
        ):
            sig_file.write_bytes(self._http_get(base + ".sig"))

    def _rollback(self, target_path: Path, backup: Path) -> None:
        shutil.copy2(backup, target_path)
        self.on_progress("rolled back to previous version")
        try:
            backup.unlink()
        except OSError:
            pass


# ---------- 工具函数 ----------

def _compare_versions(a: str, b: str) -> int:
    """语义版本比较：返回 >0 / ==0 / <0。非法段按 0 处理（fail-closed 不误报）。"""
    def _parts(v: str) -> list[int]:
        out = []
        for seg in v.strip().lstrip("vV").split("."):
            try:
                out.append(int(seg))
            except ValueError:
                out.append(0)
        return out

    pa, pb = _parts(a), _parts(b)
    for x, y in zip(pa, pb):
        if x != y:
            return 1 if x > y else -1
    return (len(pa) > len(pb)) - (len(pa) < len(pb))


def _parse_manifest(manifest: dict[str, Any], repository: str) -> UpdateInfo:
    missing = [f for f in MANIFEST_FIELDS if f not in manifest]
    if missing:
        raise VersionQueryError(f"manifest missing fields: {missing}")
    pkg = manifest["package"]
    if not isinstance(pkg, dict) or any(f not in pkg for f in PACKAGE_FIELDS):
        raise VersionQueryError("manifest package missing filename/sha256")
    return UpdateInfo(
        version=str(manifest["version"]),
        package_filename=str(pkg["filename"]),
        package_sha256=str(pkg["sha256"]),
        force_update=bool(manifest.get("force_update", False)),
        release_url=str(manifest["release_url"]),
        published_at=str(manifest.get("published_at", "")),
    )


def _release_meta_to_manifest(release: dict[str, Any]) -> dict[str, Any]:
    assets = release.get("assets", []) or []
    package = next((a for a in assets if a.get("name", "").endswith(".exe")), None)
    if not package:
        raise VersionQueryError("release has no .exe asset")
    digest = (package.get("digest") or "").removeprefix("sha256:")
    return {
        "version": release.get("tag_name", "").lstrip("v"),
        "package": {"filename": package["name"], "sha256": digest},
        "force_update": False,
        "release_url": package.get("browser_download_url", ""),
        "published_at": release.get("published_at", ""),
    }


def _manifest_to_dict(info: UpdateInfo) -> dict[str, Any]:
    return {
        "version": info.version,
        "package": {
            "filename": info.package_filename,
            "sha256": info.package_sha256,
        },
        "force_update": info.force_update,
        "release_url": info.release_url,
        "published_at": info.published_at,
    }


def _verify_signature(public_key_path: Path, data_file: Path, sig_file: Path) -> bool:
    """Ed25519 验签：data_file 的 SHA-256 摘要对 sig_file 签名用公钥验证。

    与发布端同原语（PK-04 同钥契约）：`Ed25519(SHA-256(file bytes))`，
    签名文件为原始 64 字节 `<filename>.sig`（tools/publisher/keys/README.md）。
    """
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    try:
        public_key = serialization.load_pem_public_key(public_key_path.read_bytes())
        if not isinstance(public_key, Ed25519PublicKey):
            return False
        digest = hashlib.file_digest(data_file.open("rb"), "sha256").digest()
        public_key.verify(sig_file.read_bytes(), digest)
        return True
    except (InvalidSignature, ValueError, OSError, TypeError):
        return False


def _smoke_launch(executable: Path, args: list[str]) -> bool:
    """替换后启动自检：进程能启动即返回 True（失败 → 回滚触发）。"""
    try:
        proc = subprocess.Popen(
            [str(executable), *args],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        proc.wait(timeout=8)
        # 进程能启动（无论退出码）即视为可执行
        return True
    except Exception:  # noqa: BLE001
        return False
