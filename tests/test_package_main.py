"""Tests for the package-level entry point."""

from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest


def test_main_prints_usage_guidance(capsys: pytest.CaptureFixture[str]) -> None:
    """Print guidance for using the client and endpoint functions."""
    import_module("volumeleaders").main()

    assert "Use VolumeLeadersClient" in capsys.readouterr().out
