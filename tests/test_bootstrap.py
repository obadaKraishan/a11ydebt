"""a11ydebt.bootstrap on small synthetic clusters whose answers are known exactly."""

from __future__ import annotations

import numpy as np
import pytest

from a11ydebt.bootstrap import (
    DEFAULT_N_RESAMPLES,
    DEFAULT_SEED,
    ScreenCount,
    cluster_bootstrap_rate,
    cluster_key,
    cluster_totals,
    clustered_interval,
    percentile_ci,
    wilson_ci,
)


def aissa_cluster_bootstrap_rate(k, n, rng, n_boot):
    """AISSA's loop, verbatim from phase4_validation/03_reviewer_checks.py (commit 97c0378)."""
    m = len(k)
    out = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, m, m)
        kk, nn = k[idx].sum(), n[idx].sum()
        out[b] = kk / nn if nn else np.nan
    return out


def aissa_pct_ci(draws):
    return float(np.nanquantile(draws, 0.025)), float(np.nanquantile(draws, 0.975))


def test_defaults_are_aissas():
    assert (DEFAULT_SEED, DEFAULT_N_RESAMPLES) == (20260908, 5000)


def test_equal_rates_give_a_degenerate_interval():
    # Every cluster is labelled at exactly 50%, so every resample pools to exactly 0.5.
    draws = cluster_bootstrap_rate([1, 2, 3], [2, 4, 6], n_resamples=500)
    assert np.all(draws == 0.5)
    assert percentile_ci(draws) == (0.5, 0.5)


def test_two_clusters_match_the_exact_resampling_distribution():
    # Clusters 0/1 and 1/1: a resample of 2 gives 0, 1/2 or 1 with probability 1/4, 1/2, 1/4.
    draws = cluster_bootstrap_rate([0, 1], [1, 1], n_resamples=40_000, seed=7)
    values, counts = np.unique(draws, return_counts=True)
    assert values.tolist() == [0.0, 0.5, 1.0]
    assert counts / counts.sum() == pytest.approx([0.25, 0.5, 0.25], abs=0.01)
    assert percentile_ci(draws) == (0.0, 1.0)


def test_rates_are_pooled_not_averaged():
    # 0/1 and 9/9: a mixed resample pools to 9/10 = 0.9 (a mean of rates would give 0.5).
    draws = cluster_bootstrap_rate([0, 9], [1, 9], n_resamples=2_000, seed=1)
    assert set(np.unique(draws).tolist()) == {0.0, 0.9, 1.0}


@pytest.mark.parametrize("m", [1, 2, 7, 951])
@pytest.mark.parametrize("block_elements", [1, 50, 1 << 22])
def test_bit_identical_to_aissas_loop_whatever_the_block_size(m, block_elements):
    gen = np.random.default_rng(123)
    n = gen.integers(1, 40, m)
    k = gen.integers(0, n + 1)
    theirs = np.random.default_rng(DEFAULT_SEED)
    ours = np.random.default_rng(DEFAULT_SEED)
    expected = aissa_cluster_bootstrap_rate(k, n, theirs, 300)
    got = cluster_bootstrap_rate(k, n, n_resamples=300, rng=ours, block_elements=block_elements)
    assert np.array_equal(expected, got)
    assert percentile_ci(got) == aissa_pct_ci(expected)
    # The generator ends where AISSA's does, so a shared stream stays in step across tables.
    assert ours.integers(0, 2**62) == theirs.integers(0, 2**62)


def test_a_shared_generator_continues_the_stream_like_aissa():
    k1, n1 = np.array([3, 0, 5]), np.array([4, 2, 9])
    k2, n2 = np.array([1, 1]), np.array([3, 1])
    theirs = np.random.default_rng(DEFAULT_SEED)
    a1 = aissa_cluster_bootstrap_rate(k1, n1, theirs, 100)
    a2 = aissa_cluster_bootstrap_rate(k2, n2, theirs, 100)
    ours = np.random.default_rng(DEFAULT_SEED)
    assert np.array_equal(a1, cluster_bootstrap_rate(k1, n1, n_resamples=100, rng=ours))
    assert np.array_equal(a2, cluster_bootstrap_rate(k2, n2, n_resamples=100, rng=ours))


