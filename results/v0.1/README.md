# results/v0.1: aggregate audit tables

These are the tables from `a11ydebt report` for a11ydebt 0.1.0. They hold **corpus-level aggregate
statistics only**: no per-screen, per-app or per-node rows, no screen or app identifiers, and no
Rico or AndroidControl content (see [docs/data-card.md](../../docs/data-card.md)).

| File | Contents | Rows |
|---|---|---:|
| `report.md` | All three tables per corpus, with the method note and the seed footnote | |
| `coverage.csv` | Candidates, labelled, coverage, element-level Wilson 95% CI, app-cluster and screen-cluster 95% bootstrap CIs, cluster counts, resamples, seed | 9 (3 corpora × 3 populations) |
| `roles.csv` | needs_label candidates, labelled and coverage by role | 15 (3 corpora × 5 roles) |
| `screens_with_debt.csv` | Screens, screens with candidates, and screens with at least one unlabelled element, per population | 9 |

## Corpora
| Label | Input | In the paper? |
|---|---|---|
| Rico | All 66,261 screens of `unique_uis.tar.gz`, with `ui_details.csv` | Yes |
| AndroidControl, 10 shards (the paper's sample) | Shards 00000 to 00009 (7,623 episodes), Kaggle run 1 | Yes |
| AndroidControl, all 20 shards (robustness extension, not in the paper) | Shards 00000 to 00019 (15,283 episodes), Kaggle runs 1 and 2 | **No.** It is a robustness extension; the paper's headline numbers are the 10-shard ones. |

## Method
- **Coverage** is pooled: labelled / candidates.
- **Intervals** are percentile intervals of 5,000 cluster-bootstrap resamples, with seed 20260908.
- **Clusters:** app clusters are apps. On AndroidControl, an episode with no identified app is its own cluster.
- **Seeds:** each interval has its own generator. The paper's Table I intervals came from one shared stream. They differ from these by at most 0.02 points, and `scripts/compare_aissa.py bootstrap` reproduces them exactly ([docs/reproduction-bootstrap.md](../../docs/reproduction-bootstrap.md)).

## Regenerate
```bash
a11ydebt audit rico data/raw/rico --workers 8 --out data/interim/audit_rico
# AndroidControl: Kaggle runs 1 and 2 (kaggle/androidcontrol_parse/), pulled to data/interim/androidcontrol/run1 and run2
a11ydebt summarize androidcontrol data/interim/androidcontrol/run1 --out data/interim/audit_androidcontrol_run1
a11ydebt summarize androidcontrol data/interim/androidcontrol --out data/interim/audit_androidcontrol_all20
a11ydebt report "Rico=data/interim/audit_rico" \
  "AndroidControl, 10 shards (the paper's sample)=data/interim/audit_androidcontrol_run1" \
  "AndroidControl, all 20 shards (robustness extension, not in the paper)=data/interim/audit_androidcontrol_all20" \
  --out data/release/report
```
The numbers are deterministic. Only the `generated` timestamp in `report.md` changes between runs.

## Provenance
- **Code:** a11ydebt 0.1.0, generated on 2026-11-10 at commit `1e5c4c2`.
- **Rico input:** the checksums are in [docs/reproduction-rico.md](../../docs/reproduction-rico.md).
- **AndroidControl input:** each shard's bytes and checksum were verified on Kaggle (SHA-256 from AISSA for shards 00000 to 00009, MD5 from GCS for 00010 to 00019; see `kaggle/androidcontrol_parse/config_run*.json`).
- **Human or LLM:** every number comes from deterministic parsing and a seeded bootstrap (`provenance: human_written` code; no LLM touched any data item).
