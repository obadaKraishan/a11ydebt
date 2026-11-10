"""Cluster-bootstrap intervals for pooled coverage (labelled / candidates).

Elements are nested in screens, and screens in apps, so element-level intervals are too narrow.
The cluster bootstrap resamples whole clusters with replacement and recomputes the pooled rate
``sum(labelled) / sum(candidates)``. The interval is the 2.5th and 97.5th percentile of the
draws.

Ported from accessibility-debt-agents (commit 97c0378, MIT; see NOTICE):
``cluster_bootstrap_rate`` and ``pct_ci`` from ``phase4_validation/03_reviewer_checks.py``,
``wilson_ci`` from ``src/a11ydebt/stats.py``, and the defaults (seed 20260908, 5,000 resamples)
from ``config.yaml``. AISSA's ``src/a11ydebt/bootstrap.py`` is only an import shim and holds no
bootstrap code.

The algorithm is unchanged: each resample draws ``rng.integers(0, m, m)`` cluster indices. Here
a block of resamples is drawn at once (``size=(rows, m)``), which consumes numpy's generator
exactly as AISSA's one-call-per-resample loop does. Given the same generator state, the draws are
bit-identical to AISSA's and the generator ends in the same state (``tests/test_bootstrap.py``).

Clusters follow AISSA's ReviewerChecks:

* ``screen``: each screen with at least one candidate is a cluster.
* ``app``: each app is a cluster. On AndroidControl, an episode with no identified app is its own
  cluster (``episode:<id>``), so the interval is centred on the same estimate as the others. On
  Rico, a screen with no app would be its own cluster (``screen:<id>``). AISSA drops such Rico
  screens instead, but Rico has none, so the two rules give the same clusters.

Clusters are ordered by key (Python string order, the same as pandas ``groupby``), because the
order decides which cluster each drawn index picks.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from statistics import NormalDist
from typing import NamedTuple

import numpy as np
from pydantic import BaseModel, ConfigDict

__all__ = [
    "DEFAULT_CONF",
    "DEFAULT_N_RESAMPLES",
    "DEFAULT_SEED",
    "LEVELS",
    "ClusteredInterval",
    "ScreenCount",
    "cluster_bootstrap_rate",
    "cluster_key",
    "cluster_totals",
    "clustered_interval",
    "percentile_ci",
    "wilson_ci",
]

#: AISSA config.yaml ``run.seed`` and ``run.n_bootstrap``.
DEFAULT_SEED = 20260908
DEFAULT_N_RESAMPLES = 5000
DEFAULT_CONF = 0.95
#: Cluster levels, in report order: apps (the primary interval), then screens.
LEVELS: tuple[str, ...] = ("app", "screen")
_BLOCK_ELEMENTS = 1 << 22  # cluster indices drawn per block: 32 MB of int64


class ScreenCount(NamedTuple):
    """One screen's counts for one population, as the bootstrap needs them."""

    screen_id: str
    app: str
    labelled: int
    candidates: int


def _quantile_levels(conf: float) -> tuple[float, float]:
    # (1 - 0.95) / 2 is 0.025000000000000022 in floating point; rounding gives AISSA's literal
    # 0.025 and 0.975, so the percentiles are bit-identical to its pct_ci.
    if not 0 < conf < 1:
        raise ValueError(f"conf must be between 0 and 1, got {conf}")
    low = round((1 - conf) / 2, 10)
    return low, round(1 - low, 10)


