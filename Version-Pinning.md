# Version and integrity

The package version is declared in `plugin.json`. The Vault pins captured source and data in `_INDEX/source-hashes.json` and external reference identities in `06_SOURCE/References/registry.json`. The plugin reads those registries at runtime; it has no baked-in copy of their hashes or named IDs.

`vault_cli.py verify --mode knowledge` checks note/index consistency and registered non-RAW evidence. `--mode full-data` additionally reads and checks retained RAW, registered windows, and inventory. Both report known pending separately. The Vault index builder's `--check` mode performs schema validation. `vault_cli.py doctor` also checks configured external references and MCP transport. A source update does not approve a rule; examine Vault review state and authority before claiming current semantics.
