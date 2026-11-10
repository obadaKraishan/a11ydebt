"""Content-description coverage per screen, per app and per corpus.

``coverage()`` turns parsed screens into counts and proportions for every population in
:data:`a11ydebt.rico.POPULATIONS`. ``audit_rico()`` runs the whole pipeline over a Rico folder,
optionally in parallel, and records unreadable files instead of stopping.

Proportions are pooled: an app's coverage is labelled / candidates over all of its screens,
which is how the AISSA paper reports corpus coverage. Bootstrap intervals clustered by app
arrive in S3.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from pydantic import BaseModel, ConfigDict, computed_field

from a11ydebt.rico import POPULATIONS, RicoScreen, find_screen_files, load_screen, read_ui_details

__all__ = [
    "AppCoverage",
    "CorpusCoverage",
    "Counts",
    "CoverageReport",
    "ParseFailure",
    "ScreenCoverage",
    "audit_rico",
    "coverage",
    "screen_coverage",
]


class Counts(BaseModel):
    """Elements in a population (``candidates``) and how many carry a content description."""

    model_config = ConfigDict(frozen=True)

    candidates: int = 0
    labelled: int = 0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def unlabelled(self) -> int:
        return self.candidates - self.labelled

    @computed_field  # type: ignore[prop-decorator]
    @property
    def coverage(self) -> float | None:
        """Share labelled (the paper's "label coverage"); None when there are no candidates."""
        return self.labelled / self.candidates if self.candidates else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def debt(self) -> float | None:
        """Share unlabelled, i.e. 1 - coverage; None when there are no candidates."""
        return self.unlabelled / self.candidates if self.candidates else None

    def __add__(self, other: Counts) -> Counts:
        return Counts(
            candidates=self.candidates + other.candidates, labelled=self.labelled + other.labelled
        )


class ScreenCoverage(BaseModel):
    model_config = ConfigDict(frozen=True)

    screen_id: str
    app: str
    n_nodes: int
    n_included: int
    populations: dict[str, Counts]
    needs_label_by_role: dict[str, Counts]


class AppCoverage(BaseModel):
    app: str
    n_screens: int
    n_nodes: int
    n_included: int
    populations: dict[str, Counts]
    screens_with_debt: dict[str, int]  # screens with at least one unlabelled candidate


class CorpusCoverage(BaseModel):
    n_screens: int
    n_apps: int
    n_nodes: int
    n_included: int
    populations: dict[str, Counts]
    screens_with_debt: dict[str, int]
    needs_label_by_role: dict[str, Counts]


class ParseFailure(BaseModel):
    screen_id: str
    path: str
    error: str


class CoverageReport(BaseModel):
    dataset: str
    populations: tuple[str, ...] = POPULATIONS
    screens: list[ScreenCoverage]
    apps: list[AppCoverage]
    corpus: CorpusCoverage
    failures: list[ParseFailure] = []


def screen_coverage(screen: RicoScreen) -> ScreenCoverage:
    """Counts for one screen, over included nodes only."""
    candidates = dict.fromkeys(POPULATIONS, 0)
    labelled = dict.fromkeys(POPULATIONS, 0)
    role_candidates: dict[str, int] = defaultdict(int)
    role_labelled: dict[str, int] = defaultdict(int)
    n_included = 0
    for node in screen.nodes:
        if not node.included:
            continue
        n_included += 1
        has_label = node.labelled
        for population in POPULATIONS:
            if getattr(node, population):
                candidates[population] += 1
                labelled[population] += has_label
        if node.needs_label:
            role_candidates[node.role] += 1
            role_labelled[node.role] += has_label
    return ScreenCoverage(
        screen_id=screen.screen_id,
        app=screen.app,
        n_nodes=len(screen.nodes),
        n_included=n_included,
        populations={
            p: Counts(candidates=candidates[p], labelled=labelled[p]) for p in POPULATIONS
        },
        needs_label_by_role={
            role: Counts(candidates=role_candidates[role], labelled=role_labelled[role])
            for role in sorted(role_candidates)
        },
    )


def _sum(counts: Iterable[Counts]) -> Counts:
    total = Counts()
    for c in counts:
        total = total + c
    return total


def coverage(
    screens: Iterable[RicoScreen | ScreenCoverage],
    *,
    dataset: str = "rico",
    failures: Iterable[ParseFailure] = (),
) -> CoverageReport:
    """Counts and proportions per screen, per app and for the whole corpus."""
    per_screen = [s if isinstance(s, ScreenCoverage) else screen_coverage(s) for s in screens]

    by_app: dict[str, list[ScreenCoverage]] = defaultdict(list)
    for s in per_screen:
        by_app[s.app].append(s)

    def debt_screens(group: list[ScreenCoverage]) -> dict[str, int]:
        return {p: sum(1 for s in group if s.populations[p].unlabelled > 0) for p in POPULATIONS}

    apps = [
        AppCoverage(
            app=app,
            n_screens=len(group),
            n_nodes=sum(s.n_nodes for s in group),
            n_included=sum(s.n_included for s in group),
            populations={p: _sum(s.populations[p] for s in group) for p in POPULATIONS},
            screens_with_debt=debt_screens(group),
        )
        for app, group in sorted(by_app.items())
    ]

    roles = sorted({role for s in per_screen for role in s.needs_label_by_role})
    corpus = CorpusCoverage(
        n_screens=len(per_screen),
        n_apps=len(apps),
        n_nodes=sum(s.n_nodes for s in per_screen),
        n_included=sum(s.n_included for s in per_screen),
        populations={p: _sum(a.populations[p] for a in apps) for p in POPULATIONS},
        screens_with_debt=debt_screens(per_screen),
        needs_label_by_role={
            role: _sum(
                s.needs_label_by_role[role] for s in per_screen if role in s.needs_label_by_role
            )
            for role in roles
        },
    )
    return CoverageReport(
        dataset=dataset, screens=per_screen, apps=apps, corpus=corpus, failures=list(failures)
    )


def _summarize_file(job: tuple[str, str | None]) -> ScreenCoverage | ParseFailure:
    path, app = job
    try:
        return screen_coverage(load_screen(path, app))
    except Exception as exc:  # one unreadable file must not stop a 66k-screen run
        return ParseFailure(
            screen_id=Path(path).stem, path=path, error=f"{type(exc).__name__}: {exc}"
        )


def audit_rico(
    rico_dir: str | Path,
    *,
    limit: int | None = None,
    workers: int = 1,
    progress: Callable[[int, int], None] | None = None,
) -> CoverageReport:
    """Parse every screen under ``rico_dir`` and return the coverage report.

    ``workers > 1`` parses files in a process pool. Files that fail to parse are listed in
    ``report.failures`` and are left out of every count.
    """
    root = Path(rico_dir)
    details = root / "ui_details.csv"
    apps = read_ui_details(details) if details.is_file() else {}
    files = find_screen_files(root)
    if limit:
        files = files[:limit]
    jobs = [(str(p), apps.get(p.stem)) for p in files]

    results: list[ScreenCoverage | ParseFailure] = []
    if workers > 1 and len(jobs) > 1:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            for result in pool.map(_summarize_file, jobs, chunksize=256):
                results.append(result)
                if progress:
                    progress(len(results), len(jobs))
    else:
        for job in jobs:
            results.append(_summarize_file(job))
            if progress:
                progress(len(results), len(jobs))

    screens = [r for r in results if isinstance(r, ScreenCoverage)]
    failures = [r for r in results if isinstance(r, ParseFailure)]
    return coverage(screens, dataset="rico", failures=failures)
