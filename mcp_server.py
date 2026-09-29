"""Portable read-only MCP stdio server over the Vault-local reader."""
from __future__ import annotations

import sys
import traceback
from mcp.server import MCPServer

try:
    import vault_reader as reader
except RuntimeError as exc:
    print(str(exc), file=sys.stderr)
    raise SystemExit(2) from None

mcp = MCPServer("TradingBot Knowledge")


def _call(function, *args, **kwargs):
    try:
        return function(*args, **kwargs)
    except (ValueError, OSError, KeyError, reader.VaultError) as exc:
        return reader.error_payload(exc)
    except Exception as exc:
        traceback.print_exc(file=sys.stderr)
        return reader.error_payload(exc)


@mcp.tool()
def search_knowledge(query: str, limit: int = 8, include_quarantined: bool = False,
                     entity_type: str | None = None, authority: str | None = None,
                     status: str | None = None, include_noncanonical: bool = False,
                     include_pending: bool = False, offset: int = 0) -> list[dict] | dict:
    """Search Vault notes with explicit authority, status, and diagnostic filters."""
    return _call(reader.search, query, limit, include_quarantined,
                 entity_type=entity_type, authority=authority, status=status,
                 include_noncanonical=include_noncanonical, include_pending=include_pending,
                 offset=offset)


@mcp.tool()
def get_knowledge(entity_id: str, max_bytes: int = 1_048_576) -> dict:
    """Read one complete Vault note, including its status, authority and local source anchors."""
    return _call(reader.get_entity, entity_id, max_bytes)


@mcp.tool()
def trace_relations(entity_id: str, include_quarantined: bool = False,
                    direction: str = "both", max_depth: int = 1) -> dict:
    """Trace bounded, directional Vault relations with authority metadata."""
    return _call(reader.relations, entity_id, include_quarantined,
                 direction=direction, max_depth=max_depth)


@mcp.tool()
def get_dataset(entity_id: str) -> dict:
    """Read pinned RAW metadata and presence; never return the large RAW candle array."""
    return _call(reader.get_dataset, entity_id)


@mcp.tool()
def get_raw_window(entity_id: str, include_rows: bool = False,
                   start_epoch: int | None = None, end_epoch: int | None = None,
                   limit: int = 500) -> dict:
    """Read window metadata or bounded RAW rows from its Vault-declared parent."""
    return _call(reader.get_window, entity_id, include_rows=include_rows,
                 start_epoch=start_epoch, end_epoch=end_epoch, limit=limit)


@mcp.tool()
def read_source_evidence(path: str, start_line: int = 1, line_count: int = 40) -> dict:
    """Read at most 120 hash-verified source lines by Vault source ID or pinned path."""
    return _call(reader.read_evidence, path, start_line, line_count)


@mcp.tool()
def read_algorithm_reference_evidence(reference_id: str, start_line: int = 1, line_count: int = 40) -> dict:
    """Read a pinned local reference and optionally cross-verify its Engine copy."""
    return _call(reader.read_algorithm_reference_evidence, reference_id, start_line, line_count)


@mcp.tool()
def verify_vault(mode: str = "full-data") -> dict:
    """Check knowledge-only integrity or full Vault RAW/fixture data integrity."""
    return _call(reader.verify_package, mode)


if __name__ == "__main__":
    mcp.run()
