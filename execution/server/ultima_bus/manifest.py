"""Frozen ADR-011 module manifest parsing and validation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import ManifestError


REQUIRED_FIELDS = (
    "module_id",
    "name",
    "version",
    "capability_domain",
    "entry",
    "exposes",
    "deps",
    "config_schema",
    "permissions",
    "hooks",
)
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
MODULE_RE = re.compile(
    r"^ultima\.(intent|domain|exec|scene|report|voice|dialog|guard|credential|memory|paradigm)\."
    r"[a-z0-9]+(?:-[a-z0-9]+)*$"
)
PERMISSION_RE = re.compile(
    r"^(?:cap:(?:intent\.parse|domain\.resolve|exec\.run|scene\.orchestrate|"
    r"report\.compose|voice\.speak|dialog\.ask|queue\.(?:list|reorder|cancel)|"
    r"guard\.check|credential\.(?:register|rotate|status|list|inject)|"
    r"memory\.(?:read|write)|paradigm\.run)|"
    r"dev:(?:read|write|control)|cred:[A-Za-z0-9_.-]+)$"
)
VERSION_RANGE_RE = re.compile(
    r"^(?:(?:>=|==)(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*))"
    r"(?:,(?:<)(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*))?$"
)
DOMAIN_EXPOSES = {
    "L1": {"intent.parse"},
    "L2": {"domain.resolve"},
    "L3": {"exec.run"},
    "L4": {"scene.orchestrate"},
    "L5": {"report.compose"},
    "L6": {"voice.speak"},
    "L7": {"dialog.ask", "queue.list", "queue.reorder", "queue.cancel"},
    "L8": {
        "guard.check",
        "credential.register",
        "credential.rotate",
        "credential.status",
        "credential.list",
        "credential.inject",
    },
    "L9": {"memory.read", "memory.write"},
    "L10": {"paradigm.run"},
}
INTERFACE_SIGNATURES = {
    "intent.parse": ("text", "sessionId"),
    "domain.resolve": ("intent",),
    "exec.run": ("plan", "ctx"),
    "scene.orchestrate": ("content", "intent"),
    "report.compose": ("results",),
    "voice.speak": ("text", "state"),
    "dialog.ask": ("question",),
    "queue.list": (),
    "queue.reorder": ("request",),
    "queue.cancel": ("request",),
    "guard.check": ("action", "scope"),
    "memory.read": ("query",),
    "memory.write": ("fact",),
    "paradigm.run": ("flowId", "input"),
    "credential.register": ("key_id", "value", "label"),
    "credential.rotate": ("key_id", "new_value"),
    "credential.status": ("key_id",),
    "credential.list": (),
    "credential.inject": ("key_id",),
}


@dataclass(frozen=True, slots=True)
class Manifest:
    module_id: str
    name: str
    version: str
    capability_domain: str
    entry: str
    exposes: tuple[str, ...]
    deps: dict[str, str]
    config_schema: dict[str, Any]
    permissions: tuple[str, ...]
    hooks: dict[str, str]
    path: Path

    @property
    def import_root(self) -> Path:
        return self.path.parent

    def as_dict(self) -> dict[str, Any]:
        value = {field: getattr(self, field) for field in REQUIRED_FIELDS}
        value["exposes"] = list(self.exposes)
        value["permissions"] = list(self.permissions)
        value["path"] = str(self.path)
        return value


def read_manifest(path: str | Path) -> Manifest:
    manifest_path = Path(path).resolve()
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"invalid module.json: {exc}") from exc
    validate_manifest(raw)
    return Manifest(
        module_id=raw["module_id"],
        name=raw["name"],
        version=raw["version"],
        capability_domain=raw["capability_domain"],
        entry=raw["entry"],
        exposes=tuple(raw["exposes"]),
        deps=dict(raw["deps"]),
        config_schema=dict(raw["config_schema"]),
        permissions=tuple(raw["permissions"]),
        hooks=dict(raw["hooks"]),
        path=manifest_path,
    )


def validate_manifest(raw: Any) -> None:
    if not isinstance(raw, dict):
        raise ManifestError("manifest root must be an object")
    missing = [field for field in REQUIRED_FIELDS if field not in raw]
    if missing:
        raise ManifestError(f"missing required fields: {', '.join(missing)}")
    if not isinstance(raw["module_id"], str) or not MODULE_RE.fullmatch(raw["module_id"]):
        raise ManifestError("invalid module_id")
    if not isinstance(raw["name"], str) or not raw["name"].strip():
        raise ManifestError("name must be a non-empty string")
    if not isinstance(raw["version"], str) or not SEMVER_RE.fullmatch(raw["version"]):
        raise ManifestError("version must be SemVer major.minor.patch")
    domain = raw["capability_domain"]
    if domain not in DOMAIN_EXPOSES:
        raise ManifestError("capability_domain must be L1 through L10")
    if not isinstance(raw["entry"], str) or not re.fullmatch(
        r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+", raw["entry"]
    ):
        raise ManifestError("entry must be a Python import path")
    exposes = raw["exposes"]
    if (
        not isinstance(exposes, list)
        or not exposes
        or len(exposes) != len(set(exposes))
        or not all(isinstance(item, str) for item in exposes)
        or not set(exposes).issubset(DOMAIN_EXPOSES[domain])
    ):
        raise ManifestError("exposes do not match capability_domain/API contract")
    if not isinstance(raw["deps"], dict) or not all(
        isinstance(key, str)
        and MODULE_RE.fullmatch(key)
        and isinstance(value, str)
        and VERSION_RANGE_RE.fullmatch(value)
        for key, value in raw["deps"].items()
    ):
        raise ManifestError("deps must map registered module IDs to valid version ranges")
    schema = raw["config_schema"]
    if not isinstance(schema, dict) or schema.get("type") != "object":
        raise ManifestError("config_schema must be an object JSON Schema")
    permissions = raw["permissions"]
    if not isinstance(permissions, list) or not all(
        isinstance(item, str) and PERMISSION_RE.fullmatch(item) for item in permissions
    ):
        raise ManifestError("permissions contain an invalid or path-level scope")
    hooks = raw["hooks"]
    if not isinstance(hooks, dict) or not all(
        key in {"on_load", "on_activate", "on_disable", "on_unload", "on_rollback"}
        and isinstance(value, str)
        and value.isidentifier()
        for key, value in hooks.items()
    ):
        raise ManifestError("hooks must contain named lifecycle callables")


def semver_key(version: str) -> tuple[int, int, int]:
    match = SEMVER_RE.fullmatch(version)
    if not match:
        raise ManifestError(f"invalid SemVer: {version}")
    return tuple(int(part) for part in match.groups())


def version_satisfies(version: str, constraint: str) -> bool:
    actual = semver_key(version)
    for clause in constraint.split(","):
        if clause.startswith(">=") and actual < semver_key(clause[2:]):
            return False
        if clause.startswith("<") and actual >= semver_key(clause[1:]):
            return False
        if clause.startswith("==") and actual != semver_key(clause[2:]):
            return False
    return True
