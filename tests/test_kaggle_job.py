"""The Kaggle job and the kernel build, run locally on the synthetic shard over file:// URLs."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pq = pytest.importorskip("pyarrow.parquet")

from synthetic_tfrecord import standard_records, write_shard  # noqa: E402

KAGGLE = Path(__file__).resolve().parents[1] / "kaggle" / "androidcontrol_parse"
sys.path.insert(0, str(KAGGLE))

import build_kernel  # noqa: E402
import job  # noqa: E402

SHARD = "android_control-00000-of-00001"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def config(tmp_path):
    bucket = tmp_path / "bucket"
    bucket.mkdir()
    shard = write_shard(bucket / SHARD, standard_records())
    splits = bucket / "splits.json"
    splits.write_text(json.dumps({"train": [7], "test": [9]}), encoding="utf-8")
    return {
        "name": "test",
        "time_budget_s": 3600,
        "first_shard_estimate_s": 1,
        "splits_json": {
            "url": splits.as_uri(),
            "bytes": splits.stat().st_size,
            "sha256": sha256(splits),
        },
        "shards": [
            {
                "name": SHARD,
                "url": shard.as_uri(),
                "bytes": shard.stat().st_size,
                "sha256": sha256(shard),
            }
        ],
    }


def test_job_writes_screen_counts_candidate_nodes_and_a_marker(config, tmp_path):
    out, work = tmp_path / "out", tmp_path / "work"
    summary = job.run(config, out, work)
    assert summary["status"] == "complete"

    screens = pq.read_table(out / "screens" / f"{SHARD}.parquet").to_pylist()
    assert [r["screen_id"] for r in screens] == ["7_0", "7_1", "9_0"]
    assert [r["split"] for r in screens] == ["train", "train", "test"]
    assert [r["app"] for r in screens] == [
        "com.example.shop",
        "com.example.shop",
        "com.example.news",
    ]
    s70 = screens[0]
    assert (s70["n_nodes"], s70["n_included"]) == (7, 6)
    assert (s70["needs_label_candidates"], s70["needs_label_labelled"]) == (4, 2)
    assert (s70["icon_like_candidates"], s70["interactive_image_candidates"]) == (2, 1)
    assert (s70["needs_label_button_candidates"], s70["needs_label_button_labelled"]) == (2, 1)

    nodes = pq.read_table(out / "nodes" / f"{SHARD}.parquet").to_pylist()
    assert len(nodes) == 6  # included nodes in at least one population
    assert all(n["needs_label"] or n["icon_like"] or n["interactive_image"] for n in nodes)

    marker = json.loads((out / "shards" / f"{SHARD}.json").read_text(encoding="utf-8"))
    assert marker["download"]["verified"] == ["bytes", "sha256"]
    assert marker["totals"]["needs_label_candidates"] == 6
    assert marker["truncated"] is False
    assert not (work / SHARD).exists()  # the raw shard is deleted after parsing
    assert summary["totals"]["screens"] == 3
    assert summary["totals"]["needs_label_labelled"] == 2
    assert summary["totals"]["apps"] == 2


def test_job_resumes_by_skipping_finished_shards(config, tmp_path, capsys):
    out, work = tmp_path / "out", tmp_path / "work"
    job.run(config, out, work)
    first = (out / "shards" / f"{SHARD}.json").read_text(encoding="utf-8")
    again = job.run(config, out, work)
    assert "already done, skipping" in capsys.readouterr().out
    assert again["status"] == "complete"
    assert (out / "shards" / f"{SHARD}.json").read_text(encoding="utf-8") == first


def test_job_rejects_a_bad_checksum_and_leaves_no_marker(config, tmp_path, monkeypatch):
    monkeypatch.setattr(job.time, "sleep", lambda _s: None)
    config["shards"][0]["sha256"] = "0" * 64
    summary = job.run(config, tmp_path / "out", tmp_path / "work")
    assert summary["status"] == "incomplete"
    assert [f["name"] for f in summary["shards_failed"]] == [SHARD]
    assert not list((tmp_path / "out" / "shards").glob("*.json"))


def test_job_stops_cleanly_before_the_time_limit(config, tmp_path):
    summary = job.run(config, tmp_path / "out", tmp_path / "work", budget_s=0)
    assert summary["status"] == "incomplete"
    assert summary["stopped_before_time_limit"] is True
    assert summary["shards_remaining"] == [SHARD]


def test_built_kernel_metadata_and_local_run(config, tmp_path):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps(config), encoding="utf-8")
    build_dir = build_kernel.build(KAGGLE / "config_run1.json", tmp_path / "build")

    meta = json.loads((build_dir / "kernel-metadata.json").read_text(encoding="utf-8"))
    assert meta["id"] == "obadakraishan/a11ydebt-androidcontrol-run1"
    assert (
        meta["is_private"],
        meta["enable_gpu"],
        meta["enable_tpu"],
        meta["enable_internet"],
    ) == (
        True,
        False,
        False,
        True,
    )
    assert (meta["machine_shape"], meta["kernel_type"], meta["code_file"]) == (
        "",
        "script",
        "run.py",
    )
    assert meta["docker_image_pinning_type"] == "original"

    env = dict(
        os.environ,
        A11YDEBT_CONFIG=str(cfg_path),
        A11YDEBT_OUT=str(tmp_path / "kout"),
        A11YDEBT_WORK=str(tmp_path / "kwork"),
        A11YDEBT_SRC=str(tmp_path / "ksrc"),
        A11YDEBT_SKIP_PIP="1",
    )
    proc = subprocess.run(
        [sys.executable, "-I", str(build_dir / "run.py")],
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    summary = json.loads((tmp_path / "kout" / "run_summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "complete"
    assert summary["totals"]["screens"] == 3
    assert summary["build"]["config"] == "run1"
    assert summary["build"]["pyarrow_pin"] == "skipped"
    assert (
        tmp_path / "ksrc" / "a11ydebt" / "androidcontrol.py"
    ).is_file()  # the bundle, not the venv


def test_summarize_reads_the_kernel_outputs(config, tmp_path, capsys):
    from a11ydebt.cli import main

    out = tmp_path / "out"
    job.run(config, out, tmp_path / "work")
    capsys.readouterr()
    assert main(["summarize", "androidcontrol", str(out), "--out", str(tmp_path / "tables")]) == 0
    printed = capsys.readouterr().out
    assert "androidcontrol: 3 screens, 2 apps, 10 nodes (8 included" in printed
    summary = json.loads((tmp_path / "tables" / "summary.json").read_text(encoding="utf-8"))
    pops = {
        p: (c["candidates"], c["labelled"]) for p, c in summary["corpus"]["populations"].items()
    }
    assert pops == {"needs_label": (6, 2), "icon_like": (2, 1), "interactive_image": (2, 0)}
    roles = {
        r: (c["candidates"], c["labelled"])
        for r, c in summary["corpus"]["needs_label_by_role"].items()
    }
    assert roles == {"button": (2, 1), "image": (2, 1), "input": (1, 0), "other": (1, 0)}
    assert summary["failures"] == []


def test_summarize_reports_missing_outputs(tmp_path, capsys):
    from a11ydebt.cli import main

    assert main(["summarize", "androidcontrol", str(tmp_path)]) == 2
    assert "no screens/*.parquet" in capsys.readouterr().err
