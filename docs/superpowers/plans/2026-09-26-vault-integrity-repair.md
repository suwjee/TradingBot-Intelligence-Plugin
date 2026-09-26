# Vault Integrity Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Vault and Plugin expose a strict, evidence-based repair state with explicit manual fixture-review handling and no Production mutation.

**Architecture:** The Vault schema and index builder own fixture-source review classification; the Plugin independently verifies and exposes the same classification at its read-only boundary. Markdown remains the canonical knowledge source, while `_INDEX` is regenerated only by the builder. Documentation changes are confined to proven stale claims and source-backed Type-3 semantics.

**Tech Stack:** Python 3.14 standard library, `jsonschema`, `unittest`, JSON Schema Draft 2020-12, Markdown frontmatter.

**Spec:** `docs/superpowers/specs/2026-09-26-vault-integrity-repair.md`

## Global Constraints

- Change only `D:\My-Projects\TradingBot-Knowledge` and `D:\My-Projects\TradingBot-Intelligence-Plugin`.
- Do not write to Production, create a worktree, alter RAW/sidecar bytes, fixture SHA-256 values, window boundaries, source snapshots, or HPZR6 files.
- Preserve the user-owned untracked `TradingBot-Knowledge/_GENERATED/` directory.
- Do not stage, commit, push, or clean working trees; the user has not authorized Git history changes.
- Keep Order_A canonical; quarantine Order_B/C by default while allowing explicit retrieval.
- Do not promote pending/non-canonical knowledge or complete deferred future-phase directories.
- Build `_INDEX` only through `_SCHEMA/build_indexes.py`; prove two consecutive rebuilds are byte-identical.

## Review Focus

- A pending-manual-review marker on a matching source must not create a false `KNOWN_PENDING` result; Task 2 tests this.
- A missing fixture source or an undeclared mismatch must remain an error; Tasks 1 and 2 test this.
- A source SHA mismatch must never write back a new expected SHA; Tasks 1 and 2 test fixture frontmatter before and after verification.
- Default search/relations must continue to hide B/C while explicit retrieval returns their diagnostic evidence; Task 3 tests both paths.
- Source snapshot and reference verification must remain independent of dirty Production Git state; Task 5 runs direct byte comparisons.

---

### Task 1: Fixture-review contract tests

**Files:**
- Create: `D:\My-Projects\TradingBot-Knowledge\_SCHEMA\test_build_indexes.py`
- Modify: `D:\My-Projects\TradingBot-Intelligence-Plugin\test_vault_reader.py`

**Interfaces:**
- Consumes: current full Vault copied to a temporary root with `08_DATA/Raw` excluded in knowledge mode.
- Produces: failing integration tests for declared and undeclared fixture source SHA-256 mismatches, no SHA mutation, and Plugin result classifications.

- [ ] **Step 1: Write failing Vault-builder tests**

Create temporary Vault copies. Alter only the copied fixture source. Assert an undeclared mismatch returns `1`; assert all copied fixture notes marked `pending-manual-review` produce no error, emit `KNOWN_PENDING`, and preserve original `source_fixture_sha256` values.

- [ ] **Step 2: Run the Vault-builder tests and confirm they fail for the missing review contract**

Run: `python -B -m unittest -v _SCHEMA.test_build_indexes`

Expected: failure because the current builder treats every mismatch as an error and has no warning classification.

- [ ] **Step 3: Write failing Plugin-reader tests**

Use the same isolated knowledge-mode input shape. Assert `verify_package()` returns `ok: false` and a nonempty `errors` list for an undeclared mismatch; assert a declared mismatch has `ok: true`, empty `errors`, populated `warnings`/`known_pending`, `verified_pins_ok: false`, and unchanged stored SHA fields. Assert compatibility `failures == errors`.

- [ ] **Step 4: Run the Plugin-reader tests and confirm they fail for the missing result fields**

Run: `python -B -m unittest -v test_vault_reader`

Expected: failure because `errors`, `warnings`, and `known_pending` are not exposed and declared mismatches are not supported.

### Task 2: Implement strict classified fixture validation

**Files:**
- Modify: `D:\My-Projects\TradingBot-Knowledge\_SCHEMA\note.schema.json`
- Modify: `D:\My-Projects\TradingBot-Knowledge\_SCHEMA\case.schema.json`
- Modify: `D:\My-Projects\TradingBot-Knowledge\_SCHEMA\build_indexes.py`
- Modify: `D:\My-Projects\TradingBot-Intelligence-Plugin\vault_reader.py`
- Modify: `D:\My-Projects\TradingBot-Intelligence-Plugin\TECHNICAL_ARCHITECTURE.md`

**Interfaces:**
- Consumes: `source_fixture_review` omitted or one of `verified` / `pending-manual-review`.
- Produces: builder `KNOWN_PENDING` warnings and Plugin JSON fields `errors`, `warnings`, `known_pending`, retained `failures`, `ok`, `verified_pins_ok`, and `data_status` semantics from the specification.

- [ ] **Step 1: Add the optional case-only schema field**

Permit `source_fixture_review` only with the two declared values. Do not add the field to existing 22 fixture notes.

- [ ] **Step 2: Add builder warning collection without weakening error checks**

Classify only a SHA mismatch with the explicit pending marker as `KNOWN_PENDING`; leave missing paths, invalid headings when verifiable, malformed records, and unmarked mismatch errors. Emit warnings without changing source data or generated source hashes.

