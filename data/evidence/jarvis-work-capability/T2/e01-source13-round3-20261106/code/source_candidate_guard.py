"""Read-only admission guard for the fixed source13 dependency/content candidate."""
from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
from typing import Any

ROOT = Path(r"C:/Users/Administrator/.codex/worktrees/jarvis-e03-source13/UltimaAgent")
MANIFEST = Path(r"H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e01-source13-round3-20261106/inputs/candidate-runtime-manifest.json")
EXPECTED_MANIFEST_SHA256 = "957669cb3463eab549df80f0b8fc6345c244daa2f613925abe8622d0aab3d9d3"
EXPECTED_CANDIDATE = "269aca511d88412dbb9c15d23911138469a37aa2"
EXPECTED_BRANCH = "codex/jarvis-work-source13-runtime-failure"
EXPECTED_MODEL_DIGEST = "6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330"
EXPECTED_MODEL_ALIAS = "qwen3-8b-uncensored"
EXPECTED_NATIVE_VERSION = "0.32.15"


class CandidateError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise CandidateError(message)


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        _need(key not in result, "duplicate candidate manifest key")
        result[key] = value
    return result


def _canonical_file(value: Any, label: str) -> Path:
    _need(isinstance(value, str) and bool(value), f"{label} path must be a string")
    path = Path(value)
    _need(path.is_absolute(), f"{label} path must be absolute")
    _need(".." not in path.parts, f"{label} path traversal")
    try:
        absolute = path.absolute()
        for part in (absolute, *absolute.parents):
            if not part.exists():
                continue
            info = part.lstat()
            attrs = getattr(info, "st_file_attributes", 0)
            reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
            _need(not part.is_symlink() and not attrs & reparse, f"{label} reparse path forbidden")
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise CandidateError(f"{label} path unavailable") from exc
    _need(resolved.is_file(), f"{label} must be a file")
    return resolved


def _same_path(first: Path, second: Path) -> bool:
    return os.path.normcase(str(first.resolve(strict=True))) == os.path.normcase(str(second.resolve(strict=True)))


def _verify_hash(path_value: Any, expected: Any, label: str, *, root: Path | None = None) -> Path:
    _need(isinstance(expected, str) and re.fullmatch(r"[0-9a-f]{64}", expected) is not None, f"{label} SHA256 malformed")
    path = _canonical_file(path_value, label)
    if root is not None:
        try:
            inside = path.is_relative_to(root)
        except AttributeError:
            inside = os.path.commonpath((str(path), str(root))) == str(root)
        _need(inside, f"{label} path outside candidate root")
    _need(_sha(path) == expected, f"{label} hash mismatch")
    return path


def _verify_receipt(path_value: Any, expected: Any, label: str, minimum: int) -> None:
    path = _verify_hash(path_value, expected, label)
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_pairs)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CandidateError(f"{label} JSON unreadable") from exc
    _need(isinstance(value, dict), f"{label} JSON shape")
    _need(value.get("candidate") == EXPECTED_CANDIDATE, f"{label} receipt candidate mismatch")
    counts = value.get("counts")
    _need(isinstance(counts, dict), f"{label} counts missing")
    _need(type(counts.get("tests")) is int and counts["tests"] >= minimum, f"{label} pass count missing")
    _need(all(type(counts.get(key)) is int and counts[key] == 0 for key in ("failures", "errors", "skipped")), f"{label} has failed or skipped tests")
    _need(type(value.get("exit_code")) is int and value["exit_code"] == 0, f"{label} exit failed")
    _need(type(value.get("source_unchanged")) is bool and value["source_unchanged"] is True, f"{label} source drift")
    if "only_evidence_root_changed" in value:
        _need(value["only_evidence_root_changed"] is True, f"{label} compatibility scope changed")


_PROJECT_IMPORT_ROOTS = {"src", "tasks"}


