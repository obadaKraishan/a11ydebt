"""Compare a11ydebt audits with the numbers the AISSA 2026 pipeline reported.

    uv run python scripts/compare_aissa.py [rico] AUDIT_DIR REFERENCE_DIR [--out FILE]
    uv run python scripts/compare_aissa.py androidcontrol KAGGLE_OUT REFERENCE_DIR [--out FILE]
    uv run python scripts/compare_aissa.py bootstrap RICO_AUDIT AC_AUDIT REFERENCE_DIR [--out FILE]

rico: AUDIT_DIR is the output of ``a11ydebt audit rico ... --out AUDIT_DIR`` (screens.csv,
apps.csv, summary.json). REFERENCE_DIR holds copies of the AISSA outputs (accessibility-debt-agents,
commit 97c0378): rico_parse_report.json, rico_screens.parquet, manuscript_numbers.json.

androidcontrol: KAGGLE_OUT is what ``kaggle kernels output`` pulled for run 1 (screens/*.parquet,
shards/*.json, run_summary.json). REFERENCE_DIR also needs the files written by
``scripts/aissa_androidcontrol_reference.py``.

bootstrap: RICO_AUDIT and AC_AUDIT are audit folders (screens.csv, summary.json) for Rico and for
AndroidControl run 1. It replays AISSA's ReviewerChecks Check 1: one generator seeded 20260908,
5,000 resamples per interval, drawn in AISSA's order (AndroidControl screen, AndroidControl app,
Rico screen, Rico app), and compares the clustered_coverage and clustered_gap tables. It also
prints the intervals ``a11ydebt report`` gives, where each interval has its own generator.

Prints Markdown tables: corpus totals, coverage by role (RQ1 Tables 1 and 2), and screen, episode,
shard and app agreement. Exits 1 if any AISSA quantity is not reproduced exactly. Dev-only: it needs
pyarrow (a dev dependency), which is not a runtime dependency of a11ydebt.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from a11ydebt.bootstrap import (
    DEFAULT_N_RESAMPLES,
    DEFAULT_SEED,
    cluster_bootstrap_rate,
    cluster_totals,
    percentile_ci,
    wilson_ci,
)
from a11ydebt.report import load_audit

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


def rq1_tables(
    manuscript: dict, dataset: str = "rico_2017"
) -> tuple[list[str], dict[str, list[str]]]:
    tables = {t["name"]: t for t in manuscript["reports"]["RQ1"]["tables"]}
    overall = next(r for r in tables["overall_coverage"]["rows"] if r[0] == dataset)
    by_role = {r[1]: r for r in tables["coverage_by_role"]["rows"] if r[0] == dataset}
    return overall, by_role


def main_rico(argv: list[str] | None = None) -> int:
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
        "**New in a11ydebt (no AISSA counterpart): interactive_image population**",
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


# (AISSA androidcontrol_screens.parquet column, a11ydebt screens parquet column)
AC_SCREEN_FIELDS = [
    ("n_nodes", "n_nodes"),
    ("n_included", "n_included"),
    ("n_needs_label", "needs_label_candidates"),
    ("n_labelled", "needs_label_labelled"),
    ("n_icon_like", "icon_like_candidates"),
    ("n_icon_like_labelled", "icon_like_labelled"),
]
AC_EPISODE_FIELDS = [  # (AISSA androidcontrol_episodes.parquet column, a11ydebt per-episode sum)
    ("n_observations", "screens"),
    ("n_elements", "n_nodes"),
    *AC_SCREEN_FIELDS[1:],
]


def main_androidcontrol(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Compare the AndroidControl run with AISSA.")
    parser.add_argument("kaggle_out", type=Path)
    parser.add_argument("reference_dir", type=Path)
    parser.add_argument("--out", type=Path, help="also write the Markdown to this file")
    args = parser.parse_args(argv)
    ref_dir, out = args.reference_dir, args.kaggle_out

    def load(name: str) -> dict:
        return json.loads((ref_dir / name).read_text(encoding="utf-8"))

    report, shard_ref = load("androidcontrol_parse_report.json"), load("androidcontrol_shards.json")
    manuscript = load("manuscript_numbers.json")
    overall, by_role = rq1_tables(manuscript, "androidcontrol_2024")
    reviewer = manuscript["reports"]["ReviewerChecks"]
    ref_apps = next(d["value"] for d in reviewer["descriptives"] if "apps identified" in d["label"])
    ref_shard_rows = {
        r[0]: r for r in next(t for t in reviewer["tables"] if t["name"] == "shards")["rows"]
    }
    totals = report["totals"]

    screen_files = sorted(p for p in out.rglob("*.parquet") if p.parent.name == "screens")
    ours = [row for f in screen_files for row in pq.read_table(f).to_pylist()]
    markers = [
        json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(out.rglob("*.json"))
        if p.parent.name == "shards"
    ]
    run_summary = json.loads(next(out.rglob("run_summary.json")).read_text(encoding="utf-8"))

    def total(col: str) -> int:
        return sum(r[col] for r in ours)

    episodes: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in ours:
        e = episodes[r["episode_id"]]
        e["screens"] += 1
        for _ref_col, col in AC_SCREEN_FIELDS:
            e[col] += r[col]
    # AISSA counts apps over episodes with at least one needs-label element (ReviewerChecks).
    needs_per_episode: dict[int, int] = defaultdict(int)
    for r in ours:
        needs_per_episode[r["episode_id"]] += r["needs_label_candidates"]
    apps_all = {r["app"] for r in ours if r["app"]}
    apps = {r["app"] for r in ours if r["app"] and needs_per_episode[r["episode_id"]] > 0}

    lines: list[str] = []
    all_ok = True

    def check(label: str, theirs: object, mine: object) -> None:
        nonlocal all_ok
        ok = theirs == mine
        all_ok &= ok
        fmt = (lambda v: f"{v:,}") if isinstance(theirs, int) else str
        lines.append(f"| {label} | {fmt(theirs)} | {fmt(mine)} | {'yes' if ok else '**NO**'} |")

    lines += [
        "**Corpus totals** (AISSA: androidcontrol_parse_report.json, RQ1 Table 1, ReviewerChecks)",
        "",
        "| Quantity | AISSA | a11ydebt | Match |",
        "|---|---:|---:|:-:|",
    ]
    check("Shards parsed", len(report["shards_used"]), len(markers))
    check("Episodes parsed", totals["episodes"], len(episodes))
    check("Episodes failed", totals["failed"], run_summary["episode_failures"])
    check("Truncated shards", len(report["truncated_shards"]), len(run_summary["truncated_shards"]))
    check("Screens (observations)", shard_ref["screens"], len(ours))
    check("Nodes (elements parsed)", totals["elements"], total("n_nodes"))
    check("Included (visible, positive area)", totals["included"], total("n_included"))
    nl, nll = total("needs_label_candidates"), total("needs_label_labelled")
    il, ill = total("icon_like_candidates"), total("icon_like_labelled")
    check("Needs label: candidates", totals["needs"], nl)
    check("Needs label: labelled", totals["labelled"], nll)
    check("Label coverage %", overall[4], pct(nll, nl))
    check("Icon-like: candidates", totals["icons"], il)
    check("Icon-like: labelled", totals["icons_labelled"], ill)
    check("Icon-like coverage %", overall[6], pct(ill, il))
    check("Apps from resource ids (episodes with needs-label elements)", ref_apps, len(apps))
    lines.append(
        f"| Apps from resource ids, all episodes (information only) | - | {len(apps_all):,} | - |"
    )

    lines += [
        "",
        "**Coverage by role, needs-label population** (AISSA: RQ1 Table 2, androidcontrol_2024)",
        "",
        "| Role | AISSA needs label | a11ydebt | AISSA labelled | a11ydebt "
        "| AISSA cov. % | a11ydebt | Match |",
        "|---|---:|---:|---:|---:|---:|---:|:-:|",
    ]
    for role in sorted(by_role):
        ref = by_role[role]
        mine_n = total(f"needs_label_{role}_candidates")
        mine_l = total(f"needs_label_{role}_labelled")
        ref_n, ref_l, ref_cov = int(num(ref[3])), int(num(ref[4])), ref[5]
        ok = (ref_n, ref_l, ref_cov) == (mine_n, mine_l, pct(mine_l, mine_n))
        all_ok &= ok
        lines.append(
            f"| {role} | {ref_n:,} | {mine_n:,} | {ref_l:,} | {mine_l:,} | {ref_cov} "
            f"| {pct(mine_l, mine_n)} | {'yes' if ok else '**NO**'} |"
        )

    lines += [
        "",
        "**Per-shard agreement** (AISSA: ReviewerChecks shards table and the episode table)",
        "",
        "| Shard | AISSA episodes | a11ydebt | AISSA needs label | a11ydebt | AISSA cov. % "
        "| a11ydebt | Match |",
        "|---|---:|---:|---:|---:|---:|---:|:-:|",
    ]
    by_shard: dict[str, list[dict]] = defaultdict(list)
    for r in ours:
        by_shard[r["shard"]].append(r)
    for name in sorted(ref_shard_rows):
        ref = ref_shard_rows[name]
        rows = by_shard.get(name, [])
        n_ep = len({r["episode_id"] for r in rows})
        n_need = sum(r["needs_label_candidates"] for r in rows)
        cov = pct(sum(r["needs_label_labelled"] for r in rows), n_need)
        ok = (int(num(ref[1])), int(num(ref[2])), ref[3]) == (n_ep, n_need, cov)
        all_ok &= ok
        lines.append(
            f"| {name} | {ref[1]} | {n_ep:,} | {ref[2]} | {n_need:,} | {ref[3]} | {cov} "
            f"| {'yes' if ok else '**NO**'} |"
        )

    ref_episodes = pq.read_table(ref_dir / "androidcontrol_episodes.parquet").to_pylist()
    lines += [
        "",
        "**Episode-by-episode agreement** (AISSA: androidcontrol_episodes.parquet)",
        "",
        "| Field | Episodes equal | Of | First mismatches |",
        "|---|---:|---:|---|",
    ]
    for ref_col, col in AC_EPISODE_FIELDS:
        equal, bad = 0, []
        for e in ref_episodes:
            mine = episodes.get(int(e["episode_id"]), {}).get(col)
            if mine == e[ref_col]:
                equal += 1
            elif len(bad) < 3:
                bad.append(f"{e['episode_id']}: {e[ref_col]} vs {mine}")
        all_ok &= equal == len(ref_episodes)
        lines.append(f"| {ref_col} | {equal:,} | {len(ref_episodes):,} | {'; '.join(bad) or '-'} |")
    extra = sorted(set(episodes) - {int(e["episode_id"]) for e in ref_episodes})
    all_ok &= not extra
    lines.append(
        f"| episodes only in a11ydebt | {len(extra):,} | "
        f"| {', '.join(map(str, extra[:3])) or '-'} |"
    )

    ref_screens = pq.read_table(ref_dir / "androidcontrol_screens.parquet").to_pylist()
    ours_by_screen = {r["screen_id"]: r for r in ours}
    lines += [
        "",
        "**Screen-by-screen agreement** (AISSA: per-screen counts derived from its node table)",
        "",
        "| Field | Screens equal | Of | First mismatches |",
        "|---|---:|---:|---|",
    ]
    for ref_col, col in AC_SCREEN_FIELDS:
        equal, bad = 0, []
        for s in ref_screens:
            mine = ours_by_screen.get(s["screen_uid"], {}).get(col)
            if mine == s[ref_col]:
                equal += 1
            elif len(bad) < 3:
                bad.append(f"{s['screen_uid']}: {s[ref_col]} vs {mine}")
        all_ok &= equal == len(ref_screens)
        lines.append(f"| {ref_col} | {equal:,} | {len(ref_screens):,} | {'; '.join(bad) or '-'} |")
    ref_ids = {s["screen_uid"] for s in ref_screens}
    empty = [r for r in ours if r["screen_id"] not in ref_ids]
    expected_empty = shard_ref["screens"] - len(ref_screens)
    ok = len(empty) == expected_empty and all(r["n_nodes"] == 0 for r in empty)
    all_ok &= ok
    lines.append(
        f"| screens with no nodes (absent from AISSA's node table) | {len(empty):,} "
        f"| {expected_empty:,} "
        f"| {'all empty' if ok else '**NOT ALL EMPTY**'} |"
    )

    ii, iil = total("interactive_image_candidates"), total("interactive_image_labelled")
    with_debt = sum(
        1 for r in ours if r["interactive_image_candidates"] > r["interactive_image_labelled"]
    )
    lines += [
        "",
        "**New in a11ydebt (no AISSA counterpart): interactive_image population**",
        "",
        f"- Candidates {ii:,}, labelled {iil:,}, coverage {pct(iil, ii)}%, "
        "screens with at least one "
        f"unlabelled candidate {with_debt:,} of {len(ours):,}",
        "",
        f"Run: {run_summary.get('status')}, {len(markers)} shards, "
        f"{run_summary.get('elapsed_seconds')} s, "
        f"{run_summary.get('output_bytes', 0) / 1e6:.1f} MB output, a11ydebt "
        f"{run_summary.get('build', {}).get('a11ydebt_commit', '?')}, "
        f"pyarrow {run_summary.get('pyarrow')}, "
        f"Python {run_summary.get('python')}",
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


def aissa_cluster_bootstrap_rate(k, n, rng, n_boot):
    """AISSA's loop, verbatim from phase4_validation/03_reviewer_checks.py (commit 97c0378)."""
    m = len(k)
    out = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, m, m)
        kk, nn = k[idx].sum(), n[idx].sum()
        out[b] = kk / nn if nn else np.nan
    return out


