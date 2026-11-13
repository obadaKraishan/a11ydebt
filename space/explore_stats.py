"""The Explore tab's numbers, computed from the per-screen statistics Parquet files.

Pure functions over numpy arrays (no Gradio, no pandas), so the tests run in the package's
development environment. The data is ids and counts only; see ``build_stats.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

POPULATIONS = ("needs_label", "icon_like")
POPULATION_LABELS = {
    "needs_label": "Needs a label (the paper's main measure)",
    "icon_like": "Icon-like (tappable graphic, no text)",
}
CORPUS_LABELS = {
    "rico": "Rico (2017)",
    "ac10": "AndroidControl (2024), the paper's 10 shards",
    "ac20": "AndroidControl (2024), all 20 shards",
}
SHORT_LABELS = {"rico": "Rico", "ac10": "AndroidControl", "ac20": "AndroidControl"}

#: Per-screen coverage bins: none, then tenths, then all. Coverage is labelled / candidates.
COVERAGE_BINS: tuple[str, ...] = (
    "0% (none)",
    "under 10%",
    *(f"{10 * i} to {10 * i + 9}%" for i in range(1, 10)),
    "100% (all)",
)
#: Unlabelled elements per screen: (label, low, high) with high inclusive, None for open.
UNLABELLED_BINS: tuple[tuple[str, int, int | None], ...] = (
    ("0", 0, 0),
    ("1", 1, 1),
    ("2 to 4", 2, 4),
    ("5 to 9", 5, 9),
    ("10 to 19", 10, 19),
    ("20 to 49", 20, 49),
    ("50 or more", 50, None),
)

LOOKUP = {
    "rico": (
        "To look a Rico screen up, open `combined/<screen id>.json` (the view hierarchy) or "
        "`combined/<screen id>.jpg` in your own copy of Rico's `unique_uis.tar.gz`."
    ),
    "androidcontrol": (
        "To look an AndroidControl screen up, open shard "
        "`android_control-000NN-of-00020` (NN is the shard below) in your own copy, find the "
        "record whose `episode_id` matches, and read `accessibility_trees[step]` "
        "(the screenshot is `screenshots[step]`)."
    ),
}

_NUMERIC = (
    "n_nodes",
    "n_included",
    *(f"{p}_{k}" for p in POPULATIONS for k in ("candidates", "labelled", "unlabelled")),
)


@dataclass(frozen=True)
class Stats:
    """The per-screen table as numpy columns."""

    dataset: np.ndarray  # str
    screen_id: np.ndarray  # str
    episode_id: np.ndarray  # int64, -1 for Rico
    step_index: np.ndarray  # int64, -1 for Rico
    shard: np.ndarray  # int64, -1 for Rico
    in_paper_sample: np.ndarray  # bool
    counts: dict[str, np.ndarray]  # int64 columns

    def __len__(self) -> int:
        return len(self.screen_id)

    def mask(self, corpus: str) -> np.ndarray:
        if corpus == "rico":
            return self.dataset == "rico"
        if corpus == "ac10":
            return (self.dataset == "androidcontrol") & self.in_paper_sample
        if corpus == "ac20":
            return self.dataset == "androidcontrol"
        raise ValueError(f"unknown corpus {corpus!r}")


def _ints(column: pa.ChunkedArray) -> np.ndarray:
    return np.asarray(column.fill_null(-1).to_numpy(), dtype=np.int64)


def from_table(table: pa.Table) -> Stats:
    return Stats(
        dataset=np.asarray(table.column("dataset").to_pylist(), dtype=object),
        screen_id=np.asarray(table.column("screen_id").to_pylist(), dtype=object),
        episode_id=_ints(table.column("episode_id")),
        step_index=_ints(table.column("step_index")),
        shard=_ints(table.column("shard")),
        in_paper_sample=np.asarray(table.column("in_paper_sample").to_numpy(), dtype=bool),
        counts={name: _ints(table.column(name)) for name in _NUMERIC},
    )


def load_stats(data_dir: str | Path) -> Stats:
    """Read ``rico.parquet`` and ``androidcontrol.parquet`` from ``data_dir``."""
    data_dir = Path(data_dir)
    tables = [pq.read_table(data_dir / f"{name}.parquet") for name in ("rico", "androidcontrol")]
    return from_table(pa.concat_tables(tables))


def _selection(stats: Stats, corpus: str, population: str, min_candidates: int) -> np.ndarray:
    """Screens in the corpus with at least ``min_candidates`` candidates (and at least one)."""
    floor = max(1, int(min_candidates))
    return stats.mask(corpus) & (stats.counts[f"{population}_candidates"] >= floor)


def headline(stats: Stats, corpus: str) -> dict[str, object]:
    """Corpus totals: the paper's Table 1 for this corpus, plus the share of screens with debt."""
    m = stats.mask(corpus)
    out: dict[str, object] = {
        "corpus": corpus,
        "screens": int(m.sum()),
        "n_included": int(stats.counts["n_included"][m].sum()),
    }
    for pop in POPULATIONS:
        cand = int(stats.counts[f"{pop}_candidates"][m].sum())
        lab = int(stats.counts[f"{pop}_labelled"][m].sum())
        with_cand = int((stats.counts[f"{pop}_candidates"][m] > 0).sum())
        debt = int((stats.counts[f"{pop}_unlabelled"][m] > 0).sum())
        out[pop] = {
            "candidates": cand,
            "labelled": lab,
            "coverage": lab / cand if cand else None,
            "screens_with_candidates": with_cand,
            "screens_with_debt": debt,
            "share_of_screens_with_debt": debt / out["screens"] if out["screens"] else None,
        }
    return out


