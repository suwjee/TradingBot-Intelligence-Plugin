"""Portable read-only MCP stdio server over the Vault-local reader."""
from __future__ import annotations

from mcp.server import MCPServer

import vault_reader as reader

mcp = MCPServer("TradingBot Knowledge")


@mcp.tool()
def search_knowledge(query: str, limit: int = 8) -> list[dict]:
    """Find Vault knowledge notes by ID, title and content; inspect authority before using a rule."""
    return reader.search(query, limit)


@mcp.tool()
def get_knowledge(entity_id: str) -> dict:
    """Read one complete Vault note, including its status, authority and local source anchors."""
    return reader.get_entity(entity_id)


@mcp.tool()
def trace_relations(entity_id: str) -> dict:
    """Get incoming and outgoing ID relations for a Vault entity."""
    return reader.relations(entity_id)


@mcp.tool()
def get_dataset(entity_id: str) -> dict:
    """Read pinned RAW metadata and presence; never return the large RAW candle array."""
    return reader.get_dataset(entity_id)


@mcp.tool()
def get_raw_window(entity_id: str) -> dict:
    """Read a retained RAW window's parent path and inclusive epoch range; run verify_vault for its hash."""
    return reader.get_window(entity_id)


@mcp.tool()
def read_source_evidence(path: str, start_line: int = 1, line_count: int = 40) -> dict:
    """Read at most 120 numbered lines from a hash-verified source or directional reference in this Vault."""
    return reader.read_evidence(path, start_line, line_count)


@mcp.tool()
def verify_vault() -> dict:
    """Check indexed notes, pinned evidence and RAW windows, and report unregistered physical RAW files."""
    return reader.verify_package()


if __name__ == "__main__":
    mcp.run()