def _resolve_project_import(root: Path, module_parts: tuple[str, ...], *, required: bool) -> Path | None:
    if not module_parts or module_parts[0] not in _PROJECT_IMPORT_ROOTS:
        return None
    module_file = root.joinpath(*module_parts[:-1], module_parts[-1] + ".py")
    package_dir = root.joinpath(*module_parts)
    package_file = package_dir / "__init__.py"
    candidates = [path for path in (module_file, package_file) if path.is_file()]
    _need(len(candidates) <= 1, "ambiguous project runtime import " + ".".join(module_parts))
    if candidates:
        target = candidates[0].resolve(strict=True)
        _need(target.is_relative_to(root), "project runtime import outside candidate root")
        return target
    if package_dir.is_dir():
        namespace = package_dir.resolve(strict=True)
        _need(namespace.is_relative_to(root), "project namespace import outside candidate root")
        return None
    if required:
        raise CandidateError("unresolved project runtime import " + ".".join(module_parts))
    return None


def _project_import_parts(node: ast.ImportFrom, package_parts: tuple[str, ...]) -> tuple[str, ...]:
    if node.level:
        _need(node.level <= len(package_parts), "invalid relative project runtime import")
        base = package_parts[: len(package_parts) - node.level + 1]
        tail = tuple(part for part in (node.module or "").split(".") if part)
        return base + tail
    return tuple(part for part in (node.module or "").split(".") if part)


def _verify_project_import_closure(root: Path, seeds: set[Path], pinned_source_paths: set[Path]) -> None:
    """Require every reachable src/tasks module and package initializer to be pinned."""
    pending = list(seeds)
    visited: set[Path] = set()
    while pending:
        source = pending.pop()
        _need(source.is_relative_to(root), "project runtime module outside candidate root")
        if source in visited:
            continue
        _need(
            source in pinned_source_paths,
            "unbound project runtime import " + source.relative_to(root).as_posix(),
        )
        visited.add(source)
        package_parts = source.relative_to(root).parent.parts
        for index in range(1, len(package_parts) + 1):
            initializer = root.joinpath(*package_parts[:index], "__init__.py")
            if initializer.is_file():
                initializer = initializer.resolve(strict=True)
                _need(initializer.is_relative_to(root), "project package initializer outside candidate root")
                _need(
                    initializer in pinned_source_paths,
                    "unbound project runtime import " + initializer.relative_to(root).as_posix(),
                )
                pending.append(initializer)
        try:
            tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        except (OSError, UnicodeError, SyntaxError) as exc:
            raise CandidateError("project runtime module unreadable " + source.relative_to(root).as_posix()) from exc

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    parts = tuple(alias.name.split("."))
                    if parts and parts[0] in _PROJECT_IMPORT_ROOTS:
                        target = _resolve_project_import(root, parts, required=True)
                        if target is not None:
                            pending.append(target)
            elif isinstance(node, ast.ImportFrom):
                parts = _project_import_parts(node, package_parts)
                if not parts or parts[0] not in _PROJECT_IMPORT_ROOTS:
                    continue
                target = _resolve_project_import(root, parts, required=True)
                if target is not None:
                    pending.append(target)
                package_dir = root.joinpath(*parts)
                if package_dir.is_dir():
                    for alias in node.names:
                        if alias.name == "*":
                            continue
                        child_parts = parts + (alias.name,)
                        child = _resolve_project_import(root, child_parts, required=False)
                        if child is not None:
                            pending.append(child)

