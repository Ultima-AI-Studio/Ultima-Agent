"""L8 凭证中心总线插件（M20：credential.*）。

承载凭证中心接入总线：只做对接，不重写已冻结实现（CredentialCenter 原样复用）。
本包仅做总线适配壳，职责：
- credential.register(key_id, value, label)：登记主凭证（本地 DPAPI 加密库）
- credential.rotate(key_id, new_value)：轮换（四层凭证层保留）
- credential.status(key_id)：状态（无明文）
- credential.list()：全部 keyId + 状态（无明文）
- credential.inject(key_id)：服务器能力层注入明文（仅内存，用完即弃）

安全纪律：
- 凭证明文只经 DPAPI 解密到内存；磁盘/日志/回执/审计一律不含明文；
- 对外（前端/宿主壳）永不暴露 inject 返回的明文；inject 仅服务器能力层调用
  （manifest.permissions 需 cap:credential.inject，未声明调用被总线拒绝）；
- 审计事件只记 key_id + 事件名，detail 不含凭证值。
"""

from __future__ import annotations

from pathlib import Path

# 审计留痕默认落 plugin-bus 日志同目录（相对项目根）
_AUDIT_PATH = Path(__file__).resolve().parents[4] / "logs" / "credential-audit.jsonl"

# 三类凭证命名空间（约定，不做强制校验以兼容既有 keyId）
CRED_NAMESPACES = ("model:", "channel:", "device:")


class CredentialPlugin:
    def load(self) -> None:
        from src.brain.guardrails.credentials import CredentialCenter, get_credential_center

        # 默认使用应用级单例；测试可注入独立 store_path
        center = getattr(self, "_center", None)
        if center is None:
            center = get_credential_center()
        self._center = center
        # 测试可注入独立审计路径，默认落 plugin-bus 日志同目录
        self._audit_path = getattr(self, "_audit_path", str(_AUDIT_PATH))

    def _ensure_loaded(self) -> None:
        if not hasattr(self, "_center"):
            self.load()

    def _audit(self, key_id: str, event: str, detail: str = "") -> None:
        import json
        import os
        from datetime import datetime, timezone

        path = Path(self._audit_path)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            line = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "key_id": key_id,
                "event": event,
                "detail": detail,
            }
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(line, ensure_ascii=False) + "\n")
        except OSError:
            return  # 审计失败不阻塞业务

    def activate(self) -> None:
        pass

    def disable(self) -> None:
        pass

    def unload(self) -> None:
        pass

    def rollback(self) -> None:
        pass

    def smoke(self) -> bool:
        self._ensure_loaded()
        # 未登记 keyId 状态应为 missing（不崩溃、不泄露）
        from src.brain.guardrails.credentials import CredentialNotFound

        try:
            self._center.status("__smoke_probe__")
        except CredentialNotFound:
            return True
        return True

    def credential_register(self, key_id: str, value: str, label: str = "主凭证"):
        """credential.register(key_id, value, label) —— 登记主凭证。"""
        self._ensure_loaded()
        from src.brain.guardrails.credentials import redact

        self._center.set_secret(key_id, value, label=label)
        self._audit(key_id, "register", f"登记主凭证（label={label}）")
        return {"ok": True, "key_id": key_id, "label": label, "redacted": redact(value)}

    def credential_rotate(self, key_id: str, new_value: str):
        """credential.rotate(key_id, new_value) —— 轮换（旧主自动降级备用）。"""
        self._ensure_loaded()
        self._center.rotate(key_id, new_value)
        self._audit(key_id, "rotate", "凭证轮换")
        return {"ok": True, "key_id": key_id}

    def credential_status(self, key_id: str):
        """credential.status(key_id) —— 状态（无明文）。"""
        self._ensure_loaded()
        from src.brain.guardrails.credentials import CredentialNotFound

        try:
            entry = self._center.status(key_id)
        except CredentialNotFound:
            return {"ok": False, "key_id": key_id, "state": "missing", "reason": "未登记"}
        return {
            "ok": entry.state != "missing",
            "key_id": key_id,
            "active": entry.active,
            "standby": entry.standby,
            "derived": entry.derived,
            "state": entry.state,
            "label": entry.label,
        }

    def credential_list(self):
        """credential.list() —— 全部 keyId + 状态（无明文）。"""
        self._ensure_loaded()
        out = []
        for key_id in sorted(self._center.keys()):
            st = self.credential_status(key_id)
            out.append({"key_id": key_id, "state": st.get("state"), "label": st.get("label", "")})
        return {"ok": True, "count": len(out), "items": out}

    def credential_inject(self, key_id: str):
        """credential.inject(key_id) —— 服务器能力层注入明文（仅内存）。

        返回明文值仅供同一进程内能力插件使用，用完即弃；不得进入回执/日志/前端。
        审计只记 key_id 与 inject 事件。
        """
        self._ensure_loaded()
        from src.brain.guardrails.credentials import CredentialNotFound, MissingSecret

        try:
            secret = self._center.get_secret(key_id)
        except (CredentialNotFound, MissingSecret) as exc:
            self._audit(key_id, "inject.failed", type(exc).__name__)
            return {"ok": False, "key_id": key_id, "reason": type(exc).__name__}
        self._audit(key_id, "inject", "服务器能力层注入（明文仅内存）")
        return {
            "ok": True,
            "key_id": key_id,
            "layer": secret.layer,
            "label": secret.label,
            "value": secret.value,
            "memory_only": True,
        }


def create_plugin() -> CredentialPlugin:
    return CredentialPlugin()
