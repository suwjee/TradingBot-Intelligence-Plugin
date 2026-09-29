# Current test suite maintenance plan

The full standard-library unittest suite covers generic discovery, authority, complete frontmatter/schema integrity, strict trusted JSON, canonical relations, source/local-reference evidence, optional external verification, bounded synthetic RAW windows, read-only integration, actual stdio MCP and transactional maintenance.

Synthetic test input exists only in temporary directories and does not encode market outcomes or production trading rules. Current real integration checks the active Order_A/Order_B and first-class OrderAudit metadata, exact current Engine/Reference pins, graph/node/edge agreement and zero real Data/Fixture records. Both data-dependent MCP tools must return expected ENTITY_NOT_FOUND in the intentionally empty Vault.

Run all tests with `python -B -m unittest discover -s tests -t . -v`. Configure the real Vault and optional matching Engine for integration; install requirements.txt for transport. Report PASS/FAIL, real failures, stale-contract failures and platform/dependency skips separately. Preserve a failing assertion's intended contract when currentizing it.

Maintenance tests use actual temporary capture/index-builder subprocesses with mocked read-only Git evidence. Builder failure must roll back both indexes and generated files. A clean Reference capture must refresh local bytes and all identity/version metadata without approving trading semantics. Package operation occurs through the official allowlist builder in an isolated temporary copy.
