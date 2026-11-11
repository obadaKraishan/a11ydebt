"""The README renders on PyPI, away from the repository, so every link in it must be absolute."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REPO = "https://github.com/obadaKraishan/a11ydebt"

#: Inline links and images: [text](target) and ![alt](target).
INLINE = re.compile(r"\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
#: Reference definitions, [label]: target (footnotes, [^label]:, are not links).
REFERENCE = re.compile(r"^ {0,3}\[(?!\^)[^\]]+\]:\s*<?(\S+?)>?(?:\s|$)", re.M)
#: HTML attributes.
HTML = re.compile(r"""(?:href|src)\s*=\s*["']([^"']+)["']""", re.I)
ABSOLUTE = re.compile(r"^(https?://|mailto:|#)")


def links(text: str) -> list[str]:
    return [m.group(1) for pattern in (INLINE, REFERENCE, HTML) for m in pattern.finditer(text)]


def readme() -> str:
    path = ROOT / "README.md"
    if not path.is_file():
        pytest.skip("README.md is not in this checkout")
    return path.read_text(encoding="utf-8")


def test_link_patterns_catch_relative_links():
    text = (
        "[a](docs/x.md) ![b](img.png) [c](https://example.org) [d](#anchor)\n"
        '[ref]: LICENSE\n[^note]: a footnote, not a link\n<a href="NOTICE">e</a>\n'
    )
    relative = [t for t in links(text) if not ABSOLUTE.match(t)]
    assert relative == ["docs/x.md", "img.png", "LICENSE", "NOTICE"]


def test_readme_has_no_relative_links():
    found = links(readme())
    assert len(found) >= 20  # the README has about 30 links; fewer means the patterns broke
    relative = [t for t in found if not ABSOLUTE.match(t)]
    assert relative == [], f"README.md has relative links, which break on PyPI: {relative}"


def test_readme_repository_links_point_at_real_paths():
    for target in links(readme()):
        m = re.match(rf"{re.escape(REPO)}/(blob|tree)/main/([^#?]+)", target)
        if not m:
            continue
        kind, path = m.group(1), ROOT / m.group(2).rstrip("/")
        if kind == "blob":
            assert path.is_file(), f"{target}: blob/ links must point at a file"
        else:
            assert path.is_dir(), f"{target}: tree/ links must point at a folder"
