# Tool catalog

- `search_knowledge`: find notes by title, ID, and content.
- `get_knowledge`: read one complete note and its authority.
- `trace_relations`: read incoming and outgoing entity relations.
- `get_dataset`: read metadata for a retained physical RAW; window entities use `get_raw_window`.
- `get_raw_window`: read a registered window's retained parent path, inclusive epochs, and recorded SHA-256; use `verify_vault` to recheck its bytes.
- `read_source_evidence`: read bounded, hash-verified source lines captured in the Vault.
- `verify_vault`: check indexed notes and relations, pinned source/RAW bytes, exact windows, and unregistered physical RAW inventory. Inspect `verified_pins_ok`, `inventory_complete`, and overall `ok` separately.

The CLI equivalents are `search`, `entity`, `relations`, `dataset`, `window`, `evidence`, and `verify`.
