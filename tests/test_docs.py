"""Checks on the docs: README links work on PyPI, and the counts in the prose match results/v0.1.

The README renders on PyPI, away from the repository, so every link in it must be absolute.
The counts the README and docs/how-to-audit.md quote must equal the committed aggregate tables.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REPO = "https://github.com/obadaKraishan/a11ydebt"
RESULTS = ROOT / "results" / "v0.1"
AC10 = "AndroidControl, 10 shards (the paper's sample)"

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


def _text(path: Path) -> str:
    """The file's text with all whitespace runs (including line breaks) collapsed to one space."""
    if not path.is_file():
        pytest.skip(f"{path.relative_to(ROOT)} is not in this checkout")
    return " ".join(path.read_text(encoding="utf-8").split())


def _num(s: str) -> int:
    return int(s.replace(",", ""))


def _results(name: str) -> dict[tuple[str, str], dict[str, str]]:
    path = RESULTS / name
    if not path.is_file():
        pytest.skip(f"results/v0.1/{name} is not in this checkout")
    with path.open(encoding="utf-8", newline="") as fh:
        return {(r["corpus"], r["population"]): r for r in csv.DictReader(fh)}


def test_readme_counts_match_the_results():
    text = _text(ROOT / "README.md")
    coverage = _results("coverage.csv")
    screens = _results("screens_with_debt.csv")
    m = re.search(
        r"needs_label has ([\d,]+) app clusters on Rico and ([\d,]+) on AndroidControl "
        r"\(([\d,]+) apps, plus ([\d,]+) no-app episodes",
        text,
    )
    assert m, "the README's app-cluster sentence changed; update this test with it"
    rico, ac, ac_apps, ac_no_app = (_num(g) for g in m.groups())
    assert rico == int(coverage[("Rico", "needs_label")]["app_clusters"])
    assert ac == int(coverage[(AC10, "needs_label")]["app_clusters"])
    assert ac_apps + ac_no_app == ac

    m = re.search(r"Rico has ([\d,]+) screens from ([\d,]+) apps", text)
    assert m and _num(m.group(1)) == int(screens[("Rico", "needs_label")]["screens"])
    m = re.search(r"The AndroidControl sample has ([\d,]+) screens from ([\d,]+) episodes", text)
    assert m and _num(m.group(1)) == int(screens[(AC10, "needs_label")]["screens"])


def test_how_to_audit_cluster_counts_match_the_results():
    text = _text(ROOT / "docs" / "how-to-audit.md")
    coverage = _results("coverage.csv")
    assert "| App clusters (needs_label) |" in text
    rico = int(coverage[("Rico", "needs_label")]["app_clusters"])
    ac = int(coverage[(AC10, "needs_label")]["app_clusters"])
    cells = r"[^|]*\|[^|]*\|[^|]*\|"  # the corpus, needs_label and icon_like cells
    assert re.search(rf"\| Rico \(2017\){cells} {rico:,} \|", text)
    assert re.search(rf"\| AndroidControl \(2024\), 10 shards{cells} {ac:,} \|", text)
    assert f"{rico:,} have a needs-label candidate" in text
    m = re.search(r"its ([\d,]+) clusters are ([\d,]+) of the [\d,]+ apps plus ([\d,]+) of", text)
    assert m and _num(m.group(1)) == ac == _num(m.group(2)) + _num(m.group(3))


def test_readme_app_counts_match_the_report_headers():
    report = _text(RESULTS / "report.md")
    readme = _text(ROOT / "README.md")
    how_to = _text(ROOT / "docs" / "how-to-audit.md")
    header = (
        r"from `[^`]+`: ([\d,]+) screens, [\d,]+ nodes \([^)]*\), ([\d,]+) identified apps? and "
    )
    rico = re.search(r"## Rico Dataset `rico` " + header + r"([\d,]+) screens? with no", report)
    ac10 = re.search(rf"## {re.escape(AC10)} Dataset `androidcontrol` " + header, report)
    ac10_no_app = re.search(r"([\d,]+) episodes? with no identified app", report[ac10.end() :])
    assert rico and ac10 and ac10_no_app

    m = re.search(r"Rico has ([\d,]+) screens from ([\d,]+) apps", readme)
    assert m and m.groups() == rico.groups()[:2]
    assert f"Rico has {rico.group(2)} apps" in how_to
    m = re.search(
        r"The AndroidControl sample has ([\d,]+) screens from [\d,]+ episodes: ([\d,]+) identified "
        r"apps, and ([\d,]+) episodes with no identified app",
        readme,
    )
    assert m and m.groups() == (*ac10.groups(), ac10_no_app.group(1))
    assert f"of the {ac10.group(2)} apps plus" in how_to
    assert f"of the {ac10_no_app.group(1)} no-app episodes" in how_to
