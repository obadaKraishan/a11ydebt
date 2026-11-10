"""Compare an a11ydebt Rico audit with the numbers the AISSA 2026 pipeline reported.

    uv run --with pyarrow python scripts/compare_aissa.py AUDIT_DIR REFERENCE_DIR [--out FILE]

AUDIT_DIR      output of ``a11ydebt audit rico ... --out AUDIT_DIR``
               (screens.csv, apps.csv, summary.json)
REFERENCE_DIR  copies of the AISSA outputs (accessibility-debt-agents, commit 97c0378):
               rico_parse_report.json, rico_screens.parquet, manuscript_numbers.json

Prints Markdown tables: corpus totals, coverage by role (RQ1 Tables 1 and 2), and screen-by-screen
and per-app agreement. Exits 1 if any AISSA quantity is not reproduced exactly. Dev-only: needs
pyarrow, which is not a runtime dependency of a11ydebt.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import pyarrow.parquet as pq

SCREEN_FIELDS = [  # (AISSA rico_screens.parquet column, a11ydebt screens.csv column)
    ("n_nodes", "n_nodes"),
    ("n_included", "n_included"),
    ("n_needs_label", "needs_label_candidates"),
    ("n_labelled", "needs_label_labelled"),
    ("n_icon_like", "icon_like_candidates"),
    ("n_icon_like_labelled", "icon_like_labelled"),
]
APP_FIELDS = [  # (AISSA per-app sum, a11ydebt apps.csv column)
    ("n_screens", "n_screens"),
    ("n_nodes", "n_nodes"),
    ("n_included", "n_included"),
    ("n_needs_label", "needs_label_candidates"),
    ("n_labelled", "needs_label_labelled"),
    ("n_icon_like", "icon_like_candidates"),
    ("n_icon_like_labelled", "icon_like_labelled"),
]


def num(text: str) -> float:
    return float(str(text).replace(",", ""))


def pct(labelled: int, candidates: int) -> str:
    return f"{100 * labelled / candidates:.2f}" if candidates else "n/a"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def rq1_tables(manuscript: dict) -> tuple[list[str], dict[str, list[str]]]:
    tables = {t["name"]: t for t in manuscript["reports"]["RQ1"]["tables"]}
    overall = next(r for r in tables["overall_coverage"]["rows"] if r[0] == "rico_2017")
    by_role = {r[1]: r for r in tables["coverage_by_role"]["rows"] if r[0] == "rico_2017"}
    return overall, by_role


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("audit_dir", type=Path)
    parser.add_argument("reference_dir", type=Path)
    parser.add_argument("--out", type=Path, help="also write the Markdown to this file")
    args = parser.parse_args(argv)

    summary = json.loads((args.audit_dir / "summary.json").read_text(encoding="utf-8"))
    corpus = summary["corpus"]
    pops = corpus["populations"]
    report = json.loads((args.reference_dir / "rico_parse_report.json").read_text(encoding="utf-8"))
    totals = report["totals"]
    manuscript = json.loads(
        (args.reference_dir / "manuscript_numbers.json").read_text(encoding="utf-8")
    )
    overall, by_role = rq1_tables(manuscript)
    ref_screens = pq.read_table(args.reference_dir / "rico_screens.parquet").to_pylist()
    ours_screens = {row["screen_id"]: row for row in read_csv(args.audit_dir / "screens.csv")}
    ours_apps = {row["app"]: row for row in read_csv(args.audit_dir / "apps.csv")}

    lines: list[str] = []
    all_ok = True

    def check(label: str, theirs: object, ours: object) -> None:
        nonlocal all_ok
        ok = theirs == ours
        all_ok &= ok
        fmt = (lambda v: f"{v:,}") if isinstance(theirs, int) else str
        lines.append(f"| {label} | {fmt(theirs)} | {fmt(ours)} | {'yes' if ok else '**NO**'} |")

    nl, il = pops["needs_label"], pops["icon_like"]
    lines += [
        "**Corpus totals** (AISSA: rico_parse_report.json and RQ1 Table 1)",
        "",
        "| Quantity | AISSA | a11ydebt | Match |",
        "|---|---:|---:|:-:|",
    ]
    check("Screens parsed", totals["screens"], corpus["n_screens"])
    check("Screens failed", totals["failed"], len(summary["failures"]))
    check("Nodes (elements parsed)", totals["nodes"], corpus["n_nodes"])
    check("Included (visible, positive area)", totals["included"], corpus["n_included"])
    check("Needs label: candidates", totals["needs"], nl["candidates"])
    check("Needs label: labelled", totals["labelled"], nl["labelled"])
    check("Label coverage %", overall[4], pct(nl["labelled"], nl["candidates"]))
    check("Icon-like: candidates", totals["icons"], il["candidates"])
    check("Icon-like: labelled", totals["icons_labelled"], il["labelled"])
    check("Icon-like coverage %", overall[6], pct(il["labelled"], il["candidates"]))
    ref_apps = {r["app_package"] for r in ref_screens}
    check("Apps with at least one screen", len(ref_apps), corpus["n_apps"])

    lines += [
        "",
        "**Coverage by role, needs-label population** (AISSA: RQ1 Table 2, rico_2017)",
        "",
        "| Role | AISSA needs label | a11ydebt | AISSA labelled | a11ydebt "
        "| AISSA cov. % | a11ydebt | Match |",
        "|---|---:|---:|---:|---:|---:|---:|:-:|",
    ]
    ours_roles = corpus["needs_label_by_role"]
    for role in sorted(set(by_role) | set(ours_roles)):
        ref = by_role.get(role)
        mine = ours_roles.get(role, {"candidates": 0, "labelled": 0})
        ref_needs, ref_lab = (int(num(ref[3])), int(num(ref[4]))) if ref else (0, 0)
        ref_cov = ref[5] if ref else "n/a"
        my_cov = pct(mine["labelled"], mine["candidates"])
        ok = (ref_needs, ref_lab, ref_cov) == (mine["candidates"], mine["labelled"], my_cov)
        all_ok &= ok
        lines.append(
            f"| {role} | {ref_needs:,} | {mine['candidates']:,} | {ref_lab:,} "
            f"| {mine['labelled']:,} | {ref_cov} | {my_cov} | {'yes' if ok else '**NO**'} |"
        )

    lines += [
        "",
        "**Screen-by-screen agreement** (AISSA: rico_screens.parquet, one row per screen)",
        "",
        "| Field | Screens equal | Of | First mismatches |",
        "|---|---:|---:|---|",
    ]
    for ref_col, my_col in [*SCREEN_FIELDS, ("app_package", "app")]:
        equal, mismatches = 0, []
        for row in ref_screens:
            mine = ours_screens.get(str(row["screen_uid"]))
            theirs = row[ref_col]
            value = (
                None if mine is None else (mine[my_col] if my_col == "app" else int(mine[my_col]))
            )
            if value == theirs:
                equal += 1
            elif len(mismatches) < 3:
                mismatches.append(f"{row['screen_uid']}: {theirs!r} vs {value!r}")
        all_ok &= equal == len(ref_screens)
        lines.append(
            f"| {ref_col} | {equal:,} | {len(ref_screens):,} | {'; '.join(mismatches) or '-'} |"
        )
    extra = sorted(set(ours_screens) - {str(r["screen_uid"]) for r in ref_screens})
    lines.append(f"| screens only in a11ydebt | {len(extra):,} | | {', '.join(extra[:3]) or '-'} |")
    all_ok &= not extra

    sums: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in ref_screens:
        s = sums[row["app_package"]]
        s["n_screens"] += 1
        for ref_col, _ in SCREEN_FIELDS:
            s[ref_col] += row[ref_col]
    apps_equal = sum(
        1
        for app, s in sums.items()
        if app in ours_apps and all(s[r] == int(ours_apps[app][m]) for r, m in APP_FIELDS)
    )
    all_ok &= apps_equal == len(sums) == len(ours_apps)
    lines += [
        "",
        "**Per-app agreement** (AISSA screens summed by app_package)",
        "",
        f"- Apps identical on all {len(APP_FIELDS)} counts: **{apps_equal:,} of {len(sums):,}** "
        f"(a11ydebt lists {len(ours_apps):,} apps)",
    ]

    ii = pops["interactive_image"]
    lines += [
        "",
        "**New in a11ydebt (no AISSA counterpart): P01 interactive_image population**",
        "",
        f"- Candidates {ii['candidates']:,}, labelled {ii['labelled']:,}, "
        f"coverage {pct(ii['labelled'], ii['candidates'])}%, "
        f"screens with at least one unlabelled candidate "
        f"{corpus['screens_with_debt']['interactive_image']:,} of {corpus['n_screens']:,}",
        "",
        "**Verdict: "
        + ("all AISSA quantities reproduced exactly" if all_ok else "MISMATCHES FOUND")
        + "**",
    ]

    text = "\n".join(lines)
    print(text)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
