"""coverage() on the three fixture screens. Every expected number was counted by hand."""

from __future__ import annotations

import shutil

import pytest

from a11ydebt.coverage import Counts, ScreenCoverage, audit_rico, coverage, screen_coverage
from a11ydebt.rico import iter_screens


def pops(model):
    return {p: (c.candidates, c.labelled) for p, c in model.populations.items()}


@pytest.fixture
def report(rico_dir):
    return coverage(iter_screens(rico_dir))


def test_counts_proportions():
    c = Counts(candidates=11, labelled=3)
    assert c.unlabelled == 8
    assert c.coverage == pytest.approx(3 / 11)
    assert c.debt == pytest.approx(8 / 11)
    empty = Counts()
    assert (empty.coverage, empty.debt) == (None, None)
    assert Counts(candidates=2, labelled=1) + Counts(candidates=3, labelled=1) == Counts(
        candidates=5, labelled=2
    )
    assert c.model_dump() == {
        "candidates": 11,
        "labelled": 3,
        "unlabelled": 8,
        "coverage": 3 / 11,
        "debt": 8 / 11,
    }


def test_per_screen(report):
    s101, s102, s103 = report.screens
    assert (s101.screen_id, s101.app, s101.n_nodes, s101.n_included) == (
        "101",
        "org.example.notes",
        8,
        6,
    )
    assert pops(s101) == {"needs_label": (3, 1), "icon_like": (2, 0), "interactive_image": (2, 0)}
    assert (s102.n_nodes, s102.n_included) == (10, 10)
    assert pops(s102) == {"needs_label": (5, 1), "icon_like": (2, 1), "interactive_image": (2, 1)}
    assert (s103.app, s103.n_nodes, s103.n_included) == ("com.example.weather", 7, 5)
    assert pops(s103) == {"needs_label": (3, 1), "icon_like": (2, 1), "interactive_image": (2, 1)}
    assert s101.populations["needs_label"].coverage == pytest.approx(1 / 3)
    assert s101.populations["icon_like"].debt == 1.0


def test_per_app(report):
    notes, weather = sorted(report.apps, key=lambda a: a.app, reverse=True)
    assert (notes.app, notes.n_screens, notes.n_nodes, notes.n_included) == (
        "org.example.notes",
        2,
        18,
        16,
    )
    assert pops(notes) == {"needs_label": (8, 2), "icon_like": (4, 1), "interactive_image": (4, 1)}
    assert notes.populations["needs_label"].coverage == pytest.approx(0.25)
    assert notes.screens_with_debt == {"needs_label": 2, "icon_like": 2, "interactive_image": 2}
    assert (weather.app, weather.n_screens, weather.n_nodes, weather.n_included) == (
        "com.example.weather",
        1,
        7,
        5,
    )
    assert pops(weather) == {
        "needs_label": (3, 1),
        "icon_like": (2, 1),
        "interactive_image": (2, 1),
    }
    assert weather.screens_with_debt == {"needs_label": 1, "icon_like": 1, "interactive_image": 1}


def test_corpus_and_roles(report):
    corpus = report.corpus
    assert (corpus.n_screens, corpus.n_apps, corpus.n_nodes, corpus.n_included) == (3, 2, 25, 21)
    assert pops(corpus) == {
        "needs_label": (11, 3),
        "icon_like": (6, 2),
        "interactive_image": (6, 2),
    }
    assert corpus.populations["needs_label"].coverage == pytest.approx(3 / 11)
    assert corpus.screens_with_debt == {"needs_label": 3, "icon_like": 3, "interactive_image": 3}
    roles = {r: (c.candidates, c.labelled) for r, c in corpus.needs_label_by_role.items()}
    assert roles == {"button": (2, 1), "image": (6, 2), "input": (2, 0), "other": (1, 0)}
    assert sum(c.candidates for c in corpus.needs_label_by_role.values()) == 11


def test_coverage_accepts_precomputed_screens(rico_dir, report):
    pre = [screen_coverage(s) for s in iter_screens(rico_dir)]
    assert coverage(pre).corpus == report.corpus


def test_audit_rico_serial_and_parallel_agree(rico_dir, report):
    serial = audit_rico(rico_dir)
    parallel = audit_rico(rico_dir, workers=2)
    assert serial.corpus == parallel.corpus == report.corpus
    assert [s.screen_id for s in parallel.screens] == ["101", "102", "103"]
    assert audit_rico(rico_dir, limit=1).corpus.n_screens == 1


def test_unreadable_files_are_recorded_not_fatal(rico_dir, tmp_path):
    shutil.copytree(rico_dir, tmp_path / "rico")
    (tmp_path / "rico" / "combined" / "104.json").write_text("{not json", encoding="utf-8")
    (tmp_path / "rico" / "combined" / "105.json").write_text('{"activity": {}}', encoding="utf-8")
    result = audit_rico(tmp_path / "rico")
    assert result.corpus.n_screens == 3
    assert [f.screen_id for f in result.failures] == ["104", "105"]
    assert result.failures[0].error.startswith("JSONDecodeError")
    assert "no activity.root" in result.failures[1].error


def test_screens_without_an_app_are_not_counted_as_an_app():
    def screen(sid, app):
        return ScreenCoverage(
            screen_id=sid,
            app=app,
            n_nodes=1,
            n_included=1,
            populations={p: Counts() for p in ("needs_label", "icon_like", "interactive_image")},
            needs_label_by_role={},
        )

    report = coverage([screen("1", "com.a"), screen("2", ""), screen("3", "com.b")])
    assert report.corpus.n_apps == 2
    assert {a.app for a in report.apps} == {
        "",
        "com.a",
        "com.b",
    }  # the unknown group is still listed
