# Engineering Packaging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reproducibly publish Ultima Agent 0.1.0, build and exercise an Inno Setup installer, prove detached Ed25519 signing behavior, and hand an authoritative manifest contract to work order 8 without claiming unavailable release gates.

**Architecture:** PowerShell owns .NET/Inno orchestration and Windows runtime evidence. A small Python packaging CLI owns deterministic artifact inventory, publisher-signing integration, and manifest generation by calling the existing work-order-8 modules rather than redefining their contracts. Tests execute the real Python CLI against temporary artifacts; Windows build/install gates are proven with command logs and machine-state snapshots.

**Tech Stack:** PowerShell 7/Windows PowerShell, .NET SDK 8.0.425, WinUI 3/Windows App SDK 1.8, Inno Setup 6.7.3, Python 3.13, `cryptography` Ed25519.

**Spec:** `docs/specs/build-release.md` §2.1; `tasks/queue/wo-s1-engineering-packaging.md` v1.1; `tasks/cards/s1-engineering-packaging/task.md`; `docs/specs/update-manifest-schema.md`.

## Global Constraints

- Do not modify `src/`; it is a read-only build input.
- Use actual project version `0.1.0`; do not claim or synthesize `1.0.0`.
- Do not create version tags, GitHub Releases, or upload assets.
- Do not persist a real private key; test keys live only in an OS temporary directory and are deleted after the signing check.
- Treat unavailable real-key, clean-machine, WebView2-missing, and work-order-8 upload/pull gates as BLOCKED or not exercised, never PASS.
- Any spawned installer/application process must be silent or hidden; N7 visible-window evidence is mandatory.

## Review Focus

- A missing package path must fail before a manifest or inventory is written.
- A malformed semantic version must be rejected rather than silently emitted.
- A signature over an installer changed by one byte must fail verification.
- Manifest keys and SHA-256 must exactly match the authoritative schema and real installer bytes.
- An existing WebView2 runtime must select the skip branch without launching its bootstrapper.

---

### Task 1: Packaging contract CLI (PK-04/PK-05 support)

**Files:**
- Create: `tools/packaging/packaging.py`
- Create: `tools/packaging/tests/test_packaging.py`

**Interfaces:**
- Produces: `inventory <files...> --output <json>`; `manifest --package <exe> --version <semver> --repository <owner/repo> --tag <tag> --published-at <ISO8601> --output <json>`; `sign-test --target <exe> --evidence <json>`.
- Consumes: `ultima_publisher.manifest.create_manifest/write_manifest` and `ultima_publisher.signing.generate_keypair/sign_file/verify_file`.

- [ ] Write CLI integration tests for inventory hashes, schema-exact manifest output, missing-file/invalid-version rejection, and sign/verify/tamper rejection with test-key cleanup.
- [ ] Run the tests and observe failures because `packaging.py` does not exist.
- [ ] Implement only the tested commands and stable JSON receipts.
- [ ] Run the focused tests, then the publisher test suite.

### Task 2: Reproducible publishing (PK-01)

**Files:**
- Create: `tools/packaging/build.ps1`

**Interfaces:**
- Produces: `dist/publish/host/`, `dist/publish/orb/`, and `dist/artifact-inventory.json`.
- Consumes: the two existing `.csproj` files read-only and Task 1 inventory command.

- [ ] Add a dry-run/validation test that exercises parameter and toolchain checks without publishing.
- [ ] Implement fixed `DOTNET_ROOT`/PATH setup and the required single-file flags for both projects.
- [ ] Run Release publishing and record whether Windows App SDK actually permits HostShell single-file output.
- [ ] If incompatible, record the exact error and implement only the verified self-contained-directory fallback plus launcher; otherwise retain the real single-file output.
- [ ] Hash every distributable artifact and capture build logs.

### Task 3: Installer and dependency bootstrap (PK-02/PK-03)

**Files:**
- Create: `tools/packaging/UltimaAgentSetup.iss`
- Create: `tools/packaging/build-installer.ps1`
- Create: `tools/packaging/test-webview2-detection.ps1`

**Interfaces:**
- Produces: `dist/UltimaAgent-Setup-0.1.0.exe` and branch receipts for WebView2 detection.
- Consumes: PK-01 publish output and Inno compile-time defines.

- [ ] Implement registry/file detection and test the installed-runtime skip branch on this machine.
- [ ] Define per-user silent-capable installation, Start Menu/Desktop shortcuts, uninstall metadata, and hidden Evergreen bootstrapper execution only when missing.
- [ ] Compile with ISCC and check the output artifact.
- [ ] Run `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART`, verify files/shortcuts/uninstall registry, then run the uninstaller silently and verify removal.
- [ ] Mark the physically missing-runtime branch as logic-only unless it is truly exercised.

### Task 4: Runtime N7 and signing evidence (PK-01/PK-04)

**Files:**
- Create: `tools/packaging/window-evidence.ps1`
- Evidence: `docs/reports/evidence/wo-s1-engineering-packaging/`

**Interfaces:**
- Produces: visible-window ownership JSON, signing test receipt, command logs, and artifact hashes.

- [ ] Launch the packaged GUI hidden from the shell, enumerate visible top-level windows by PID/process tree, and capture the host/extra counts.
- [ ] Exercise Task 1 `sign-test` on the actual installer and retain only public/signature/receipt evidence, not private test material.
- [ ] Verify the installer itself remains byte-identical after the signing test.

### Task 5: Contract handoff and receipt (PK-05)

**Files:**
- Create: `dist/update-manifest.sample.json`
- Create: `dist/release-assets.json`
- Create: `docs/reports/wo-s1-engineering-packaging.md`
- Modify: `tasks/cards/s1-engineering-packaging/task.md`

**Interfaces:**
- Produces: installer path/version/SHA-256/signature references consumable by `tools/publisher` and a field-by-field schema reconciliation.

- [ ] Generate the sample manifest from actual installer bytes with version `0.1.0` and a non-published illustrative URL/tag.
- [ ] Compare every field against `update-manifest-schema.md` and the publisher generator tests.
- [ ] Record PK-01 through PK-05 truthfully, including real-key and remote upload/pull blockers.
- [ ] Run focused tests, publisher tests, build checks, artifact verification, and inspect the final diff for out-of-scope changes.

## Self-review

- Spec coverage: PK-01 through PK-05 each map to exactly one gate/evidence task; no release upload or source modification is planned.
- Step scan/type consistency: `packaging.py` is the sole JSON contract adapter; PowerShell scripts consume its stable command outputs.
- Failure coverage: missing artifacts, invalid versions, tampering, schema drift, and WebView2-present branching are explicitly exercised.
- Proportion: installer mechanics remain in `.iss`; Python contains only reusable contract logic; evidence prose is not unit-tested.
