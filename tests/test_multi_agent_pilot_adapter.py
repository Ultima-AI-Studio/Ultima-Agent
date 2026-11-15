from __future__ import annotations

import copy
import hashlib
import importlib.util
import inspect
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures" / "multi-agent-pilot"
ADAPTER = ROOT / "scripts" / "multi-agent-pilot-adapter.py"
LIVE = Path(r"C:\Users\Administrator\AppData\Local\Doubao\User Data\Default\.doubao\agent_mode\workspace\.user_skills\dev-conductor")
VALIDATOR = LIVE / "scripts" / "validate_multi_agent_profile.py"
SCHEMA = LIVE / "references" / "multi-agent-work-package.schema.json"
GIT = r"C:\Program Files\Git\cmd\git.exe"
spec = importlib.util.spec_from_file_location("stub_adapter", ADAPTER)
adapter = importlib.util.module_from_spec(spec); spec.loader.exec_module(adapter)


def command(repo: Path, *args: str) -> str:
    result = subprocess.run([GIT, "-C", str(repo), *args], text=True, capture_output=True, check=True)
    return result.stdout.strip()


def repository(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run([GIT, "init", str(repo)], check=True, capture_output=True)
    command(repo, "config", "user.email", "stub@example.invalid"); command(repo, "config", "user.name", "Stub")
    (repo / "base.txt").write_text("base\n", encoding="utf-8"); command(repo, "add", "base.txt"); command(repo, "commit", "-m", "base")
    return repo


def bundle(repo: Path, packages: int = 2, *, parallel: bool = False):
    value = json.loads((FIX / "valid-serial.json").read_text(encoding="utf-8"))
    base = value["manifests"][0]; base["baseline"]["commit"] = command(repo, "rev-parse", "HEAD")
    base["baseline"]["treeHash"] = hashlib.sha256(command(repo, "rev-parse", "HEAD^{tree}").encode("ascii")).hexdigest()
    if packages == 2:
        other = copy.deepcopy(base); other["manifestId"]="manifest-b"; other["packageId"]="pkg-b"
        other["fileDomain"]=[{"path":"docs/specs/b","kind":"directory","recursive":True}]
        other["budget"]["ownerPackageId"]="pkg-b"; other["budget"]["reservationId"]="budget-b"
        other["cas"]["admissionToken"]="token-b"; other["cas"]["activeAdmissionToken"]="token-b"
        other["trace"]["correlationId"]="corr-b"; other["authorRef"]="author-b"; other["auditAssigneeRef"]="auditor-b"
        value["manifests"].append(other)
    if parallel:
        profile_fixture = json.loads((FIX / "valid-two-way-stub.json").read_text(encoding="utf-8"))
        assert profile_fixture == {"base":"valid-serial.json","mutation":"add-independent-package","runnerType":"stub"}
        value["profile"].update(profile="multi_agent", taskMaxParallelism=2, maxParallelism=2)
        value["capacitySnapshot"]["projectLimit"] = 2
        for manifest in value["manifests"]: manifest["profile"]="multi_agent"
    return value


def run(tmp_path: Path, *, packages=2, parallel=1, scenario=None):
    repo=repository(tmp_path); root=tmp_path/"run"
    result=adapter.run_stub(bundle(repo, packages, parallel=parallel>1), run_root=root, repo=repo, git=GIT, max_parallel=parallel, scenario=scenario)
    return result, root, repo


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fanin(value, expected_packages, expected_digests):
    value["fanInManifests"]=[{"fanInGroupId":"stub-fanin","expectedMemberPackageIds":expected_packages,
        "members":[{"packageId":pkg,"expectedReceiptDigest":digest} for pkg,digest in expected_digests.items()]}]


def test_adapter_rejects_non_stub_runner_before_side_effects(tmp_path):
    root=tmp_path/"never"
    with pytest.raises(adapter.AdapterFailure, match="RUNNER_TYPE_NOT_STUB"):
        adapter.run_stub({}, run_root=root, repo=tmp_path/"repo", git=GIT, max_parallel=1, runner_type="other")
    assert not root.exists()


def test_adapter_contains_no_real_worker_entrypoint():
    source=ADAPTER.read_text(encoding="utf-8").lower()
    for forbidden in ('add_parser("pilot")', "codex.exe", "deepseek", "--dangerously", "--skip-permission"):
        assert forbidden not in source


def test_valid_serial_fixture_effective_parallelism_one(tmp_path):
    result=subprocess.run([sys.executable,str(VALIDATOR),"--schema",str(SCHEMA),"--input",str(FIX/"valid-serial.json"),"--expect-effective-parallelism","1"],text=True,capture_output=True)
    assert result.returncode == 0, result.stdout+result.stderr


def test_serial_stub_runs_a_audit_a_b_audit_b(tmp_path):
    result,root,_=run(tmp_path)
    events=[json.loads(x) for x in (root/"ledger.jsonl").read_text().splitlines()]
    chain=[(e["type"],e.get("packageId")) for e in events if e["type"] not in ("fan-in","cleanup")]
    assert chain[:5] == [(x,"pkg-a") for x in ("manifest","attempt","session","receipt","audit")]
    assert chain[5:10] == [(x,"pkg-b") for x in ("manifest","attempt","session","receipt","audit")]
    assert result["observedMaxStubProcesses"] == 1


def test_two_way_stub_never_invokes_real_agent(tmp_path):
    result,root,_=run(tmp_path,parallel=2)
    assert result["observedMaxStubProcesses"]==2 and result["realAgentStarted"] is False and result["realFanoutTested"] is False
    assert all(json.loads(p.read_text())["runnerType"]=="stub" for p in (root/"sessions").glob("*.json"))


def test_persistent_edges_and_usage_are_complete(tmp_path):
    _,root,_=run(tmp_path,packages=1)
    attempt=json.loads(next((root/"attempts").glob("*.json")).read_text()); session=json.loads(next((root/"sessions").glob("*.json")).read_text())
    receipt=json.loads(next((root/"receipts").glob("*.json")).read_text()); audit=json.loads(next((root/"audits").glob("*.json")).read_text())
    assert {"attemptId","packageId","revision","leaseId","admissionToken","canonicalWorktreePath","baseCommit","repairAttemptCount"} <= attempt.keys()
    assert {"attemptId","pid","processIdentity","exitCode","runnerType"} <= session.keys()
    assert {"calls","inputTokens","outputTokens","wallSeconds"} <= receipt["usage"].keys()
    assert {"auditReceiptId","receiptId","disposition","auditAssigneeRef","revisionOrdinal"} <= audit.keys()
    manifest=json.loads((root/"manifest-bundle.json").read_text()); fan=json.loads((root/"fanin/final.json").read_text()); cleanup=json.loads((root/"cleanup.json").read_text())
    assert {"manifestId","packageId","revision","baselineTreeHash","fileDomain"} <= manifest["packages"][0].keys()
    assert {"fanInGroupId","members","targetBaselineTreeHash","applicationCount"} <= fan.keys()
    assert {"runId","ownedWorktrees","removedWorktrees","retainedWorktrees"} <= cleanup.keys()


def test_cleanup_removes_only_owned_temp_worktrees(tmp_path):
    result,_,repo=run(tmp_path)
    listing=command(repo,"worktree","list","--porcelain")
    assert all(path not in listing for path in result["cleanup"]["ownedWorktrees"])


def test_cleanup_retains_foreign_and_failed_readback_worktrees(tmp_path):
    repo=repository(tmp_path); foreign=tmp_path/"foreign"; command(repo,"worktree","add","--detach",str(foreign),"HEAD")
    result=adapter.run_stub(bundle(repo,1),run_root=tmp_path/"run",repo=repo,git=GIT,max_parallel=1,scenario={"readbackFailurePackage":"pkg-a"})
    error=result["cleanup"]["readbackErrors"][0]
    assert Path(error["path"]) == tmp_path/"run/attempts/attempt-pkg-a-0.json"
    assert error["exceptionType"] == "JSONDecodeError"
    assert foreign.as_posix() in command(repo,"worktree","list","--porcelain")
    assert str(foreign) not in result["cleanup"]["removedWorktrees"]
    owned=result["cleanup"]["ownedWorktrees"][0]
    assert Path(owned).as_posix() in command(repo,"worktree","list","--porcelain") and owned in result["cleanup"]["retainedWorktrees"] and owned not in result["cleanup"]["removedWorktrees"]
    command(repo,"worktree","remove","--force",owned)
    command(repo,"worktree","remove","--force",str(foreign))


def test_failure_stale_token_zero_processes(tmp_path):
    repo=repository(tmp_path); root=tmp_path/"run"
    value=bundle(repo); mutation=json.loads((FIX/"invalid-admission-token-stale.json").read_text()); value["manifests"][0]["cas"]["admissionToken"]=mutation["admissionToken"]
    with pytest.raises(adapter.AdapterFailure,match="ADMISSION_TOKEN_STALE"): adapter.run_stub(value,run_root=root,repo=repo,git=GIT,max_parallel=1)
    assert not root.exists()


def test_failure_baseline_drift_zero_fanin(tmp_path):
    repo=repository(tmp_path); root=tmp_path/"run"
    value=bundle(repo); value["manifests"][0]["baseline"]["treeHash"]=json.loads((FIX/"invalid-baseline-hash-mismatch.json").read_text())["treeHash"]
    with pytest.raises(adapter.AdapterFailure,match="BASELINE_HASH_MISMATCH"): adapter.run_stub(value,run_root=root,repo=repo,git=GIT,max_parallel=1)
    assert json.loads((root/"fanin/final.json").read_text())["applicationCount"]==0


def test_failure_file_domain_overlap_validator_rejects(tmp_path):
    repo=repository(tmp_path); value=bundle(repo,2,parallel=True); mutation=json.loads((FIX/"invalid-file-domain-overlap.json").read_text())
    assert mutation["mutation"]=="duplicate-file-domain"; value["manifests"][1]["fileDomain"]=copy.deepcopy(value["manifests"][0]["fileDomain"])
    path=tmp_path/"overlap.json"; path.write_text(json.dumps(value),encoding="utf-8")
    result=subprocess.run([sys.executable,str(VALIDATOR),"--schema",str(SCHEMA),"--input",str(path)],text=True,capture_output=True)
    assert result.returncode==1 and "FILE_DOMAIN_OVERLAP" in result.stdout


def test_failure_process_exit_records_identity_and_bounded_retry(tmp_path,monkeypatch):
    original=adapter._write; first_bytes={}
    def recording_write(path,value):
        data=original(path,value)
        if path.name in {"attempt-pkg-a-0.json","receipt-attempt-pkg-a-0.json"}: first_bytes[path]=data
        return data
    monkeypatch.setattr(adapter,"_write",recording_write)
    result,root,_=run(tmp_path,packages=1,scenario=json.loads((FIX/"scenario-process-exit.json").read_text()))
    sessions=[json.loads(p.read_text()) for p in (root/"sessions").glob("*.json")]; attempts=[json.loads(p.read_text()) for p in (root/"attempts").glob("*.json")]
    assert any(s["exitCode"]==7 and s["pid"]>0 for s in sessions); assert {a["attemptId"] for a in attempts}=={"attempt-pkg-a-0","attempt-pkg-a-1"} and max(a["repairAttemptCount"] for a in attempts)<=2
    assert {json.loads(p.read_text())["status"] for p in (root/"receipts").glob("*.json")}=={"STUB_PROCESS_FAILED","PASS"}
    assert len(attempts)==len(sessions)==len(list((root/"receipts").glob("*.json")))==2
    assert all(path.read_bytes()==data for path,data in first_bytes.items())
    events=[json.loads(line) for line in (root/"ledger.jsonl").read_text().splitlines()]
    assert [(event["type"],event.get("attemptId")) for event in events if event.get("attemptId") in {"attempt-pkg-a-1"}]==[(kind,"attempt-pkg-a-1") for kind in ("attempt","session","receipt")]
    assert any(event["type"]=="audit" and event.get("receiptId")=="receipt-attempt-pkg-a-1" for event in events)


def test_failure_process_exit_max_retries_zero_stops_after_first(tmp_path):
    repo=repository(tmp_path); root=tmp_path/"run"
    with pytest.raises(adapter.AdapterFailure,match="STUB_PROCESS_FAILED"):
        adapter.run_stub(bundle(repo,1),run_root=root,repo=repo,git=GIT,max_parallel=1,
                         scenario={"processExitPackage":"pkg-a","processExitCodes":[7],"maxRetries":0})
    assert len(list((root/"attempts").glob("*.json")))==1
    assert len(list((root/"sessions").glob("*.json")))==1
    receipts=list((root/"receipts").glob("*.json")); assert len(receipts)==1
    assert json.loads(receipts[0].read_text())["status"]=="STUB_PROCESS_FAILED"


def test_failure_process_exit_max_retries_one_exhausts_after_two(tmp_path,monkeypatch):
    repo=repository(tmp_path); root=tmp_path/"run"; original=adapter._write; first_bytes={}
    def recording_write(path,value):
        data=original(path,value)
        if path.name in {"attempt-pkg-a-0.json","receipt-attempt-pkg-a-0.json"}: first_bytes[path]=data
        return data
    monkeypatch.setattr(adapter,"_write",recording_write)
    with pytest.raises(adapter.AdapterFailure,match="STUB_PROCESS_FAILED"):
        adapter.run_stub(bundle(repo,1),run_root=root,repo=repo,git=GIT,max_parallel=1,
                         scenario={"processExitPackage":"pkg-a","processExitCodes":[7,9],"maxRetries":1})
    assert len(list((root/"attempts").glob("*.json")))==2
    assert len(list((root/"sessions").glob("*.json")))==2
    receipts=list((root/"receipts").glob("*.json")); assert len(receipts)==2
    assert {json.loads(path.read_text())["status"] for path in receipts}=={"STUB_PROCESS_FAILED"}
    assert all(path.read_bytes()==data for path,data in first_bytes.items())
    events=[json.loads(line) for line in (root/"ledger.jsonl").read_text().splitlines()]
    assert [(event["type"],event.get("attemptId")) for event in events if event.get("attemptId")=="attempt-pkg-a-1"]==[(kind,"attempt-pkg-a-1") for kind in ("attempt","session","receipt")]
    assert any(event["type"]=="audit" and event.get("receiptId")=="receipt-attempt-pkg-a-1" for event in events)


def test_failure_receipt_return_loss_is_idempotently_recovered(tmp_path,monkeypatch):
    original=adapter._recover_receipt; recovery_stacks=[]
    def recording_recovery(*args):
        recovery_stacks.append([frame.function for frame in inspect.stack()])
        return original(*args)
    monkeypatch.setattr(adapter,"_recover_receipt",recording_recovery)
    result,root,_=run(tmp_path,packages=1,scenario=json.loads((FIX/"scenario-receipt-return-lost.json").read_text()))
    receipt=next((root/"receipts").glob("*.json")); payload=json.loads(receipt.read_text()); recovery=result["recoveredReceipts"][0]
    assert recovery["sha256Before"]==recovery["sha256After"]==sha(receipt)
    assert recovery["receiptId"]==payload["receiptId"] and recovery["outputDigest"]==payload["outputDigest"]
    assert result["runnerCalls"]==1 and result["settlements"]==1 and len(list((root/"sessions").glob("*.json")))==len(list((root/"attempts").glob("*.json")))==1
    assert len(recovery_stacks)==1 and "runner_attempt" in recovery_stacks[0] and "attempt" not in recovery_stacks[0]
    event_types=[json.loads(line)["type"] for line in (root/"ledger.jsonl").read_text().splitlines()]
    assert event_types.index("receipt") < event_types.index("RECEIPT_RETURN_LOST") < event_types.index("RECEIPT_RECOVERED") < event_types.index("audit")


def test_failure_budget_exhausted_never_borrows_sibling(tmp_path):
    repo=repository(tmp_path); root=tmp_path/"run"
    value=bundle(repo); fixture=json.loads((FIX/"invalid-budget-exhausted.json").read_text()); value["manifests"][0]["budget"].update(fixture["budget"])
    sibling_before=copy.deepcopy(value["manifests"][1]["budget"])
    with pytest.raises(adapter.AdapterFailure,match="BUDGET_EXHAUSTED"): adapter.run_stub(value,run_root=root,repo=repo,git=GIT,max_parallel=1,scenario={"usageByPackage":fixture["usageByPackage"]})
    receipt=json.loads(next((root/"receipts").glob("*.json")).read_text()); assert receipt["status"]=="BLOCKED_TERMINATED" and receipt["usage"]["calls"]==2
    assert not list((root/"attempts").glob("*pkg-b*")) and not list((root/"sessions").glob("*pkg-b*")) and not list((root/"receipts").glob("*pkg-b*"))
    assert all(json.loads(line).get("packageId")!="pkg-b" for line in (root/"ledger.jsonl").read_text().splitlines())
    assert "pkg-b" not in command(repo,"worktree","list","--porcelain")
    assert value["manifests"][1]["budget"]==sibling_before
    assert not any(json.loads(path.read_text()).get("packageId")=="pkg-b" for path in (root/"receipts").glob("*.json"))


def test_failure_audit_revise_only_revises_matching_package(tmp_path):
    result,root,_=run(tmp_path,scenario=json.loads((FIX/"scenario-audit-revise.json").read_text()))
    audits=[json.loads(p.read_text()) for p in (root/"audits").glob("*.json")]
    assert {a["disposition"] for a in audits if "pkg-b" in a["receiptId"]}=={"REVISE","PASS"}
    assert next(a for a in audits if "pkg-a" in a["receiptId"])["revisionOrdinal"]==0
    assert len(list((root/"attempts").glob("*pkg-b*")))==2 and len(list((root/"attempts").glob("*pkg-a*")))==1
    sibling=json.loads((root/"revise-sibling.json").read_text())
    assert sibling["before"] and sibling["after"] and sibling["before"]==sibling["after"]
    assert all("pkg-a" in Path(item["path"]).name for item in sibling["before"])
    for relative,digest in result["writtenSha256"].items(): assert sha(root/relative)==digest


@pytest.mark.parametrize("fixture,reason",[("invalid-fanin-set-mismatch.json","FANIN_SET_MISMATCH"),("invalid-fanin-digest-mismatch.json","FANIN_DIGEST_MISMATCH")])
def test_failure_fanin_mismatch_zero_application(tmp_path,fixture,reason):
    repo=repository(tmp_path); root=tmp_path/"run"; value=bundle(repo); mutation=json.loads((FIX/fixture).read_text())
    digests={pkg:hashlib.sha256(f"{pkg}:attempt-{pkg}-0:PASS".encode()).hexdigest() for pkg in ("pkg-a","pkg-b")}
    if reason=="FANIN_SET_MISMATCH": fanin(value,mutation["expectedMemberPackageIds"],digests)
    else: digests[mutation["packageId"]]=mutation["expectedReceiptDigest"]; fanin(value,["pkg-a","pkg-b"],digests)
    with pytest.raises(adapter.AdapterFailure,match=reason): adapter.run_stub(value,run_root=root,repo=repo,git=GIT,max_parallel=1)
    assert json.loads((root/"fanin/final.json").read_text())["applicationCount"]==0


def test_cli_stub_serial(tmp_path):
    repo=repository(tmp_path); value=bundle(repo,1); source=tmp_path/"bundle.json"; source.write_text(json.dumps(value),encoding="utf-8")
    argv=[sys.executable,str(ADAPTER),"stub","--bundle",str(source),"--run-root",str(tmp_path/"run"),"--repo",str(repo),"--validator",str(VALIDATOR),"--schema",str(SCHEMA),"--runner-type","stub","--max-parallel","1","--git",GIT]
    result=subprocess.run(argv,text=True,capture_output=True)
    payload=json.loads(result.stdout); assert result.returncode==0 and payload["status"]=="P0A_STUB_PASS" and payload["realSerialShadowTested"] is False and payload["realFanoutTested"] is False
