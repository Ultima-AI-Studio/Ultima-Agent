"""Runtime capability registry."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .errors import RoutingError
from .manifest import semver_key
from .storage import now_iso


class Registry:
    def __init__(self, records: dict[str, Any] | None = None) -> None:
        self.records: dict[str, Any] = records or {}

    def register(self, manifest: dict[str, Any]) -> dict[str, Any]:
        module_id = manifest["module_id"]
        version = manifest["version"]
        timestamp = now_iso()
        record = self.records.setdefault(
            module_id,
            {
                "module_id": module_id,
                "capability_domain": manifest["capability_domain"],
                "routing_version": None,
                "ready_versions": [],
                "installed_versions": [],
                "route_history": [],
                "deps_resolved": {"ok": None, "reason": "not checked"},
                "error_reason": None,
                "registered_at": timestamp,
                "updated_at": timestamp,
                "versions": {},
            },
        )
        if record["capability_domain"] != manifest["capability_domain"]:
            raise ValueError("module_id cannot change capability_domain")
        record["versions"].setdefault(
            version,
            {"state": "registered", "manifest": manifest, "updated_at": timestamp},
        )
        if version not in record["installed_versions"]:
            record["installed_versions"].append(version)
            record["installed_versions"].sort(key=semver_key, reverse=True)
            retained = record["installed_versions"][:3]
            routing_version = record.get("routing_version")
            if routing_version and routing_version not in retained:
                retained = retained[:2] + [routing_version]
                retained.sort(key=semver_key, reverse=True)
            dropped = set(record["installed_versions"]) - set(retained)
            record["installed_versions"] = retained
            for dropped_version in dropped:
                if dropped_version != record.get("routing_version"):
                    record["versions"].pop(dropped_version, None)
        record["updated_at"] = timestamp
        record.setdefault("route_history", [])
        return record

    def list(self, domain: str | None = None) -> list[dict[str, Any]]:
        values = self.records.values()
        if domain:
            values = (item for item in values if item["capability_domain"] == domain)
        return [deepcopy(item) for item in sorted(values, key=lambda item: item["module_id"])]

    def get(self, module_id: str) -> dict[str, Any]:
        try:
            return deepcopy(self.records[module_id])
        except KeyError as exc:
            raise RoutingError(f"module is not registered: {module_id}") from exc

    def resolve(self, module_id: str) -> tuple[str, dict[str, Any]]:
        record = self.records.get(module_id)
        if not record or not record["routing_version"]:
            raise RoutingError(f"module has no routing version: {module_id}")
        version = record["routing_version"]
        return version, deepcopy(record["versions"][version]["manifest"])

    def find_by_expose(self, interface_name: str) -> dict[str, Any]:
        matches = []
        for record in self.records.values():
            version = record.get("routing_version")
            if version and interface_name in record["versions"][version]["manifest"]["exposes"]:
                matches.append((record, version))
        if len(matches) != 1:
            raise RoutingError(
                f"interface requires exactly one routing provider: {interface_name}; found {len(matches)}"
            )
        record, version = matches[0]
        return {
            "module_id": record["module_id"],
            "version": version,
            "manifest": deepcopy(record["versions"][version]["manifest"]),
        }

    def snapshot(self) -> dict[str, Any]:
        return deepcopy(self.records)
