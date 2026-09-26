"""Portable read-only MCP stdio server over the Vault-local reader."""
from __future__ import annotations

from mcp.server import MCPServer

import vault_reader as reader

mcp = MCPServer("TradingBot Knowledge")


@mcp.tool()
def search_knowledge(query: str, limit: int = 8, include_quarantined: bool = False) -> list[dict]:
    """Search knowledge; known-invalid Order_B/C require explicit include_quarantined."""
    return reader.search(query, limit, include_quarantined)


@mcp.tool()
def get_knowledge(entity_id: str) -> dict:
    """Read one complete Vault note, including its status, authority and local source anchors."""
    return reader.get_entity(entity_id)


@mcp.tool()
def trace_relations(entity_id: str, include_quarantined: bool = False) -> dict:
    """Trace authority-labelled relations; hide known-invalid routes by default."""
    return reader.relations(entity_id, include_quarantined)


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
def read_algorithm_reference_evidence(reference_id: str, start_line: int = 1, line_count: int = 40) -> dict:
    """Optionally read a hash-verified HPZR6 reference using TRADINGBOT_ENGINE_ROOT; B/C remain known-invalid."""
    return reader.read_algorithm_reference_evidence(reference_id, start_line, line_count)


@mcp.tool()
def verify_vault(mode: str = "full-data") -> dict:
    """Check knowledge-only integrity or full Vault RAW/fixture data integrity."""
    return reader.verify_package(mode)


if __name__ == "__main__":
    mcp.run()