def test_seed_and_resample_count_are_configurable():
    k, n = [0, 1, 2, 3], [4, 4, 4, 4]
    a = cluster_bootstrap_rate(k, n, n_resamples=250, seed=1)
    assert a.shape == (250,)
    assert np.array_equal(a, cluster_bootstrap_rate(k, n, n_resamples=250, seed=1))
    assert not np.array_equal(a, cluster_bootstrap_rate(k, n, n_resamples=250, seed=2))


def test_no_clusters_and_bad_input():
    assert np.isnan(cluster_bootstrap_rate([], [], n_resamples=5)).all()
    assert all(np.isnan(v) for v in percentile_ci(np.full(5, np.nan)))
    with pytest.raises(ValueError):
        cluster_bootstrap_rate([1], [1, 2])
    with pytest.raises(ValueError):
        cluster_bootstrap_rate([3], [2])
    with pytest.raises(ValueError):
        cluster_bootstrap_rate([1], [2], n_resamples=0)
    with pytest.raises(ValueError):
        percentile_ci(np.zeros(3), conf=1.0)


def test_percentile_levels_match_aissas_literals():
    draws = np.random.default_rng(0).random(4_999)
    assert percentile_ci(draws) == aissa_pct_ci(draws)
    assert percentile_ci(np.arange(101) / 100, conf=0.90) == pytest.approx((0.05, 0.95))


def test_wilson_interval():
    low, high = wilson_ci(50, 100)
    assert (low, high) == pytest.approx((0.40383, 0.59617), abs=1e-5)
    assert wilson_ci(0, 10)[0] == 0.0
    assert all(np.isnan(v) for v in wilson_ci(0, 0))


def test_cluster_keys():
    assert cluster_key("screen", "androidcontrol", "12_3", "") == "12_3"
    assert cluster_key("app", "androidcontrol", "12_3", "com.example") == "com.example"
    assert cluster_key("app", "androidcontrol", "12_3", "") == "episode:12"
    assert cluster_key("app", "rico", "4711", "") == "screen:4711"
    with pytest.raises(ValueError):
        cluster_key("episode", "rico", "1", "")


def test_cluster_totals_group_sort_and_skip_empty_screens():
    screens = [
        ScreenCount("7_0", "org.b", 1, 2),
        ScreenCount("7_1", "org.b", 0, 0),  # no candidates: not a cluster at any level
        ScreenCount("10_0", "", 2, 3),  # no app: its episode is the cluster
        ScreenCount("10_1", "", 1, 1),
        ScreenCount("3_0", "com.a", 0, 4),
    ]
    keys, k, n = cluster_totals(screens, level="app", dataset="androidcontrol")
    assert keys == ["com.a", "episode:10", "org.b"]
    assert k.tolist() == [0, 3, 1]
    assert n.tolist() == [4, 4, 2]
    keys, k, n = cluster_totals(screens, level="screen", dataset="androidcontrol")
    assert keys == ["10_0", "10_1", "3_0", "7_0"]  # string order, as pandas groupby sorts
    assert n.tolist() == [3, 1, 4, 2]


def test_clustered_interval():
    screens = [
        ScreenCount("1", "a", 1, 2),
        ScreenCount("2", "a", 2, 4),
        ScreenCount("3", "b", 3, 6),
        ScreenCount("4", "c", 0, 0),
    ]
    result = clustered_interval(screens, level="app", dataset="rico", n_resamples=100)
    assert (result.n_clusters, result.labelled, result.candidates) == (2, 6, 12)
    assert (result.coverage, result.ci_low, result.ci_high) == (0.5, 0.5, 0.5)
    assert (result.n_resamples, result.seed, result.conf) == (100, DEFAULT_SEED, 0.95)
    empty = clustered_interval([], level="screen", dataset="rico", n_resamples=10)
    assert (empty.n_clusters, empty.coverage, empty.ci_low, empty.ci_high) == (0, None, None, None)
