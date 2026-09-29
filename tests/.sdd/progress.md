# SDD ledger — plan: tests/TEST_SUITE_IMPLEMENTATION_PLAN.md

## Setup

- Execution method: subagent-driven development, selected by the user.
- Plan and approved specification are both under `tests/`.
- The skill-provided Bash workspace helper could not run because `bash` is not installed on this Windows host. Equivalent plan-scoped artifacts live under `tests/.sdd/` to preserve the user-required test-only boundary.
- Git baseline: `808435cdf5c8cfa9fcb0ab97678b1d36cfd9c516` on `main` before Task 1. No worktree, branch, stage, commit, push, clean, or deletion is authorized.

## Rulings

- Ruling: Execute in the existing `D:\My-Projects\TradingBot-Intelligence-Plugin` checkout rather than creating a worktree — the user fixed the deliverable root to this checkout's `tests/` directory and no Git/worktree operation is authorized — cost if wrong: task artifacts share the existing checkout, mitigated by touching only `tests/` and review-scoped diffs.
- Ruling: Keep SDD ledger, task briefs, reports, and review packages under `tests/.sdd/` — the required helper script is unavailable and the user requires test-related artifacts to remain under `tests/` — cost if wrong: this differs from the skill's ignored `.superpowers/sdd/` default, mitigated by an explicit test-root-only status check.
- Ruling: Use uncommitted task-scoped file review packages instead of commit-range review packages — commits are not authorized for this task — cost if wrong: reviewers do not receive Git commit metadata, mitigated by each package listing exact changed files and full current content/diff for the task.
- Ruling: Interpret TDD "RED" steps in a test-suite task as a test that fails before its supporting test helper/fixture exists, not a test-module import attempted before the test file is written — this preserves the requested red/green evidence without contradicting the task's file-creation order — cost if wrong: the RED state validates scaffolding rather than production behavior, but production code is explicitly read-only.
- Ruling: Create `tests/helpers/real_roots.py` in Task 4 — Task 5 consumes real-root resolution but Task 4 otherwise defines it only inside a test module — cost if wrong: one additional focused test-only helper is introduced, mitigating cross-module duplication and matching the approved helper architecture.

## Preflight interface and consistency scan

| Tasks | Producer / consumer surface | Finding and resolution |
| --- | --- | --- |
| 1 -> 2 | `EntitySpec`, `build_fake_vault`, `plugin_reader` | Compatible; Task 1 creates the required synthetic/runtime interfaces. |
| 1 -> 3 | Fake source/reference/RAW, snapshots | Compatible; Task 1 provides fixture roots and identity helpers. |
| 1 -> 4 | Snapshots | Compatible; Task 4 uses the same immutable file-identity contract. |
| 1 -> 5 | `run_mcp_session` | Compatible; Task 5 is the only intended MCP consumer. |
| 1 -> 6 | Fake roots and snapshots | Compatible; Task 6 can construct a disposable installable-copy environment. |
| 2 -> 3 | Generic authority fixture behavior | Compatible; Task 3 can reuse metadata-driven entity specifications. |
| 3 -> 4 | Verifier and evidence error semantics | Compatible; Task 4 separately tests real data without importing test assertions. |
| 4 -> 5 | Real-root resolution | Gap found: Task 4 described a local fixture but Task 5 needs it. Resolved by the `tests/helpers/real_roots.py` ruling above. |
| 5 -> 6 | MCP session helper | Compatible; Task 6 uses the Task 1 helper, not a test-local client. |
| 1-6 -> 7 | Documented category commands/results | Compatible; Task 7 consumes only test modules and README commands. |

| Task | Internal consistency check | Finding and resolution |
| --- | --- | --- |
| 1 | Helper imports, isolated reloading, and README agree. | Clean. |
| 2 | "Run before module exists" wording conflicts with test-file creation. | Resolved by the TDD ruling above. |
| 3 | Full Order integrity assertion may fail against read-only source. | Intentional product-bug detector; no weakening authorized. |
| 4 | Dynamic manifest/registry discovery prevents filename hardcoding. | Clean after real-root helper ruling. |
| 5 | Dynamic MCP catalog remains source/documentation-based. | Clean. |
| 6 | Temporary package copy avoids editable `.plugin-package` mutation. | Clean. |
| 7 | Full suite runs after all category suites and retains real failures. | Clean. |

## Task 1 review

