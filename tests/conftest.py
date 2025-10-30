"""Shared pytest configuration and fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def fixture_dir():
    """Return the path to test fixtures directory."""
    return Path(__file__).parent.absolute() / "fixtures"
