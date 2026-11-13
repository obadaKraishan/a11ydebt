"""Build the per-screen statistics dataset from existing a11ydebt audit outputs.

One row per screen, with only identifiers and counts: the dataset, the screen (and, for
AndroidControl, the episode, step and shard), the element counts and the two coverage measures
the AISSA 2026 paper reports (``needs_label`` and ``icon_like``). No app package, no split, no
class names, no text of any kind.

Inputs are the tables a11ydebt already writes:

* Rico: ``screens.csv`` from ``a11ydebt audit rico``.
* AndroidControl: the ``screens/*.parquet`` files from the Kaggle kernel in
  ``kaggle/androidcontrol_parse/`` (run 1 is shards 00000 to 00009, the paper's sample; run 2
  is shards 00010 to 00019). Only named count and id columns are read. The kernel's
  ``nodes/`` tables hold UI text and are refused.

Usage (from the repository root)::

    uv run python space/build_stats.py \\
        --rico data/interim/audit_rico/screens.csv \\
        --androidcontrol data/interim/androidcontrol/run1/screens \\
                         data/interim/androidcontrol/run2/screens \\
        --out space/data

It writes ``rico.parquet``, ``androidcontrol.parquet`` and ``build_info.json`` (row counts,
corpus totals and output checksums) to ``--out``.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections.abc import Iterable
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

#: Shards 00000 to 00009 are the sample the AISSA 2026 paper analyses.
PAPER_SHARDS = range(10)
POPULATIONS = ("needs_label", "icon_like")
DATASETS = ("rico", "androidcontrol")

SCHEMA = pa.schema(
    [
        pa.field("dataset", pa.string(), nullable=False),
        pa.field("screen_id", pa.string(), nullable=False),
        pa.field("episode_id", pa.int64()),
        pa.field("step_index", pa.int32()),
        pa.field("shard", pa.int16()),
        pa.field("in_paper_sample", pa.bool_(), nullable=False),
        pa.field("n_nodes", pa.int32(), nullable=False),
        pa.field("n_included", pa.int32(), nullable=False),
        *(
            field
            for pop in POPULATIONS
            for field in (
                pa.field(f"{pop}_candidates", pa.int32(), nullable=False),
                pa.field(f"{pop}_labelled", pa.int32(), nullable=False),
                pa.field(f"{pop}_unlabelled", pa.int32(), nullable=False),
                pa.field(f"{pop}_coverage", pa.float64()),
            )
        ),
    ]
)
COLUMNS: tuple[str, ...] = tuple(SCHEMA.names)
#: The only string columns, and the values each may hold. Everything else is numeric or boolean.
#: ASCII digits only: Python's \d would also accept other scripts' digits.
STRING_PATTERNS: dict[str, re.Pattern[str]] = {
    "dataset": re.compile(r"(rico|androidcontrol)"),
    "screen_id": re.compile(r"[0-9]+(_[0-9]+)?"),
}

_COUNT_INPUTS = (
    "n_nodes",
    "n_included",
    *(f"{pop}_{kind}" for pop in POPULATIONS for kind in ("candidates", "labelled")),
)
_AC_COLUMNS = ("screen_id", "episode_id", "step_index", "shard", *_COUNT_INPUTS)
_SHARD = re.compile(r"android_control-([0-9]{5})-of-[0-9]{5}")
_DIGITS = re.compile(r"[0-9]+")


class BuildError(ValueError):
    """The inputs are not what this script expects; nothing is written."""


def _empty() -> dict[str, list]:
    return {name: [] for name in COLUMNS}


def _add_counts(rows: dict[str, list], counts: dict[str, int], where: str) -> None:
    for name in ("n_nodes", "n_included"):
        rows[name].append(counts[name])
    for pop in POPULATIONS:
        cand, lab = counts[f"{pop}_candidates"], counts[f"{pop}_labelled"]
        if not 0 <= lab <= cand:
            raise BuildError(f"{where}: {pop} labelled {lab} is outside 0..{cand}")
        rows[f"{pop}_candidates"].append(cand)
        rows[f"{pop}_labelled"].append(lab)
        rows[f"{pop}_unlabelled"].append(cand - lab)
        rows[f"{pop}_coverage"].append(lab / cand if cand else None)
    if not 0 <= counts["n_included"] <= counts["n_nodes"]:
        raise BuildError(f"{where}: n_included is outside 0..n_nodes")


def read_rico(path: Path) -> pa.Table:
    """Rows from an ``a11ydebt audit rico`` screens.csv. The ``app`` column is not read."""
    rows = _empty()
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        missing = {"screen_id", *_COUNT_INPUTS} - set(reader.fieldnames or ())
        if missing:
            raise BuildError(f"{path.name}: missing columns {sorted(missing)}")
        for line, record in enumerate(reader, start=2):
            screen_id = (record["screen_id"] or "").strip()
            if not _DIGITS.fullmatch(screen_id):
                raise BuildError(f"{path.name}:{line}: Rico screen ids are numbers")
            try:
                counts = {name: int(record[name]) for name in _COUNT_INPUTS}
            except (TypeError, ValueError) as exc:
                raise BuildError(f"{path.name}:{line}: a count is not an integer") from exc
            rows["dataset"].append("rico")
            rows["screen_id"].append(screen_id)
            rows["episode_id"].append(None)
            rows["step_index"].append(None)
            rows["shard"].append(None)
            rows["in_paper_sample"].append(True)
            _add_counts(rows, counts, f"{path.name}:{line}")
    order = sorted(range(len(rows["screen_id"])), key=lambda i: int(rows["screen_id"][i]))
    return _table({name: [values[i] for i in order] for name, values in rows.items()})


def androidcontrol_files(paths: Iterable[Path]) -> list[Path]:
    """The screen Parquet files under each path (a file or a folder of them)."""
    files: list[Path] = []
    for path in paths:
        if "nodes" in path.parts:
            raise BuildError(f"{path}: node tables hold UI text and are never read")
        files.extend(sorted(path.glob("*.parquet")) if path.is_dir() else [path])
    if not files:
        raise BuildError("no AndroidControl screen Parquet files found")
    return files


def read_androidcontrol(paths: Iterable[Path]) -> pa.Table:
    """Rows from the Kaggle kernel's screens/*.parquet. Only id and count columns are read."""
    rows = _empty()
    for path in androidcontrol_files(paths):
        names = set(pq.read_schema(path).names)
        missing = set(_AC_COLUMNS) - names
        if missing:
            raise BuildError(f"{path.name}: missing columns {sorted(missing)}")
        data = pq.read_table(path, columns=list(_AC_COLUMNS)).to_pydict()
        for i, screen_id in enumerate(data["screen_id"]):
            episode, step = int(data["episode_id"][i]), int(data["step_index"][i])
            if screen_id != f"{episode}_{step}":
                raise BuildError(f"{path.name}: screen {screen_id!r} is not episode_step")
            match = _SHARD.fullmatch(data["shard"][i] or "")
            if not match:
                raise BuildError(f"{path.name}: unexpected shard name")
            shard = int(match.group(1))
            rows["dataset"].append("androidcontrol")
            rows["screen_id"].append(screen_id)
            rows["episode_id"].append(episode)
            rows["step_index"].append(step)
            rows["shard"].append(shard)
            rows["in_paper_sample"].append(shard in PAPER_SHARDS)
            _add_counts(rows, {n: int(data[n][i]) for n in _COUNT_INPUTS}, path.name)
    order = sorted(
        range(len(rows["screen_id"])), key=lambda i: (rows["episode_id"][i], rows["step_index"][i])
    )
    return _table({name: [values[i] for i in order] for name, values in rows.items()})


