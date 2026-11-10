"""Kaggle job: parse AndroidControl shards into per-screen counts and candidate-node rows.

Inside Kaggle it runs from the generated ``run.py`` (see ``build_kernel.py``), which puts the
a11ydebt modules on ``sys.path`` first. Locally (tests, dry runs):

    python job.py --config CONFIG.json --out OUT_DIR --work WORK_DIR [--budget-s SECONDS]

For each shard in the config, in order:
  1. Skip it if ``OUT_DIR/shards/<name>.json`` exists (the checkpoint marker).
  2. Stop cleanly if the time left is under 1.5 times the slowest shard so far.
  3. Download it over HTTPS to WORK_DIR (not to the saved output) and verify bytes and checksum.
  4. Parse it with a11ydebt and write ``screens/<name>.parquet`` (one row per screen) and
     ``nodes/<name>.parquet`` (only nodes in at least one population), then the marker.
  5. Delete the raw shard before fetching the next one.
Finally it writes ``run_summary.json`` with the status, the totals, the versions and the timings.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import platform
import sys
import time
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from a11ydebt import __version__
from a11ydebt.androidcontrol import ShardReader, load_splits
from a11ydebt.counts import LABEL_ROLES, POPULATIONS, count_screen

DEFAULT_BUDGET_S = 11 * 3600  # Kaggle stops CPU sessions at 12 hours
CHUNK = 8 << 20

SCREEN_SCHEMA = pa.schema(
    [
        ("screen_id", pa.string()),
        ("episode_id", pa.int64()),
        ("step_index", pa.int32()),
        ("shard", pa.string()),
        ("split", pa.string()),
        ("app", pa.string()),
        ("n_nodes", pa.int32()),
        ("n_included", pa.int32()),
        *[(f"{p}_{k}", pa.int32()) for p in POPULATIONS for k in ("candidates", "labelled")],
        *[
            (f"needs_label_{r}_{k}", pa.int32())
            for r in LABEL_ROLES
            for k in ("candidates", "labelled")
        ],
    ]
)
NODE_SCHEMA = pa.schema(
    [
        ("screen_id", pa.string()),
        ("episode_id", pa.int64()),
        ("step_index", pa.int32()),
        ("window_index", pa.int32()),
        ("window_layer", pa.int32()),
        ("node_uid", pa.int32()),
        ("depth", pa.int32()),
        ("class_name", pa.string()),
        ("role", pa.string()),
        ("resource_id", pa.string()),
        ("content_desc", pa.string()),
        ("text", pa.string()),
        ("hint_text", pa.string()),
        ("clickable", pa.bool_()),
        ("long_clickable", pa.bool_()),
        ("focusable", pa.bool_()),
        ("enabled", pa.bool_()),
        ("x1", pa.int32()),
        ("y1", pa.int32()),
        ("x2", pa.int32()),
        ("y2", pa.int32()),
        ("labelled", pa.bool_()),
        ("needs_label", pa.bool_()),
        ("icon_like", pa.bool_()),
        ("interactive_image", pa.bool_()),
    ]
)


def log(message: str) -> None:
    print(f"[{datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S}Z] {message}", flush=True)


# ------------------------------------------------------------------ download


def _check(entry: dict[str, Any], size: int, sha256: str, md5_b64: str) -> None:
    if "bytes" in entry and size != int(entry["bytes"]):
        raise ValueError(f"{entry['name']}: {size:,} bytes, expected {int(entry['bytes']):,}")
    if "sha256" in entry and sha256 != entry["sha256"]:
        raise ValueError(f"{entry['name']}: SHA-256 mismatch")
    if "md5_b64" in entry and md5_b64 != entry["md5_b64"]:
        raise ValueError(f"{entry['name']}: MD5 mismatch")


def download(
    entry: dict[str, Any], work_dir: Path, attempts: int = 3
) -> tuple[Path, dict[str, Any]]:
    """Fetch one file to work_dir, hashing while streaming; retry on network or checksum errors."""
    work_dir.mkdir(parents=True, exist_ok=True)
    dest = work_dir / entry["name"]
    part = work_dir / (entry["name"] + ".part")
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        started = time.monotonic()
        sha, md5, size = hashlib.sha256(), hashlib.md5(), 0
        try:
            with (
                urllib.request.urlopen(entry["url"], timeout=120) as response,
                part.open("wb") as fh,
            ):
                while chunk := response.read(CHUNK):
                    fh.write(chunk)
                    sha.update(chunk)
                    md5.update(chunk)
                    size += len(chunk)
            md5_b64 = base64.b64encode(md5.digest()).decode()
            _check(entry, size, sha.hexdigest(), md5_b64)
            part.replace(dest)
            return dest, {
                "bytes": size,
                "sha256": sha.hexdigest(),
                "md5_b64": md5_b64,
                "verified": [k for k in ("bytes", "sha256", "md5_b64") if k in entry],
                "seconds": round(time.monotonic() - started, 1),
                "attempts": attempt,
            }
        except (OSError, ValueError) as exc:
            last_error = exc
            part.unlink(missing_ok=True)
            log(f"  download attempt {attempt}/{attempts} for {entry['name']} failed: {exc}")
            if attempt < attempts:
                time.sleep(15 * attempt)
    raise RuntimeError(f"{entry['name']}: download failed after {attempts} attempts: {last_error}")


# ------------------------------------------------------------------ parse


def parse_shard(
    path: Path, name: str, splits: dict[int, str]
) -> tuple[list[dict], list[dict], dict]:
    reader = ShardReader(path, splits, shard=name)
    screens: list[dict[str, Any]] = []
    nodes: list[dict[str, Any]] = []
    episodes = 0
    apps: Counter[str] = Counter()
    for episode in reader:
        episodes += 1
        apps[episode.app] += 1
        for screen in episode.screens:
            c = count_screen(screen)
            row: dict[str, Any] = {
                "screen_id": screen.screen_id,
                "episode_id": screen.episode_id,
                "step_index": screen.step_index,
                "shard": name,
                "split": episode.split,
                "app": screen.app,
                "n_nodes": c.n_nodes,
                "n_included": c.n_included,
            }
            for p in POPULATIONS:
                row[f"{p}_candidates"] = c.candidates[p]
                row[f"{p}_labelled"] = c.labelled[p]
            for r in LABEL_ROLES:
                row[f"needs_label_{r}_candidates"] = c.role_candidates.get(r, 0)
                row[f"needs_label_{r}_labelled"] = c.role_labelled.get(r, 0)
            screens.append(row)
            for n in screen.nodes:
                if n.included and (n.needs_label or n.icon_like or n.interactive_image):
                    x1, y1, x2, y2 = n.bounds
                    nodes.append(
                        {
                            "screen_id": screen.screen_id,
                            "episode_id": screen.episode_id,
                            "step_index": screen.step_index,
                            "window_index": n.window_index,
                            "window_layer": n.window_layer,
                            "node_uid": n.node_uid,
                            "depth": n.depth,
                            "class_name": n.class_name,
                            "role": n.role,
                            "resource_id": n.resource_id,
                            "content_desc": n.content_desc,
                            "text": n.text,
                            "hint_text": n.hint_text,
                            "clickable": n.clickable,
                            "long_clickable": n.long_clickable,
                            "focusable": n.focusable,
                            "enabled": n.enabled,
                            "x1": x1,
                            "y1": y1,
                            "x2": x2,
                            "y2": y2,
                            "labelled": n.labelled,
                            "needs_label": n.needs_label,
                            "icon_like": n.icon_like,
                            "interactive_image": n.interactive_image,
                        }
                    )
    totals = {
        "episodes": episodes,
        "screens": len(screens),
        "nodes": sum(r["n_nodes"] for r in screens),
        "included": sum(r["n_included"] for r in screens),
        **{
            f"{p}_{k}": sum(r[f"{p}_{k}"] for r in screens)
            for p in POPULATIONS
            for k in ("candidates", "labelled")
        },
        "candidate_node_rows": len(nodes),
        "apps": len([a for a in apps if a]),
        "episodes_without_app": apps.get("", 0),
    }
    stats = {
        "records": reader.records,
        "truncated": reader.truncated,
        "n_failures": len(reader.failures),
        "failures": reader.failures[:50],
        "totals": totals,
    }
    return screens, nodes, stats


def _write_json(path: Path, data: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    tmp.replace(path)


def _dir_bytes(path: Path) -> int:
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


# ------------------------------------------------------------------ run


def run(
    config: dict[str, Any],
    out_dir: Path,
    work_dir: Path,
    budget_s: float | None = None,
    build: dict[str, Any] | None = None,
) -> dict[str, Any]:
    started = time.monotonic()
    budget_s = float(
        budget_s if budget_s is not None else config.get("time_budget_s", DEFAULT_BUDGET_S)
    )
    for sub in ("screens", "nodes", "shards"):
        (out_dir / sub).mkdir(parents=True, exist_ok=True)
    log(
        f"a11ydebt {__version__} | config {config.get('name')} | "
        f"{len(config['shards'])} shard(s) | budget {budget_s / 3600:.1f} h"
    )

    splits: dict[int, str] = {}
    if config.get("splits_json"):
        path, _ = download({"name": "splits.json", **config["splits_json"]}, work_dir)
        splits = load_splits(path)
        log(f"splits.json: {len(splits):,} episodes labelled")

    durations: list[float] = []
    failed: list[dict[str, str]] = []
    stopped_early = False
    for entry in config["shards"]:
        name = entry["name"]
        marker = out_dir / "shards" / f"{name}.json"
        if marker.exists():
            log(f"{name}: already done, skipping")
            continue
        expected = (
            max(durations) if durations else float(config.get("first_shard_estimate_s", 1800))
        )
        elapsed = time.monotonic() - started
        if elapsed + 1.5 * expected > budget_s:
            log(f"{name}: not started; {elapsed / 3600:.2f} h used of {budget_s / 3600:.2f} h")
            stopped_early = True
            break
        shard_started = time.monotonic()
        log(f"{name}: downloading")
        try:
            path, download_info = download(entry, work_dir)
        except RuntimeError as exc:
            log(str(exc))
            failed.append({"name": name, "error": str(exc)})
            continue
        log(
            f"{name}: {download_info['bytes'] / 1e9:.2f} GB in "
            f"{download_info['seconds']} s; parsing"
        )
        parse_started = time.monotonic()
        screens, nodes, stats = parse_shard(path, name, splits)
        pq.write_table(
            pa.Table.from_pylist(screens, schema=SCREEN_SCHEMA),
            out_dir / "screens" / f"{name}.parquet",
            compression="zstd",
        )
        pq.write_table(
            pa.Table.from_pylist(nodes, schema=NODE_SCHEMA),
            out_dir / "nodes" / f"{name}.parquet",
            compression="zstd",
        )
        path.unlink()
        seconds = time.monotonic() - shard_started
        durations.append(seconds)
        _write_json(
            marker,
            {
                "name": name,
                "download": download_info,
                "parse_seconds": round(time.monotonic() - parse_started, 1),
                "total_seconds": round(seconds, 1),
                "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                **stats,
            },
        )
        t = stats["totals"]
        log(
            f"{name}: {t['episodes']:,} episodes, {t['screens']:,} screens, {t['nodes']:,} nodes, "
            f"needs_label {t['needs_label_labelled']:,}/{t['needs_label_candidates']:,}, "
            f"{seconds / 60:.1f} min"
        )

    done = sorted(p.stem for p in (out_dir / "shards").glob("*.json"))
    markers = [
        json.loads((out_dir / "shards" / f"{n}.json").read_text(encoding="utf-8")) for n in done
    ]
    wanted = [e["name"] for e in config["shards"]]
    totals: Counter[str] = Counter()
    for m in markers:
        totals.update({k: v for k, v in m["totals"].items() if isinstance(v, int)})
    summary = {
        "status": "complete" if set(wanted) <= set(done) else "incomplete",
        "stopped_before_time_limit": stopped_early,
        "config": config.get("name"),
        "a11ydebt_version": __version__,
        "build": build or {},
        "python": platform.python_version(),
        "pyarrow": pa.__version__,
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
        "shards_done": [n for n in wanted if n in done],
        "shards_failed": failed,
        "shards_remaining": [n for n in wanted if n not in done],
        "truncated_shards": [m["name"] for m in markers if m.get("truncated")],
        "episode_failures": sum(m.get("n_failures", 0) for m in markers),
        "totals": dict(totals),
        "elapsed_seconds": round(time.monotonic() - started, 1),
        "output_bytes": _dir_bytes(out_dir),
    }
    _write_json(out_dir / "run_summary.json", summary)
    log(
        f"done: {summary['status']}, {len(summary['shards_done'])}/{len(wanted)} shards, "
        f"{summary['output_bytes'] / 1e6:.1f} MB of output"
    )
    return summary


def main(
    argv: list[str] | None = None, *, config: dict | None = None, build: dict | None = None
) -> int:
    parser = argparse.ArgumentParser(description="Parse AndroidControl shards for a11ydebt.")
    parser.add_argument("--config", type=Path, help="config JSON (the kernel embeds one instead)")
    parser.add_argument(
        "--out", type=Path, default=Path(os.environ.get("A11YDEBT_OUT", "/kaggle/working"))
    )
    parser.add_argument(
        "--work", type=Path, default=Path(os.environ.get("A11YDEBT_WORK", "/tmp/a11ydebt_work"))
    )
    parser.add_argument("--budget-s", type=float, default=None)
    args = parser.parse_args(argv)
    if args.config:
        config = json.loads(args.config.read_text(encoding="utf-8"))
    if config is None:
        parser.error("a config is required")
    run(config, args.out, args.work, args.budget_s, build)
    return 0  # the outcome is in run_summary.json; a non-zero exit could cost Kaggle the outputs


if __name__ == "__main__":
    sys.exit(main())
