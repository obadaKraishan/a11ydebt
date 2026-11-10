"""The version and the title agree across pyproject, CITATION.cff and .zenodo.json."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from a11ydebt import __version__

ROOT = Path(__file__).resolve().parents[1]


def test_citation_cff_matches_the_package():
    path = ROOT / "CITATION.cff"
    if not path.is_file():
        pytest.skip("CITATION.cff is not in this checkout")
    text = path.read_text(encoding="utf-8")
    assert re.search(r'^version: "(.+)"$', text, re.M).group(1) == __version__
    assert "license: Apache-2.0" in text
    assert "preferred-citation:" in text


def test_zenodo_json_matches_the_citation():
    path = ROOT / ".zenodo.json"
    if not path.is_file():
        pytest.skip(".zenodo.json is not in this checkout")
    meta = json.loads(path.read_text(encoding="utf-8"))
    assert meta["version"] == __version__
    assert meta["upload_type"] == "software" and meta["license"] == "Apache-2.0"
    cff = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    assert re.search(r'^title: "(.+)"$', cff, re.M).group(1) == meta["title"]
