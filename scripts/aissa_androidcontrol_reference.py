"""Build the AISSA AndroidControl reference that run 1 is compared against. Dev-only.

    uv run --with pyarrow python scripts/aissa_androidcontrol_reference.py AISSA_REPO OUT_DIR

AISSA_REPO is the accessibility-debt-agents checkout (read only; nothing there is written).
OUT_DIR is normally data/interim/aissa_reference. It writes:

  androidcontrol_shards.json        the 10 shards AISSA parsed (URL, bytes, SHA-256) and the
                                    episode ids found in each, plus AISSA's totals
  androidcontrol_parse_report.json  a copy of AISSA's parse report
  androidcontrol_episodes.parquet   a copy of AISSA's per-episode table
  androidcontrol_screens.parquet    per-screen counts derived from AISSA's node table
                                    (screens with zero nodes do not appear in it)
"""

from __future__ import annotations

import argparse
import json
import shutil
from collections import defaultdict
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

COMMIT = "97c0378"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("aissa_repo", type=Path)
    parser.add_argument("out_dir", type=Path)
    args = parser.parse_args(argv)
    repo, out = args.aissa_repo, args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    report_path = repo / "data/interim/androidcontrol_parse_report.json"
    episodes_path = repo / "data/processed/androidcontrol_episodes.parquet"
    nodes_path = repo / "data/processed/androidcontrol_nodes.parquet"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    manifest = json.loads(
        (repo / "data/raw/androidcontrol/download_manifest.json").read_text(encoding="utf-8")
    )

    episodes = pq.read_table(
        episodes_path, columns=["episode_id", "shard", "n_observations"]
    ).to_pylist()
    ids_by_shard: dict[str, list[int]] = defaultdict(list)
    for row in episodes:
        ids_by_shard[row["shard"]].append(int(row["episode_id"]))

    shards = []
    for name in report["shards_used"]:
        entry = manifest[name]
        shards.append(
            {
                "name": name,
                "url": entry["url"],
                "bytes": entry["bytes"],
                "sha256": entry["sha256"],
                "episodes": len(ids_by_shard[name]),
                "screens": sum(r["n_observations"] for r in episodes if r["shard"] == name),
                "episode_ids": sorted(ids_by_shard[name]),
            }
        )
    reference = {
        "source": f"accessibility-debt-agents commit {COMMIT}: {report_path.name}, "
        f"download_manifest.json and {episodes_path.name}",
        "shards": shards,
        "totals": report["totals"],
        "screens": sum(r["n_observations"] for r in episodes),
        "splits_json": {k: manifest["splits.json"][k] for k in ("url", "bytes", "sha256")},
    }
    (out / "androidcontrol_shards.json").write_text(
        json.dumps(reference, indent=1) + "\n", encoding="utf-8"
    )
    shutil.copy2(report_path, out / report_path.name)
    shutil.copy2(episodes_path, out / episodes_path.name)

    nodes = pq.read_table(
        nodes_path,
        columns=[
            "screen_uid",
            "episode_id",
            "step_index",
            "included",
            "needs_label",
            "icon_like",
            "label_status",
        ],
    )
    labelled = pc.equal(nodes["label_status"], "labelled")
    included = nodes["included"]
    needs = pc.and_(included, nodes["needs_label"])
    icon = pc.and_(included, nodes["icon_like"])
    table = pa.table(
        {
            "screen_uid": nodes["screen_uid"],
            "episode_id": nodes["episode_id"],
            "step_index": nodes["step_index"],
            "one": pa.array([1] * nodes.num_rows, pa.int32()),
            "inc": pc.cast(included, pa.int32()),
            "needs": pc.cast(needs, pa.int32()),
            "needs_lab": pc.cast(pc.and_(needs, labelled), pa.int32()),
            "icon": pc.cast(icon, pa.int32()),
            "icon_lab": pc.cast(pc.and_(icon, labelled), pa.int32()),
        }
    )
    grouped = table.group_by(["screen_uid", "episode_id", "step_index"]).aggregate(
        [(c, "sum") for c in ("one", "inc", "needs", "needs_lab", "icon", "icon_lab")]
    )
    screens = grouped.rename_columns(
        [
            "screen_uid",
            "episode_id",
            "step_index",
            "n_nodes",
            "n_included",
            "n_needs_label",
            "n_labelled",
            "n_icon_like",
            "n_icon_like_labelled",
        ]
    )
    pq.write_table(screens, out / "androidcontrol_screens.parquet", compression="zstd")

    n_screens = reference["screens"]
    print(
        f"shards: {len(shards)}, episodes: {len(episodes):,}, screens (observations): {n_screens:,}"
    )
    print(f"screens with at least one node in AISSA's node table: {screens.num_rows:,}")
    print(f"node rows aggregated: {nodes.num_rows:,}")
    print(f"wrote {out}/androidcontrol_shards.json, androidcontrol_screens.parquet and two copies")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
