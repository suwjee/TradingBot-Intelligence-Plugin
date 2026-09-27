# Tool catalog

The MCP server exposes eight read-only tools. Each uses the current configured Vault:

| MCP tool | CLI command | Result |
| --- | --- | --- |
| `search_knowledge` | `search QUERY` | Ranked indexed notes; optional type, authority, status, diagnostic filters, and offset. Each hit reports total matches and continuation offset. |
| `get_knowledge` | `entity ID` | Complete note and indexed authority metadata, subject to an explicit configurable byte cap. |
| `trace_relations` | `relations ID` | Incoming/outgoing edges and bounded directional traversal. |
| `get_dataset` | `dataset ID` | Registered RAW metadata and file availability. |
| `get_raw_window` | `window ID` | Registered inclusive range; optional bounded rows. |
| `read_source_evidence` | `evidence SOURCE_ID_OR_PATH` | At most 120 pinned, hash-checked source lines. |
| `read_algorithm_reference_evidence` | `reference-evidence ID` | At most 120 registered, hash-checked external reference lines. |
| `verify_vault` | `verify --mode knowledge|full-data` | Integrity, inventory, known pending, and optional reference availability. |

`vault_cli.py doctor` adds a real stdio MCP check. Search and relations hide unresolved or invalid-for-reasoning entities by default; diagnostic flags do not change authority. Full-data verification is required for retained RAW integrity claims.

Search returns at most 25 hits per page and reports `truncated` and `next_offset` on each hit. `get_knowledge` defaults to a 1 MiB note cap (`max_bytes`, at most 4 MiB); oversized notes return `RESPONSE_TOO_LARGE` rather than a partial note. Relation depth is at most five, source/reference excerpts at most 120 lines, and RAW window rows at most 1,000.