def _table(rows: dict[str, list]) -> pa.Table:
    table = pa.Table.from_pydict(rows, schema=SCHEMA)
    ids = table.column("screen_id").to_pylist()
    if len(set(ids)) != len(ids):
        raise BuildError("duplicate screen ids")
    check_no_free_text(table)
    return table


def check_no_free_text(table: pa.Table) -> None:
    """Fail unless the columns are exactly the schema's and every string is an id or a dataset
    name. This is the redistribution boundary: no UI text, app names or paths can pass."""
    if tuple(table.column_names) != COLUMNS:
        raise BuildError(f"unexpected columns: {table.column_names}")
    for field in table.schema:
        if pa.types.is_string(field.type) or pa.types.is_large_string(field.type):
            pattern = STRING_PATTERNS.get(field.name)
            if pattern is None:
                raise BuildError(f"column {field.name!r} holds text and is not an id column")
            for value in table.column(field.name).to_pylist():
                if value is None or not pattern.fullmatch(value):
                    raise BuildError(f"column {field.name!r} holds a value that is not an id")
        elif not (
            pa.types.is_integer(field.type)
            or pa.types.is_floating(field.type)
            or pa.types.is_boolean(field.type)
        ):
            raise BuildError(f"column {field.name!r} has type {field.type}")


def totals(table: pa.Table) -> dict[str, object]:
    """Corpus totals, the numbers the paper's Table 1 reports."""
    out: dict[str, object] = {"screens": table.num_rows}
    for name in ("n_nodes", "n_included"):
        out[name] = sum(table.column(name).to_pylist())
    for pop in POPULATIONS:
        cand = sum(table.column(f"{pop}_candidates").to_pylist())
        lab = sum(table.column(f"{pop}_labelled").to_pylist())
        debt = sum(1 for u in table.column(f"{pop}_unlabelled").to_pylist() if u > 0)
        out[pop] = {
            "candidates": cand,
            "labelled": lab,
            "coverage": round(lab / cand, 6) if cand else None,
            "screens_with_debt": debt,
        }
    return out


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(rico: Path, androidcontrol: list[Path], out: Path) -> dict[str, object]:
    tables = {"rico": read_rico(rico), "androidcontrol": read_androidcontrol(androidcontrol)}
    out.mkdir(parents=True, exist_ok=True)
    info: dict[str, object] = {"schema": list(COLUMNS), "files": {}, "totals": {}}
    for name, table in tables.items():
        target = out / f"{name}.parquet"
        pq.write_table(table, target, compression="zstd")
        info["files"][name] = {"rows": table.num_rows, "sha256": _sha256(target)}
        info["totals"][name] = totals(table)
    ac = tables["androidcontrol"]
    paper = ac.filter(ac.column("in_paper_sample"))
    info["totals"]["androidcontrol_paper_sample"] = totals(paper)
    (out / "build_info.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    return info


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--rico", type=Path, required=True, help="screens.csv from audit rico")
    parser.add_argument(
        "--androidcontrol",
        type=Path,
        nargs="+",
        required=True,
        help="the Kaggle kernel's screens/ folders or files",
    )
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "data")
    args = parser.parse_args(argv)
    try:
        info = build(args.rico, args.androidcontrol, args.out)
    except BuildError as exc:
        print(f"build_stats: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(info["totals"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
