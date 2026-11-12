"""ADR-011 capability plugin bus kernel."""

from __future__ import annotations

import ast
import importlib
import inspect
import json
import sys
import time
import uuid
from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError as FutureTimeout
from pathlib import Path
from threading import RLock
from typing import Any

from .errors import (
    BusError,
    CallTimeout,
    LifecycleError,
    ManifestError,
    PermissionDenied,
    PluginFailure,
    RoutingError,
)
from .events import EventBus
from .manifest import INTERFACE_SIGNATURES, Manifest, read_manifest, version_satisfies
from .registry import Registry
from .storage import append_jsonl, load_json, now_iso, save_json


TRANSITIONS = {
    "registered": {"loading"},
    "loading": {"ready", "error"},
    "ready": {"routing", "error"},
    "routing": {"disabling", "error"},
    "disabling": {"disabled", "error"},
    "disabled": {"unloading"},
    "unloading": {"unloaded", "error"},
    "unloaded": {"loading"},
    "error": set(),
}
HOOK_TIMEOUTS = {
    "on_load": 5.0,
    "on_activate": 5.0,
    "on_disable": 10.0,
    "on_unload": 10.0,
    "on_rollback": 5.0,
}

# 强制驻留域（plugin-bus-spec §5.4）：guard/paradigm 不可热卸载/禁用，
# 总线启动时缺失任一 → 拒绝对外服务（fail-closed）
RESIDENT_DOMAINS = {"L8", "L10"}
# 域 → 模块名前缀（boot_check 判定"该域是否登记"）
RESIDENT_PREFIXES = {
    "L8": "ultima.guard.",
    "L10": "ultima.paradigm.",
}


