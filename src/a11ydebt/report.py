"""Coverage report: Markdown and CSV tables with cluster-bootstrap intervals.

``a11ydebt report`` reads audit folders, the ``--out`` of ``a11ydebt audit`` or
``a11ydebt summarize``. From each folder it reads ``summary.json`` (corpus totals, the role
breakdown, screens with debt) and ``screens.csv`` (the per-screen counts the bootstrap
resamples). For each corpus it builds three tables:

1. Coverage for every population, with 95% cluster-bootstrap intervals for app clusters (the
   primary interval) and screen clusters (see ``a11ydebt.bootstrap``).
2. needs_label coverage by role.
3. Screens with at least one unlabelled element, per population.

``write_report`` writes ``report.md`` (every corpus), plus ``coverage.csv``, ``roles.csv`` and
``screens_with_debt.csv`` in long format with a ``corpus`` column. Each interval uses its own
generator seeded with ``seed``, so an interval never depends on which other intervals were
computed, or in what order.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel

from a11ydebt import __version__
from a11ydebt.bootstrap import (
    DEFAULT_CONF,
    DEFAULT_N_RESAMPLES,
    DEFAULT_SEED,
    LEVELS,
    ClusteredInterval,
    ScreenCount,
    cluster_key,
    clustered_interval,
    wilson_ci,
)
from a11ydebt.counts import LABEL_ROLES, POPULATIONS

__all__ = [
    "Audit",
    "CorpusReport",
    "build_report",
    "format_markdown",
    "load_audit",
    "write_report",
]


@dataclass(frozen=True)
class Audit:
    """One audit folder: its ``summary.json`` and its per-screen counts by population."""

    label: str
    path: Path
    summary: dict
    screens: dict[str, list[ScreenCount]]

    @property
    def dataset(self) -> str:
        return str(self.summary["dataset"])


def load_audit(path: str | Path, label: str | None = None) -> Audit:
    """Read ``summary.json`` and ``screens.csv`` from an audit folder.

    Raises ``FileNotFoundError`` when either file is missing, and ``ValueError`` when the
    per-screen counts do not add up to the corpus totals in ``summary.json``.
    """
    root = Path(path)
    summary_path, screens_path = root / "summary.json", root / "screens.csv"
    for p in (summary_path, screens_path):
        if not p.is_file():
            raise FileNotFoundError(f"{p} not found; run `a11ydebt audit` or `summarize` first")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    populations = [p for p in summary.get("populations", POPULATIONS) if p in POPULATIONS]
    screens: dict[str, list[ScreenCount]] = {p: [] for p in populations}
    with screens_path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            for p in populations:
                screens[p].append(
                    ScreenCount(
                        screen_id=row["screen_id"],
                        app=row["app"],
                        labelled=int(row[f"{p}_labelled"]),
                        candidates=int(row[f"{p}_candidates"]),
                    )
                )
    corpus = summary["corpus"]
    for p, rows in screens.items():
        totals = (sum(r.candidates for r in rows), sum(r.labelled for r in rows))
        expected = corpus["populations"][p]
        if totals != (expected["candidates"], expected["labelled"]) or (
            len(rows) != corpus["n_screens"]
        ):
            raise ValueError(
                f"{screens_path} does not add up to {summary_path} for {p}: "
                f"{len(rows):,} screens, {totals[0]:,} candidates, {totals[1]:,} labelled"
            )
    return Audit(
        label=label or str(summary["dataset"]), path=root, summary=summary, screens=screens
    )


class PopulationRow(BaseModel):
    population: str
    candidates: int
    labelled: int
    coverage: float | None
    wilson_low: float | None
    wilson_high: float | None
    intervals: dict[str, ClusteredInterval]  # by cluster level


class RoleRow(BaseModel):
    role: str
    candidates: int
    labelled: int
    coverage: float | None


class DebtRow(BaseModel):
    population: str
    screens: int
    screens_with_candidates: int
    screens_with_debt: int


class CorpusReport(BaseModel):
    label: str
    dataset: str
    source: str
    n_screens: int
    n_apps: int  # identified apps; screens with app "" are not an app
    n_no_app: int = 0  # app clusters with no identified app: episodes (AndroidControl), screens
    n_nodes: int
    n_included: int
    n_resamples: int
    seed: int | None
    conf: float
    populations: list[PopulationRow]
    roles: list[RoleRow]
    debt: list[DebtRow]


#: The report's intervals and the paper's are both exact, from different seeds.
SEED_FOOTNOTE = (
    "[^seeds]: Intervals use independent seeds. The AISSA 2026 paper's shared-stream intervals "
    "(Table I) are reproduced exactly by `scripts/compare_aissa.py bootstrap`; see "
    "[docs/reproduction-bootstrap.md](https://github.com/obadaKraishan/a11ydebt/blob/main/docs/"
    "reproduction-bootstrap.md)."
)


def _none_if_nan(value: float) -> float | None:
    return None if value != value else value


def no_app_unit(dataset: str) -> str:
    """What a no-app app cluster is (``bootstrap.cluster_key``): an episode or a screen."""
    return "episode" if dataset == "androidcontrol" else "screen"


def _no_app_clusters(audit: Audit) -> int:
    """App clusters with no identified app, over all screens (with or without candidates)."""
    rows = next(iter(audit.screens.values()), [])
    return len({cluster_key("app", audit.dataset, r.screen_id, r.app) for r in rows if not r.app})


def build_report(
    audit: Audit,
    *,
    n_resamples: int = DEFAULT_N_RESAMPLES,
    seed: int | None = DEFAULT_SEED,
    conf: float = DEFAULT_CONF,
) -> CorpusReport:
    """The three tables for one corpus. Every interval is seeded with ``seed`` on its own."""
    corpus = audit.summary["corpus"]
    populations = []
    debt = []
    for p, rows in audit.screens.items():
        totals = corpus["populations"][p]
        k, n = totals["labelled"], totals["candidates"]
        low, high = wilson_ci(k, n, conf)
        intervals = {
            level: clustered_interval(
                rows,
                level=level,
                dataset=audit.dataset,
                n_resamples=n_resamples,
                seed=seed,
                conf=conf,
            )
            for level in LEVELS
        }
        populations.append(
            PopulationRow(
                population=p,
                candidates=n,
                labelled=k,
                coverage=k / n if n else None,
                wilson_low=_none_if_nan(low),
                wilson_high=_none_if_nan(high),
                intervals=intervals,
            )
        )
        with_debt = sum(1 for r in rows if r.labelled < r.candidates)
        if with_debt != corpus["screens_with_debt"][p]:
            raise ValueError(f"{audit.path}: screens with debt for {p} disagree with summary.json")
        debt.append(
            DebtRow(
                population=p,
                screens=corpus["n_screens"],
                screens_with_candidates=sum(1 for r in rows if r.candidates > 0),
                screens_with_debt=with_debt,
            )
        )
    by_role = corpus["needs_label_by_role"]
    order = [r for r in LABEL_ROLES if r in by_role] + sorted(set(by_role) - set(LABEL_ROLES))
    roles = [
        RoleRow(
            role=r,
            candidates=by_role[r]["candidates"],
            labelled=by_role[r]["labelled"],
            coverage=by_role[r]["coverage"],
        )
        for r in order
    ]
    return CorpusReport(
        label=audit.label,
        dataset=audit.dataset,
        source=str(audit.summary.get("source") or audit.path),
        n_screens=corpus["n_screens"],
        n_apps=corpus["n_apps"],
        n_no_app=_no_app_clusters(audit),
        n_nodes=corpus["n_nodes"],
        n_included=corpus["n_included"],
        n_resamples=n_resamples,
        seed=seed,
        conf=conf,
        populations=populations,
        roles=roles,
        debt=debt,
    )


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{100 * value:.2f}"


def _ci(low: float | None, high: float | None) -> str:
    return "n/a" if low is None or high is None else f"[{100 * low:.2f}, {100 * high:.2f}]"


def _share(part: int, whole: int) -> float | None:
    return part / whole if whole else None


def _count(n: int, noun: str) -> str:
    """``1 identified app``, ``701 identified apps``, ``0 screens``."""
    return f"{n:,} {noun}{'' if n == 1 else 's'}"


def format_markdown(reports: list[CorpusReport], *, generated_at: str = "") -> str:
    """``report.md``: a header that states the method, then three tables per corpus."""
    first = reports[0]
    level = f"{100 * first.conf:g}%"
    lines = [
        "# a11ydebt coverage report",
        "",
        f"a11ydebt {__version__}" + (f" · generated {generated_at}" if generated_at else ""),
        "",
        f"Coverage is pooled: labelled / candidates. The {level} intervals are the percentile "
        f"intervals of {first.n_resamples:,} cluster-bootstrap resamples (seed {first.seed}). "
        "Each interval has its own generator seeded with the seed.[^seeds] App clusters are "
        "apps; on AndroidControl, an episode with no identified app is its own cluster. Screen "
        "clusters are screens. Only clusters with at least one candidate are resampled, so the "
        "App clusters column, which counts them per population, can be smaller than the "
        "identified apps plus the episodes with no identified app.",
    ]
    for r in reports:
        no_app = _count(r.n_no_app, no_app_unit(r.dataset))
        lines += [
            "",
            f"## {r.label}",
            "",
            f"Dataset `{r.dataset}` from `{r.source}`: {r.n_screens:,} screens, {r.n_nodes:,} "
            f"nodes ({r.n_included:,} included: visible, positive area), "
            f"{_count(r.n_apps, 'identified app')} and {no_app} with no identified app.",
            "",
            f"**Coverage with {level} cluster-bootstrap intervals**",
            "",
            f"| Population | Candidates | Labelled | Coverage % | {level} CI, app clusters "
            f"| App clusters | {level} CI, screen clusters | Screen clusters |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for p in r.populations:
            app, screen = p.intervals["app"], p.intervals["screen"]
            lines.append(
                f"| {p.population} | {p.candidates:,} | {p.labelled:,} | {_pct(p.coverage)} "
                f"| {_ci(app.ci_low, app.ci_high)} | {app.n_clusters:,} "
                f"| {_ci(screen.ci_low, screen.ci_high)} | {screen.n_clusters:,} |"
            )
        lines += [
            "",
            "**needs_label by role**",
            "",
            "| Role | Candidates | Labelled | Coverage % |",
            "|---|---:|---:|---:|",
        ]
        lines += [
            f"| {x.role} | {x.candidates:,} | {x.labelled:,} | {_pct(x.coverage)} |"
            for x in r.roles
        ]
        lines += [
            "",
            "**Screens with at least one unlabelled element**",
            "",
            "| Population | Screens with candidates | Screens with ≥1 unlabelled "
            "| % of all screens | % of screens with candidates |",
            "|---|---:|---:|---:|---:|",
        ]
        lines += [
            f"| {d.population} | {d.screens_with_candidates:,} | {d.screens_with_debt:,} "
            f"| {_pct(_share(d.screens_with_debt, d.screens))} "
            f"| {_pct(_share(d.screens_with_debt, d.screens_with_candidates))} |"
            for d in r.debt
        ]
    lines += ["", SEED_FOOTNOTE]
    return "\n".join(lines) + "\n"


def _cell(value: float | None) -> str:
    return "" if value is None else f"{value:.6f}"


def write_report(reports: list[CorpusReport], out: str | Path) -> list[Path]:
    """Write report.md, coverage.csv, roles.csv and screens_with_debt.csv into ``out``."""
    if not reports:
        raise ValueError("nothing to report")
    root = Path(out)
    root.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    md = root / "report.md"
    md.write_text(format_markdown(reports, generated_at=generated_at), encoding="utf-8")

    coverage_csv = root / "coverage.csv"
    with coverage_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        level_headers = [
            f"{lv}_{field}" for lv in LEVELS for field in ("clusters", "ci_low", "ci_high")
        ]
        writer.writerow(
            [
                "corpus",
                "dataset",
                "population",
                "candidates",
                "labelled",
                "coverage",
                "wilson_low",
                "wilson_high",
                *level_headers,
                "n_resamples",
                "seed",
                "conf",
            ]
        )
        for r in reports:
            for p in r.populations:
                levels = [
                    cell
                    for lv in LEVELS
                    for cell in (
                        p.intervals[lv].n_clusters,
                        _cell(p.intervals[lv].ci_low),
                        _cell(p.intervals[lv].ci_high),
                    )
                ]
                writer.writerow(
                    [
                        r.label,
                        r.dataset,
                        p.population,
                        p.candidates,
                        p.labelled,
                        _cell(p.coverage),
                        _cell(p.wilson_low),
                        _cell(p.wilson_high),
                        *levels,
                        r.n_resamples,
                        "" if r.seed is None else r.seed,
                        r.conf,
                    ]
                )

    roles_csv = root / "roles.csv"
    with roles_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["corpus", "dataset", "role", "candidates", "labelled", "coverage"])
        for r in reports:
            for x in r.roles:
                writer.writerow(
                    [r.label, r.dataset, x.role, x.candidates, x.labelled, _cell(x.coverage)]
                )

    debt_csv = root / "screens_with_debt.csv"
    with debt_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "corpus",
                "dataset",
                "population",
                "screens",
                "screens_with_candidates",
                "screens_with_debt",
                "share_of_screens",
                "share_of_screens_with_candidates",
            ]
        )
        for r in reports:
            for d in r.debt:
                writer.writerow(
                    [
                        r.label,
                        r.dataset,
                        d.population,
                        d.screens,
                        d.screens_with_candidates,
                        d.screens_with_debt,
                        _cell(_share(d.screens_with_debt, d.screens)),
                        _cell(_share(d.screens_with_debt, d.screens_with_candidates)),
                    ]
                )
    return [md, coverage_csv, roles_csv, debt_csv]