def _verify_work_agent_dynamic_imports(root: Path, pinned_source_paths: set[Path]) -> None:
    """Bind the literal dynamic tool-registry imports used by the isolated work agent."""
    server_path = root / "src" / "brain" / "agent_server.py"
    if not server_path.exists():
        return  # Synthetic guard fixtures do not model the product runtime.
    server_path = server_path.resolve(strict=True)
    _need(server_path in pinned_source_paths, "work-agent server entrypoint is not pinned")

    try:
        tree = ast.parse(server_path.read_text(encoding="utf-8"), filename=str(server_path))
    except (OSError, UnicodeError, SyntaxError) as exc:
        raise CandidateError("work-agent runtime entrypoint is unreadable") from exc

    registration = next(
        (
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "_ensure_tools_registered"
        ),
        None,
    )
    _need(registration is not None, "work-agent tool registration entrypoint is missing")

    package_parts = server_path.relative_to(root).parent.parts
    imported_paths: set[Path] = set()
    found = False
    for node in ast.walk(registration):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "import_module"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "importlib"
        ):
            continue
        found = True
        _need(
            bool(node.args)
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str),
            "unresolved dynamic runtime import in work-agent tool registration",
        )
        module_name = node.args[0].value
        if module_name.startswith("."):
            level = len(module_name) - len(module_name.lstrip("."))
            _need(level <= len(package_parts), "invalid relative dynamic runtime import")
            base_parts = package_parts[: len(package_parts) - level + 1]
            tail = tuple(part for part in module_name[level:].split(".") if part)
            module_parts = base_parts + tail
        elif "." not in module_name:
            module_parts = package_parts + (module_name,)
        else:
            module_parts = tuple(part for part in module_name.split(".") if part)

        _need(bool(module_parts), "empty dynamic runtime import")
        module_file = root.joinpath(*module_parts[:-1], module_parts[-1] + ".py")
        package_file = root.joinpath(*module_parts, "__init__.py")
        candidates = [path for path in (module_file, package_file) if path.is_file()]
        _need(
            len(candidates) == 1,
            f"unresolved or ambiguous dynamic runtime import {module_name}",
        )
        target = candidates[0].resolve(strict=True)
        _need(target.is_relative_to(root), "dynamic runtime import outside candidate root")
        _need(
            target in pinned_source_paths,
            "unbound dynamic runtime import " + target.relative_to(root).as_posix(),
        )
        imported_paths.add(target)

    _need(found and imported_paths, "work-agent dynamic import closure could not be established")
    # E03 reaches LocalExecChannel lazily, outside legacy tool registration.
    # Pin that observed execution dependency and its transitive local imports.
    exec_channel = _resolve_project_import(root, ("src", "brain", "exec", "channel"), required=True)
    _need(exec_channel is not None, "E03 local execution channel missing")
    imported_paths.add(exec_channel)
    _verify_project_import_closure(root, imported_paths, pinned_source_paths)

_EXPECTED_SDK_COMPONENT_NAMES = frozenset({"openjarvis", "openjarvis_rust", "openjarvis-1.0.4.dist-info", "openjarvis_rust-0.1.0.dist-info"})


def _canonical_directory(value: Any, label: str) -> Path:
    _need(isinstance(value, str) and bool(value), f"{label} path must be a string")
    path = Path(value)
    _need(path.is_absolute(), f"{label} path must be absolute")
    _need(".." not in path.parts, f"{label} path traversal")
    try:
        absolute = path.absolute()
        for part in (absolute, *absolute.parents):
            if not part.exists():
                continue
            info = part.lstat()
            attrs = getattr(info, "st_file_attributes", 0)
            reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
            _need(not part.is_symlink() and not attrs & reparse, f"{label} reparse path forbidden")
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise CandidateError(f"{label} path unavailable") from exc
    _need(resolved.is_dir(), f"{label} must be a directory")
    return resolved


def _sdk_component_file_entries(value: Any, *, verify_hashes: bool = False) -> dict[str, str]:
    _need(isinstance(value, dict), "SDK component inventory missing")
    _need(set(value) == _EXPECTED_SDK_COMPONENT_NAMES, "SDK component inventory must bind all required OpenJarvis distribution components")
    canonical_entries: dict[str, str] = {}
    seen_absolute: set[str] = set()
    for package_name in sorted(_EXPECTED_SDK_COMPONENT_NAMES):
        descriptor = value[package_name]
        _need(isinstance(descriptor, dict) and set(descriptor) == {"root", "files"}, "SDK component descriptor malformed")
        root = _canonical_directory(descriptor.get("root"), "SDK component root")
        _need(root.name.casefold() == package_name and root.parent.name.casefold() == "site-packages", "SDK component root must be the named installed site-packages package")
        file_entries = descriptor.get("files")
        _need(isinstance(file_entries, dict) and bool(file_entries), "SDK component files missing")
        actual_paths: dict[str, Path] = {}
        try:
            for item in root.rglob("*"):
                info = item.lstat()
                attrs = getattr(info, "st_file_attributes", 0)
                reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
                _need(not item.is_symlink() and not attrs & reparse, "SDK component reparse entry forbidden")
                if item.is_dir():
                    continue
                _need(item.is_file(), "SDK component contains unsupported filesystem entry")
                relative = item.relative_to(root).as_posix().casefold()
                _need(relative not in actual_paths, "SDK component case-fold path collision")
                actual_paths[relative] = item
        except OSError as exc:
            raise CandidateError("SDK component inventory unavailable") from exc
        pinned_paths: set[str] = set()
        for relative_value, expected in file_entries.items():
            _need(isinstance(relative_value, str) and relative_value, "SDK component relative path malformed")
            _need("\\" not in relative_value and not relative_value.startswith("/") and ":" not in relative_value, "SDK component relative path malformed")
            parts = relative_value.split("/")
            _need(all(part not in ("", ".", "..") for part in parts), "SDK component relative path traversal")
            relative = "/".join(parts).casefold()
            _need(relative not in pinned_paths, "duplicate SDK component relative path")
            pinned_paths.add(relative)
            _need(isinstance(expected, str) and re.fullmatch(r"[0-9a-f]{64}", expected) is not None, "SDK component file SHA256 malformed")
            _need(relative in actual_paths, "SDK component inventory mismatch")
            path = _canonical_file(str(root.joinpath(*parts)), "SDK component file")
            _need(path.is_relative_to(root), "SDK component file outside package root")
            canonical_key = str(path)
            normalized_key = os.path.normcase(canonical_key)
            _need(normalized_key not in seen_absolute, "duplicate SDK component file path")
            seen_absolute.add(normalized_key)
            if verify_hashes:
                _need(_sha(path) == expected, "SDK component file hash mismatch")
            canonical_entries[canonical_key] = expected
        _need(pinned_paths == set(actual_paths), "SDK component inventory mismatch")
    return canonical_entries


