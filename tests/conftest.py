from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures" / "rico"


@pytest.fixture
def rico_dir() -> Path:
    """Three synthetic Rico-format screens (two apps). Not derived from real Rico data."""
    return FIXTURES