- Task 1 initial review: spec compliance partial; task quality needs fixes.
- Important: `fake_vault.py` writes supplied relation rows only into `_INDEX/relations.json`, while `verify_package()` reconstructs expected relations from note frontmatter. A fixture built with `relations=[...]` can therefore fail knowledge verification for helper-induced drift.
- Minor: `plugin_reader()` restoration is asserted only on normal context exit.
- Task 1: fix round 1/5 opened. The Important finding must be fixed and re-reviewed. The Minor finding is included in the same focused correction because it directly covers a documented helper contract.
- Task 1: fix round 1/5 (Important and Minor addressed; no new Critical/Important breakage; no commits).
- Task 1: complete (uncommitted, scoped review clean). Focused suite: `python -B -m unittest tests.unit.test_helpers -v` — 7 passed, exit code 0.
- Ruling: Implement the Task 2 machine-path scan's forbidden needles by concatenating components (for example, `"D" + ":" + chr(92)`) rather than embedding a forbidden literal in the scanning test — otherwise the test necessarily flags itself — cost if wrong: reduced direct readability in one assertion, mitigated by a local explanatory comment.
- Ruling: Treat a duplicate stable ID encoded directly in an index JSON object as a reader-level rejection requirement — the user requires structured duplicate-ID failure and a builder-only assertion cannot establish that boundary — cost if wrong: the test will expose the current JSON-decoder overwrite behavior as an intentional unresolved Plugin defect; no production weakening or fixture-only exception is permitted.
- Ruling: Complete every Task 2 review finding in the same bounded correction, including the five-pattern portability scan, strict `VaultError` check, referenced missing-Engine branch, positive type filtering, and concurrent `get` isolation — cost if wrong: Task 2 expands from its initial 25 tests, mitigated by keeping all additions inside its existing test modules and a focused re-review.

## Task 2 review

- Task 2 initial review: spec compliance partial; no Critical findings. Important: portability scan does not cover all five specified absolute-path patterns or all scoped runtime/test files; duplicate-ID coverage stops at the fake builder rather than exercising the reader.
- Minor: discovery asserts a generic exception shape rather than `VaultError`; missing-Engine verification is vacuous without a registry reference; type filtering has no positive match; concurrent coverage omits `get` isolation.
- Task 2: fix round 1/5 opened. The duplicate raw-index assertion may remain a deliberate failing product-bug detector if the current reader silently overwrites duplicate JSON keys. Reviewer did not rerun the implementer-reported 25-test command.
- Task 2: fix round 1 results: focused command ran 26 tests with 25 pass and one deliberate `VaultError not raised` failure. The detector reached the reader but wrote the malformed index before module import, so a future correct reader would raise during import instead of inside its asserted boundary.
- Ruling: Import a valid synthetic Vault before introducing the duplicate raw-index JSON, then call `reader.locate_vault()` within the explicit `assertRaises` boundary — the test must both retain the current product failure and become green when the reader correctly rejects duplicate keys — cost if wrong: the test relies on an already-loaded module, mitigated by invoking the public locator again after mutation.
- Task 2: fix round 2/5 opened for that one Important future-correctness issue. Final reviewer personally reran the focused suite: 26 tests, 25 passed, one deliberate failure, exit code 1; all other prior review findings were closed.
- Task 2: fix round 2 result: the reader module loads while the synthetic index is valid; the duplicate raw JSON keys are then written and `reader.locate_vault()` is invoked inside the asserted `VaultError(code="INVALID_VAULT")` boundary. The focused command remains 26 tests, 25 passed, one deliberate current-product failure, exit code 1.
- Task 2: final round review accepted the import-order correction. No new Critical/Minor findings. The remaining Important item is the intentionally preserved Plugin defect: current `locate_vault()` accepts duplicate JSON object keys. Reviewer package-verified the result but did not rerun it in this round.
- Task 2: complete as `DONE_WITH_CONCERNS` (uncommitted, scoped review accepted). Do not weaken the duplicate-ID detector; it is deferred to a separately authorized Plugin product-fix task.

## Task 3 review

