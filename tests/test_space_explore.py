"""The Space's Explore tab: corpus totals, distributions, the top-debt table, the published
numbers it shows beside them, and the chart HTML. Synthetic tables only."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

pa = pytest.importorskip("pyarrow")
bs = pytest.importorskip("build_stats")
ex = pytest.importorskip("explore_stats")
published = pytest.importorskip("published")
charts = pytest.importorskip("charts")

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "v0.1"


def screen(dataset, screen_id, need, need_lab, icon=0, icon_lab=0, shard=None, included=10):
    episode, step = (None, None)
    if dataset == "androidcontrol":
        episode, step = (int(x) for x in screen_id.split("_"))
    return {
        "dataset": dataset,
        "screen_id": screen_id,
        "episode_id": episode,
        "step_index": step,
        "shard": shard,
        "in_paper_sample": True if shard is None else shard < 10,
        "n_nodes": included + 5,
        "n_included": included,
        "needs_label_candidates": need,
        "needs_label_labelled": need_lab,
        "needs_label_unlabelled": need - need_lab,
        "needs_label_coverage": need_lab / need if need else None,
        "icon_like_candidates": icon,
        "icon_like_labelled": icon_lab,
        "icon_like_unlabelled": icon - icon_lab,
        "icon_like_coverage": icon_lab / icon if icon else None,
    }


@pytest.fixture
def stats():
    rows = [
        screen("rico", "1", 10, 3, icon=4, icon_lab=1),  # 30%: the 30 to 39% bin
        screen("rico", "2", 10, 0),  # 0%
        screen("rico", "3", 4, 4),  # 100%
        screen("rico", "4", 0, 0),  # no candidates: left out of the distributions
        screen("rico", "5", 25, 1),  # 4%: under 10%
        screen("androidcontrol", "7_0", 6, 3, shard=0),  # 50%
        screen("androidcontrol", "7_1", 60, 0, shard=0),  # 50 or more unlabelled
        screen("androidcontrol", "9_0", 3, 2, shard=15),  # not in the paper's sample
    ]
    table = pa.Table.from_pylist(rows, schema=bs.SCHEMA)
    bs.check_no_free_text(table)
    return ex.from_table(table)


def test_masks(stats):
    assert stats.mask("rico").sum() == 5
    assert stats.mask("ac10").sum() == 2
    assert stats.mask("ac20").sum() == 3
    with pytest.raises(ValueError):
        stats.mask("rico-semantics")


def test_headline(stats):
    h = ex.headline(stats, "rico")
    assert h["screens"] == 5 and h["n_included"] == 50
    need = h["needs_label"]
    assert (need["candidates"], need["labelled"]) == (49, 8)
    assert need["coverage"] == pytest.approx(8 / 49)
    assert need["screens_with_candidates"] == 4
    assert need["screens_with_debt"] == 3
    assert need["share_of_screens_with_debt"] == pytest.approx(3 / 5)
    assert ex.headline(stats, "ac10")["needs_label"]["candidates"] == 66


def test_coverage_distribution_bins(stats):
    rows = ex.coverage_distribution(stats, "rico", "needs_label")
    assert [label for label, _, _ in rows] == list(ex.COVERAGE_BINS)
    counts = {label: n for label, n, _ in rows}
    assert counts["0% (none)"] == 1
    assert counts["under 10%"] == 1
    assert counts["30 to 39%"] == 1  # exactly 30% lands here, not in 20 to 29%
    assert counts["100% (all)"] == 1
    assert sum(counts.values()) == 4
    assert sum(share for _, _, share in rows) == pytest.approx(1.0)


def test_min_candidates_filter(stats):
    rows = ex.coverage_distribution(stats, "rico", "needs_label", min_candidates=10)
    assert sum(n for _, n, _ in rows) == 3
    empty = ex.coverage_distribution(stats, "rico", "icon_like", min_candidates=20)
    assert all(n == 0 and share == 0.0 for _, n, share in empty)


def test_unlabelled_distribution(stats):
    rows = dict(
        (label, n) for label, n, _ in ex.unlabelled_distribution(stats, "ac10", "needs_label")
    )
    assert rows["2 to 4"] == 1 and rows["50 or more"] == 1
    assert sum(rows.values()) == 2


def test_top_debt_rico(stats):
    rows = ex.top_debt(stats, "rico", "needs_label", n=3)
    assert [row[1] for row in rows] == ["5", "2", "1"]
    assert rows[0] == [1, "5", 25, 1, 24, "4.0%"]
    assert len(rows[0]) == len(ex.TOP_HEADERS["rico"])


def test_top_debt_ties_go_to_lower_coverage():
    rows = [screen("rico", "1", 10, 5), screen("rico", "2", 6, 1), screen("rico", "3", 5, 0)]
    stats = ex.from_table(pa.Table.from_pylist(rows, schema=bs.SCHEMA))
    assert [row[1] for row in ex.top_debt(stats, "rico", "needs_label")] == ["3", "2", "1"]


def test_top_debt_androidcontrol(stats):
    rows = ex.top_debt(stats, "ac20", "needs_label")
    assert rows[0] == [1, "7_1", 7, 1, "00000", 60, 0, 60, "0.0%"]
    assert {row[1] for row in rows} == {"7_0", "7_1", "9_0"}
    assert len(rows[0]) == len(ex.TOP_HEADERS["androidcontrol"])
    assert {row[1] for row in ex.top_debt(stats, "ac10", "needs_label")} == {"7_0", "7_1"}


def test_lookup_lines_name_no_local_paths():
    for line in ex.LOOKUP.values():
        assert "combined/" in line or "accessibility_trees" in line
        assert "/Users/" not in line and "Volumes" not in line


# ------------------------------------------------------------------ published numbers


def _rows(name: str) -> list[dict[str, str]]:
    path = RESULTS / name
    if not path.is_file():
        pytest.skip(f"results/v0.1/{name} is not in this checkout")
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_published_intervals_match_results():
    rows = {(r["corpus"], r["population"]): r for r in _rows("coverage.csv")}
    for key, corpus in published.CORPUS_NAMES.items():
        for pop, (low, high) in published.APP_CLUSTER_CI[key].items():
            row = rows[(corpus, pop)]
            assert (low, high) == (float(row["app_ci_low"]), float(row["app_ci_high"]))


def test_published_roles_match_results():
    rows = {(r["corpus"], r["role"]): r for r in _rows("roles.csv")}
    for key, corpus in published.CORPUS_NAMES.items():
        assert set(published.ROLE_COUNTS[key]) == set(published.ROLES)
        for role, (cand, lab) in published.ROLE_COUNTS[key].items():
            row = rows[(corpus, role)]
            assert (cand, lab) == (int(row["candidates"]), int(row["labelled"]))


# ------------------------------------------------------------------ charts


def _series(**overrides):
    values = {
        "name": "Rico (2017)",
        "tag": "Rico",
        "css": "s1",
        "values": [0.5, 0.0],
        "labels": ["50.0%", "0.0%"],
        "cells": ["5 screens (50.0%)", "0 screens (0.0%)"],
    }
    values.update(overrides)
    return charts.Series(**values)


def test_bar_chart_structure():
    html = charts.bar_chart(
        "Title", "Caption", ["a", "b"], [_series(), _series(css="s2", tag="AC")]
    )
    assert html.count('class="ad-row"') == 2
    assert html.count('class="ad-swatch') == 2  # a legend entry per series
    assert "Rico: 50.0%" in html and "AC: 50.0%" in html  # direct labels on the first row only
    assert html.count("Rico:") == 1
    assert 'title="Rico (2017), a: 5 screens (50.0%)"' in html
    assert "<table>" in html and "<td>5 screens (50.0%)</td>" in html
    assert "min-width:0" in html  # a zero value draws no bar
    assert "<script" not in html


def test_bar_chart_escapes_text():
    html = charts.bar_chart(
        "<b>x</b>", "a & b", ['"q"'], [_series(values=[1], labels=["1"], cells=["<i>"])]
    )
    assert "<b>x</b>" not in html and "&lt;b&gt;x&lt;/b&gt;" in html
    assert "a &amp; b" in html and "&lt;i&gt;" in html


def test_headline_cards():
    card = charts.Card("Rico (2017)", "s1", "17.74%", "caption", "meta", [("Icon-like", "33.20%")])
    html = charts.headline_cards([card], note="note")
    assert 'aria-label="Rico (2017)"' in html and "<dt>Icon-like</dt><dd>33.20%</dd>" in html
    assert '<p class="ad-note">note</p>' in html


def test_chart_css_has_both_themes():
    assert ".dark .ad-root" in charts.CSS
    assert "#2a78d6" in charts.CSS and "#3987e5" in charts.CSS  # series 1, light and dark
