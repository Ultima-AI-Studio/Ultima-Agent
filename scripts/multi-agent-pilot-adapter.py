"""Deterministic stub adapter for a validated work-package bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from tasks.queue_engine.dispatcher import process_identity  # noqa: E402


class AdapterFailure(RuntimeError):
    def __init__(self, reason: str, *, application_count: int = 0) -> None:
        super().__init__(reason)
        self.reason = reason
        self.application_count = application_count


class ReceiptReturnLost(RuntimeError):
    def __init__(self, receipt_id: str) -> None:
        super().__init__(receipt_id)
        self.receipt_id = receipt_id


def _write(path: Path, value: Any) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    path.write_bytes(data)
    return data


def _event(ledger: Path, event_type: str, **values: Any) -> None:
    with ledger.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"type": event_type, **values}, sort_keys=True) + "\n")


def _git(git: str, repo: Path, *args: str) -> str:
    result = subprocess.run([git, "-C", str(repo), *args], text=True, capture_output=True, shell=False)
    if result.returncode:
        raise AdapterFailure("GIT_OPERATION_FAILED")
    return result.stdout.strip()


def validate(validator: Path, schema: Path, bundle: Path, expected: int | None = None) -> dict[str, Any]:
    command = [sys.executable, str(validator), "--schema", str(schema), "--input", str(bundle)]
    if expected is not None:
        command.extend(["--expect-effective-parallelism", str(expected)])
    result = subprocess.run(command, text=True, capture_output=True, shell=False)
    payload = json.loads(result.stdout)
    if result.returncode:
        raise AdapterFailure(payload.get("reason_codes", ["CONTRACT_INVALID"])[0])
    return payload


def _spawn(exit_code: int, delay: float, release: Path | None = None) -> tuple[subprocess.Popen[bytes], str | None, float]:
    code = f"import time,sys; time.sleep({delay!r}); sys.exit({exit_code})"
    if release is not None:
        code = (f"import os,time,sys\nwhile not os.path.exists({str(release)!r}): time.sleep(.005)\n"
                f"time.sleep({delay!r})\nsys.exit({exit_code})")
    process = subprocess.Popen(
        [sys.executable, "-c", code],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False,
    )
    return process, process_identity(process.pid), time.monotonic()


def _recover_receipt(run_root: Path, receipt_id: str) -> tuple[dict[str, Any], bytes]:
    data = (run_root / "receipts" / f"{receipt_id}.json").read_bytes()
    return json.loads(data), data


def _run_stub_v2(bundle: dict[str, Any], *, run_root: Path, repo: Path, git: str,
                 max_parallel: int, scenario: dict[str, Any]) -> dict[str, Any]:
    manifests = sorted(bundle["manifests"], key=lambda m: (m["topologyOrdinal"], m["packageId"]))
    if any(m["cas"]["admissionToken"] != m["cas"]["activeAdmissionToken"] for m in manifests):
        raise AdapterFailure("ADMISSION_TOKEN_STALE")
    base_commit = _git(git, repo, "rev-parse", "HEAD")
    tree = hashlib.sha256(_git(git, repo, "rev-parse", "HEAD^{tree}").encode("ascii")).hexdigest()
    if any(m["baseline"]["treeHash"] != tree for m in manifests):
        run_root.mkdir(parents=True, exist_ok=False)
        _write(run_root / "fanin" / "final.json", {"fanInGroupId": "stub-fanin", "members": [],
               "targetBaselineTreeHash": tree, "applicationCount": 0, "reasonCode": "BASELINE_HASH_MISMATCH"})
        raise AdapterFailure("BASELINE_HASH_MISMATCH")
    run_root.mkdir(parents=True, exist_ok=False)
    ledger = run_root / "ledger.jsonl"
    _write(run_root / "manifest-bundle.json", {"packages": [
        {k: m[k] for k in ("manifestId", "packageId", "revision", "fileDomain")} |
        {"baselineTreeHash": m["baseline"]["treeHash"]} for m in manifests]})
    owned: list[dict[str, str]] = []
    final: list[dict[str, Any]] = []
    runner_calls = settlements = observed = 0
    recovered: list[dict[str, Any]] = []
    written_sha256: dict[str, str] = {}

    def attempt(m: dict[str, Any], ordinal: int, exit_code: int = 0) -> tuple[dict[str, Any], str]:
        nonlocal runner_calls, settlements, observed
        pkg = m["packageId"]; aid = f"attempt-{pkg}-{ordinal}"; path = (run_root / "worktrees" / aid).resolve()
        fact = {"attemptId": aid, "packageId": pkg, "revision": m["revision"], "leaseId": f"lease-{pkg}-{ordinal}",
                "admissionToken": m["cas"]["admissionToken"], "canonicalWorktreePath": str(path),
                "baseCommit": base_commit, "repairAttemptCount": ordinal}
        attempt_path = run_root / "attempts" / f"{aid}.json"
        written_sha256[str(attempt_path.relative_to(run_root))] = hashlib.sha256(_write(attempt_path, fact)).hexdigest()
        _event(ledger, "attempt", packageId=pkg, attemptId=aid)
        _git(git, repo, "worktree", "add", "--detach", str(path), base_commit)
        owned.append({"packageId": pkg, "attemptId": aid, "path": str(path), "baseCommit": base_commit})
        proc = subprocess.Popen([sys.executable, "-c", f"import time,sys;time.sleep({float(scenario.get('delaySeconds', .03))!r});sys.exit({exit_code})"],
                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
        identity = process_identity(proc.pid); started = time.monotonic(); observed = max(observed, 1)
        code = proc.wait(timeout=10); runner_calls += 1
        usage = dict(scenario.get("usageByPackage", {}).get(pkg, {}))
        usage = {"calls": usage.get("calls", 1), "inputTokens": usage.get("inputTokens", 1),
                 "outputTokens": usage.get("outputTokens", 1), "wallSeconds": usage.get("wallSeconds", time.monotonic()-started)}
        _write(run_root / "sessions" / f"{aid}.json", {"attemptId": aid, "pid": proc.pid,
               "processIdentity": identity, "exitCode": code, "runnerType": "stub"})
        _event(ledger, "session", packageId=pkg, attemptId=aid, exitCode=code)
        exceeded = any(usage[key] > m["budget"][limit] for key, limit in (("calls","maxCalls"),("inputTokens","maxInputTokens"),("outputTokens","maxOutputTokens"),("wallSeconds","maxWallSeconds")))
        status = "STUB_PROCESS_FAILED" if code else ("BLOCKED_TERMINATED" if exceeded else "PASS")
        rid = f"receipt-{aid}"; digest = hashlib.sha256(f"{pkg}:{aid}:{status}".encode()).hexdigest()
        receipt = {"receiptId": rid, "attemptId": aid, "packageId": pkg, "status": status,
                   "outputDigest": digest, "usage": usage}
        receipt_path = run_root / "receipts" / f"{rid}.json"
        data = _write(receipt_path, receipt); settlements += 1
        written_sha256[str(receipt_path.relative_to(run_root))] = hashlib.sha256(data).hexdigest()
        _event(ledger, "receipt", packageId=pkg, attemptId=aid, receiptId=rid)
        if scenario.get("receiptReturnLostPackage") == pkg and ordinal == 0:
            _event(ledger, "RECEIPT_RETURN_LOST", packageId=pkg, attemptId=aid, receiptId=rid)
            raise ReceiptReturnLost(rid)
        return receipt, status

    def runner_attempt(m: dict[str, Any], ordinal: int, exit_code: int = 0) -> tuple[dict[str, Any], str]:
        try:
            return attempt(m, ordinal, exit_code)
        except ReceiptReturnLost as lost:
            receipt, data = _recover_receipt(run_root, lost.receipt_id)
            relative = str((run_root / "receipts" / f"{lost.receipt_id}.json").relative_to(run_root))
            digest = hashlib.sha256(data).hexdigest()
            recovered.append({"receiptId": lost.receipt_id, "outputDigest": receipt["outputDigest"],
                              "sha256Before": written_sha256[relative], "sha256After": digest})
            _event(ledger, "RECEIPT_RECOVERED", packageId=m["packageId"], attemptId=receipt["attemptId"],
                   receiptId=lost.receipt_id)
            return receipt, receipt["status"]

    def audit(m: dict[str, Any], receipt: dict[str, Any], disposition: str, ordinal: int) -> None:
        value = {"auditReceiptId": f"audit-{receipt['receiptId']}-{ordinal}", "receiptId": receipt["receiptId"],
                 "disposition": disposition, "auditAssigneeRef": m["auditAssigneeRef"], "revisionOrdinal": ordinal}
        _write(run_root / "audits" / f"{value['auditReceiptId']}.json", value)
        _event(ledger, "audit", packageId=m["packageId"], receiptId=receipt["receiptId"], disposition=disposition)

    def one(m: dict[str, Any]) -> dict[str, Any]:
        pkg=m["packageId"]; _event(ledger, "manifest", packageId=pkg, manifestId=m["manifestId"])
        exit_codes = scenario.get("processExitCodes", [])
        def exit_code(ordinal: int) -> int:
            if scenario.get("processExitPackage") != pkg:
                return 0
            if ordinal < len(exit_codes):
                return int(exit_codes[ordinal])
            return int(scenario.get("processExitCode", 7)) if ordinal == 0 else 0
        ordinal = 0
        receipt,status=runner_attempt(m,ordinal,exit_code(ordinal))
        if status=="BLOCKED_TERMINATED": audit(m,receipt,"BLOCKED",0); raise AdapterFailure("BUDGET_EXHAUSTED")
        while status=="STUB_PROCESS_FAILED":
            if ordinal >= int(scenario.get("maxRetries",0)):
                audit(m,receipt,"BLOCKED",ordinal)
                raise AdapterFailure("STUB_PROCESS_FAILED")
            audit(m,receipt,"RETRY",ordinal)
            ordinal += 1
            receipt,status=runner_attempt(m,ordinal,exit_code(ordinal))
        if ordinal:
            audit(m,receipt,"PASS",ordinal)
            return receipt
        if scenario.get("auditRevisePackage")==pkg:
            audit(m,receipt,"REVISE",0)
            if min(int(scenario.get("maxRepairs",2)),int(m["budget"]["maxAttempts"])-1)<1: raise AdapterFailure("REPAIR_LIMIT_EXHAUSTED")
            sibling_paths = sorted(
                [*run_root.glob("attempts/*.json"), *run_root.glob("receipts/*.json")],
                key=lambda path: str(path),
            )
            sibling_paths = [path for path in sibling_paths if pkg not in path.name]
            if not sibling_paths:
                raise AdapterFailure("REVISE_SIBLING_EVIDENCE_MISSING")
            before = [{"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in sibling_paths]
            receipt,status=runner_attempt(m,1)
            after = [{"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in sibling_paths]
            _write(run_root / "revise-sibling.json", {"targetPackageId": pkg, "before": before, "after": after})
            audit(m,receipt,"PASS",1); return receipt
        audit(m,receipt,"PASS",0); return receipt

    try:
        if max_parallel==1 or len(manifests)==1:
            for m in manifests: final.append(one(m))
        else:
            pending=[]; release=run_root/"parallel-release"
            for m in manifests:
                pkg=m["packageId"]; _event(ledger,"manifest",packageId=pkg,manifestId=m["manifestId"])
                aid=f"attempt-{pkg}-0"; path=(run_root/"worktrees"/aid).resolve()
                fact={"attemptId":aid,"packageId":pkg,"revision":m["revision"],"leaseId":f"lease-{pkg}-0","admissionToken":m["cas"]["admissionToken"],"canonicalWorktreePath":str(path),"baseCommit":base_commit,"repairAttemptCount":0}
                _write(run_root/"attempts"/f"{aid}.json",fact);_event(ledger,"attempt",packageId=pkg,attemptId=aid);_git(git,repo,"worktree","add","--detach",str(path),base_commit)
                owned.append({"packageId":pkg,"attemptId":aid,"path":str(path),"baseCommit":base_commit})
                proc,identity,started=_spawn(0,float(scenario.get("delaySeconds",.15)),release);pending.append((m,fact,proc,identity,started))
                observed=max(observed,sum(x[2].poll() is None for x in pending))
            release.write_text("release",encoding="utf-8")
            for m,fact,proc,identity,started in pending:
                pkg=m["packageId"];code=proc.wait(timeout=10);runner_calls+=1;usage={"calls":1,"inputTokens":1,"outputTokens":1,"wallSeconds":time.monotonic()-started}
                _write(run_root/"sessions"/f"{fact['attemptId']}.json",{"attemptId":fact["attemptId"],"pid":proc.pid,"processIdentity":identity,"exitCode":code,"runnerType":"stub"});_event(ledger,"session",packageId=pkg,attemptId=fact["attemptId"],exitCode=code)
                rid=f"receipt-{fact['attemptId']}";receipt={"receiptId":rid,"attemptId":fact["attemptId"],"packageId":pkg,"status":"PASS","outputDigest":hashlib.sha256(f"{pkg}:{fact['attemptId']}:PASS".encode()).hexdigest(),"usage":usage}
                _write(run_root/"receipts"/f"{rid}.json",receipt);settlements+=1;_event(ledger,"receipt",packageId=pkg,attemptId=fact["attemptId"],receiptId=rid);audit(m,receipt,"PASS",0);final.append(receipt)
        actual=[r["packageId"] for r in final]; contracts=bundle.get("fanInManifests",[]); reason=None
        if contracts:
            c=contracts[0]
            if c["expectedMemberPackageIds"]!=actual: reason="FANIN_SET_MISMATCH"
            else:
                expected={x["packageId"]:x["expectedReceiptDigest"] for x in c["members"]}
                if any(expected.get(r["packageId"])!=r["outputDigest"] for r in final): reason="FANIN_DIGEST_MISMATCH"
        fanin={"fanInGroupId":contracts[0]["fanInGroupId"] if contracts else "stub-fanin","members":[r["receiptId"] for r in final],"targetBaselineTreeHash":tree,"applicationCount":0 if reason else 1,"reasonCode":reason or "OK"}
        _write(run_root/"fanin"/"final.json",fanin);_event(ledger,"fan-in",applicationCount=fanin["applicationCount"],reasonCode=fanin["reasonCode"])
        if reason: raise AdapterFailure(reason)
    except AdapterFailure:
        cleanup=_cleanup(git,repo,run_root,owned,scenario);_event(ledger,"cleanup",runId=run_root.name);raise
    cleanup=_cleanup(git,repo,run_root,owned,scenario);_event(ledger,"cleanup",runId=run_root.name)
    return {"status":"P0A_STUB_PASS","runnerCalls":runner_calls,"settlements":settlements,"recoveredReceipts":recovered,"observedMaxStubProcesses":observed,"writtenSha256":written_sha256,"realAgentStarted":False,"realSerialShadowTested":False,"realFanoutTested":False,"cleanup":cleanup}


def run_stub(
    bundle: dict[str, Any], *, run_root: Path, repo: Path, git: str,
    max_parallel: int, runner_type: str = "stub", scenario: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if runner_type != "stub":
        raise AdapterFailure("RUNNER_TYPE_NOT_STUB")
    scenario = scenario or {}
    return _run_stub_v2(bundle, run_root=run_root, repo=repo, git=git, max_parallel=max_parallel, scenario=scenario)


def _cleanup(git: str, repo: Path, run_root: Path, owned: list[Any], scenario: dict[str, Any]) -> dict[str, Any]:
    normalized = [item if isinstance(item, dict) else {"path": item, "packageId": "", "attemptId": "", "baseCommit": ""} for item in owned]
    removed: list[str] = []; retained: list[str] = []; readback_errors: list[dict[str, str]] = []
    for item in normalized:
        path = item.get("path", item.get("canonicalWorktreePath"))
        attempt_path = run_root / "attempts" / f"{item.get('attemptId')}.json"
        if item.get("packageId") == scenario.get("readbackFailurePackage"):
            attempt_path.write_text("{invalid-json", encoding="utf-8")
        try:
            fact = json.loads(attempt_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            readback_errors.append({"path": str(attempt_path), "exceptionType": type(exc).__name__})
            retained.append(path); continue
        if fact.get("canonicalWorktreePath") != path or fact.get("baseCommit") != item.get("baseCommit"):
            retained.append(path); continue
        _git(git, repo, "worktree", "remove", "--force", path); removed.append(path)
    fact = {"runId": run_root.name, "ownedWorktrees": [item.get("path", item.get("canonicalWorktreePath")) for item in normalized], "removedWorktrees": removed,
            "retainedWorktrees": retained, "readbackErrors": readback_errors}
    _write(run_root / "cleanup.json", fact)
    return fact


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    stub = sub.add_parser("stub")
    for name in ("bundle", "run-root", "repo", "validator", "schema", "git"):
        stub.add_argument(f"--{name}", required=True)
    stub.add_argument("--runner-type", required=True); stub.add_argument("--max-parallel", type=int, required=True)
    args = parser.parse_args(argv)
    if args.runner_type != "stub":
        print(json.dumps({"status": "BLOCKED", "reasonCode": "RUNNER_TYPE_NOT_STUB"})); return 2
    try:
        validate(Path(args.validator), Path(args.schema), Path(args.bundle), 1 if args.max_parallel == 1 else None)
        result = run_stub(json.loads(Path(args.bundle).read_text(encoding="utf-8")), run_root=Path(args.run_root),
                          repo=Path(args.repo), git=args.git, max_parallel=args.max_parallel, runner_type=args.runner_type)
        print(json.dumps(result, sort_keys=True)); return 0
    except AdapterFailure as error:
        print(json.dumps({"status": "BLOCKED", "reasonCode": error.reason, "applicationCount": error.application_count}, sort_keys=True)); return 2


if __name__ == "__main__":
    raise SystemExit(main())