def coverage_distribution(
    stats: Stats, corpus: str, population: str, min_candidates: int = 1
) -> list[tuple[str, int, float]]:
    """(bin, screens, share of selected screens) for per-screen coverage."""
    sel = _selection(stats, corpus, population, min_candidates)
    cand = stats.counts[f"{population}_candidates"][sel]
    lab = stats.counts[f"{population}_labelled"][sel]
    total = int(sel.sum())
    if total == 0:
        return [(label, 0, 0.0) for label in COVERAGE_BINS]
    # Integer arithmetic, so a screen at exactly 30% cannot land in the 20-29% bin.
    tenths = (10 * lab) // cand
    index = np.where(lab == 0, 0, np.where(lab >= cand, 11, 1 + tenths))
    counts = np.bincount(index, minlength=len(COVERAGE_BINS))
    return [(label, int(n), n / total) for label, n in zip(COVERAGE_BINS, counts, strict=True)]


def unlabelled_distribution(
    stats: Stats, corpus: str, population: str, min_candidates: int = 1
) -> list[tuple[str, int, float]]:
    """(bin, screens, share of selected screens) for unlabelled elements per screen."""
    sel = _selection(stats, corpus, population, min_candidates)
    unl = stats.counts[f"{population}_unlabelled"][sel]
    total = int(sel.sum())
    rows = []
    for label, low, high in UNLABELLED_BINS:
        inside = (unl >= low) if high is None else ((unl >= low) & (unl <= high))
        n = int(inside.sum())
        rows.append((label, n, n / total if total else 0.0))
    return rows


TOP_HEADERS = {
    "rico": ["Rank", "Screen id", "Need a label", "Labelled", "Unlabelled", "Coverage"],
    "androidcontrol": [
        "Rank",
        "Screen id",
        "Episode",
        "Step",
        "Shard",
        "Need a label",
        "Labelled",
        "Unlabelled",
        "Coverage",
    ],
}


def top_debt(
    stats: Stats, corpus: str, population: str, min_candidates: int = 1, n: int = 25
) -> list[list[object]]:
    """The screens with the most unlabelled elements; ties go to lower coverage, then id.

    Ids and counts only, so a reader can find each screen in their own copy of the corpus.
    """
    sel = np.flatnonzero(_selection(stats, corpus, population, min_candidates))
    cand = stats.counts[f"{population}_candidates"][sel]
    lab = stats.counts[f"{population}_labelled"][sel]
    unl = stats.counts[f"{population}_unlabelled"][sel]
    order = np.lexsort((sel, lab / cand, -unl))[: max(0, int(n))]
    rows: list[list[object]] = []
    for rank, i in enumerate(order, start=1):
        row = sel[i]
        coverage = f"{100 * lab[i] / cand[i]:.1f}%"
        if corpus == "rico":
            rows.append(
                [rank, stats.screen_id[row], int(cand[i]), int(lab[i]), int(unl[i]), coverage]
            )
        else:
            rows.append(
                [
                    rank,
                    stats.screen_id[row],
                    int(stats.episode_id[row]),
                    int(stats.step_index[row]),
                    f"{int(stats.shard[row]):05d}",
                    int(cand[i]),
                    int(lab[i]),
                    int(unl[i]),
                    coverage,
                ]
            )
    return rows