- [ ] **Step 3: Add Plugin parity verification**

Inspect each case note through real frontmatter and classify fixture source failures independently. Preserve existing `failures` callers by aliasing it to `errors`; set `ok`, `verified_pins_ok`, and `data_status` exactly as specified.

- [ ] **Step 4: Run both focused test modules and confirm the RED tests are green**

Run: `python -B -m unittest -v _SCHEMA.test_build_indexes` from the Vault, then `python -B -m unittest -v test_vault_reader` from the Plugin.

Expected: all focused tests pass; no expected fixture SHA has changed.

### Task 3: Retrieval-boundary regression tests and documentation

**Files:**
- Modify: `D:\My-Projects\TradingBot-Intelligence-Plugin\test_vault_reader.py`
- Modify: `D:\My-Projects\TradingBot-Intelligence-Plugin\TECHNICAL_ARCHITECTURE.md`
- Modify: `D:\My-Projects\TradingBot-Knowledge\04_ALGORITHMS\Order\Order-B.md`
- Modify: `D:\My-Projects\TradingBot-Knowledge\04_ALGORITHMS\Order\Order-C.md`
- Modify only audited OrderAudit leakage notes in the Vault.

**Interfaces:**
- Consumes: `search`, `get_entity`, `relations`, and `verify_package` public reader API.
- Produces: tests showing canonical Order_A retrieval, default B/C quarantine, explicit B/C diagnostic retrieval, OrderAudit absence, and HPZR6 evidence access.

- [ ] **Step 1: Add focused failing reader tests**

Assert the public reader returns Order_A normally, omits B/C from default search/relations, returns B/C under explicit quarantined retrieval with warning text, rejects OrderAudit as an entity/retrieval concept, and verifies both external HPZR6 identities when an Engine root is configured.

- [ ] **Step 2: Run the focused reader test names and confirm a missing or incomplete coverage failure**

Run: `python -B -m unittest -v test_vault_reader`

Expected: newly added coverage fails until the expected behavior or test route is completed; existing behavior is not weakened to satisfy it.

- [ ] **Step 3: Make only necessary reader/documentation corrections**

Keep existing working exclusion behavior; add implementation only if the test exposes a public-boundary gap. Add the exact future-semantics sentence to Order_B/C and replace active OrderAudit wording with source-evidence/exclusion wording.

- [ ] **Step 4: Run the focused reader suite**

Run: `python -B -m unittest -v test_vault_reader`

Expected: all reader tests pass.

### Task 4: Repair source-backed Vault documentation

**Files:**
- Modify: `D:\My-Projects\TradingBot-Knowledge\03_BEHAVIORS\S\Blue-Type-3.md`
- Modify: audited stale documents in `00_SYSTEM`, `01_CORE`, `04_ALGORITHMS`, `05_MIRROR`, `06_SOURCE`, `07_VALIDATION`, and `08_DATA` only.

**Interfaces:**
- Consumes: current captured S source, `04_ALGORITHMS/S/Type-3.md`, HPZR6 reference registry/evidence, and physically verified data inventory.
- Produces: source-backed behavior prose, accurate frontmatter guidance, audit exclusion wording, current data-inventory wording, and no ungrounded source/reference claim.

- [ ] **Step 1: Write the Type-3 and stale-document edits without changing frontmatter identity or evidence hashes**

Document behavior semantics separately from algorithm mechanics. State seven physical RAWs, five physical sidecars, and three logical windows. Correct claims that references are absent when they are hash-pinned external evidence. Do not touch source snapshots or RAW evidence.

- [ ] **Step 2: Run knowledge-mode validation before generation**

Run: `python -B _SCHEMA/build_indexes.py --check --mode knowledge`

Expected: no schema, relation, frontmatter, or source-evidence error.

### Task 5: Generate, validate, and audit final state

**Files:**
- Modify only generated `D:\My-Projects\TradingBot-Knowledge\_INDEX\*.json` through the builder.

**Interfaces:**
- Consumes: validated canonical Markdown/schema and Plugin code.
- Produces: deterministic indexes and a complete evidence report.

- [ ] **Step 1: Compile changed Python files**

Run: `python -B -m py_compile _SCHEMA/build_indexes.py _SCHEMA/test_build_indexes.py` and `python -B -m py_compile vault_reader.py test_vault_reader.py`.

- [ ] **Step 2: Rebuild indexes twice and compare byte hashes**

Run the builder twice in full-data mode; hash every `_INDEX/*.json` after each run. Require identical path/hash maps.

- [ ] **Step 3: Run full validation suites and smoke tests**

Run builder checks in knowledge and full-data modes, Vault generator tests, Plugin reader plus maintenance tests, VaultReader calls, CLI verification, and MCP smoke tests when `mcp` support imports.

- [ ] **Step 4: Independently verify Production boundaries and final Git state**

Compare each of the nine production Engine byte hashes to its Vault snapshot and compare both HPZR6 production references to the registry. Confirm Production Git status is unchanged from the pre-repair baseline and report other user-owned paths separately.

- [ ] **Step 5: Perform final branch self-review and report only evidenced results**

Review the local diff against this plan and specification. Do not commit or push. Report `READY_FOR_NEXT_PHASE` only when fresh evidence shows zero real errors.
