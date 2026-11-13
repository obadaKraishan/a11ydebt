"""The per-screen statistics dataset: what goes in, what comes out, and the free-text boundary.

Synthetic inputs only. The last tests check the real build output when it is present locally
(space/data/ is gitignored, so they skip in CI).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

pa = pytest.importorskip("pyarrow")
pq = pytest.importorskip("pyarrow.parquet")
bs = pytest.importorskip("build_stats")

ROOT = Path(__file__).resolve().parents[1]
REAL = ROOT / "space" / "data"

RICO_HEADER = [
    "screen_id",
    "app",
    "n_nodes",
    "n_included",
    "needs_label_candidates",
    "needs_label_labelled",
    "needs_label_unlabelled",
    "needs_label_coverage",
    "icon_like_candidates",
    "icon_like_labelled",
    "icon_like_unlabelled",
    "icon_like_coverage",
    "interactive_image_candidates",
    "interactive_image_labelled",
    "interactive_image_unlabelled",
    "interactive_image_coverage",
]


def write_rico(path: Path, rows: list[list[object]]) -> Path:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(RICO_HEADER)
        writer.writerows(rows)
    return path


def rico_rows() -> list[list[object]]:
    # screen 10 is listed before 2 on purpose: the output sorts numerically.
    return [
        [10, "com.example.alpha", 40, 30, 4, 1, 3, 0.25, 2, 1, 1, 0.5, 2, 1, 1, 0.5],
        [2, "com.example.beta", 12, 0, 0, 0, 0, "", 0, 0, 0, "", 0, 0, 0, ""],
        [7, "com.example.alpha", 25, 20, 5, 5, 0, 1.0, 1, 1, 0, 1.0, 1, 1, 0, 1.0],
    ]


def write_ac(folder: Path, shard: int, rows: list[dict[str, object]]) -> Path:
    """A Kaggle screens/*.parquet file, with the text columns the builder must leave behind."""
    folder.mkdir(parents=True, exist_ok=True)
    name = f"android_control-{shard:05d}-of-00020"
    columns: dict[str, list] = {
        "screen_id": [],
        "episode_id": [],
        "step_index": [],
        "shard": [],
        "split": [],
        "app": [],
        "n_nodes": [],
        "n_included": [],
        "needs_label_candidates": [],
        "needs_label_labelled": [],
        "icon_like_candidates": [],
        "icon_like_labelled": [],
        "interactive_image_candidates": [],
        "interactive_image_labelled": [],
        "needs_label_image_candidates": [],
        "needs_label_image_labelled": [],
    }
    for row in rows:
        episode, step = row["episode"], row["step"]
        values = {
            "screen_id": row.get("screen_id", f"{episode}_{step}"),
            "episode_id": episode,
            "step_index": step,
            "shard": row.get("shard_name", name),
            "split": "train",
            "app": "com.example.secret",
            "n_nodes": row["nodes"],
            "n_included": row["included"],
            "needs_label_candidates": row["need"],
            "needs_label_labelled": row["need_lab"],
            "icon_like_candidates": row["icon"],
            "icon_like_labelled": row["icon_lab"],
            "interactive_image_candidates": 0,
            "interactive_image_labelled": 0,
            "needs_label_image_candidates": 0,
            "needs_label_image_labelled": 0,
        }
        for key, value in values.items():
            columns[key].append(value)
    path = folder / f"{name}.parquet"
    pq.write_table(pa.table(columns), path)
    return path


def ac_row(episode: int, step: int, need: int = 3, need_lab: int = 1, **extra) -> dict:
    row = {
        "episode": episode,
        "step": step,
        "nodes": 50,
        "included": 40,
        "need": need,
        "need_lab": need_lab,
        "icon": 2,
        "icon_lab": 2,
    }
    row.update(extra)
    return row


@pytest.fixture
def inputs(tmp_path: Path) -> tuple[Path, list[Path]]:
    rico = write_rico(tmp_path / "screens.csv", rico_rows())
    run1 = tmp_path / "run1" / "screens"
    run2 = tmp_path / "run2" / "screens"
    write_ac(run1, 0, [ac_row(5, 1), ac_row(5, 0, need=0, need_lab=0)])
    write_ac(run2, 12, [ac_row(3, 0, need=4, need_lab=4)])
    return rico, [run1, run2]


def test_build_writes_ids_and_counts_only(tmp_path, inputs):
    rico, ac = inputs
    info = bs.build(rico, ac, tmp_path / "out")
    for name in ("rico", "androidcontrol"):
        table = pq.read_table(tmp_path / "out" / f"{name}.parquet")
        assert table.schema.equals(bs.SCHEMA)
        bs.check_no_free_text(table)
        assert "app" not in table.column_names and "split" not in table.column_names
    assert info["files"]["rico"]["rows"] == 3
    assert info["files"]["androidcontrol"]["rows"] == 3
    saved = json.loads((tmp_path / "out" / "build_info.json").read_text(encoding="utf-8"))
    assert saved["schema"] == list(bs.COLUMNS)


def test_rico_rows(tmp_path, inputs):
    rico, ac = inputs
    bs.build(rico, ac, tmp_path / "out")
    rows = pq.read_table(tmp_path / "out" / "rico.parquet").to_pylist()
    assert [r["screen_id"] for r in rows] == ["2", "7", "10"]
    first, _, last = rows
    assert first["needs_label_coverage"] is None and first["episode_id"] is None
    assert last["needs_label_unlabelled"] == 3 and last["needs_label_coverage"] == 0.25
    assert all(r["in_paper_sample"] for r in rows)


def test_androidcontrol_rows(tmp_path, inputs):
    rico, ac = inputs
    bs.build(rico, ac, tmp_path / "out")
    rows = pq.read_table(tmp_path / "out" / "androidcontrol.parquet").to_pylist()
    assert [r["screen_id"] for r in rows] == ["3_0", "5_0", "5_1"]
    by_id = {r["screen_id"]: r for r in rows}
    assert by_id["3_0"]["shard"] == 12 and not by_id["3_0"]["in_paper_sample"]
    assert by_id["5_1"]["shard"] == 0 and by_id["5_1"]["in_paper_sample"]
    assert by_id["5_1"]["needs_label_unlabelled"] == 2
    assert by_id["5_0"]["needs_label_coverage"] is None


def test_totals_split_the_paper_sample(tmp_path, inputs):
    rico, ac = inputs
    info = bs.build(rico, ac, tmp_path / "out")
    paper = info["totals"]["androidcontrol_paper_sample"]
    everything = info["totals"]["androidcontrol"]
    assert paper["screens"] == 2 and everything["screens"] == 3
    assert paper["needs_label"] == {
        "candidates": 3,
        "labelled": 1,
        "coverage": round(1 / 3, 6),
        "screens_with_debt": 1,
    }
    assert info["totals"]["rico"]["n_included"] == 50


def test_node_tables_are_refused(tmp_path, inputs):
    rico, _ = inputs
    nodes = tmp_path / "run1" / "nodes"
    nodes.mkdir(parents=True)
    with pytest.raises(bs.BuildError, match="UI text"):
        bs.build(rico, [nodes], tmp_path / "out")


def test_bad_inputs_are_refused(tmp_path):
    bad_id = write_rico(
        tmp_path / "a.csv", [["home", "x", 1, 1, 0, 0, 0, "", 0, 0, 0, "", 0, 0, 0, ""]]
    )
    with pytest.raises(bs.BuildError, match="numbers"):
        bs.read_rico(bad_id)
    too_many = write_rico(
        tmp_path / "b.csv", [[1, "x", 9, 9, 2, 3, 0, "", 0, 0, 0, "", 0, 0, 0, ""]]
    )
    with pytest.raises(bs.BuildError, match="outside"):
        bs.read_rico(too_many)
    mismatch = write_ac(tmp_path / "c", 1, [ac_row(4, 2, screen_id="4_3")])
    with pytest.raises(bs.BuildError, match="episode_step"):
        bs.read_androidcontrol([mismatch])
    bad_shard = write_ac(tmp_path / "d", 1, [ac_row(4, 2, shard_name="somewhere/else")])
    with pytest.raises(bs.BuildError, match="shard"):
        bs.read_androidcontrol([bad_shard])


def _valid_table() -> pa.Table:
    rows = {name: [] for name in bs.COLUMNS}
    rows.update(dataset=["rico"], screen_id=["1"], episode_id=[None], step_index=[None])
    rows.update(shard=[None], in_paper_sample=[True], n_nodes=[3], n_included=[2])
    for pop in bs.POPULATIONS:
        rows.update(
            {
                f"{pop}_candidates": [1],
                f"{pop}_labelled": [0],
                f"{pop}_unlabelled": [1],
                f"{pop}_coverage": [0.0],
            }
        )
    return pa.Table.from_pydict(rows, schema=bs.SCHEMA)


def test_free_text_guard_accepts_ids_and_counts():
    bs.check_no_free_text(_valid_table())


@pytest.mark.parametrize(
    "value",
    ["Search", "com.example.app", "1 2", "12_", "_3", "data/raw/rico/1.json", "", "١٢"],
)
def test_free_text_guard_rejects_text_in_id_columns(value):
    table = _valid_table()
    table = table.set_column(1, bs.SCHEMA.field("screen_id"), pa.array([value]))
    with pytest.raises(bs.BuildError, match="not an id"):
        bs.check_no_free_text(table)


def test_free_text_guard_rejects_an_extra_text_column():
    table = _valid_table().append_column("content_desc", pa.array(["Navigate up"]))
    with pytest.raises(bs.BuildError):
        bs.check_no_free_text(table)


def test_free_text_guard_rejects_a_dataset_name_it_does_not_know():
    table = _valid_table()
    table = table.set_column(0, bs.SCHEMA.field("dataset"), pa.array(["rico-semantics"]))
    with pytest.raises(bs.BuildError, match="not an id"):
        bs.check_no_free_text(table)


# ------------------------------------------------------------------ the real build, if present

#: The paper's Table 1 (Rico, and AndroidControl's 10 shards).
PAPER = {
    "rico": {"n_included": 2_862_639, "needs": (502_585, 89_146), "icon": (127_552, 42_341)},
    "ac10": {"n_included": 6_831_063, "needs": (1_462_544, 837_536), "icon": (194_529, 122_074)},
}


def _real(name: str) -> pa.Table:
    path = REAL / f"{name}.parquet"
    if not path.is_file():
        pytest.skip(f"space/data/{name}.parquet is not built in this checkout")
    return pq.read_table(path)


@pytest.mark.parametrize("name", ["rico", "androidcontrol"])
def test_real_build_holds_no_free_text(name):
    bs.check_no_free_text(_real(name))


def test_real_build_matches_the_paper():
    rico = bs.totals(_real("rico"))
    ac = _real("androidcontrol")
    ac10 = bs.totals(ac.filter(ac.column("in_paper_sample")))
    for got, want in ((rico, PAPER["rico"]), (ac10, PAPER["ac10"])):
        assert got["n_included"] == want["n_included"]
        need, icon = got["needs_label"], got["icon_like"]
        assert (need["candidates"], need["labelled"]) == want["needs"]
        assert (icon["candidates"], icon["labelled"]) == want["icon"]
    assert rico["screens"] == 66_261 and ac10["screens"] == 49_892
    assert ac.num_rows == 99_131


def test_dataset_card_totals_match_the_real_build():
    card = (ROOT / "space" / "dataset_card.md").read_text(encoding="utf-8")
    ac = _real("androidcontrol")
    splits = {
        "`rico`, all": bs.totals(_real("rico")),
        "`androidcontrol`, the": bs.totals(ac.filter(ac.column("in_paper_sample"))),
        "`androidcontrol`, all": bs.totals(ac),
    }
    for label, t in splits.items():
        need, icon = t["needs_label"], t["icon_like"]
        cells = (
            f"{t['n_included']:,} | {need['candidates']:,} | {need['labelled']:,} | "
            f"{100 * need['coverage']:.2f}% | {icon['candidates']:,} | "
            f"{100 * icon['coverage']:.2f}% |"
        )
        line = next(row for row in card.splitlines() if row.startswith(f"| {label}"))
        assert f"{t['screens']:,}" in line
        assert line.endswith(cells), f"{label}: the card says {line!r}"
