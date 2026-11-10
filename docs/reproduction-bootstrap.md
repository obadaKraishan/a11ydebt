# Reproduction: cluster-bootstrap intervals (S3)

The AISSA camera-ready reports cluster-bootstrap intervals for needs-label coverage (Table I and
ReviewerChecks Check 1, from `phase4_validation/03_reviewer_checks.py`). a11ydebt ports that
bootstrap as `a11ydebt.bootstrap` and reproduces all six published intervals exactly.

## Method (unchanged from AISSA)
- Clusters are screens, or apps. On AndroidControl, an episode with no identified app is its own
  cluster (`episode:<id>`). Only clusters with at least one candidate are resampled, in sorted
  key order (pandas `groupby` order).
- Each resample draws `rng.integers(0, m, m)` cluster indices and pools
  `sum(labelled) / sum(candidates)`. The interval is the 2.5th and 97.5th `np.nanquantile` of the
  draws.
- There are 5,000 resamples, from one `np.random.default_rng(20260908)` generator (AISSA
  `config.yaml`).
- a11ydebt draws resamples in blocks (`size=(rows, m)`), which consumes the generator exactly as
  AISSA's loop does. The draws are bit-identical, and the generator ends in the same state.

## Replay of AISSA's intervals
```bash
uv run python scripts/compare_aissa.py bootstrap data/interim/audit_rico \
    data/interim/audit_androidcontrol_run1 data/interim/aissa_reference
```
AISSA draws all four intervals from **one shared generator**, in this order: AndroidControl
screen, AndroidControl app, Rico screen, Rico app (its datasets sort as `androidcontrol_2024`,
then `rico_2017`). The replay does the same, using a11ydebt's own per-screen counts and apps.

| Dataset | Cluster | Clusters | Coverage % | AISSA 95% CI | a11ydebt replay | Draws bit-identical |
|---|---|---:|---:|---:|---:|:-:|
| AndroidControl (10 shards) | screen | 49,745 | 57.27 | [56.99, 57.53] | [56.99, 57.53] | yes |
| AndroidControl (10 shards) | app | 951 | 57.27 | [55.65, 58.86] | [55.65, 58.86] | yes |
| Rico | screen | 60,637 | 17.74 | [17.50, 17.97] | [17.50, 17.97] | yes |
| Rico | app | 8,904 | 17.74 | [17.14, 18.37] | [17.14, 18.37] | yes |

The cross-corpus gap (AndroidControl minus Rico, +39.53 pp) also matches: screen
[39.17, 39.90] and app [37.81, 41.21]. The element-level Wilson intervals match too.

## `a11ydebt report` seeds each interval on its own
In AISSA's shared stream, an interval depends on every interval drawn before it. For example,
Rico's interval depends on AndroidControl's data. `a11ydebt report` instead gives each interval
its own generator seeded with `--seed` (default 20260908). Every interval is then reproducible on
its own, whatever else is in the report. The cost is Monte Carlo noise against the paper's
numbers.

| Interval (needs_label) | Paper (shared stream) | `a11ydebt report` (own generator) |
|---|---:|---:|
| AndroidControl, screen | [56.99, 57.53] | [56.99, 57.53] (first in AISSA's stream, so identical) |
| AndroidControl, app | [55.65, 58.86] | [55.66, 58.84] |
| Rico, screen | [17.50, 17.97] | [17.49, 17.98] |
| Rico, app | [17.14, 18.37] | [17.12, 18.37] |

The largest difference is 0.02 points, at the scale of the bootstrap's own Monte Carlo error.
To get the paper's exact numbers, run the replay above.
