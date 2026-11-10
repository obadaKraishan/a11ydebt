"""Read the AndroidControl Kaggle kernel's outputs back into a CoverageReport.

The kernel (``kaggle/androidcontrol_parse``) writes ``screens/<shard>.parquet`` (one row per
screen), ``nodes/<shard>.parquet``, ``shards/<shard>.json`` markers and ``run_summary.json``.
``read_androidcontrol_outputs(path)`` turns the screen rows into the same report the CLI prints
for a local audit. It needs pyarrow (``pip install pyarrow``), which is imported only here.
"""

from __future__ import annotations

import json
from pathlib import Path

from a11ydebt.counts import LABEL_ROLES, POPULATIONS
from a11ydebt.coverage import Counts, CoverageReport, ParseFailure, ScreenCoverage, coverage

__all__ = ["read_androidcontrol_outputs", "screen_files"]


def screen_files(path: str | Path) -> list[Path]:
    """Every ``screens/*.parquet`` under ``path`` (the layout `kaggle kernels output` creates)."""
    return sorted(p for p in Path(path).rglob("*.parquet") if p.parent.name == "screens")


def _screen(row: dict) -> ScreenCoverage:
    roles = {
        r: Counts(
            candidates=row[f"needs_label_{r}_candidates"], labelled=row[f"needs_label_{r}_labelled"]
        )
        for r in LABEL_ROLES
        if row[f"needs_label_{r}_candidates"]
    }
    return ScreenCoverage(
        screen_id=row["screen_id"],
        app=row["app"],
        n_nodes=row["n_nodes"],
        n_included=row["n_included"],
        populations={
            p: Counts(candidates=row[f"{p}_candidates"], labelled=row[f"{p}_labelled"])
            for p in POPULATIONS
        },
        needs_label_by_role=roles,
    )


def read_androidcontrol_outputs(path: str | Path) -> CoverageReport:
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:  # pragma: no cover - depends on the environment
        raise ImportError("reading Kaggle outputs needs pyarrow: pip install pyarrow") from exc
    root = Path(path)
    files = screen_files(root)
    if not files:
        raise FileNotFoundError(f"no screens/*.parquet under {root}")
    screens = [_screen(row) for f in files for row in pq.read_table(f).to_pylist()]

    failures: list[ParseFailure] = []
    for marker in sorted(p for p in root.rglob("*.json") if p.parent.name == "shards"):
        info = json.loads(marker.read_text(encoding="utf-8"))
        for f in info.get("failures", []):
            failures.append(
                ParseFailure(
                    screen_id=f"{info['name']}#record{f['record']}",
                    path=info["name"],
                    error=f["error"],
                )
            )
        if info.get("truncated"):
            failures.append(
                ParseFailure(
                    screen_id=f"{info['name']}#truncated", path=info["name"], error="TruncatedShard"
                )
            )
    summary_path = next(root.rglob("run_summary.json"), None)
    if summary_path is not None:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        for f in summary.get("shards_failed", []):
            failures.append(
                ParseFailure(screen_id=f"{f['name']}#download", path=f["name"], error=f["error"])
            )
    return coverage(screens, dataset="androidcontrol", failures=failures)
