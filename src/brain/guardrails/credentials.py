"""L8 凭证中心（B2 缺口补建）。

对齐 security-spec §1 凭证中心强制项：
1. 凭证只存**本地加密库**（DPAPI/等效），内存与磁盘均不明文。
2. 多 key 轮换：失效自动切备用，缺失主动提示不阻塞（四层凭证层）。
3. 凭证引用（keyId）进消息与数据模型，明文 key 禁止出现在日志/回执/源码。
4. 日志敏感字段脱敏（key/凭证/隐私）。

设计：
- DPAPI 加密：Windows 原生 CryptProtectData/CryptUnprotectData（当前用户级），
  每个 secret 独立加密存储，磁盘与内存不落明文（仅 get 时解密到内存）。
- 四层凭证层：active（主）/ standby（备用）/ derived（派生）/ missing（缺失提示）。
  active 解密失败自动切 standby 为 active（并记审计事件）；全部失效 → missing，
  主动提示不阻塞业务。
- keyId 引用：对外只暴露 keyId，明文值仅经 get_secret 解密返回内存副本。
- 脱敏：redact(value) 对任意凭证值做通用脱敏（前后 2 字符 + 掩码），
  不依赖固定模式；日志/回执一律经 redact 后再输出。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

import base64
import ctypes
import json
import os
import threading
from ctypes import wintypes
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# DPAPI 封装（Windows 原生，无第三方依赖）
# ---------------------------------------------------------------------------


class _DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]


def _dpapi_protect(data: bytes, entropy: bytes = b"") -> bytes:
    """CryptProtectData 加密。entropy 为可选应用级附加熵。"""
    if not data:
        raise CredentialError("凭证明文为空，拒绝加密空值")
    in_blob = _DATA_BLOB(
        len(data),
        ctypes.cast(ctypes.create_string_buffer(data), ctypes.POINTER(ctypes.c_char)),
    )
    ent_blob = _DATA_BLOB()
    if entropy:
        ent_blob = _DATA_BLOB(
            len(entropy),
            ctypes.cast(ctypes.create_string_buffer(entropy), ctypes.POINTER(ctypes.c_char)),
        )
    out_blob = _DATA_BLOB()
    ok = ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(in_blob),  # pDataIn
        None,  # szDataDescr
        ctypes.byref(ent_blob) if entropy else None,  # pOptionalEntropy
        None,  # pvReserved
        None,  # pPromptStruct
        0,  # dwFlags
        ctypes.byref(out_blob),  # pDataOut
    )
    if not ok:
        raise CredentialError(f"DPAPI 加密失败（错误码 {ctypes.get_last_error()}）")
    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(out_blob.pbData)


def _dpapi_unprotect(data: bytes, entropy: bytes = b"") -> bytes:
    """CryptUnprotectData 解密。解密失败抛 CredentialError。"""
    if not data:
        raise CredentialError("凭证密文为空，拒绝解密")
    in_blob = _DATA_BLOB(
        len(data),
        ctypes.cast(ctypes.create_string_buffer(data), ctypes.POINTER(ctypes.c_char)),
    )
    ent_blob = _DATA_BLOB()
    if entropy:
        ent_blob = _DATA_BLOB(
            len(entropy),
            ctypes.cast(ctypes.create_string_buffer(entropy), ctypes.POINTER(ctypes.c_char)),
        )
    out_blob = _DATA_BLOB()
    ok = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(in_blob),  # pDataIn
        None,  # pszDataDescr out
        ctypes.byref(ent_blob) if entropy else None,  # pOptionalEntropy
        None,  # pvReserved
        None,  # pPromptStruct
        0,  # dwFlags
        ctypes.byref(out_blob),  # pDataOut
    )
    if not ok:
        raise CredentialError(f"DPAPI 解密失败（错误码 {ctypes.get_last_error()}）")
    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(out_blob.pbData)


# 应用级附加熵：绑定到 UltimaAgent 项目域，防止跨应用误读
_ENTROPY = b"UltimaAgent::L8::credential-center::v1"


def _encrypt(value: str) -> str:
    return base64.b64encode(_dpapi_protect(value.encode("utf-8"), _ENTROPY)).decode("ascii")


def _decrypt(encoded: str) -> str:
    return _dpapi_unprotect(base64.b64decode(encoded.encode("ascii")), _ENTROPY).decode("utf-8")


# ---------------------------------------------------------------------------
# 异常与数据结构
# ---------------------------------------------------------------------------


class CredentialError(RuntimeError):
    """凭证中心错误（加密失败/损坏/类型错误等）。"""


class MissingSecret(RuntimeError):
    """凭证缺失（第四层）。主动提示、不阻塞业务。"""


class CredentialNotFound(KeyError):
    """keyId 未登记。"""


@dataclass(frozen=True)
class SecretEntry:
    """单条凭证状态（不包含明文）。"""

    key_id: str
    active: bool  # True=主凭证在位可解密
    standby: bool  # 备用凭证在位
    derived: int  # 派生凭证条数
    state: str  # "active" | "standby" | "missing"
    label: str = ""


@dataclass(frozen=True)
class SecretValue:
    """解密后的凭证值（仅内存中存在）。"""

    key_id: str
    value: str
    layer: str  # "active" | "standby" | "derived"
    label: str = ""


# ---------------------------------------------------------------------------
# 通用脱敏（不依赖固定模式，对任意凭证值）
# ---------------------------------------------------------------------------


def redact(value: str, *, head: int = 2, tail: int = 2) -> str:
    """对凭证明文做通用脱敏：保留前后 head/tail 字符，其余掩码。

    长度 <= head+tail 时整体掩码为 '***'（不泄露任何片段）。
    日志/回执必须经本函数后再输出明文 key 值。
    """
    if not value:
        return ""
    total = head + tail
    if len(value) <= total:
        return "***"
    return f"{value[:head]}***{value[-tail:] if tail else ''}"


def scrub_log_text(text: str, secret_values: List[str]) -> str:
    """将 *text* 中出现的任意 secret 明文替换为脱敏形。

    Parameters
    ----------
    text: 待清理的日志/回执文本。
    secret_values: 已知凭证明文（get_secret 解密得到的值），逐个替换。
    """
    for value in secret_values:
        if value and value in text:
            text = text.replace(value, redact(value))
    return text


# ---------------------------------------------------------------------------
# 凭证中心
# ---------------------------------------------------------------------------

_STORE_VERSION = 1


class CredentialCenter:
    """本地加密凭证库（DPAPI），线程安全，四层凭证层。

    Parameters
    ----------
    store_path:
        凭证库文件路径（默认 data/secrets/credential_store.json）。
        测试可注入临时路径。
    """

    def __init__(self, store_path: str | Path | None = None) -> None:
        if store_path is None:
            default_dir = Path(__file__).resolve().parents[3] / "data" / "secrets"
            default_dir.mkdir(parents=True, exist_ok=True)
            store_path = default_dir / "credential_store.json"
        self._path = Path(store_path).resolve()
        self._lock = threading.RLock()
        self._cache: Dict[str, Dict[str, Any]] = {}  # 仅缓存元数据（不含明文）
        self._plain_cache: Dict[str, Dict[str, str]] = {}  # 内存明文（会话级）
        self._load()

    # ------------------------------------------------------------------
    # 存储层
    # ------------------------------------------------------------------
    def _load(self) -> None:
        with self._lock:
            if not self._path.exists():
                self._cache = {}
                return
            try:
                raw = json.loads(self._path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                raise CredentialError(f"凭证库损坏无法读取：{exc}") from exc
            if not isinstance(raw, dict) or raw.get("version") != _STORE_VERSION:
                raise CredentialError("凭证库版本不匹配，拒绝加载")
            self._cache = raw.get("secrets", {})

    def _persist(self) -> None:
        with self._lock:
            payload = {"version": _STORE_VERSION, "secrets": self._cache}
            # 0600 权限；Windows 下以 chmod 近似处理（NTFS ACL 由系统账户隔离）
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            try:
                os.chmod(self._path, 0o600)
            except OSError:
                pass  # Windows 下 chmod 语义有限，目录权限由账户隔离保证

    def _append_event(self, key_id: str, event: str, detail: str = "") -> None:
        """审计事件 append-only（不含明文凭证值）。"""
        path = self._path.with_name("credential_audit.jsonl")
        line = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "key_id": key_id,
            "event": event,
            "detail": detail,
        }
        with self._lock:
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(line, ensure_ascii=False) + "\n")

    # ------------------------------------------------------------------
    # 凭证层：set / get / rotate / derive / delete
    # ------------------------------------------------------------------
    def set_secret(
        self,
        key_id: str,
        value: str,
        *,
        label: str = "主凭证",
    ) -> None:
        """登记/覆盖主凭证。已有值时旧主凭证降级为备用（若备用位已占用则覆盖备用）。"""
        stripped = value.strip()
        if not stripped:
            raise CredentialError("凭证值不能为空")
        encrypted = _encrypt(stripped)
        with self._lock:
            entry = self._cache.get(key_id)
            if entry is None:
                entry = {
                    "active": {"enc": encrypted, "created_at": self._now(), "label": label},
                    "standby": None,
                    "derived": [],
                }
            else:
                old_active = entry.get("active")
                entry["standby"] = old_active  # 旧主 → 备用（覆盖旧备用）
                entry["active"] = {"enc": encrypted, "created_at": self._now(), "label": label}
            self._cache[key_id] = entry
            self._persist()
        self._plain_cache.pop(key_id, None)
        self._append_event(key_id, "set", f"登记主凭证（label={label}）")

    def get_secret(self, key_id: str) -> SecretValue:
        """读取主凭证明文（仅内存）。解密失败自动切备用；全部失效 → MissingSecret。

        缺失（missing）抛 MissingSecret，不阻塞业务（调用方决定降级路径）。
        """
        with self._lock:
            entry = self._cache.get(key_id)
            if entry is None:
                raise CredentialNotFound(f"凭证 keyId '{key_id}' 未登记")
            active = entry.get("active")
            standby = entry.get("standby")
            # 优先内存明文（同一进程内避免重复解密）
            cached = self._plain_cache.get(key_id)
            if cached and cached.get("layer") == "active":
                return SecretValue(key_id, cached["value"], "active", cached.get("label", ""))

            # 尝试主凭证
            if active:
                try:
                    value = _decrypt(active["enc"])
                    self._plain_cache[key_id] = {
                        "value": value,
                        "layer": "active",
                        "label": active.get("label", ""),
                    }
                    return SecretValue(key_id, value, "active", active.get("label", ""))
                except CredentialError:
                    self._append_event(key_id, "active_failed", "主凭证解密失败")

            # 主失败 → 自动切备用
            if standby:
                try:
                    value = _decrypt(standby["enc"])
                    # 备用提升为主
                    entry["active"] = {
                        "enc": standby["enc"],
                        "created_at": standby.get("created_at", self._now()),
                        "label": standby.get("label", "备用凭证（已提升）"),
                    }
                    entry["standby"] = None
                    self._persist()
                    self._plain_cache[key_id] = {
                        "value": value,
                        "layer": "active",
                        "label": standby.get("label", ""),
                    }
                    self._append_event(key_id, "standby_promoted", "备用凭证提升为主")
                    return SecretValue(key_id, value, "active", standby.get("label", ""))
                except CredentialError:
                    self._append_event(key_id, "standby_failed", "备用凭证解密失败")

            # 第四层：缺失（主动提示，不阻塞）
            entry["broken"] = True  # 标记不可用（密文保留存档）
            self._persist()
            self._append_event(key_id, "missing", "主/备用均不可用，凭证缺失")
            raise MissingSecret(
                f"凭证 '{key_id}' 缺失（主/备用均不可用）。请登记主凭证或轮换备用。"
            )

    def rotate(self, key_id: str, new_value: str, *, label: str = "主凭证") -> None:
        """轮换凭证：新值 → 主；旧主 → 备用；旧备用 → 丢弃（派生保留）。"""
        self.set_secret(key_id, new_value, label=label)
        self._append_event(key_id, "rotate", "凭证轮换完成（新主/旧主转备用）")

    def derive(self, key_id: str, value: str, *, label: str = "派生凭证") -> None:
        """追加派生凭证（第三层）。"""
        stripped = value.strip()
        if not stripped:
            raise CredentialError("派生凭证值不能为空")
        encrypted = _encrypt(stripped)
        with self._lock:
            entry = self._cache.get(key_id)
            if entry is None:
                raise CredentialNotFound(f"凭证 keyId '{key_id}' 未登记")
            derived = entry.setdefault("derived", [])
            derived.append({"enc": encrypted, "created_at": self._now(), "label": label})
            self._persist()
        self._append_event(key_id, "derive", f"追加派生凭证（label={label}）")

    def get_derived(self, key_id: str, index: int = -1) -> SecretValue:
        """读取派生凭证明文（默认最新一条）。"""
        with self._lock:
            entry = self._cache.get(key_id)
            if entry is None:
                raise CredentialNotFound(f"凭证 keyId '{key_id}' 未登记")
            derived = entry.get("derived", [])
            if not derived:
                raise MissingSecret(f"凭证 '{key_id}' 无派生凭证")
            item = derived[index]
            try:
                value = _decrypt(item["enc"])
            except CredentialError as exc:
                self._append_event(key_id, "derived_failed", "派生凭证解密失败")
                raise MissingSecret(f"凭证 '{key_id}' 派生凭证不可用") from exc
            return SecretValue(key_id, value, "derived", item.get("label", ""))

    def delete(self, key_id: str) -> bool:
        """删除凭证（主/备用/派生全清）。"""
        with self._lock:
            existed = self._cache.pop(key_id, None) is not None
            if existed:
                self._persist()
        self._plain_cache.pop(key_id, None)
        self._append_event(key_id, "delete", "凭证已删除")
        return existed

    # ------------------------------------------------------------------
    # 查询与状态
    # ------------------------------------------------------------------
    def status(self, key_id: str) -> SecretEntry:
        """查询凭证层状态（不含明文）。broken 标记的凭证报 missing。"""
        with self._lock:
            entry = self._cache.get(key_id)
            if entry is None:
                return SecretEntry(key_id, False, False, 0, "missing")
            if entry.get("broken"):
                return SecretEntry(key_id, False, False, len(entry.get("derived", [])), "missing")
            active = entry.get("active") is not None
            standby = entry.get("standby") is not None
            derived = len(entry.get("derived", []))
            state = "active" if active else ("standby" if standby else "missing")
            label = (entry.get("active") or entry.get("standby") or {}).get("label", "")
            return SecretEntry(key_id, active, standby, derived, state, label)

    def has_secret(self, key_id: str) -> bool:
        return self.status(key_id).state != "missing"

    def keys(self) -> List[str]:
        with self._lock:
            return sorted(self._cache.keys())

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # ------------------------------------------------------------------
    # 兼容底座：从 OpenJarvis credentials.toml 注入（可选后备）
    # ------------------------------------------------------------------
    def inject_env_backup(self) -> int:
        """把底座（openjarvis.core.credentials）已有环境变量凭证迁入本中心。

        仅迁移 os.environ 中存在且本中心未登记的值（作为主凭证登记），
        返回迁移条数。明文不落盘日志。
        """
        migrated = 0
        for key, value in os.environ.items():
            if not value or self.status(key).state != "missing":
                continue
            if key.endswith(("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")):
                try:
                    self.set_secret(key, value, label="env 兼容迁移")
                    migrated += 1
                except CredentialError:
                    continue
        return migrated


# 单例（应用级）
_default_center: Optional[CredentialCenter] = None


def get_credential_center() -> CredentialCenter:
    """返回应用级凭证中心单例。"""
    global _default_center
    if _default_center is None:
        _default_center = CredentialCenter()
    return _default_center


__all__ = [
    "CredentialCenter",
    "CredentialError",
    "CredentialNotFound",
    "MissingSecret",
    "SecretEntry",
    "SecretValue",
    "redact",
    "scrub_log_text",
    "get_credential_center",
]