def main_bootstrap(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Replay AISSA's clustered coverage intervals.")
    parser.add_argument("rico_audit", type=Path)
    parser.add_argument("androidcontrol_audit", type=Path)
    parser.add_argument("reference_dir", type=Path)
    parser.add_argument("--out", type=Path, help="also write the Markdown to this file")
    args = parser.parse_args(argv)

    manuscript = json.loads(
        (args.reference_dir / "manuscript_numbers.json").read_text(encoding="utf-8")
    )
    reviewer = manuscript["reports"]["ReviewerChecks"]
    tables = {t["name"]: t for t in reviewer["tables"]}
    ref_cov = {(r[0], r[1]): r for r in tables["clustered_coverage"]["rows"]}
    ref_gap = {r[0]: r for r in tables["clustered_gap"]["rows"]}
    seed = reviewer["provenance"]["seed"]
    n_boot = reviewer["provenance"]["n_boot"]

    # AISSA groups by dataset name, so androidcontrol_2024 is drawn before rico_2017, and within
    # each dataset the screen level before the app level, all from one generator.
    corpora = [
        ("androidcontrol_2024", load_audit(args.androidcontrol_audit)),
        ("rico_2017", load_audit(args.rico_audit)),
    ]
    rng_ours = np.random.default_rng(seed)
    rng_aissa = np.random.default_rng(seed)
    lines = [
        "**Clustered coverage, needs_label** (AISSA: ReviewerChecks `clustered_coverage`; "
        f"seed {seed}, {n_boot:,} resamples)",
        "",
        "| Dataset | Cluster | Clusters (AISSA / ours) | Coverage % (AISSA / ours) "
        "| 95% CI, AISSA | 95% CI, replay | Wilson, AISSA / ours | Match | Draws identical "
        "| `a11ydebt report` CI |",
        "|---|---|---:|---:|---:|---:|---:|:-:|:-:|---:|",
    ]
    all_ok = True
    draws: dict[tuple[str, str], np.ndarray] = {}
    points: dict[str, float] = {}

    def ci_text(lo: float, hi: float) -> str:
        return f"[{100 * lo:.2f}, {100 * hi:.2f}]"

    for name, audit in corpora:
        screens = audit.screens["needs_label"]
        k_el = sum(s.labelled for s in screens)
        n_el = sum(s.candidates for s in screens)
        points[name] = k_el / n_el
        wilson = ci_text(*wilson_ci(k_el, n_el))
        for level in ("screen", "app"):
            _keys, k, n = cluster_totals(screens, level=level, dataset=audit.dataset)
            ours = cluster_bootstrap_rate(k, n, n_resamples=n_boot, rng=rng_ours)
            theirs = aissa_cluster_bootstrap_rate(k, n, rng_aissa, n_boot)
            draws[(name, level)] = ours
            own = cluster_bootstrap_rate(k, n, n_resamples=DEFAULT_N_RESAMPLES, seed=DEFAULT_SEED)
            ref = ref_cov[(name, level)]
            row = [f"{len(k):,}", f"{100 * k_el / n_el:.2f}", ci_text(*percentile_ci(ours))]
            ok = row == [ref[2], ref[3], ref[4]] and wilson == ref[5]
            identical = bool(np.array_equal(ours, theirs))
            all_ok &= ok and identical
            lines.append(
                f"| {name} | {level} | {ref[2]} / {row[0]} | {ref[3]} / {row[1]} | {ref[4]} "
                f"| {row[2]} | {ref[5]} / {wilson} | {'yes' if ok else '**NO**'} "
                f"| {'yes' if identical else '**NO**'} | {ci_text(*percentile_ci(own))} |"
            )
    lines += [
        "",
        "**Cross-corpus gap, AndroidControl minus Rico** (AISSA: `clustered_gap`)",
        "",
        "| Cluster | Gap pp (AISSA / ours) | 95% CI, AISSA | 95% CI, replay | Match |",
        "|---|---:|---:|---:|:-:|",
    ]
    for level in ("screen", "app"):
        gap = draws[("androidcontrol_2024", level)] - draws[("rico_2017", level)]
        point = f"{100 * (points['androidcontrol_2024'] - points['rico_2017']):+.2f}"
        ci = ci_text(*percentile_ci(gap))
        ref = ref_gap[level]
        ok = [point, ci] == [ref[1], ref[2]]
        all_ok &= ok
        lines.append(
            f"| {level} | {ref[1]} / {point} | {ref[2]} | {ci} | {'yes' if ok else '**NO**'} |"
        )
    lines += [
        "",
        "The replay uses a11ydebt's own per-screen counts and app assignments with "
        "`a11ydebt.bootstrap` on one shared generator. *Draws identical* compares all "
        f"{n_boot:,} draws, bit for bit, with AISSA's loop copied verbatim and run on the same "
        "clusters. The last column gives one generator per interval, seeded "
        f"{DEFAULT_SEED}, which is what `a11ydebt report` uses.",
        "",
        "**Verdict: "
        + ("all AISSA intervals reproduced exactly" if all_ok else "MISMATCHES FOUND")
        + "**",
    ]
    text = "\n".join(lines)
    print(text)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    return 0 if all_ok else 1


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "androidcontrol":
        return main_androidcontrol(args[1:])
    if args and args[0] == "bootstrap":
        return main_bootstrap(args[1:])
    if args and args[0] == "rico":
        args = args[1:]
    return main_rico(args)


if __name__ == "__main__":
    sys.exit(main())
