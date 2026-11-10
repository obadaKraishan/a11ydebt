"""Command line interface.

    a11ydebt audit rico PATH [--limit N] [--workers N] [--out DIR] [--quiet]
    a11ydebt audit androidcontrol SHARD [SHARD ...] [--splits splits.json] [--out DIR] [--quiet]
    a11ydebt summarize androidcontrol KAGGLE_OUTPUT_DIR [--out DIR]
    a11ydebt report [LABEL=]AUDIT_DIR [...] [--out DIR] [--n-resamples N] [--seed S] [--conf C]

For Rico, PATH is a folder holding ``combined/*.json`` (or the JSON files directly) and, ideally,
``ui_details.csv`` for app names. For AndroidControl, each SHARD is a GZIP TFRecord file such as
``android_control-00000-of-00020``. The corpus table goes to stdout. With ``--out``, it also
writes ``screens.csv``, ``apps.csv`` and ``summary.json``. The full AndroidControl corpus (about
47 GB) is parsed on Kaggle instead (``kaggle/androidcontrol_parse/``); ``summarize androidcontrol``
turns the pulled kernel outputs into the same tables (it needs pyarrow). ``report`` reads one or
more of those ``--out`` folders and writes ``report.md`` plus CSV tables with cluster-bootstrap
intervals (default folder ``data/release/report``).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from a11ydebt import __version__
from a11ydebt.androidcontrol import load_splits
from a11ydebt.bootstrap import DEFAULT_CONF, DEFAULT_N_RESAMPLES, DEFAULT_SEED
from a11ydebt.coverage import Counts, CoverageReport, audit_androidcontrol, audit_rico
from a11ydebt.report import build_report, format_markdown, load_audit, write_report
from a11ydebt.rico import find_screen_files

__all__ = ["format_summary", "main", "write_outputs"]

INCLUSION_RULE = {
    "require_visible_to_user": True,
    "require_positive_area": True,
    "require_enabled": False,
}
_COUNT_FIELDS = ("candidates", "labelled", "unlabelled", "coverage")


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{100 * value:.2f}%"


def _count_cells(counts: Counts) -> list[object]:
    share = "" if counts.coverage is None else f"{counts.coverage:.6f}"
    return [counts.candidates, counts.labelled, counts.unlabelled, share]


def format_summary(report: CoverageReport) -> str:
    """The corpus table printed by ``a11ydebt audit``."""
    c = report.corpus
    lines = [
        f"a11ydebt {__version__} | {report.dataset}: {c.n_screens:,} screens, {c.n_apps:,} apps, "
        f"{c.n_nodes:,} nodes ({c.n_included:,} included: visible, positive area)",
        "",
        f"{'population':<18}{'candidates':>12}{'labelled':>11}{'coverage':>10}{'debt':>9}"
        f"{'screens w/ debt':>17}",
    ]
    for p in report.populations:
        k = c.populations[p]
        lines.append(
            f"{p:<18}{k.candidates:>12,}{k.labelled:>11,}{_pct(k.coverage):>10}{_pct(k.debt):>9}"
            f"{c.screens_with_debt[p]:>17,}"
        )
    lines += [
        "",
        "needs_label by role",
        f"{'role':<18}{'candidates':>12}{'labelled':>11}{'coverage':>10}",
    ]
    for role, k in c.needs_label_by_role.items():
        lines.append(f"{role:<18}{k.candidates:>12,}{k.labelled:>11,}{_pct(k.coverage):>10}")
    if report.failures:
        lines += [
            "",
            f"WARNING: {len(report.failures):,} file(s) could not be parsed; see summary.json.",
        ]
    return "\n".join(lines)


def write_outputs(
    report: CoverageReport, out: Path, *, source: str = "", elapsed: float | None = None
) -> list[Path]:
    """Write screens.csv, apps.csv and summary.json into ``out``; return their paths."""
    out.mkdir(parents=True, exist_ok=True)
    pops = report.populations
    count_headers = [f"{p}_{field}" for p in pops for field in _COUNT_FIELDS]

    screens_csv = out / "screens.csv"
    with screens_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["screen_id", "app", "n_nodes", "n_included", *count_headers])
        for s in report.screens:
            cells = [cell for p in pops for cell in _count_cells(s.populations[p])]
            writer.writerow([s.screen_id, s.app, s.n_nodes, s.n_included, *cells])

    apps_csv = out / "apps.csv"
    with apps_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        debt_headers = [f"{p}_screens_with_debt" for p in pops]
        writer.writerow(
            ["app", "n_screens", "n_nodes", "n_included", *count_headers, *debt_headers]
        )
        for a in report.apps:
            cells = [cell for p in pops for cell in _count_cells(a.populations[p])]
            debts = [a.screens_with_debt[p] for p in pops]
            writer.writerow([a.app, a.n_screens, a.n_nodes, a.n_included, *cells, *debts])

    summary_json = out / "summary.json"
    summary = {
        "a11ydebt_version": __version__,
        "dataset": report.dataset,
        "source": source,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "elapsed_seconds": None if elapsed is None else round(elapsed, 1),
        "inclusion_rule": INCLUSION_RULE,
        "role_rule": "class name only (AISSA 2026 codebook)",
        "populations": list(pops),
        "corpus": report.corpus.model_dump(),
        "failures": [f.model_dump() for f in report.failures],
    }
    summary_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return [screens_csv, apps_csv, summary_json]


def _progress(done: int, total: int) -> None:
    if done == total or done % 10_000 == 0:
        print(f"  parsed {done:,}/{total:,} screens", file=sys.stderr, flush=True)


def _audit_rico(args: argparse.Namespace) -> int:
    if not find_screen_files(args.path):
        print(
            f"a11ydebt: no screen JSON files in {args.path} or {args.path}/combined",
            file=sys.stderr,
        )
        return 2
    started = time.perf_counter()
    report = audit_rico(
        args.path,
        limit=args.limit,
        workers=args.workers,
        progress=None if args.quiet else _progress,
    )
    elapsed = time.perf_counter() - started
    print(format_summary(report))
    print(f"\n{elapsed:.1f}s with {args.workers} worker(s)")
    if args.out:
        for path in write_outputs(report, args.out, source=str(args.path), elapsed=elapsed):
            print(f"wrote {path}")
    return 0


def _audit_androidcontrol(args: argparse.Namespace) -> int:
    missing = [p for p in args.shards if not p.is_file()]
    if missing:
        print(f"a11ydebt: shard file(s) not found: {', '.join(map(str, missing))}", file=sys.stderr)
        return 2
    splits = load_splits(args.splits) if args.splits else None

    def shard_progress(done: int, total: int) -> None:
        print(f"  parsed {done}/{total} shards", file=sys.stderr, flush=True)

    started = time.perf_counter()
    report = audit_androidcontrol(
        args.shards, splits=splits, progress=None if args.quiet else shard_progress
    )
    elapsed = time.perf_counter() - started
    print(format_summary(report))
    print(f"\n{elapsed:.1f}s")
    if args.out:
        source = " ".join(str(p) for p in args.shards)
        for path in write_outputs(report, args.out, source=source, elapsed=elapsed):
            print(f"wrote {path}")
    return 0


def _summarize_androidcontrol(args: argparse.Namespace) -> int:
    from a11ydebt.kaggle_outputs import read_androidcontrol_outputs

    try:
        report = read_androidcontrol_outputs(args.path)
    except (FileNotFoundError, ImportError) as exc:
        print(f"a11ydebt: {exc}", file=sys.stderr)
        return 2
    print(format_summary(report))
    if args.out:
        for path in write_outputs(report, args.out, source=str(args.path)):
            print(f"wrote {path}")
    return 0


def _report_input(text: str) -> tuple[str | None, Path]:
    """``DIR`` or ``LABEL=DIR``; a folder whose own name contains "=" still works."""
    label, sep, rest = text.partition("=")
    if sep and label and Path(rest).is_dir() and not Path(text).is_dir():
        return label, Path(rest)
    return None, Path(text)


def _report(args: argparse.Namespace) -> int:
    if args.n_resamples < 1:
        print("a11ydebt: --n-resamples must be at least 1", file=sys.stderr)
        return 2
    if not 0 < args.conf < 1:
        print("a11ydebt: --conf must be between 0 and 1", file=sys.stderr)
        return 2
    try:
        audits = [load_audit(path, label) for label, path in map(_report_input, args.inputs)]
    except (FileNotFoundError, ValueError) as exc:
        print(f"a11ydebt: {exc}", file=sys.stderr)
        return 2
    labels = [a.label for a in audits]
    if len(set(labels)) != len(labels):
        print(
            f"a11ydebt: two inputs share a label ({', '.join(labels)}); "
            "name each one as LABEL=AUDIT_DIR",
            file=sys.stderr,
        )
        return 2
    reports = [
        build_report(a, n_resamples=args.n_resamples, seed=args.seed, conf=args.conf)
        for a in audits
    ]
    print(format_markdown(reports))
    for path in write_report(reports, args.out):
        print(f"wrote {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="a11ydebt", description="Audit accessibility debt in GUI-agent corpora."
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    audit = commands.add_parser("audit", help="measure content-description coverage")
    corpora = audit.add_subparsers(dest="corpus", required=True)
    rico = corpora.add_parser(
        "rico", help="Rico view hierarchies (combined/*.json + ui_details.csv)"
    )
    rico.add_argument("path", type=Path, help="Rico folder, e.g. data/raw/rico")
    rico.add_argument("--limit", type=int, help="only the first N screens (pilot runs)")
    rico.add_argument("--workers", type=int, default=1, help="parallel processes (default 1)")
    rico.add_argument("--out", type=Path, help="write screens.csv, apps.csv and summary.json here")
    rico.add_argument("--quiet", action="store_true", help="no progress lines on stderr")
    ac = corpora.add_parser("androidcontrol", help="AndroidControl GZIP TFRecord shards")
    ac.add_argument(
        "shards", type=Path, nargs="+", help="shard files, e.g. android_control-00000-of-00020"
    )
    ac.add_argument(
        "--splits", type=Path, help="splits.json, to label episodes train/validation/test"
    )
    ac.add_argument("--out", type=Path, help="write screens.csv, apps.csv and summary.json here")
    ac.add_argument("--quiet", action="store_true", help="no progress lines on stderr")
    summarize = commands.add_parser(
        "summarize", help="build the tables from a Kaggle kernel's outputs"
    )
    s_corpora = summarize.add_subparsers(dest="corpus", required=True)
    s_ac = s_corpora.add_parser(
        "androidcontrol", help="outputs of kaggle/androidcontrol_parse (needs pyarrow)"
    )
    s_ac.add_argument("path", type=Path, help="the folder `kaggle kernels output` wrote")
    s_ac.add_argument("--out", type=Path, help="write screens.csv, apps.csv and summary.json here")
    rep = commands.add_parser(
        "report", help="Markdown and CSV tables with cluster-bootstrap intervals"
    )
    rep.add_argument(
        "inputs",
        nargs="+",
        metavar="[LABEL=]AUDIT_DIR",
        help="an --out folder of `audit` or `summarize`; LABEL names it in the report",
    )
    rep.add_argument(
        "--out",
        type=Path,
        default=Path("data/release/report"),
        help="output folder (default data/release/report)",
    )
    rep.add_argument(
        "--n-resamples",
        type=int,
        default=DEFAULT_N_RESAMPLES,
        help=f"bootstrap resamples per interval (default {DEFAULT_N_RESAMPLES:,}, as AISSA)",
    )
    rep.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"seed for every interval's generator (default {DEFAULT_SEED}, as AISSA)",
    )
    rep.add_argument(
        "--conf", type=float, default=DEFAULT_CONF, help="interval level (default 0.95)"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "audit" and args.corpus == "rico":
        return _audit_rico(args)
    if args.command == "audit" and args.corpus == "androidcontrol":
        return _audit_androidcontrol(args)
    if args.command == "summarize" and args.corpus == "androidcontrol":
        return _summarize_androidcontrol(args)
    if args.command == "report":
        return _report(args)
    return 2  # pragma: no cover - argparse enforces the choices above


if __name__ == "__main__":
    raise SystemExit(main())