- Task 3 initial result: the focused suite ran 22 tests with 20 pass, one required Order-integrity detector failure, and one Windows symlink capability skip; exit code 1. The active detector shows `verify_package("knowledge")` accepts tampered synthetic `valid_for_regression_baseline` frontmatter.
- Task 3 initial review: no Critical findings. Important: pending-manual-review does not prove a missing source remains visible; path rejection does not prove no outside file read; symlink skip catches broad `OSError`; missing Engine does not prove ordinary knowledge retrieval survives. Minor: tighten stale-integrity condition and add an upper exact RAW boundary.
- Ruling: Treat all four path-bearing public routes as untrusted until the test can prove the outside canary was not read — an error code alone does not establish validation order — cost if wrong: test-only instrumentation may be more coupled to filesystem access, mitigated by a controlled synthetic outside canary and no production monkey patch.
- Ruling: Correct every Task 3 review item in one focused test-only round, while retaining the exact active Order-integrity failure — cost if wrong: more cases add to the category count, mitigated by focused category rerun and a second scoped review.
- Task 3: fix round 1/5 opened. No Plugin, Vault, Production, configuration, cache, or Git change is authorized.
- Task 3: fix round 1 results: 24 tests, 22 passed, one required Order detector failure, one recognized Windows symlink privilege skip, exit code 1. All six initial review additions were present.
- Task 3: fix round 1 re-review found one Important detector-quality issue: the synthetic index does not include `valid_for_regression_baseline`, and the test does not prove its untampered Order A baseline first. The current failure is a real Plugin gap, but the test could accept a future blanket Order-A rejection or reject a valid general integrity fix due to an overly specific message condition.
- Ruling: Keep the corrected Order test self-contained by inserting the matching field only into its raw synthetic entities index, asserting the untampered `algorithm.order.a` package verifies first, then tampering note frontmatter without rebuilding that index — cost if wrong: this manually shaped test index adds setup detail, mitigated by testing exactly the required stale-index boundary and leaving shared fixtures stable.
- Ruling: Require a stale integrity signal tied to the tampered Order entity/field, but permit a structurally equivalent public verifier diagnostic rather than a single brittle message format — cost if wrong: condition may accept one alternative diagnostic, mitigated by the preceding positive baseline and `ok=false` assertion.
- Task 3: fix round 2/5 opened for this single Important test-quality correction. The active product failure remains required and must not be weakened.
- Task 3: fix round 2 results: the detector now has a valid indexed baseline, frontmatter-only tamper, and tied flexible integrity assertion. The final reviewer reran the single detector and exact category command: 24 tests, 22 passed, one active failure, one WinError 1314 skip, exit code 1.
- Task 3: final round review accepted the Order detector as truthful but found one Important generality limitation: one named Order A case cannot rule out a special-case implementation response.
- Ruling: Add one independent, non-Order synthetic entity with an indexed metadata field and repeat the baseline/tamper verifier contract through metadata-derived entity selection — cost if wrong: a second deliberate current-source failure can enlarge the focused failure count, mitigated by explicitly classifying both as evidence of the same generalized index-versus-frontmatter integrity defect.
- Task 3: fix round 3/5 opened for this final genericity check. No test may use a named production-path exception or conceal either failure.
- Task 3: fix round 3 results: 25 tests, 22 passed, two active stale-index detector failures, and one recognized WinError 1314 symlink skip; exit code 1. The neutral `system.sample`/`validation_tier` control and Order A control both pass baseline verification then fail because the current verifier accepts note-only indexed-field tampering.
- Task 3: final genericity review accepted. No Critical/Important/Minor findings. The two active failures are one generalized Plugin integrity defect; each test snapshots the whole temporary Vault after tampering and proves verifier no-mutation. Reviewer package-verified but did not rerun.
- Task 3: complete as `DONE_WITH_CONCERNS` (uncommitted, scoped review accepted). Preserve both active detector failures for a separately authorized general verifier product fix; do not specialize an Order-only repair.

## Task 4 review

- Task 4 initial results: with inherited roots, all nine integration tests skipped because Vault was unconfigured; with process-local real roots, 9 passed, 0 failed, 0 skipped. The active manifest had 12 Engine pairs rather than the plan's recorded nine; tests derive this count dynamically. The initial selected-artifact snapshot covered 35 files and 58,114,599 bytes unchanged.
- Task 4 initial review: no Critical findings. Important: helper requires Engine for all tests, suppressing Vault-only tests when only Engine is absent; some Order/Type3 metadata assertions are tautological or vacuous; protected-file snapshot does not cover every object public operations may inspect while report opening language overstates it. Minor: RED was an import failure rather than behavioral evidence.
- Ruling: Split real-root availability so Vault-only retrieval/graph tests require only the Vault, while Engine/reference and full identity operations require Engine explicitly — cost if wrong: more fixture states and targeted skips, mitigated by a single helper API and a rerun with Vault-only plus full-root environments.
- Ruling: Replace fallback/vacuous metadata checks with required public-field presence and observed current authority/quarantine/linkage contracts, but do not assert an unverified trading formation — cost if wrong: live integration may uncover current source/Vault mismatch, mitigated by reporting it as evidence rather than weakening.
- Ruling: Keep no-mutation claims scoped to exact snapshotted artifacts unless the test expands its protected set; do not generalize selected-file identities to entire repositories — cost if wrong: wording is more conservative, mitigated by explicit paths/counts/bytes and later final protected-root validation.
- Task 4: fix round 1/5 opened. No Graphify, Git, Plugin/Vault/Engine/Production mutation, or non-tests write is authorized.