class BusKernel:
    def __init__(
        self,
        *,
        root: str | Path | None = None,
        package_root: str | Path | None = None,
        state_path: str | Path | None = None,
        log_path: str | Path | None = None,
        ops_path: str | Path | None = None,
        static_registry: set[str] | None = None,
        sync_timeout: float = 10.0,
        smoke_timeout: float = 30.0,
    ) -> None:
        self.root = Path(root).resolve() if root else Path(__file__).resolve().parents[3]
        if str(self.root) not in sys.path:
            sys.path.insert(0, str(self.root))
        self.package_root = (
            Path(package_root).resolve()
            if package_root
            else self.root / "execution" / "packages"
        )
        self.state_path = Path(state_path).resolve() if state_path else self.root / "data" / "plugin-bus-state.json"
        self.log_path = Path(log_path).resolve() if log_path else self.root / "logs" / "plugin-bus.jsonl"
        self.ops_path = Path(ops_path).resolve() if ops_path else self.root / "sync" / "plugin-ops.jsonl"
        self._assert_in_domain(self.state_path, self.log_path, self.ops_path, self.package_root)
        self.static_registry = static_registry or self._load_static_registry()
        self.registry = Registry(load_json(self.state_path, {}))
        self.events = EventBus()
        self.sync_timeout = sync_timeout
        self.smoke_timeout = smoke_timeout
        self._instances: dict[tuple[str, str], Any] = {}
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ultima-bus")
        self._async: dict[str, Future] = {}
        self._lock = RLock()
        self._fail_closed_reason: str | None = None

    def close(self) -> None:
        self._executor.shutdown(wait=True, cancel_futures=True)

    def __enter__(self) -> "BusKernel":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    # ------------------------------------------------------------------
    # 强制驻留自检（plugin-bus-spec §5.4 fail-closed）
    # ------------------------------------------------------------------
    def boot_check(self) -> dict:
        """启动自检：guard/paradigm 驻留域必须登记且 routing，否则拒绝对外服务。

        以静态注册表（static_registry.json）为权威放行清单：
        - 某驻留域在静态注册表中无任何模块 → 该域缺失（fail-closed）；
        - 有登记但未注册、未 routing、或状态 error → fail-closed。
        """
        missing: list[str] = []
        not_routing: list[str] = []
        errored: list[str] = []
        for domain, prefix in RESIDENT_PREFIXES.items():
            candidates = [m for m in self.static_registry if m.startswith(prefix)]
            if not candidates:
                missing.append(f"{domain} 域未登记（静态注册表缺 {prefix}*）")
                continue
            for module_id in sorted(candidates):
                record = self.registry.records.get(module_id)
                if not record:
                    missing.append(f"{module_id} 未注册")
                    continue
                if not record.get("routing_version"):
                    not_routing.append(module_id)
                    continue
                state = record["versions"][record["routing_version"]]["state"]
                if state == "error":
                    errored.append(module_id)
        problems = []
        if missing:
            problems.append(f"驻留插件缺失: {'、'.join(missing)}")
        if not_routing:
            problems.append(f"驻留插件未就绪(routing): {', '.join(not_routing)}")
        if errored:
            problems.append(f"驻留插件加载失败(error): {', '.join(errored)}")
        if problems:
            self._fail_closed_reason = "；".join(problems)
            self._log(
                "boot.fail-closed",
                "server.kernel",
                {"reason": self._fail_closed_reason, "missing": missing,
                 "not_routing": not_routing, "errored": errored},
            )
            return {"ok": False, "fail_closed": True, "reason": self._fail_closed_reason}
        self._fail_closed_reason = None
        self._log("boot.ready", "server.kernel", {"resident_domains": sorted(RESIDENT_DOMAINS)})
        return {"ok": True, "fail_closed": False}

    def _guard_external_services(self, exempt_module_id: str | None = None) -> None:
        """对外服务入口硬闸：fail-closed 激活时拒绝对外调用。

        驻留插件自身（guard/paradigm）的 load 属于解除 fail-closed 的
        合法途径，予以豁免；其余模块一律受闸。
        """
        if self._fail_closed_reason:
            if exempt_module_id and any(
                exempt_module_id.startswith(prefix) for prefix in RESIDENT_PREFIXES.values()
            ):
                return
            raise BusError(
                "总线拒绝对外服务（fail-closed）：" + self._fail_closed_reason
            )

    def discover(self) -> list[dict[str, Any]]:
        results = []
        if not self.package_root.exists():
            return results
        for path in sorted(self.package_root.rglob("module.json")):
            results.append(self.register_manifest(path))
        return results

    def register_manifest(self, path: str | Path) -> dict[str, Any]:
        try:
            manifest = read_manifest(path)
            try:
                manifest.path.relative_to(self.package_root)
            except ValueError as exc:
                raise ManifestError(f"manifest is outside registered package root: {manifest.path}") from exc
            if manifest.module_id not in self.static_registry:
                raise ManifestError(f"module is absent from static registry: {manifest.module_id}")
            record = self.registry.register(manifest.as_dict())
            self._save()
            self._log("manifest.registered", manifest.module_id, {"version": manifest.version})
            self.boot_check()
            return {"ok": True, "record": record}
        except BusError as exc:
            self._log(
                "manifest.rejected",
                "server.kernel",
                {"path": str(path), "error_reason": str(exc)},
            )
            return {"ok": False, "error_reason": str(exc)}

    def load(self, module_id: str, version: str | None = None, *, source: str = "CLI") -> dict:
        self._guard_external_services(exempt_module_id=module_id)
        record = self.registry.records.get(module_id)
        if not record:
            raise RoutingError(f"module is not registered: {module_id}")
        version = version or record["installed_versions"][0]
        current = record["versions"][version]["state"]
        if current == "routing":
            self.boot_check()
            return {"ok": True, "module_id": module_id, "version": version, "state": current}
        if current == "ready":
            if record.get("routing_version") and record["routing_version"] != version:
                return {"ok": True, "module_id": module_id, "version": version, "state": "ready"}
            instance = self._get_instance(module_id, version)
            self._smoke(instance)
            self._transition(module_id, version, "routing")
            self.boot_check()
            return {"ok": True, "module_id": module_id, "version": version, "state": "routing"}
        self._transition(module_id, version, "loading")
        try:
            manifest = self._manifest(module_id, version)
            self._resolve_dependencies(manifest)
            self._audit_imports(manifest)
            instance = self._import_instance(manifest)
            self._validate_entry(instance, manifest)
            self._validate_config(manifest, {})
            self._run_hook(instance, manifest, "on_load")
            self._transition(module_id, version, "ready")
            self._run_hook(instance, manifest, "on_activate")
            if record.get("routing_version") and record["routing_version"] != version:
                return {"ok": True, "module_id": module_id, "version": version, "state": "ready"}
            self._smoke(instance)
            self._transition(module_id, version, "routing")
            # fail-closed 解除：驻留域（L8/L10）加载到 routing 后必须重算闸门，
            # 否则 _fail_closed_reason 会一直停留在"未就绪"，总线永久拒绝对外服务。
            # 非驻留插件加载后重算同样无害（boot_check 只看驻留域）。
            self.boot_check()
            self._write_op(source, module_id, None, version, "success")
            return {"ok": True, "module_id": module_id, "version": version, "state": "routing"}
        except Exception as exc:
            record["deps_resolved"] = {"ok": False, "reason": str(exc)}
            self._save()
            if self._state(module_id, version) in {"loading", "ready"}:
                self._transition(module_id, version, "error", str(exc))
            self._write_op(source, module_id, None, version, "failed", str(exc))
            self.boot_check()
            raise

    def unload(self, module_id: str, version: str | None = None, *, source: str = "CLI") -> dict:
        record = self.registry.records.get(module_id)
        if not record:
            raise RoutingError(f"module is not registered: {module_id}")
        version = version or record.get("routing_version")
        if not version:
            raise RoutingError(f"module has no loaded version: {module_id}")
        manifest = self._manifest(module_id, version)
        if manifest.capability_domain in RESIDENT_DOMAINS:
            self._audit("resident.unload.denied", module_id, {"version": version})
            raise PermissionDenied(f"resident plugin cannot be unloaded: {module_id}")
        self._disable_and_unload(module_id, version)
        self._write_op(source, module_id, version, None, "success")
        self.boot_check()
        return {"ok": True, "module_id": module_id, "version": version, "state": "unloaded"}

    def switch(self, module_id: str, version: str, *, source: str = "CLI") -> dict:
        self._guard_external_services()
        record = self.registry.records.get(module_id)
        if not record or version not in record["versions"]:
            raise RoutingError(f"version is not registered: {module_id}@{version}")
        old_version = record.get("routing_version")
        try:
            result = self.load(module_id, version, source=source)
            if result["state"] != "ready":
                if old_version == version:
                    return result
                raise LifecycleError("candidate did not stop in ready state")
            candidate = self._instances[(module_id, version)]
            self._smoke(candidate)
            if old_version and old_version != version:
                self._route_transfer(module_id, old_version, version)
                try:
                    self._disable_and_unload(module_id, old_version)
                except Exception as cleanup_error:
                    self._audit(
                        "blue-green.old-version-cleanup.failed",
                        module_id,
                        {"version": old_version, "error": str(cleanup_error)},
                    )
                    self._write_op(
                        source,
                        module_id,
                        old_version,
                        version,
                        "success",
                        f"old version cleanup failed: {cleanup_error}",
                    )
                    return {
                        "ok": True,
                        "module_id": module_id,
                        "from": old_version,
                        "to": version,
                        "cleanup_warning": str(cleanup_error),
                    }
            else:
                self._transition(module_id, version, "routing")
            self._write_op(source, module_id, old_version, version, "success")
            return {"ok": True, "module_id": module_id, "from": old_version, "to": version}
        except Exception as exc:
            if self._state(module_id, version) in {"loading", "ready"}:
                self._transition(module_id, version, "error", str(exc))
            # Routing never moved before smoke passed, so the old version remains live.
            if old_version:
                record["routing_version"] = old_version
                record["versions"][old_version]["state"] = "routing"
                self._save()
            self._run_rollback_hook(module_id, version)
            self._write_op(source, module_id, version, old_version, "rollback", str(exc))
            return {
                "ok": False,
                "rolled_back": old_version,
                "error": {"code": "E-500", "message": str(exc)},
            }

    def rollback(self, module_id: str, *, source: str = "CLI") -> dict:
        self._guard_external_services()
        record = self.registry.records.get(module_id)
        if not record or not record.get("routing_version"):
            raise RoutingError(f"module has no routing version: {module_id}")
        current = record["routing_version"]
        history = [item for item in record.get("route_history", []) if item != current]
        candidates = list(reversed(history))
        if not candidates:
            candidates = [item for item in record["installed_versions"] if item != current]
        if not candidates:
            raise RoutingError(f"module has no retained rollback version: {module_id}")
        target = candidates[0]
        state = self._state(module_id, target)
        if state == "unloaded":
            self.load(module_id, target, source=source)
        elif state == "error":
            raise LifecycleError(f"rollback target is in error: {module_id}@{target}")
        return self.switch(module_id, target, source=source)

    def call(
        self,
        interface_name: str,
        *args: Any,
        caller_module_id: str | None = None,
        timeout: float | None = None,
        req_id: str | None = None,
        **kwargs: Any,
    ) -> dict:
        self._guard_external_services()
        req_id = req_id or str(uuid.uuid4())
        try:
            provider = self.registry.find_by_expose(interface_name)
            self._authorize(caller_module_id, interface_name)
            instance = self._get_instance(provider["module_id"], provider["version"])
            callable_ = self._interface_callable(instance, interface_name)
            data = self._run_timed(
                lambda: callable_(*args, **kwargs), timeout or self.sync_timeout, interface_name
            )
            result = {"ok": True, "data": data, "reqId": req_id}
            self._log_call("KP-001", caller_module_id, provider["module_id"], interface_name, result)
            return result
        except BusError as exc:
            result = exc.as_result() | {"reqId": req_id}
            self._log_call("KP-001", caller_module_id, "server.kernel", interface_name, result)
            return result
        except Exception as exc:
            error = PluginFailure(str(exc))
            result = error.as_result() | {"reqId": req_id}
            self._log_call("KP-001", caller_module_id, "server.kernel", interface_name, result)
            return result

    def call_async(
        self,
        interface_name: str,
        *args: Any,
        req_id: str,
        caller_module_id: str | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> Future:
        self._guard_external_services()
        with self._lock:
            if req_id in self._async:
                self._audit("async.duplicate", caller_module_id or "external", {"reqId": req_id})
                return self._async[req_id]
            self._log(
                "bus.call.async.accepted",
                caller_module_id or "external",
                self._envelope(
                    "KP-002",
                    caller_module_id or "external",
                    "server.kernel",
                    {"interface": interface_name},
                    req_id=req_id,
                ),
            )
            future = self._executor.submit(
                self.call,
                interface_name,
                *args,
                caller_module_id=caller_module_id,
                timeout=timeout,
                req_id=req_id,
                **kwargs,
            )
            self._async[req_id] = future
            future.add_done_callback(
                lambda done: self.publish(
                    "async.result",
                    {"result": done.result()},
                    source="server.kernel",
                    msg_no="KP-005",
                    req_id=req_id,
                )
            )
            return future

    def publish(
        self,
        event_name: str,
        payload: dict[str, Any],
        *,
        source: str,
        msg_no: str = "KP-003",
        req_id: str | None = None,
    ) -> dict:
        submitted = self._envelope(
            msg_no,
            source,
            "server.kernel",
            {"event": event_name, "data": payload},
            req_id=req_id,
        )
        dispatched = submitted
        if msg_no == "KP-003":
            dispatched = self._envelope(
                "KP-004",
                "server.kernel",
                "server.plugin.subscribers",
                submitted["payload"],
                req_id=req_id,
            )
        submitted["delivered"] = self.events.publish(dispatched)
        self._log("event.published", source, {"submitted": submitted, "dispatched": dispatched})
        return submitted

    def subscribe(self, module_id: str, event_name: str, handler: Any) -> None:
        self.events.subscribe(module_id, event_name, handler)

    def direct_call(self, caller_module_id: str, target_module_id: str, interface_name: str) -> None:
        self._audit(
            "plugin.direct-connect.denied",
            caller_module_id,
            {"target": target_module_id, "interface": interface_name},
        )
        raise PermissionDenied("plugin-to-plugin direct connection is forbidden; use KP-001/KP-002")

    def status(self) -> dict:
        records = self.registry.list()
        boot = self.boot_check()
        return {
            "healthy": boot["ok"]
            and all(
                version["state"] != "error"
                for record in records
                for version in record["versions"].values()
                if version["state"] in {"routing", "error"}
            ),
            "fail_closed": boot["fail_closed"],
            "fail_closed_reason": boot.get("reason"),
            "sync_timeout_seconds": self.sync_timeout,
            "smoke_timeout_seconds": self.smoke_timeout,
            "modules": records,
        }

    def _transition(
        self, module_id: str, version: str, target: str, error_reason: str | None = None
    ) -> None:
        record = self.registry.records[module_id]
        version_record = record["versions"][version]
        source = version_record["state"]
        if target not in TRANSITIONS[source]:
            raise LifecycleError(f"invalid lifecycle transition: {source} -> {target}")
        if target == "routing":
            active = record.get("routing_version")
            if active and active != version and record["versions"][active]["state"] != "routing":
                raise LifecycleError("registry routing_version is inconsistent")
            record["routing_version"] = version
            if version in record["ready_versions"]:
                record["ready_versions"].remove(version)
        elif target == "ready" and version not in record["ready_versions"]:
            record["ready_versions"].append(version)
        elif source == "routing" and target in {"disabling", "error"}:
            if record.get("routing_version") == version:
                record["routing_version"] = None
        version_record["state"] = target
        if target == "routing" and (
            not record["route_history"] or record["route_history"][-1] != version
        ):
            record["route_history"].append(version)
            record["route_history"] = record["route_history"][-3:]
        version_record["updated_at"] = now_iso()
        record["updated_at"] = version_record["updated_at"]
        record["error_reason"] = error_reason
        self._save()
        payload = {"module_id": module_id, "version": version, "from": source, "to": target}
        if error_reason:
            payload["error_reason"] = error_reason
        self._log("lifecycle.transition", module_id, payload)
        envelope = self._envelope("KP-006", "server.kernel", "server.plugin.*", {"event": "lifecycle", "data": payload})
        self.events.publish(envelope)

    def _disable_and_unload(self, module_id: str, version: str) -> None:
        instance = self._get_instance(module_id, version)
        manifest = self._manifest(module_id, version)
        if self._state(module_id, version) == "routing":
            self._transition(module_id, version, "disabling")
        try:
            self._run_hook(instance, manifest, "on_disable")
        except Exception as exc:
            self._audit("hook.on_disable.failed", module_id, {"version": version, "error": str(exc)})
        self.events.unsubscribe_module(module_id)
        self._transition(module_id, version, "disabled")
        self._transition(module_id, version, "unloading")
        try:
            self._run_hook(instance, manifest, "on_unload")
        except Exception as exc:
            self._transition(module_id, version, "error", str(exc))
            self._instances.pop((module_id, version), None)
            raise
        self._transition(module_id, version, "unloaded")
        self._instances.pop((module_id, version), None)

    def _route_transfer(self, module_id: str, old_version: str, new_version: str) -> None:
        """Atomically select the new route and begin draining the old version."""
        with self._lock:
            record = self.registry.records[module_id]
            if self._state(module_id, old_version) != "routing" or self._state(module_id, new_version) != "ready":
                raise LifecycleError("route transfer requires routing old and ready new versions")
            timestamp = now_iso()
            record["routing_version"] = new_version
            record["versions"][new_version]["state"] = "routing"
            record["versions"][new_version]["updated_at"] = timestamp
            record["versions"][old_version]["state"] = "disabling"
            record["versions"][old_version]["updated_at"] = timestamp
            record["ready_versions"].remove(new_version)
            if not record["route_history"] or record["route_history"][-1] != new_version:
                record["route_history"].append(new_version)
                record["route_history"] = record["route_history"][-3:]
            record["updated_at"] = timestamp
            self._save()
        for version, source, target in (
            (new_version, "ready", "routing"),
            (old_version, "routing", "disabling"),
        ):
            payload = {"module_id": module_id, "version": version, "from": source, "to": target}
            self._log("lifecycle.transition", module_id, payload)
            self.events.publish(
                self._envelope(
                    "KP-006", "server.kernel", "server.plugin.*", {"event": "lifecycle", "data": payload}
                )
            )

    def _smoke(self, instance: Any) -> None:
        smoke = getattr(instance, "smoke", None)
        if not callable(smoke):
            raise ManifestError("entry must expose smoke()")
        smoke_result = self._run_timed(smoke, self.smoke_timeout, "smoke")
        if smoke_result is not True:
            raise PluginFailure(f"smoke failed: {smoke_result!r}")

    def _resolve_dependencies(self, manifest: Manifest) -> None:
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(module_id: str) -> None:
            if module_id in visiting:
                raise ManifestError(f"dependency cycle detected at {module_id}")
            if module_id in visited:
                return
            visiting.add(module_id)
            record = self.registry.records.get(module_id)
            if record:
                for candidate in record["versions"].values():
                    for dependency in candidate["manifest"]["deps"]:
                        visit(dependency)
            visiting.remove(module_id)
            visited.add(module_id)

        visit(manifest.module_id)
        for dependency, constraint in manifest.deps.items():
            record = self.registry.records.get(dependency)
            if not record:
                raise ManifestError(f"missing dependency: {dependency}")
            matching = [
                version for version in record["installed_versions"] if version_satisfies(version, constraint)
            ]
            if not matching:
                raise ManifestError(f"dependency version conflict: {dependency} {constraint}")
        record = self.registry.records[manifest.module_id]
        record["deps_resolved"] = {"ok": True, "reason": "resolved"}
        self._save()

    def _audit_imports(self, manifest: Manifest) -> None:
        registered_ids = {
            record["module_id"]
            for record in self.registry.records.values()
        }
        own_id = manifest.module_id
        for source in manifest.import_root.rglob("*.py"):
            tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
            imported: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module)
                elif isinstance(node, ast.Call):
                    dynamic_name = None
                    if isinstance(node.func, ast.Name):
                        dynamic_name = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        dynamic_name = node.func.attr
                    if dynamic_name in {"eval", "exec", "__import__", "import_module"}:
                        self._audit(
                            "plugin.dynamic-code.denied",
                            manifest.module_id,
                            {"call": dynamic_name, "source": str(source)},
                        )
                        raise PermissionDenied(
                            f"dynamic loading/execution is forbidden: {dynamic_name}"
                        )
            # 按完整 module_id 前缀判定跨模块直连：命中已注册插件自身或其子包即违规
            forbidden: set[str] = set()
            for target in imported:
                if target == own_id or target.startswith(own_id + "."):
                    continue  # 插件自引用（内部子包）放行
                for rid in sorted(registered_ids):
                    if rid == own_id:
                        continue
                    if target == rid or target.startswith(rid + "."):
                        forbidden.add(rid)
            if forbidden:
                self._audit(
                    "plugin.direct-import.denied",
                    manifest.module_id,
                    {"imports": sorted(forbidden), "source": str(source)},
                )
                raise PermissionDenied(f"direct plugin import forbidden: {', '.join(sorted(forbidden))}")

    def _import_instance(self, manifest: Manifest) -> Any:
        import_root = str(manifest.import_root)
        if import_root not in sys.path:
            sys.path.insert(0, import_root)
        module = importlib.import_module(manifest.entry)
        factory = getattr(module, "create_plugin", None)
        if not callable(factory):
            raise ManifestError("entry must export create_plugin()")
        instance = factory()
        self._instances[(manifest.module_id, manifest.version)] = instance
        return instance

    def _validate_entry(self, instance: Any, manifest: Manifest) -> None:
        for interface_name in manifest.exposes:
            callable_ = self._interface_callable(instance, interface_name)
            actual = tuple(inspect.signature(callable_).parameters)
            expected = INTERFACE_SIGNATURES[interface_name]
            if actual != expected:
                raise ManifestError(
                    f"signature mismatch for {interface_name}: expected {expected}, got {actual}"
                )
        for hook in manifest.hooks.values():
            if not callable(getattr(instance, hook, None)):
                raise ManifestError(f"missing lifecycle hook: {hook}")

    def _validate_config(self, manifest: Manifest, options: dict[str, Any]) -> None:
        schema = manifest.config_schema
        required = schema.get("required", [])
        missing = [key for key in required if key not in options]
        if missing:
            raise ManifestError(f"config missing required properties: {', '.join(missing)}")
        if schema.get("additionalProperties") is False:
            unknown = set(options) - set(schema.get("properties", {}))
            if unknown:
                raise ManifestError(f"config has unknown properties: {', '.join(sorted(unknown))}")

    def _authorize(self, caller_module_id: str | None, interface_name: str) -> None:
        if not caller_module_id:
            return
        record = self.registry.records.get(caller_module_id)
        if not record or not record.get("routing_version"):
            raise PermissionDenied(f"caller is not routing: {caller_module_id}")
        manifest = record["versions"][record["routing_version"]]["manifest"]
        if f"cap:{interface_name}" not in manifest["permissions"]:
            self._audit(
                "permission.denied",
                caller_module_id,
                {"scope": f"cap:{interface_name}"},
            )
            raise PermissionDenied(f"undeclared capability scope: cap:{interface_name}")

    def _run_hook(self, instance: Any, manifest: Manifest, hook_name: str) -> None:
        method_name = manifest.hooks.get(hook_name)
        if method_name:
            self._run_timed(getattr(instance, method_name), HOOK_TIMEOUTS[hook_name], hook_name)

    def _run_rollback_hook(self, module_id: str, version: str) -> None:
        instance = self._instances.get((module_id, version))
        if not instance:
            return
        try:
            self._run_hook(instance, self._manifest(module_id, version), "on_rollback")
        except Exception as exc:
            self._audit("hook.on_rollback.failed", module_id, {"version": version, "error": str(exc)})

    def _run_timed(self, callable_: Any, timeout: float, label: str) -> Any:
        future = self._executor.submit(callable_)
        try:
            return future.result(timeout=timeout)
        except FutureTimeout as exc:
            future.cancel()
            raise CallTimeout(f"{label} timed out after {timeout:g}s") from exc

    def _get_instance(self, module_id: str, version: str) -> Any:
        key = (module_id, version)
        if key not in self._instances:
            self._instances[key] = self._import_instance(self._manifest(module_id, version))
        return self._instances[key]

    def _manifest(self, module_id: str, version: str) -> Manifest:
        path = self.registry.records[module_id]["versions"][version]["manifest"]["path"]
        return read_manifest(path)

    def _state(self, module_id: str, version: str) -> str:
        return self.registry.records[module_id]["versions"][version]["state"]

    @staticmethod
    def _interface_callable(instance: Any, interface_name: str) -> Any:
        method = interface_name.replace(".", "_")
        callable_ = getattr(instance, method, None)
        if not callable(callable_):
            raise ManifestError(f"entry does not implement {interface_name} as {method}")
        return callable_

    def _load_static_registry(self) -> set[str]:
        path = Path(__file__).with_name("static_registry.json")
        return set(json.loads(path.read_text(encoding="utf-8"))["modules"])

    def _save(self) -> None:
        self._assert_in_domain(self.state_path)
        save_json(self.state_path, self.registry.snapshot())

    def _log(self, event_type: str, source: str, payload: dict[str, Any]) -> None:
        self._assert_in_domain(self.log_path)
        append_jsonl(
            self.log_path,
            {
                "ts": now_iso(),
                "session_id": "plugin-bus",
                "source": source,
                "event_type": event_type,
                "payload": payload,
            },
        )

    def _audit(self, event_type: str, source: str, payload: dict[str, Any]) -> None:
        self._log(f"audit.{event_type}", source, payload)

    def _log_call(
        self, msg_no: str, source: str | None, target: str, interface_name: str, result: dict
    ) -> None:
        self._log(
            "bus.call",
            source or "external",
            {"msgNo": msg_no, "to": target, "interface": interface_name, "result": result},
        )

    def _write_op(
        self,
        source: str,
        module_id: str,
        from_version: str | None,
        to_version: str | None,
        result: str,
        reason: str | None = None,
    ) -> None:
        self._assert_in_domain(self.ops_path)
        append_jsonl(
            self.ops_path,
            {
                "source": source,
                "ts": now_iso(),
                "module_id": module_id,
                "from_version": from_version,
                "to_version": to_version,
                "result": result,
                "reason": reason,
            },
        )

    @staticmethod
    def _envelope(
        msg_no: str,
        source: str,
        target: str,
        payload: dict[str, Any],
        *,
        req_id: str | None = None,
    ) -> dict[str, Any]:
        return {
            "v": 2,
            "msgId": str(uuid.uuid4()),
            "type": "event" if msg_no in {"KP-003", "KP-004", "KP-006"} else "result",
            "ts": int(time.time() * 1000),
            "from": f"server.plugin.{source}" if not source.startswith("server.") else source,
            "to": target,
            "msgNo": msg_no,
            "reqId": req_id,
            "payload": payload,
            "meta": {},
        }

    def _assert_in_domain(self, *paths: Path) -> None:
        for path in paths:
            try:
                path.resolve().relative_to(self.root)
            except ValueError as exc:
                raise PermissionDenied(f"path escapes fileDomain: {path}") from exc
