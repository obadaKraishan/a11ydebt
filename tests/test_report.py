"""a11ydebt.report and `a11ydebt report` on synthetic audits (never real corpus data)."""

from __future__ import annotations

import csv
import json

import pytest

from a11ydebt.cli import main, write_outputs
from a11ydebt.coverage import Counts, ScreenCoverage, coverage
from a11ydebt.report import build_report, format_markdown, load_audit, write_report


def screen(screen_id: str, app: str, needs: tuple[int, int], icon: tuple[int, int] = (0, 0)):
    """A screen with (labelled, candidates) for needs_label and icon_like."""

    def counts(pair: tuple[int, int]) -> Counts:
        return Counts(labelled=pair[0], candidates=pair[1])

    return ScreenCoverage(
        screen_id=screen_id,
        app=app,
        n_nodes=10,
        n_included=8,
        populations={
            "needs_label": counts(needs),
            "icon_like": counts(icon),
            "interactive_image": counts((0, 0)),
        },
        needs_label_by_role={"image": counts(needs)} if needs[1] else {},
    )


@pytest.fixture
def ac_audit(tmp_path):
    """AndroidControl-style screens: episode 1 has an app, episodes 2 and 3 have none."""
    screens = [
        screen("1_0", "com.a", (2, 4), (1, 1)),
        screen("1_1", "com.a", (1, 1)),
        screen("2_0", "", (0, 2), (0, 1)),
        screen("2_1", "", (1, 2)),
        screen("3_0", "", (3, 3)),
        screen("3_1", "", (0, 0)),  # no candidates: in the screen count, not a cluster
    ]
    out = tmp_path / "ac"
    write_outputs(coverage(screens, dataset="androidcontrol"), out, source="synthetic")
    return out


def test_report_tables_for_androidcontrol(ac_audit):
    report = build_report(load_audit(ac_audit, "AC synthetic"), n_resamples=400, seed=3)
    assert (report.label, report.dataset, report.n_screens, report.n_apps) == (
        "AC synthetic",
        "androidcontrol",
        6,
        1,
    )
    needs = next(p for p in report.populations if p.population == "needs_label")
    assert (needs.candidates, needs.labelled, needs.coverage) == (12, 7, 7 / 12)
    app, scr = needs.intervals["app"], needs.intervals["screen"]
    # com.a (3/5), episode:2 (1/4) and episode:3 (3/3) are the app clusters.
    assert (app.n_clusters, scr.n_clusters) == (3, 5)
    assert (app.n_resamples, app.seed) == (400, 3)
    for interval in (app, scr):
        assert 0.0 <= interval.ci_low <= 7 / 12 <= interval.ci_high <= 1.0
    assert needs.wilson_low < 7 / 12 < needs.wilson_high

    icon = next(p for p in report.populations if p.population == "icon_like")
    assert (icon.intervals["app"].n_clusters, icon.intervals["screen"].n_clusters) == (2, 2)
    interactive = next(p for p in report.populations if p.population == "interactive_image")
    assert interactive.coverage is None
    assert interactive.intervals["app"].ci_low is None

    debt = {d.population: d for d in report.debt}
    assert (debt["needs_label"].screens_with_candidates, debt["needs_label"].screens_with_debt) == (
        5,
        3,
    )
    assert [(r.role, r.candidates, r.labelled) for r in report.roles] == [("image", 12, 7)]


def test_header_states_identified_apps_and_no_app_episodes_separately(ac_audit):
    # P08: the header said "1 apps"-style totals, which read as if they included the no-app
    # clusters. It now gives identified apps and no-app episodes separately; the App clusters
    # column (3 = com.a, episode:2, episode:3) stays as it was.
    report = build_report(load_audit(ac_audit, "AC synthetic"), n_resamples=100)
    assert (report.n_apps, report.n_no_app) == (1, 2)
    md = format_markdown([report])
    assert (
        "6 screens, 60 nodes (48 included: visible, positive area), 1 identified app and "
        "2 episodes with no identified app." in md
    )
    assert "can be smaller than the identified apps plus the episodes with no identified" in md
    assert "| needs_label | 12 | 7 | 58.33 |" in md and "| 3 |" in md


