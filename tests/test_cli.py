from __future__ import annotations

import csv
import json

import pytest

from a11ydebt import __version__
from a11ydebt.cli import main


def test_audit_rico_prints_the_table_and_writes_outputs(rico_dir, tmp_path, capsys):
    out_dir = tmp_path / "out"
    assert main(["audit", "rico", str(rico_dir), "--out", str(out_dir), "--quiet"]) == 0
    printed = capsys.readouterr().out
    assert "3 screens, 2 apps, 25 nodes (21 included" in printed
    assert "27.27%" in printed  # needs_label coverage, 3/11
    assert "33.33%" in printed  # icon_like and interactive_image coverage, 2/6

    with (out_dir / "screens.csv").open(encoding="utf-8") as fh:
        screens = list(csv.DictReader(fh))
    assert [row["screen_id"] for row in screens] == ["101", "102", "103"]
    assert screens[0]["needs_label_candidates"] == "3"
    assert screens[0]["needs_label_labelled"] == "1"
    assert screens[0]["icon_like_coverage"] == "0.000000"

    with (out_dir / "apps.csv").open(encoding="utf-8") as fh:
        apps = {row["app"]: row for row in csv.DictReader(fh)}
    assert set(apps) == {"com.example.weather", "org.example.notes"}
    assert apps["org.example.notes"]["n_screens"] == "2"
    assert apps["org.example.notes"]["needs_label_screens_with_debt"] == "2"

    summary = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["a11ydebt_version"] == __version__
    assert summary["corpus"]["populations"]["icon_like"]["candidates"] == 6
    assert summary["corpus"]["needs_label_by_role"]["image"] == {
        "candidates": 6,
        "labelled": 2,
        "unlabelled": 4,
        "coverage": pytest.approx(1 / 3),
        "debt": pytest.approx(2 / 3),
    }
    assert summary["failures"] == []


def test_missing_data_is_a_clear_error(tmp_path, capsys):
    assert main(["audit", "rico", str(tmp_path), "--quiet"]) == 2
    assert "no screen JSON files" in capsys.readouterr().err


def test_package_metadata_version_is_the_module_version():
    from importlib.metadata import version

    assert version("a11ydebt") == __version__  # pyproject reads it from a11ydebt/__init__.py


def test_version(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])
    assert exit_info.value.code == 0
    assert __version__ in capsys.readouterr().out
