"""Shared fixtures for MCP tool tests."""

from __future__ import annotations

from importlib import import_module
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

_mcp_module = import_module("volumeleaders.mcp")


@pytest.fixture
def mcp_context() -> object:
    """Minimal MCP context with a mock client for tool tests."""
    return SimpleNamespace(lifespan_context=_mcp_module.VLContext(client=Mock()))
