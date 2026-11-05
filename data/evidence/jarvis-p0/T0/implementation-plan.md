# Jarvis P0 Implementation Plan

> **For agentic workers:** inline execution only. Execute T1 through T4 in order, keep RED/GREEN evidence per stage, and never change frozen KWS parameters or production defaults.

**Goal:** Deliver work order `wo-ultimaagent-20261103-0023` P0-1 prompt boundaries, P0-2 guarded memory writes, and P0-3 Windows voice hardening without changing the main-brain model, inference parameters, production defaults, or frozen 0016/0017 semantics.

**Architecture:** Add focused Python policy modules and connect them through the narrowest tracked production seams. Prompt input is rendered as explicitly bounded data; memory writes go through a fail-closed guard before any delegate store; voice enhancements wrap the current KWS/ASR implementation without changing its parameter constants. Existing upstream call signatures stay stable.

**Tech Stack:** Python 3.13.16, pytest 9.2.0, standard library only, existing sherpa-onnx runtime and saved WAV corpus.

**Spec:** `tasks/queue/wo-ultimaagent-20261103-0023--jarvis-p0.md`; authoritative detail in `docs/plans/jarvis-open-source-refactor-plan-20261101.md` sections 3, 5, 7, and 8.

## Global Constraints

- Do not change the main-brain model, inference parameters, production defaults, frozen 0016/0017 semantics, or any KWS/ASR/VAD/TTS frozen parameter value.
- Do not restart or stop an existing voice process. T3 validation is offline against saved WAVs and isolated test doubles.
- Use `tools/venv-openjarvis/Scripts/python.exe`; add the installed Ollama directory to the test process `PATH` only.
- Keep Jarvis and DockWright MIT copyright/license attribution and fixed donor commits in source headers.
- Do not embed AGPL code or touch P1 modules.
- Tests write only to pytest `tmp_path` or `data/evidence/jarvis-p0/<stage>/`; never to production memory or real user files.
- Stage progression requires a fresh RED, GREEN, cumulative regression, and independently readable `gate.json`.

## Approaches

1. **Chosen: isolated policy modules plus thin tracked integration.** This preserves frozen behavior, avoids committing the pre-existing untracked `src/brain/memory` tree, and lets each requirement be mutation-tested independently.
2. **Rejected: edit the whole existing memory and voice stacks in place.** The memory tree is pre-existing and untracked, so staging it would absorb unrelated work; the voice stack also contains frozen parameter history that this order must not rewrite.
3. **Rejected: vendor or run the donor applications.** DockWright is macOS/Swift and Jarvis is Electron/macOS-oriented; whole-repository adoption would violate the Windows mapping and dependency boundaries.

## File Structure

- `src/brain/prompt_boundary.py`: immutable boundary markers, four-level priority text, risk classification for optional context, lossless speech rendering/extraction.
- `src/brain/agent_server.py`: append the boundary contract to the existing system prompt and send each query as bounded user data while keeping the 0016/0017 rule and reply pipeline intact.
- `src/memory/poison_guard.py`: DockWright-derived deterministic guard and structured decision.
- `src/memory/writer.py`: fail-closed delegate writer; rejected content never reaches the store.
- `src/brain/voice/wake_matching.py`: normalized Levenshtein sliding-window matcher with strict ratio `< 0.35`.
- `src/brain/voice/transcription_backends.py`: backend protocol, local-first router, optional injected backend registration.
- `src/brain/voice/asr.py`: preserve `asr_transcribe` and route its existing implementations through the registry.
- `src/brain/voice/session_restart.py`: 50-second session guard; restart only at an inactive boundary.
- `src/brain/voice/kws_listener.py`: replace only the stream object at the guard boundary; do not recreate the microphone process or alter KWS constants.
- Focused tests under `src/brain/tests/`, `src/memory/tests/`, and `src/brain/voice/tests/`.

## Review Focus

- Boundary marker text inside user speech must not break extraction or become an instruction.
- Unicode confusables and base64-like text remain data and do not mutate the instruction block.
- Secret/card/SSN patterns and all-caps directives must be blocked before a memory delegate is called.
- A 50-second deadline reached during active audio must defer restart until the first inactive block.
- Unknown or unavailable transcription backends must fail explicitly or fall through in declared order without changing upper-layer call sites.

---

### Task 1: P0-1 Prompt Boundary

**Interfaces:** `build_user_data(speech: str, selected_text: str | None, trusted_context: str | None) -> BoundedPrompt`; `BoundedPrompt.render() -> str`; `extract_speech(rendered: str) -> str`.

- [ ] Add five adversarial tests plus a 100% speech preservation assertion; run them and record expected failures.
- [ ] Implement the minimum boundary/risk policy and append its immutable rule block to the existing main-brain system prompt.
- [ ] Integrate `ask_once` without changing model/reply settings; run focused tests and cumulative 0016/0017 routing/reply tests.
- [ ] Record RED/GREEN outputs and `T1/gate.json`.

### Task 2: P0-2 Memory PoisonGuard

**Interfaces:** `MemoryPoisonGuard.evaluate(content: str) -> PoisonDecision`; `GuardedMemoryWriter.write(content: str, **metadata) -> str`.

- [ ] Add tests for multilingual injection phrases, `sk-`, `sk-ant-`, `AIza`, bearer, bank-card, SSN, instruction regexes, all-caps ratio, and 5/500 boundaries; run RED.
- [ ] Add a literal 100-record normal corpus and assert zero false positives.
- [ ] Implement the guard and fail-closed writer; verify rejected input never invokes the delegate.
- [ ] Run T1+T2 cumulative tests and record `T2/gate.json`.

### Task 3: P0-3 Windows Voice Hardening

**Interfaces:** `WakePhraseMatcher.matches(input_text: str, target: str) -> bool`; `TranscriptionRouter.transcribe(path: Path, backend: str = "auto") -> dict`; `RecognitionSessionGuard.observe(active_audio: bool) -> bool`.

- [ ] Add RED tests for exact/fuzzy/strict-boundary matching, 50-second deferred restart, local-first fallback, optional backend selection, and stable upper API.
- [ ] Implement modules and thin integrations while preserving all KWS constants.
- [ ] Run the saved 8-positive/8-negative KWS corpus offline with baseline and candidate paths; require no new false wakes.
- [ ] Run local sherpa transcription on a saved WAV and prove backend switching through a fake optional backend without modifying caller code.
- [ ] Run T1+T2+T3 cumulative tests and record `T3/gate.json`.

### Task 4: Regression, Audit, Commit, Tag, Push

- [ ] Run focused acceptance tests and `python -m pytest src -q` with the dedicated interpreter and isolated basetemp.
- [ ] Re-read the work-order checklist, inspect the exact diff, license headers, dependency imports, and staged paths.
- [ ] Obtain an independent code review; repair Important/Critical findings with RED/GREEN evidence.
- [ ] Stage only work-order paths, commit with work-order ID, create `ultimaagent-jarvis-p0-20261103`, resolve commit/tag hashes, and use the required no-proxy push command.
- [ ] Write `docs/reports/stage-jarvis-p0-20261103.md` and `T4/gate.json`.
- [ ] Do not state Owner real-experience acceptance unless the Owner actually supplies it; report that closure gate separately.

### Task 5: T5 Receipt

- [ ] Write the eight fields with actual status, root-cause conclusion, paths, evidence, boundary statement, and environment statement.
- [ ] Independently parse all stage `gate.json` files and record the readback under `T5/`.
