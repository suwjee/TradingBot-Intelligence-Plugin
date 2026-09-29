# Task 4 fix round 1 report

## Result

The real-root helper now requires only the Vault for Vault/entity/graph/RAW
tests. Engine mirror, external reference, and combined public-operation tests
request the Engine explicitly. No integration test infers a missing Engine from
a default Vault-only result.

| Environment | Exact test command | Exit | PASS | FAIL | SKIP | Elapsed |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Vault configured; Engine variable removed | `python -B -m unittest discover -s tests/integration -t . -v` | 0 | 6 | 0 | 3 | 1.054 s |
| Vault and Engine configured | `python -B -m unittest discover -s tests/integration -t . -v` | 0 | 9 | 0 | 0 | 5.860 s |

All three Vault-only skips said `Set TRADINGBOT_ENGINE_ROOT to the Engine
checkout root`. They were the Engine-mirror identity test, external-reference
identity/evidence test, and combined public-operation/no-mutation test. The
Vault-only retrieval, graph, source-anchor, knowledge verifier, and registered
RAW tests ran and passed. The root variables were set or removed only in the
respective test command's process environment.

## Strengthened assertions and current facts

- Order A public fields `status`, `authority`, `valid_for_reasoning`, and
  `implementation_validity` must be present and equal the returned canonical
  frontmatter. The frontmatter also declares accepted validation and regression
  eligibility. Order B/C frontmatter currently declares `pending-fix`,
  `non-canonical`, `known-invalid`, false reasoning/validation/regression
  eligibility, and `rewrite_required=true`; public indexed fields must be
  present and agree. Default search excludes B/C, while explicit diagnostic
  search and retrieval retain them.
- Type-3 S must have nonempty `calculated_by`, `implemented_by`, and
  `source_refs` lists. The test resolves their graph targets and reads bounded
  pinned evidence at each source anchor. It does not test trading formation.
- The active manifest yielded 12 Engine mirror pairs and the registry yielded
  2 external references. Both counts are discovered from live records.

## No-mutation evidence and limits

The combined test now snapshots the entire configured Vault `08_DATA/Raw`
directory, including every RAW JSON file that either verifier or window access
can read. Its selected protected snapshot also includes four Vault index and
registry files, every manifest-derived Vault Engine mirror and matching Engine
file, both external references, and three selected entity notes. The resulting
deduplicated snapshot covered **48 files**, **120,221,848 bytes**, including
**15 RAW-directory files**. Its sorted path/size/SHA-256 identity aggregate was
`1951587bd80a6e71e5d26c92817ad3d3da633b231dfdd10773eeb25ebea51044`.
The test took before/after snapshots around the listed public operations and
both `knowledge` and `full-data` verification; identity comparison passed.
This supports no mutation of those exact 48 files during that test, not of
every file under the Vault, Engine, or Plugin roots.

The earlier Task 4 report's import-error RED remains historical, but is now
explicitly labeled a **scaffolding-only** check. It did not demonstrate a
failing retrieval or mutation behavior. No Graphify or Git command was run;
no files outside `tests/` were edited, staged, or committed.
