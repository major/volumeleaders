"""MCP server for VolumeLeaders institutional block trade data."""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING

try:
    from fastmcp import FastMCP
except ModuleNotFoundError as exc:
    sys.stderr.write(
        "volumeleaders-mcp requires the 'fastmcp' package.\n"
        "Install it with: uv add volumeleaders\n"
        "or: pip install fastmcp\n",
    )
    raise SystemExit(1) from exc

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from volumeleaders._client import VolumeLeadersClient

# When fastmcp loads this file by path (e.g. fastmcp run __init__.py:mcp),
# it gets a different module identity than the installed package's
# volumeleaders.mcp. Register under the canonical name so tool modules
# importing `from volumeleaders.mcp import mcp` get this same instance.
if __name__ != "volumeleaders.mcp":
    sys.modules["volumeleaders.mcp"] = sys.modules[__name__]


@dataclass
class VLContext:
    """Shared state available to all MCP tool invocations.

    The ``client`` is created lazily on first tool call so that transient
    auth failures (expired browser session, locked cookies database, network
    blip) do not prevent the MCP server from starting. Tools resolve the
    shared client via ``resolve_client(context)`` which initializes the
    client on first use and caches it for subsequent calls.
    """

    client: VolumeLeadersClient | None = None


@asynccontextmanager
async def _lifespan(server: FastMCP) -> AsyncIterator[VLContext]:
    """Provide an empty VLContext; the client is created on first tool call.

    Deferring ``VolumeLeadersClient`` construction keeps the MCP server
    process alive even when auth cookies are missing or stale. Auth errors
    surface as per-tool errors instead of crashing the whole server.
    """
    del server
    context = VLContext()
    try:
        yield context
    finally:
        if context.client is not None:
            context.client.close()


mcp = FastMCP("volumeleaders", lifespan=_lifespan)

# Import tool registration after server initialization.
import volumeleaders.mcp.tools  # noqa: F401,E402


def main() -> None:
    """Entry point for the volumeleaders-mcp console script."""
    mcp.run()
