"""Sanity checks for the all-20-shard AndroidControl tables (dev-only; needs pyarrow).

    uv run python scripts/check_androidcontrol_all20.py data/interim/androidcontrol \
        data/interim/audit_androidcontrol_all20 data/interim/audit_androidcontrol_run1 \
        data/interim/aissa_reference [--out FILE]

KAGGLE_ROOT holds the pulled kernel outputs of every run (run1/, run2/). ALL20 and RUN1 are the
``a11ydebt summarize androidcontrol --out`` folders for KAGGLE_ROOT and for run 1 alone. The
checks: all 20 shards are present once, with no failed or truncated shard and no episode
failure; no episode appears twice; the episode count is the expected 15,283; the rows of AISSA's
10 shards inside ALL20 are identical to RUN1 and still add up to AISSA's totals; and the ALL20
totals equal the sum of the shard rows. Prints Markdown and exits 1 on any failure.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

import pyarrow.parquet as pq

EXPECTED_EPISODES = 15_283  # AndroidControl release: 15,283 episodes over 20 shards
COUNT_COLUMNS = [
    "n_nodes",
    "n_included",
    "needs_label_candidates",
    "needs_label_labelled",
    "icon_like_candidates",
    "icon_like_labelled",
    "interactive_image_candidates",
    "interactive_image_labelled",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the all-20 AndroidControl tables.")
    parser.add_argument("kaggle_root", type=Path)
    parser.add_argument("all20", type=Path)
    parser.add_argument("run1", type=Path)
    parser.add_argument("reference_dir", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    markers = [
        json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(args.kaggle_root.rglob("*.json"))
        if p.parent.name == "shards"
    ]
    summaries = [
        json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(args.kaggle_root.rglob("run_summary.json"))
    ]
    rows = [
        row
        for f in sorted(args.kaggle_root.rglob("*.parquet"))
        if f.parent.name == "screens"
        for row in pq.read_table(f).to_pylist()
    ]
    shard_ref = json.loads(
        (args.reference_dir / "androidcontrol_shards.json").read_text(encoding="utf-8")
    )
    aissa_shards = {s["name"] for s in shard_ref["shards"]}
    aissa_totals = json.loads(
        (args.reference_dir / "androidcontrol_parse_report.json").read_text(encoding="utf-8")
    )["totals"]

    lines = ["| Check | Expected | Found | OK |", "|---|---:|---:|:-:|"]
    all_ok = True

    def check(label: str, expected: object, found: object) -> None:
        nonlocal all_ok
        ok = expected == found
        all_ok &= ok
        is_count = isinstance(expected, int) and not isinstance(expected, bool)
        fmt = (lambda v: f"{v:,}") if is_count else str
        lines.append(f"| {label} | {fmt(expected)} | {fmt(found)} | {'yes' if ok else '**NO**'} |")

    names = Counter(m["name"] for m in markers)
    check("Shard markers (distinct, none twice)", 20, len(names))
    check("Shards present twice", 0, sum(1 for c in names.values() if c > 1))
    check("Runs complete", len(summaries), sum(s["status"] == "complete" for s in summaries))
    check("Shards failed to download", 0, sum(len(s["shards_failed"]) for s in summaries))
    check("Truncated shards", 0, sum(len(s["truncated_shards"]) for s in summaries))
    check("Episode failures", 0, sum(s["episode_failures"] for s in summaries))

    episode_shards: dict[int, set[str]] = {}
    for r in rows:
        episode_shards.setdefault(r["episode_id"], set()).add(r["shard"])
    check("Episodes in more than one shard", 0, sum(len(s) > 1 for s in episode_shards.values()))
    check("Episodes, all 20 shards", EXPECTED_EPISODES, len(episode_shards))
    check("Screen ids seen twice", 0, len(rows) - len({r["screen_id"] for r in rows}))

    all20 = read_csv(args.all20 / "screens.csv")
    run1 = read_csv(args.run1 / "screens.csv")
    in_aissa = {r["screen_id"] for r in rows if r["shard"] in aissa_shards}
    subset = [r for r in all20 if r["screen_id"] in in_aissa]
    check("Run-1 rows inside all-20 identical to run 1", True, subset == run1)

    def total(table: list[dict[str, str]], col: str) -> int:
        return sum(int(r[col]) for r in table)

    for label, col, key in [
        ("Run-1 subset: nodes", "n_nodes", "elements"),
        ("Run-1 subset: included", "n_included", "included"),
        ("Run-1 subset: needs-label candidates", "needs_label_candidates", "needs"),
        ("Run-1 subset: needs-label labelled", "needs_label_labelled", "labelled"),
    ]:
        check(f"{label} = AISSA", aissa_totals[key], total(subset, col))
    check("Run-1 subset: screens = AISSA", shard_ref["screens"], len(subset))

    summary = json.loads((args.all20 / "summary.json").read_text(encoding="utf-8"))["corpus"]
    check("All-20 screens = shard rows", len(rows), summary["n_screens"])
    check("All-20 nodes = shard rows", sum(r["n_nodes"] for r in rows), summary["n_nodes"])
    for p in ("needs_label", "icon_like", "interactive_image"):
        found = (
            summary["populations"][p]["candidates"],
            summary["populations"][p]["labelled"],
        )
        expected = (
            sum(r[f"{p}_candidates"] for r in rows),
            sum(r[f"{p}_labelled"] for r in rows),
        )
        check(f"All-20 {p} (candidates, labelled) = shard rows", expected, found)

    per_run = [s["totals"]["episodes"] for s in summaries]
    lines += [
        "",
        f"Episodes per run: {' + '.join(f'{n:,}' for n in per_run)} = {sum(per_run):,}",
        "",
        "**Verdict: " + ("all checks pass" if all_ok else "CHECKS FAILED") + "**",
    ]
    text = "\n".join(lines)
    print(text)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