def cluster_bootstrap_rate(
    labelled: Iterable[int] | np.ndarray,
    candidates: Iterable[int] | np.ndarray,
    *,
    n_resamples: int = DEFAULT_N_RESAMPLES,
    seed: int | None = DEFAULT_SEED,
    rng: np.random.Generator | None = None,
    block_elements: int = _BLOCK_ELEMENTS,
) -> np.ndarray:
    """Bootstrap draws of the pooled rate ``sum(labelled) / sum(candidates)`` over clusters.

    ``labelled[i]`` and ``candidates[i]`` are cluster ``i``'s totals. Each of the
    ``n_resamples`` draws resamples the ``m`` clusters with replacement. Pass ``rng`` to continue
    an existing generator (as AISSA does across its tables); otherwise a new generator is seeded
    with ``seed``. ``block_elements`` only bounds memory and never changes the draws. A draw whose
    resampled clusters have no candidates is NaN, and with no clusters every draw is NaN.
    """
    k = np.asarray(labelled, dtype=np.int64)
    n = np.asarray(candidates, dtype=np.int64)
    if k.ndim != 1 or k.shape != n.shape:
        raise ValueError("labelled and candidates must be 1-D arrays of the same length")
    if n_resamples < 1:
        raise ValueError(f"n_resamples must be at least 1, got {n_resamples}")
    if (k < 0).any() or (k > n).any():
        raise ValueError("every cluster needs 0 <= labelled <= candidates")
    out = np.full(n_resamples, np.nan)
    m = k.size
    if m == 0:
        return out
    gen = rng if rng is not None else np.random.default_rng(seed)
    rows = max(1, block_elements // m)
    for start in range(0, n_resamples, rows):
        stop = min(start + rows, n_resamples)
        idx = gen.integers(0, m, size=(stop - start, m))
        kk = k[idx].sum(axis=1)
        nn = n[idx].sum(axis=1)
        with np.errstate(invalid="ignore", divide="ignore"):
            out[start:stop] = np.where(nn > 0, kk / nn, np.nan)
    return out


def percentile_ci(draws: np.ndarray, conf: float = DEFAULT_CONF) -> tuple[float, float]:
    """Percentile interval of the draws, ignoring NaN (AISSA ``pct_ci``)."""
    low, high = _quantile_levels(conf)
    arr = np.asarray(draws, dtype=float)
    if np.isnan(arr).all():
        return float("nan"), float("nan")
    return float(np.nanquantile(arr, low)), float(np.nanquantile(arr, high))


def wilson_ci(labelled: int, candidates: int, conf: float = DEFAULT_CONF) -> tuple[float, float]:
    """Element-level Wilson score interval (AISSA ``stats.wilson_ci``, with a stdlib z)."""
    if candidates == 0:
        return float("nan"), float("nan")
    _quantile_levels(conf)
    z = NormalDist().inv_cdf(1 - (1 - conf) / 2)
    p = labelled / candidates
    denom = 1 + z**2 / candidates
    centre = (p + z**2 / (2 * candidates)) / denom
    half = z * (p * (1 - p) / candidates + z**2 / (4 * candidates**2)) ** 0.5 / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def _episode(screen_id: str) -> str:
    # AndroidControl screen ids are f"{episode_id}_{step_index}" (a11ydebt.androidcontrol).
    return screen_id.rsplit("_", 1)[0]


def cluster_key(level: str, dataset: str, screen_id: str, app: str) -> str:
    """The cluster a screen belongs to at ``level`` (``"app"`` or ``"screen"``)."""
    if level == "screen":
        return screen_id
    if level != "app":
        raise ValueError(f"level must be one of {LEVELS}, got {level!r}")
    if app:
        return app
    if dataset == "androidcontrol":
        return f"episode:{_episode(screen_id)}"
    return f"screen:{screen_id}"


def cluster_totals(
    screens: Iterable[ScreenCount], *, level: str, dataset: str
) -> tuple[list[str], np.ndarray, np.ndarray]:
    """Sorted cluster keys with their labelled and candidate totals.

    Only screens with at least one candidate contribute, so every cluster has candidates.
    """
    labelled: dict[str, int] = defaultdict(int)
    candidates: dict[str, int] = defaultdict(int)
    for s in screens:
        if s.candidates <= 0:
            continue
        key = cluster_key(level, dataset, s.screen_id, s.app)
        labelled[key] += s.labelled
        candidates[key] += s.candidates
    keys = sorted(candidates)
    return (
        keys,
        np.array([labelled[key] for key in keys], dtype=np.int64),
        np.array([candidates[key] for key in keys], dtype=np.int64),
    )


class ClusteredInterval(BaseModel):
    """Pooled coverage with its cluster-bootstrap percentile interval."""

    model_config = ConfigDict(frozen=True)

    level: str
    n_clusters: int
    labelled: int
    candidates: int
    coverage: float | None
    ci_low: float | None
    ci_high: float | None
    n_resamples: int
    seed: int | None
    conf: float


def clustered_interval(
    screens: Iterable[ScreenCount],
    *,
    level: str,
    dataset: str,
    n_resamples: int = DEFAULT_N_RESAMPLES,
    seed: int | None = DEFAULT_SEED,
    conf: float = DEFAULT_CONF,
    rng: np.random.Generator | None = None,
) -> ClusteredInterval:
    """Coverage and its ``conf`` cluster-bootstrap interval at ``level`` for one population."""
    _keys, k, n = cluster_totals(screens, level=level, dataset=dataset)
    draws = cluster_bootstrap_rate(k, n, n_resamples=n_resamples, seed=seed, rng=rng)
    low, high = percentile_ci(draws, conf)
    total_k, total_n = int(k.sum()), int(n.sum())
    return ClusteredInterval(
        level=level,
        n_clusters=len(k),
        labelled=total_k,
        candidates=total_n,
        coverage=total_k / total_n if total_n else None,
        ci_low=None if np.isnan(low) else low,
        ci_high=None if np.isnan(high) else high,
        n_resamples=n_resamples,
        seed=seed if rng is None else None,
        conf=conf,
    )
