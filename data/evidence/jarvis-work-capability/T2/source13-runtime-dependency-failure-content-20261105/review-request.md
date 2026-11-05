# Source13 independent whole-change review

Read-only review of candidate269aca511d88412dbb9c15d23911138469a37aa2 at C:/Users/Administrator/.codex/worktrees/jarvis-e03-source13/UltimaAgent against base7975e477665c02820fa235b73d203718bd33b2c9.
Scope: four source/test files plus runtime inventory and test evidence. Product delta: existing environment_upgrade.py exact copy; WorkService exception content now server-owned incomplete/uncertain message. No new actual case.

Requirements: plan.md and original contract H:/UltimaAI/UltimaAgent/docs/specs/jarvis-work-capability-contract-20261101.md R03/R05/R07/E03/E06. R3 result review at ../e03-source12-input-guidance-20261105-r3/independent-result-review.json confirms two actual defects. Original case/result review remain spent. Offline implementation follows ongoing user goal/controller ruling; not a new Owner or live authorization.

Evidence: candidate-manifest.json pins50source files,7dependencies,1346SDK files; source13.diff is exact four-file delta. dependency-copy.json records preexisting source bytes. local-dependency-closure.json traverses18explicit local modules, no dynamic/external/resource completeness claim. Tests: source13-red.log is CP936 (original bytes retained; stdout reader error was separate); subsequent logs UTF8. dependency-red.log proves exact missing module, dependency-green-content-red.log shows dependency fixed while partial-effect completion text still fails. source13-green.log6PASS. Broader source13-work-suite-isolated.log460PASS111.73s. Earlier guard collection failure and319PASS/141FAIL from inherited default prompt remain, diagnosed in test-isolation-diagnosis.json. Fresh OPENJARVIS_HOME is now set before collection, no default SDK state file mtime changed in the inspected earlier suite interval; this is limited metadata evidence, not a whole-home audit. Python socket/subprocess guard allowed4owned loopback connections and1owned junction,0denials/openlisteners. Tests use fake native I/O and fake engines/MockTransport, no real E03 or actual model.

Review focus verbatim from plan:
1. A complete hash inventory can still omit required files: require the actual selection path's local dependency closure, not just matching listed hashes.
2. The existing main environment_upgrade.py is untracked and absent from source12: provenance must be explicit, and the differing pinned .environment must be preserved.
3. Failure after a possibly committed mutation must say incomplete/uncertain, retain effects and never replay.
4. Failure before a response exists must produce truthful content without depending on a model response variable.
5. Successful delivery must remain compatible; generic failure wording must not hide error or verified partial artifacts.

Rulings in progress.md: preserve both old worktrees; reuse existing meaningful regression instead of source-mirroring test; offline full work suite rather than unsafe repository-wide native/audio tests; retain all failures; earlier rejected standalone probe/push never retried. Judge whether these remain aligned to the full product objective. No whole-product PASS is claimed.

Use requesting-code-review/code-reviewer.md: effect-based Critical/Important/Minor findings with concrete lines, strengths, and every declined-to-judge item. Do not execute reviewed code/tests, import product modules, run UI/model/audio/network, mutate Git/files, issue authority, or spawn subagents. Standard-library hashing/AST and readonly Git allowed. Return JSON verdict PASS or NEEDS_FIXES, bind candidate+candidate-manifest+review-package manifest hashes, scoped findings and limitations. Evidence author can persist your response. Review pass means code/package readiness only, not E03 delivery or broader task acceptance.
