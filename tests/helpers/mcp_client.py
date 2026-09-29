"""Actual stdio MCP client, imported lazily when transport tests run."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence


@dataclass(frozen=True)
class MCPTranscript:
    initialized: bool
    listed_tools: tuple[str, ...]
    results: Mapping[str, object]


def run_mcp_session(
    command: Sequence[str], *, cwd: Path, env: Mapping[str, str],
    calls: Mapping[str, dict],
) -> MCPTranscript:
    """Initialize a real server, list tools, invoke calls, then close it."""
    if not command:
        raise ValueError("MCP command must include an executable")

    async def exercise() -> MCPTranscript:
        from mcp import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client

        parameters = StdioServerParameters(command=command[0], args=list(command[1:]),
                                           cwd=str(cwd), env=dict(env))
        async with stdio_client(parameters) as streams:
            async with ClientSession(*streams, read_timeout_seconds=60) as session:
                await session.initialize()
                listed = await session.list_tools()
                results = {}
                for name, arguments in calls.items():
                    results[name] = await session.call_tool(name, arguments)
                return MCPTranscript(True, tuple(tool.name for tool in listed.tools), results)

    return asyncio.run(exercise())
