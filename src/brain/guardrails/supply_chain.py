"""供应链闸门（s3-supply-chain · M23）。

对齐 plugin-bus-spec §13 / security-spec §3：
1. 依赖白名单登记（module_id/版本/来源），未登记依赖拒绝加载；
2. License 审查（GPL 底座拒绝）+ 依赖 CVE 扫描（本地漏洞库，高危阻断）；
3. 第三方插件准入：Owner 批准 + 独立安全审查留痕；
4. 版本锁定 vendor 进仓库（升级走 M3 评审与蓝绿回滚）；
5. 未审查模块拒绝加载。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

LICENSE_ALLOWLIST = {
    "MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "MPL-2.0",
    "Unlicense", "CC0-1.0", "LGPL-2.1", "LGPL-3.0",
}
LICENSE_DENYLIST = {"GPL-2.0", "GPL-3.0", "AGPL-3.0"}

# 本地 CVE 漏洞库样例（真实接入时替换为扫描器输出）
_DEFAULT_CVE_DB = {
    "fastembed": [{"cve": "CVE-2024-0001", "severity": "high", "fix": ">=0.3.0"}],
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class SupplyChainError(Exception):
    """供应链闸门拒绝。"""


@dataclass
class DependencyRecord:
    module_id: str
    version: str
    source: str            # pypi | github | vendor | local
    license: str
    owner_approved: bool
    security_reviewed: bool
    approved_at: str = ""
    reviewed_at: str = ""
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "module_id": self.module_id, "version": self.version, "source": self.source,
            "license": self.license, "owner_approved": self.owner_approved,
            "security_reviewed": self.security_reviewed,
            "approved_at": self.approved_at, "reviewed_at": self.reviewed_at, "notes": self.notes,
        }


class SupplyChainGate:
    """供应链闸门：白名单 + License + CVE + 准入 + 版本锁定。"""

    def __init__(
        self,
        data_dir: str | Path,
        cve_db: Optional[dict[str, list[dict[str, Any]]]] = None,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.registry_path = self.data_dir / "supply-chain-registry.json"
        self.vendor_dir = self.data_dir / "vendor"
        self.cve_db = dict(cve_db if cve_db is not None else _DEFAULT_CVE_DB)
        self._registry: dict[str, DependencyRecord] = {}
        self._load()

    def _load(self) -> None:
        if self.registry_path.exists():
            try:
                data = json.loads(self.registry_path.read_text(encoding="utf-8"))
                for mid, obj in data.items():
                    self._registry[mid] = DependencyRecord(**obj)
            except (json.JSONDecodeError, TypeError):
                pass

    def _save(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.registry_path.write_text(
            json.dumps({k: v.as_dict() for k, v in self._registry.items()},
                       ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # -- 白名单登记 ---------------------------------------------------------

    def register(
        self,
        module_id: str,
        version: str,
        source: str,
        license: str,
        *,
        owner_approved: bool = False,
        security_reviewed: bool = False,
        notes: str = "",
    ) -> DependencyRecord:
        rec = DependencyRecord(
            module_id=module_id, version=version, source=source, license=license,
            owner_approved=owner_approved, security_reviewed=security_reviewed,
            notes=notes,
        )
        self._registry[module_id] = rec
        self._save()
        return rec

    def is_registered(self, module_id: str, version: Optional[str] = None) -> bool:
        rec = self._registry.get(module_id)
        if rec is None:
            return False
        if version and rec.version != version:
            return False
        return True

    # -- License 审查 -------------------------------------------------------

    def check_license(self, license: str) -> tuple[bool, str]:
        lic = str(license).strip()
        if lic in LICENSE_DENYLIST:
            return False, f"License {lic} 在拒绝名单（GPL 系底座不采）"
        if lic not in LICENSE_ALLOWLIST:
            return False, f"License {lic} 不在允许名单"
        return True, f"License {lic} 允许"

    # -- CVE 扫描 -----------------------------------------------------------

    def scan_cve(self, module_id: str, version: str) -> list[dict[str, Any]]:
        """本地漏洞库扫描：命中高危返回（阻断加载）。"""
        hits: list[dict[str, Any]] = []
        for entry in self.cve_db.get(module_id, []):
            if self._vuln_applies(entry, version):
                hits.append(dict(entry))
        return hits

    @staticmethod
    def _version_tuple(version: str) -> tuple[int, ...]:
        parts = []
        for seg in re.findall(r"\d+", version):
            parts.append(int(seg))
        return tuple(parts or (0,))

    def _vuln_applies(self, entry: dict[str, Any], version: str) -> bool:
        fix = entry.get("fix", "")
        if not fix:
            return True  # 无修复信息按受影响处理
        if fix.startswith(">="):
            # 修复版本为 X：受影响 = 当前版本 < X
            return self._version_tuple(version) < self._version_tuple(fix[2:].strip())
        if fix.startswith("<"):
            return self._version_tuple(version) < self._version_tuple(fix[1:].strip())
        return True

    # -- 准入与审查 ---------------------------------------------------------

    def approve_owner(self, module_id: str, approved: bool = True) -> None:
        rec = self._registry.get(module_id)
        if rec is None:
            raise SupplyChainError(f"未登记依赖 {module_id}，先 register")
        rec.owner_approved = approved
        rec.approved_at = _now_iso() if approved else ""
        self._save()

    def security_review(self, module_id: str, reviewed: bool = True) -> None:
        rec = self._registry.get(module_id)
        if rec is None:
            raise SupplyChainError(f"未登记依赖 {module_id}，先 register")
        rec.security_reviewed = reviewed
        rec.reviewed_at = _now_iso() if reviewed else ""
        self._save()

    # -- 版本锁定 vendor ----------------------------------------------------

    def vendor_lock(self, module_id: str, artifact_path: str | Path) -> Path:
        """版本锁定：将依赖产物复制进 vendor 目录（进仓库）。"""
        artifact = Path(artifact_path)
        if not artifact.exists():
            raise SupplyChainError(f"产物不存在 {artifact}")
        self.vendor_dir.mkdir(parents=True, exist_ok=True)
        rec = self._registry.get(module_id)
        tag = f"{module_id}-{rec.version if rec else 'unknown'}"
        dest = self.vendor_dir / f"{tag}{artifact.suffix}"
        dest.write_bytes(artifact.read_bytes())
        return dest

    # -- 加载前总闸门 -------------------------------------------------------

    def gate_load(
        self,
        module_id: str,
        version: str,
        *,
        license: str = "",
        require_owner: bool = True,
        require_review: bool = True,
    ) -> dict[str, Any]:
        """加载前检查：未审查/未登记/许可证拒绝/CVE 高危 → 拒绝加载。"""
        errors: list[str] = []
        if not self.is_registered(module_id, version):
            errors.append(f"未登记依赖 {module_id}@{version}")
            rec = self._registry.get(module_id)
        else:
            rec = self._registry[module_id]
            if license:
                ok, why = self.check_license(license)
                if not ok:
                    errors.append(why)
            elif rec.license:
                ok, why = self.check_license(rec.license)
                if not ok:
                    errors.append(why)
            if require_owner and not rec.owner_approved:
                errors.append(f"{module_id} 未经 Owner 批准")
            if require_review and not rec.security_reviewed:
                errors.append(f"{module_id} 未经独立安全审查")
            for hit in self.scan_cve(module_id, version):
                if hit.get("severity") in ("high", "critical"):
                    errors.append(f"{module_id}@{version} 命中 CVE {hit.get('cve')}（{hit.get('severity')}）阻断加载")
        return {
            "allowed": len(errors) == 0,
            "module_id": module_id,
            "version": version,
            "errors": errors,
        }


__all__ = ["SupplyChainGate", "SupplyChainError", "DependencyRecord",
           "LICENSE_ALLOWLIST", "LICENSE_DENYLIST"]
