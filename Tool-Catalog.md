# Tool catalog

- `search_knowledge`: find notes by title, ID, and content; known-invalid B/C require `include_quarantined=true`.
- `get_knowledge`: read one complete note and its authority.
- `trace_relations`: read authority-labelled incoming and outgoing entity relations; known-invalid B/C require `include_quarantined=true`.
- `get_dataset`: read metadata for a retained physical RAW; window entities use `get_raw_window`.
- `get_raw_window`: read a registered window's retained parent path, inclusive epochs, and recorded SHA-256; use `verify_vault` to recheck its bytes.
- `read_source_evidence`: read bounded, hash-verified source lines captured in the Vault.
- `read_algorithm_reference_evidence`: optionally read bounded, hash-verified HPZR6 lines from `TRADINGBOT_ENGINE_ROOT`; registry sections remain diagnostic unless accepted independently.
- `verify_vault`: `mode="knowledge"` checks indexed notes, relations, and pinned non-RAW evidence without reading RAW bytes; `data_status=NOT_RUN` and `inventory_complete=null` are explicit. `mode="full-data"` (default) also checks physical RAW bytes, exact windows, and unregistered inventory. Inspect `verified_pins_ok`, `inventory_complete`, and overall `ok` separately.

The CLI equivalents are `search`, `entity`, `relations`, `dataset`, `window`, `evidence`, `reference-evidence`, and `verify --mode knowledge|full-data`.