def _verify_candidate_manifest(
    root_value: Path,
    manifest_value: Path,
    expected_manifest_sha256: str,
    observed_head: str,
    observed_branch: str,
) -> dict[str, Any]:
    root = Path(root_value).resolve(strict=True)
    _need(root.is_dir(), "candidate root must be a directory")
    manifest_path = _canonical_file(str(manifest_value), "candidate manifest")
    raw = manifest_path.read_bytes()
    _need(hashlib.sha256(raw).hexdigest() == expected_manifest_sha256, "candidate manifest hash mismatch")
    _need(len(raw) <= 2 * 1024 * 1024, "candidate manifest too large")
    try:
        manifest = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CandidateError("candidate manifest JSON unreadable") from exc
    _need(isinstance(manifest, dict) and manifest.get("schema_version") == 1, "candidate manifest schema")
    _need(manifest.get("candidate") == EXPECTED_CANDIDATE and observed_head == EXPECTED_CANDIDATE, "candidate HEAD mismatch")
    _need(manifest.get("branch") == EXPECTED_BRANCH and observed_branch == EXPECTED_BRANCH, "candidate branch mismatch")
    _need(isinstance(manifest.get("candidate_root"), str) and _same_path(Path(manifest["candidate_root"]), root), "candidate root mismatch")

    model = manifest.get("model")
    _need(isinstance(model, dict), "candidate model descriptor missing")
    _need(model.get("alias") == EXPECTED_MODEL_ALIAS and model.get("digest") == EXPECTED_MODEL_DIGEST, "candidate model mismatch")
    _need(model.get("expected_native_version") == EXPECTED_NATIVE_VERSION, "candidate native version mismatch")
    _need(model.get("only_current8b") is True and model.get("otherweights_or_larger_allowed") is False, "candidate model policy widened")
    _verify_hash(model.get("local_manifest_path"), model.get("local_manifest_observed_sha256"), "local 8B manifest")
    _verify_hash(model.get("policy_path"), model.get("policy_sha256"), "8B model policy")

    source_files = manifest.get("source_files")
    _need(isinstance(source_files, dict) and len(source_files) >= 1, "candidate source inventory missing")
    pinned_source_paths: set[Path] = set()
    for path_value, expected in source_files.items():
        pinned_source_paths.add(_verify_hash(path_value, expected, "source file", root=root))
    _verify_work_agent_dynamic_imports(root, pinned_source_paths)

    dependencies = manifest.get("dependencies")
    _need(isinstance(dependencies, dict) and len(dependencies) >= 1, "candidate dependency inventory missing")
    for path_value, expected in dependencies.items():
        _verify_hash(path_value, expected, "candidate dependency")

    sdk_files = _sdk_component_file_entries(manifest.get("sdk_components"), verify_hashes=True)
    for path_value, expected in sdk_files.items():
        _verify_hash(path_value, expected, "SDK source")

    gate = manifest.get("code_gate")
    _need(isinstance(gate, dict), "candidate code gate missing")
    verdict = _verify_hash(gate.get("path"), gate.get("sha256"), "source10 code verdict")
    try:
        verdict_data = json.loads(verdict.read_text(encoding="utf-8"), object_pairs_hook=_pairs)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CandidateError("source10 code verdict unreadable") from exc
    _need(isinstance(verdict_data, dict), "source10 code verdict shape")
    _need(verdict_data.get("SPEC") == "PASS" and verdict_data.get("QUALITY") == "PASS", "source10 code review not PASS")
    _need(verdict_data.get("code_candidate_ready") is True, "source10 candidate not ready")
    _need(verdict_data.get("open_findings") == [] and verdict_data.get("new_breakage") == [], "source10 code findings remain")
    _need(verdict_data.get("actual") is False and verdict_data.get("model_calls") == 0, "source10 review includes actual execution")
    _verify_hash(gate.get("report_path"), gate.get("report_sha256"), "source10 code review report")

    tests = manifest.get("final_code_tests")
    _need(isinstance(tests, dict) and tests.get("covering") == 485 and tests.get("compat") == 8, "source10 test inventory mismatch")
    _verify_receipt(tests.get("full_receipt"), tests.get("full_sha256"), "source10 covering receipt", 485)
    _verify_receipt(tests.get("compat_receipt"), tests.get("compat_sha256"), "source10 compatibility receipt", 8)
    _verify_hash(manifest.get("original_corpus_readback"), manifest.get("original_corpus_readback_sha256"), "source10 corpus readback")
    _verify_hash(manifest.get("last_protected_readback"), manifest.get("last_protected_readback_sha256"), "source10 protected readback")
    _verify_hash(manifest.get("historical_source21_path"), manifest.get("historical_source21_sha256"), "historical source21 baseline")

    return {
        "candidate": EXPECTED_CANDIDATE,
        "branch": EXPECTED_BRANCH,
        "candidate_manifest_sha256": expected_manifest_sha256,
        "model_digest": EXPECTED_MODEL_DIGEST,
        "source_file_count": len(source_files),
        "dependency_count": len(dependencies),
        "sdk_component_count": len(_EXPECTED_SDK_COMPONENT_NAMES),
        "sdk_component_file_count": len(sdk_files),
        "code_gate": "PASS",
        "covering_tests": tests["covering"],
        "compatibility_tests": tests["compat"],
        "actual_release": False,
    }


