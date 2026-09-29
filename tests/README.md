# TradingBot Intelligence Plugin tests

This standard-library `unittest` suite checks Plugin retrieval, provenance,
integrity, and read-only operation. It does not calculate trading outcomes.
Test helpers create synthetic Vaults in temporary directories. Unit, contract,
and security tests use those Vaults; integration tests inspect configured real
resources without writing to them. MCP tests use an actual stdio subprocess.
Operational package tests build only inside a temporary copy.

## Prerequisites

- Python supported by the Plugin runtime, available as `python`.
- Run commands from the Plugin repository root.
- Install the existing requirements.txt dependencies, including jsonschema; no separate test framework is needed. MCP tests need the Plugin's existing
  `mcp` runtime dependency.
- Real integration needs `TRADINGBOT_KNOWLEDGE_VAULT` pointing to a valid Vault.
  External Engine reference checks additionally need `TRADINGBOT_ENGINE_ROOT`
  pointing to the matching Engine repository. `TRADINGBOT_PLUGIN_CONFIG` is an
  alternative Vault configuration file for runtime use; synthetic tests override
  it only in process and restore it afterward.

## Commands

```powershell
python -B -m unittest discover -s tests/unit -t . -v
python -B -m unittest discover -s tests/contract -t . -v
python -B -m unittest discover -s tests/security -t . -v
python -B -m unittest discover -s tests/integration -t . -v
python -B -m unittest discover -s tests/mcp -t . -v
python -B -m unittest discover -s tests/operational -t . -v
python -B -m unittest discover -s tests -t . -v
```

The first six commands isolate test categories; the final command discovers the
full suite. All category packages are discoverable. An empty category or skipped integration is not evidence that its contract passed. A focused foundation check is:

```powershell
python -B -m unittest tests.unit.test_helpers -v
```

An unavailable optional real Vault, Engine root, reference, or MCP dependency
may skip only the tests that require it. A skip must state the unavailable
resource precisely. Never label a skipped test `PASS`. The knowledge-only
`verify_package("knowledge")` checks knowledge and pinned evidence without
reading retained RAW bytes and reports `data_status=NOT_RUN`. Full-data
`verify_package("full-data")` reads retained RAW files, windows, sidecars, and
inventory. Empty-by-design stores need no market files; missing registered files still fail.
