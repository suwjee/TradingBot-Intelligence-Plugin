# Task 4 read-only integration report

## Outcome

The Task 4 integration layer contains nine `unittest` tests in three integration
modules, plus one real-root helper and the package initializer. The live run
completed with **9 PASS, 0 FAIL, 0 SKIP** and exit code **0**. No Plugin runtime,
Vault, Engine, external reference, Production, configuration, dependency, cache,
or Git state was changed by this task.

## Commands and exact results

| Purpose | Command | Exit | PASS | FAIL | SKIP |
| --- | --- | ---: | ---: | ---: | ---: |
| Scaffolding-only RED precondition | `python -B -m unittest tests.integration.test_real_vault -v` | 1 | 0 | 1 import error | 0 |
| Exact Task 4 command, inherited environment | `python -B -m unittest discover -s tests/integration -t . -v` | 0 | 0 | 0 | 9 |
| Live integration, process-local root variables | `python -B -m unittest discover -s tests/integration -t . -v` | 0 | 9 | 0 | 0 |

This historical RED was a scaffolding import check, not behavioral test evidence.
The import error was `ModuleNotFoundError: No module named
'tests.helpers.real_roots'`; that helper did not yet exist. The exact command
skipped all nine tests because `TRADINGBOT_KNOWLEDGE_VAULT` was unset. The live
run set `TRADINGBOT_KNOWLEDGE_VAULT` and `TRADINGBOT_ENGINE_ROOT` only in the
test process's shell; it took 4.951 seconds. Both configured roots were present.
No required resource was missing in the live run.

## Current facts and bounded identity evidence

- The active manifest produced **12** captured Engine file pairs, not the
  plan's recorded nine. Every pair passed byte, length, and SHA-256 equality.
  The count comes from the active manifest; the tests do not encode filenames.
- The active registry produced **2** external references. Both passed byte,
  length, and SHA-256 checks and bounded public evidence reads.
- `algorithm.order.a` returned canonical, normative, valid metadata. Explicit
  `algorithm.order.b` and `.c` retrieval retained non-canonical warnings while
  default search excluded them. `algorithm.orderaudit` was absent from the active
  entity index, and a pinned source containing `order_audit` remained readable.
  `behavior.s.blue.type3` returned indexed metadata, graph links, and pinned
  source anchors. These are retrieval facts, not trading-rule validation.
- The selected registered data IDs were `data.dataset_062df750` and
  `data.window_0291455b`. Metadata-only window retrieval omitted rows; bounded
  reads honored both exact endpoint epochs and the row cap.
- The protected snapshot covered **35 distinct files** and **58,114,599 bytes**:
  selected Vault indexes/notes/RAW, every derived Vault Engine mirror, every
  corresponding configured Engine file, and both external references. The
  sorted path/size/SHA-256 identity aggregate was
  `4986b5de2b15a2cf5efa2505b95d3b5b7760cabe4f936be70bce21a65c34ff88`.
  The test asserted identical before/after identities around public search,
  knowledge, relations, source, reference, dataset, window, `knowledge`
  verification, and `full-data` verification. Both verification modes returned
  empty `errors`; each returned `known_pending` count **0** in this observed run.

## Scope and limits

The first exact command is a valid skip result, not a live PASS. The live PASS
depends on process-local root configuration and the current contents of those
roots; a later checkout should rerun it. The snapshot proves no mutation of
the selected 35 files during the operation sequence, not of every file under
all roots. No Graphify command, Git command, stage, commit, or push was run.