def candidate_input_snapshot(
    manifest_value: Path = MANIFEST,
    *,
    expected_manifest_sha256: str | None = None,
) -> dict[str, str]:
    manifest_path = _canonical_file(str(manifest_value), "candidate manifest")
    raw = manifest_path.read_bytes()
    if expected_manifest_sha256 is not None:
        _need(hashlib.sha256(raw).hexdigest() == expected_manifest_sha256, "candidate manifest hash mismatch")
    try:
        manifest = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CandidateError("candidate manifest JSON unreadable") from exc
    _need(isinstance(manifest, dict), "candidate manifest shape")
    root_value = manifest.get("candidate_root")
    _need(isinstance(root_value, str), "candidate root missing")
    root = Path(root_value).resolve(strict=True)
    snapshots: dict[str, str] = {}
    groups = (
        ("source_files", manifest.get("source_files")),
        ("dependencies", manifest.get("dependencies")),
        ("sdk_components", _sdk_component_file_entries(manifest.get("sdk_components"))),
    )
    for group, entries in groups:
        _need(isinstance(entries, dict) and bool(entries), f"candidate {group} inventory missing")
        for path_value in entries:
            path = _canonical_file(path_value, f"candidate {group} entry")
            if group == "source_files":
                _need(path.is_relative_to(root), "source file path outside candidate root")
            key = f"{group}:{path}"
            _need(key not in snapshots, "duplicate candidate input path")
            snapshots[key] = _sha(path)
    return snapshots

def verify_current_candidate() -> dict[str, Any]:
    root = ROOT.resolve(strict=True)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True, encoding="utf-8"
    ).stdout.strip()
    branch = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root, check=True, capture_output=True, text=True, encoding="utf-8"
    ).stdout.strip()
    return _verify_candidate_manifest(root, MANIFEST, EXPECTED_MANIFEST_SHA256, head, branch)
