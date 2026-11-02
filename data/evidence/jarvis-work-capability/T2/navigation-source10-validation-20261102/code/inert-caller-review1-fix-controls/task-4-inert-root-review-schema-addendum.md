# ROOT review-output contract clarification — no source change / no release

The dispatched reviewer brief requests spec_verdict/quality_verdict. The concrete caller's existing check_controls (lines159–160) reads the future review's spec/quality fields. ROOT found this mismatch while reading the exact future approval/release contract. No such runtime approval, review approval or release has been issued.

Ruling: use canonical spec and quality in the new caller verdict JSON, and also emit equal spec_verdict and quality_verdict aliases so the originally dispatched metadata contract remains readable. Each pair must agree. Other requested fields and independent review scope remain unchanged. This is correction of ROOT's output instructions to the same code/requirements contract, not a caller source fix, finding waiver, runtime permission or instruction about what findings to raise.

Why: the task requires a future independent SPEC PASS / QUALITY APPROVED verdict bound to the caller manifest; it does not require changing a supported field-name convention. A consistent new review object can be created once without modifying reviewed bytes or adding a new code version.

Cost if wrong: admission must refuse the approval/release before runtime; ROOT will separately reopen and assert both aliases and the canonical values before any sealing. Do not silently change or overwrite the already published review brief/input hashes. Preserve this addendum as a separate new root-owned control input and report its hash. The reviewer remains responsible for judging all actual code and interface defects independently.