def test_header_counts_screens_with_no_app_outside_androidcontrol(tmp_path):
    # Every screen has an app (as in Rico), then one screen without: its own cluster.
    screens = [screen("10", "com.a", (1, 2)), screen("11", "com.b", (0, 1))]
    out = tmp_path / "rico_like"
    write_outputs(coverage(screens, dataset="rico"), out, source="synthetic")
    md = format_markdown([build_report(load_audit(out), n_resamples=50)])
    assert "2 identified apps and 0 screens with no identified app." in md

    screens.append(screen("12", "", (1, 1)))
    write_outputs(coverage(screens, dataset="rico"), out, source="synthetic")
    report = build_report(load_audit(out), n_resamples=50)
    assert (report.n_apps, report.n_no_app) == (2, 1)
    assert "2 identified apps and 1 screen with no identified app." in format_markdown([report])


def test_intervals_do_not_depend_on_the_other_corpora(ac_audit):
    alone = build_report(load_audit(ac_audit), n_resamples=300)
    again = build_report(load_audit(ac_audit), n_resamples=300)
    assert alone.populations == again.populations


def test_write_report_files(ac_audit, tmp_path):
    report = build_report(load_audit(ac_audit, "AC synthetic"), n_resamples=200)
    paths = write_report([report], tmp_path / "out")
    assert [p.name for p in paths] == [
        "report.md",
        "coverage.csv",
        "roles.csv",
        "screens_with_debt.csv",
    ]
    md = paths[0].read_text(encoding="utf-8")
    assert "## AC synthetic" in md
    assert "| needs_label | 12 | 7 | 58.33 |" in md
    assert "| image | 12 | 7 | 58.33 |" in md
    assert "| needs_label | 5 | 3 | 50.00 | 60.00 |" in md
    with paths[1].open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert [r["population"] for r in rows] == ["needs_label", "icon_like", "interactive_image"]
    assert rows[0]["app_clusters"] == "3" and rows[0]["screen_clusters"] == "5"
    assert rows[0]["n_resamples"] == "200" and rows[0]["seed"] == "20260908"
    assert rows[2]["coverage"] == "" and rows[2]["app_ci_low"] == ""
    assert format_markdown([report]).startswith("# a11ydebt coverage report")
    assert "seeded with the seed.[^seeds]" in md
    assert md.rstrip().endswith("docs/reproduction-bootstrap.md).")
    assert md.count("[^seeds]: Intervals use independent seeds.") == 1


def test_mismatched_files_are_refused(ac_audit):
    summary_path = ac_audit / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["corpus"]["populations"]["needs_label"]["labelled"] += 1
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    with pytest.raises(ValueError, match="does not add up"):
        load_audit(ac_audit)


def test_cli_report_on_the_rico_fixtures(rico_dir, ac_audit, tmp_path, capsys):
    audit = tmp_path / "rico_audit"
    assert main(["audit", "rico", str(rico_dir), "--out", str(audit), "--quiet"]) == 0
    capsys.readouterr()
    out = tmp_path / "report"
    args = ["report", str(audit), f"AC synthetic={ac_audit}", "--out", str(out)]
    assert main([*args, "--n-resamples", "100", "--seed", "5"]) == 0
    printed = capsys.readouterr().out
    assert "## rico" in printed and "## AC synthetic" in printed
    assert "| needs_label | 11 | 3 | 27.27 |" in printed
    assert "seed 5" in printed
    with (out / "coverage.csv").open(encoding="utf-8") as fh:
        corpora = [r["corpus"] for r in csv.DictReader(fh)]
    assert corpora == ["rico"] * 3 + ["AC synthetic"] * 3


def test_cli_report_errors(ac_audit, tmp_path, capsys):
    assert main(["report", str(ac_audit), str(ac_audit), "--out", str(tmp_path)]) == 2
    assert "share a label" in capsys.readouterr().err
    assert main(["report", str(tmp_path / "missing"), "--out", str(tmp_path)]) == 2
    assert "not found" in capsys.readouterr().err
    assert main(["report", str(ac_audit), "--n-resamples", "0"]) == 2
    assert main(["report", str(ac_audit), "--conf", "1.5"]) == 2
