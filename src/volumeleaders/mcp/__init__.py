"""MCP server for VolumeLeaders institutional block trade data."""

from __future__ import annotations

import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastmcp import FastMCP

from volumeleaders._client import VolumeLeadersClient

# When fastmcp loads this file by path (e.g. fastmcp run __init__.py:mcp),
# it gets a different module identity than the installed package's
# volumeleaders.mcp. Register under the canonical name so tool modules
# importing `from volumeleaders.mcp import mcp` get this same instance.
if __name__ != "volumeleaders.mcp":
    sys.modules["volumeleaders.mcp"] = sys.modules[__name__]


@dataclass
class VLContext:
    """Shared state available to all MCP tool invocations."""

    client: VolumeLeadersClient


@asynccontextmanager
async def _lifespan(server: FastMCP) -> AsyncIterator[VLContext]:
    """Initialize VolumeLeadersClient once at startup, close on shutdown."""
    del server
    client = VolumeLeadersClient()
    try:
        yield VLContext(client=client)
    finally:
        client.close()


mcp = FastMCP("volumeleaders", lifespan=_lifespan)

# Import tool registration after server initialization.
import volumeleaders.mcp.tools  # noqa: F401,E402


def main() -> None:
    """Entry point for the volumeleaders-mcp console script."""
    mcp.run()
