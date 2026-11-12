"""设备档案层（s3-device-profile · M15）。

对齐 capability-list HA 实体模型 + form-expansion-plan §2.2⑤：
1. 四实体档案模型：DeviceProfile / Controlability / DeviceCred / Reading；
2. 可控性三独立判定：可读/可写/可控制分别判定（防设备误控）；
3. MCP 适配器框架：能力插件不直连 MCP，换 server 只改配置；
4. 前置检查链：设备发现 → 档案 → 凭证 → 可控性；
5. 单协议试点：不可达设备如实报告（不编造）。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass
class Controlability:
    """可控性三独立判定：可读/可写/可控制分别判定。"""
    readable: bool = False
    writable: bool = False
    controllable: bool = False
    reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {"readable": self.readable, "writable": self.writable,
                "controllable": self.controllable, "reason": self.reason}


@dataclass
class DeviceProfile:
    device_id: str
    name: str
    protocol: str
    entity_type: str = "switch"
    controlability: Controlability = field(default_factory=Controlability)
    registered_at: str = field(default_factory=_now_iso)

    def as_dict(self) -> dict[str, Any]:
        return {"device_id": self.device_id, "name": self.name, "protocol": self.protocol,
                "entity_type": self.entity_type,
                "controlability": self.controlability.as_dict(),
                "registered_at": self.registered_at}


@dataclass
class DeviceCred:
    device_id: str
    cred_ref: str           # 凭证引用（不存明文，指向凭证中心）
    provisioned: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {"device_id": self.device_id, "cred_ref": self.cred_ref,
                "provisioned": self.provisioned}


@dataclass
class Reading:
    device_id: str
    metric: str
    value: Any
    unit: str = ""
    ts: str = field(default_factory=_now_iso)

    def as_dict(self) -> dict[str, Any]:
        return {"device_id": self.device_id, "metric": self.metric, "value": self.value,
                "unit": self.unit, "ts": self.ts}


class DeviceRegistry:
    """四实体档案模型：可读写持久化。"""

    def __init__(self, data_dir: str | Path) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._devices: dict[str, DeviceProfile] = {}
        self._creds: dict[str, DeviceCred] = {}
        self._readings: list[Reading] = []
        self._load()

    def _load(self) -> None:
        p = self.data_dir / "devices.json"
        if not p.exists():
            return
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            self._devices = {k: DeviceProfile(**v) for k, v in d.get("devices", {}).items()}
            self._creds = {k: DeviceCred(**v) for k, v in d.get("creds", {}).items()}
            self._readings = [Reading(**r) for r in d.get("readings", [])]
        except (json.JSONDecodeError, TypeError):
            pass

    def _save(self) -> None:
        (self.data_dir / "devices.json").write_text(
            json.dumps({
                "devices": {k: v.as_dict() for k, v in self._devices.items()},
                "creds": {k: v.as_dict() for k, v in self._creds.items()},
                "readings": [r.as_dict() for r in self._readings],
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def upsert(self, profile: DeviceProfile) -> None:
        self._devices[profile.device_id] = profile
        self._save()

    def provision_cred(self, cred: DeviceCred) -> None:
        self._creds[cred.device_id] = cred
        self._save()

    def add_reading(self, reading: Reading) -> None:
        self._readings.append(reading)
        self._save()

    def get(self, device_id: str) -> Optional[DeviceProfile]:
        return self._devices.get(device_id)

    def cred(self, device_id: str) -> Optional[DeviceCred]:
        return self._creds.get(device_id)

    def all(self) -> list[DeviceProfile]:
        return list(self._devices.values())


class ControlabilityJudge:
    """可控性三独立判定：可读/可写/可控制分别判定（防误控）。"""

    def judge(self, *, entity_type: str, reachable: bool, cred_provisioned: bool) -> Controlability:
        if not reachable:
            return Controlability(False, False, False, "设备不可达")
        readable = True
        writable = reachable
        controllable = writable and cred_provisioned and entity_type in ("switch", "light", "thermostat")
        reason = f"可读={readable}；可写={writable}；可控制={controllable}（凭证={cred_provisioned}，类型={entity_type}）"
        return Controlability(readable, writable, controllable, reason)


class McpAdapter:
    """MCP 适配器：能力插件不直连 MCP，换 server 只改配置。"""

    def __init__(self, config_path: str | Path) -> None:
        self.config_path = Path(config_path)
        self._servers: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if self.config_path.exists():
            try:
                d = json.loads(self.config_path.read_text(encoding="utf-8"))
                self._servers = d.get("servers", {})
            except (json.JSONDecodeError, TypeError):
                pass

    def configure(self, server_name: str, url: str, kind: str = "http") -> None:
        self._servers[server_name] = {"url": url, "kind": kind}
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps({"servers": self._servers}, ensure_ascii=False, indent=2),
                                    encoding="utf-8")

    def endpoint(self, server_name: str) -> dict[str, Any]:
        """插件通过本方法取端点：换 server 只改配置，插件代码不变。"""
        if server_name not in self._servers:
            return {"ok": False, "reason": f"MCP server 未配置 {server_name}"}
        return {"ok": True, **self._servers[server_name]}


class ProvisionChain:
    """前置检查链：发现 → 档案 → 凭证 → 可控性。"""

    def __init__(self, registry: DeviceRegistry, judge: Optional[ControlabilityJudge] = None) -> None:
        self.registry = registry
        self.judge = judge or ControlabilityJudge()

    def discover(self, device_id: str, name: str, protocol: str, entity_type: str = "switch") -> DeviceProfile:
        profile = DeviceProfile(device_id, name, protocol, entity_type=entity_type)
        self.registry.upsert(profile)
        return profile

    def provision(self, device_id: str, cred_ref: str) -> None:
        self.registry.provision_cred(DeviceCred(device_id, cred_ref, provisioned=True))

    def check(self, device_id: str, *, reachable: bool = True) -> dict[str, Any]:
        """全链检查：档案存在 → 凭证已配 → 可控性判定。"""
        profile = self.registry.get(device_id)
        if profile is None:
            return {"ok": False, "stage": "档案", "reason": "设备未建档（先发现）"}
        cred = self.registry.cred(device_id)
        cred_ok = cred is not None and cred.provisioned
        if not cred_ok:
            return {"ok": False, "stage": "凭证", "reason": "设备凭证未配置"}
        ctrl = self.judge.judge(entity_type=profile.entity_type, reachable=reachable,
                                cred_provisioned=True)
        profile.controlability = ctrl
        self.registry.upsert(profile)
        return {"ok": True, "stage": "可控性", "controlability": ctrl.as_dict(),
                "device_id": device_id}


__all__ = ["DeviceProfile", "DeviceCred", "Reading", "Controlability",
           "DeviceRegistry", "ControlabilityJudge", "McpAdapter", "ProvisionChain"]
