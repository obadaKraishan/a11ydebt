"""Corpus-level numbers the explorer shows beside the per-screen data.

These are copies of rows in a11ydebt's published tables (``results/v0.1/coverage.csv`` and
``results/v0.1/roles.csv`` in the GitHub repository). The intervals need the app of each screen,
which the per-screen dataset leaves out, so they cannot be recomputed from it. A test checks
every value here against those tables.
"""

from __future__ import annotations

#: The corpus keys the explorer uses, and the corpus names in results/v0.1.
CORPUS_NAMES = {
    "rico": "Rico",
    "ac10": "AndroidControl, 10 shards (the paper's sample)",
    "ac20": "AndroidControl, all 20 shards (robustness extension, not in the paper)",
}

#: 95% app-cluster bootstrap intervals (5,000 resamples, seed 20260908), as fractions.
APP_CLUSTER_CI: dict[str, dict[str, tuple[float, float]]] = {
    "rico": {"needs_label": (0.171244, 0.183668), "icon_like": (0.319637, 0.344696)},
    "ac10": {"needs_label": (0.556603, 0.588421), "icon_like": (0.577632, 0.673857)},
    "ac20": {"needs_label": (0.556930, 0.586485), "icon_like": (0.570673, 0.670338)},
}

#: Needs-label candidates and labelled elements by role (the paper's Table 2 measure).
ROLES: tuple[str, ...] = ("image", "button", "input", "other", "text")
ROLE_COUNTS: dict[str, dict[str, tuple[int, int]]] = {
    "rico": {
        "button": (76_461, 34_619),
        "image": (302_202, 29_063),
        "input": (29_416, 646),
        "other": (92_964, 24_755),
        "text": (1_542, 63),
    },
    "ac10": {
        "button": (108_037, 78_066),
        "image": (1_203_560, 703_149),
        "input": (24_402, 6_640),
        "other": (119_895, 46_654),
        "text": (6_650, 3_027),
    },
    "ac20": {
        "button": (218_529, 156_460),
        "image": (2_383_470, 1_389_033),
        "input": (49_004, 13_090),
        "other": (230_038, 89_759),
        "text": (13_144, 6_478),
    },
}
