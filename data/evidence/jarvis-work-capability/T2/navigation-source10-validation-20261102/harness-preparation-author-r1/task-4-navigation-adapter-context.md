# Task4 absolute bindings and receipt location clarification

Root omitted the absolute V binding in the original dispatch; use these exact
paths. This supplements the immutable ac193a81 brief, without changing source,
model, execution or ownership authority.

- C = `C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent`
- H = `H:/UltimaAI/UltimaAgent`
- T = `H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2`
- V = `H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102`
- W = `C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent/.superpowers/sdd/jarvis-work-capability-delivery-plan-20261101`
- Preparation authority = `H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/harness-preparation-authority.json`, SHA256 `0e8c2e273bc2a4c35d0fd01e4c0022955609cb4bcecc2ec1f47d3bf95cdd5418`
- Candidate manifest = `H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/source10-candidate-manifest.json`, SHA256 `cdfbfb059f889ef9e92221c503dffe2ca7fa08106ebf4968bcc26037f214be50`
- Python = `H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe`, always `-B -X utf8`
- Existing P4 = `H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e03-resume-20261102/preparation-r4/controller.py`
- Existing P1 = `H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e03-resume-20261102/preparation/acceptance_adapter.py`
- Original corpus = `H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/source6-native-reference/controlled-corpus-inputs/corpus.json`

Ruling: the precise root preparation authority controls generated test receipts.
Use a NEW `V/code/harness-preparation-*` directory for adapter.xml, exact argv,
stdout/stderr, receipt, environment and temp/cache data. The old plan shorthand
`harness/adapter.xml` does not add a seventh immutable source file or authorize
overwriting previous test output. The six harness source files stay the exact
allowlist. Cost if wrong is a relocated receipt link; no behavior, test or later
inert/actual acceptance requirement is relaxed. Document the actual location in
README and report. Do not change the original authority or approved plan.

No inert, original-corpus runtime profile, product CLI/server/model/native11434,
external request, source9 slot, production, UI or audio execution is released.
