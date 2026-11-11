# Reproducing the AISSA 2026 Rico numbers

The run was on 2026-11-10 with a11ydebt 0.1.0.dev0 (code at commit 2c24f29), on an Apple M3 Pro
with 8 worker processes. It took 417 s. The reference is the AISSA pipeline
(accessibility-debt-agents, commit 97c0378): `rico_parse_report.json`, `rico_screens.parquet` and
RQ1 Tables 1 and 2 in `manuscript_numbers.json`.

**Verdict: every AISSA Rico quantity is reproduced exactly.** That covers the corpus totals, the
role table, all 66,261 screens on seven fields, and all 9,384 apps on seven counts.

## Input (not redistributed; Rico research-use terms)
| File | Bytes | SHA-256 |
|---|---:|---|
| `unique_uis.tar.gz` (source of `combined/*.json`, 66,261 members) | 6,471,262,799 | `53f0374357273f22aee5359b7d9254b4bd9fc80f4f0c3aa9133899ee2d6976f1` |
| `ui_details.csv` | 2,405,809 | `0b80662bf5e06a480dcf382f64510a93107e5018ec56453ccff082ae4e4f4bc6` |
| `app_details.csv` | 2,025,565 | `494c3147aa2290cb7aec03c1943c976dce88f44e9590cf6303819f1d976f0d58` |

The extracted view hierarchies are 66,261 JSON files totalling 16,441,238,341 bytes.

## Commands
```bash
uv run a11ydebt audit rico data/raw/rico --workers 8 --out data/interim/audit_rico_s1
uv run --with pyarrow python scripts/compare_aissa.py data/interim/audit_rico_s1 data/interim/aissa_reference
```

## Corpus totals
| Quantity | AISSA | a11ydebt | Match |
|---|---:|---:|:-:|
| Screens parsed (failed) | 66,261 (0) | 66,261 (0) | yes |
| Nodes | 6,371,389 | 6,371,389 | yes |
| Included (visible, positive area) | 2,862,639 | 2,862,639 | yes |
| Needs label: candidates / labelled | 502,585 / 89,146 | 502,585 / 89,146 | yes |
| **Label coverage** | **17.74%** | **17.74%** | yes |
| Icon-like: candidates / labelled | 127,552 / 42,341 | 127,552 / 42,341 | yes |
| **Icon-like coverage** | **33.20%** | **33.20%** | yes |
| Apps with at least one screen | 9,384 | 9,384 | yes |

## Coverage by role (needs-label population, RQ1 Table 2)
| Role | Needs label | Labelled | Coverage | Match |
|---|---:|---:|---:|:-:|
| button | 76,461 | 34,619 | 45.28% | yes |
| image | 302,202 | 29,063 | 9.62% | yes |
| input | 29,416 | 646 | 2.20% | yes |
| other | 92,964 | 24,755 | 26.63% | yes |
| text | 1,542 | 63 | 4.09% | yes |

## Screen and app agreement
- **Screens:** `n_nodes`, `n_included`, `n_needs_label`, `n_labelled`, `n_icon_like`,
  `n_icon_like_labelled` and `app_package` are equal on **66,261 of 66,261** screens.
  a11ydebt has no extra screens.
- **Apps:** AISSA screens summed by app match a11ydebt on all seven counts for
  **9,384 of 9,384** apps.

## New in a11ydebt: the `interactive_image` population
This is an image-based node (ImageView family, ImageButton, FAB) that is clickable or
focusable. It has no AISSA counterpart.

| Population | Candidates | Labelled | Coverage | Screens with at least one unlabelled candidate |
|---|---:|---:|---:|---:|
| needs_label | 502,585 | 89,146 | 17.74% | 56,941 of 66,261 |
| icon_like | 127,552 | 42,341 | 33.20% | 25,949 of 66,261 |
| interactive_image | 105,780 | 35,217 | 33.29% | 23,048 of 66,261 |
