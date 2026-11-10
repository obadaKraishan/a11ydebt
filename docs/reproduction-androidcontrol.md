# Reproducing the AISSA 2026 AndroidControl numbers

Run 1 ran on 2026-11-10 as Kaggle kernel `obadakraishan/a11ydebt-androidcontrol-run1`, version 1.
It is private and ran on CPU (4 cores), Python 3.13.18 and pyarrow 26.0.1 (pinned). The code is
a11ydebt at commit cc969a9. It took 1,233 s (20.6 min) and wrote 12.1 MB of output. The reference
is the AISSA pipeline (accessibility-debt-agents, commit 97c0378):
`androidcontrol_parse_report.json`, `androidcontrol_episodes.parquet`, per-screen counts derived
from its node table, and RQ1 Tables 1 and 2 plus the ReviewerChecks figures in
`manuscript_numbers.json`.

**Verdict: every AISSA AndroidControl quantity is reproduced exactly.** That covers:
- the corpus totals and the role table
- all 10 shards
- all 7,623 episodes on 7 fields
- all 49,888 non-empty screens on 6 fields, plus the 4 empty screens
- the 700 apps

## Input
The input is AndroidControl (Apache-2.0), shards `android_control-00000-of-00020` to `-00009`, the
same 10 that AISSA parsed. That is 25.3 GB, downloaded inside Kaggle from
`storage.googleapis.com/gresearch/android_control/`. Each shard was checked against AISSA's
recorded size and SHA-256 (`data/interim/aissa_reference/androidcontrol_shards.json`).

## Commands
```bash
uv run python kaggle/androidcontrol_parse/build_kernel.py kaggle/androidcontrol_parse/config_run1.json
kaggle kernels push -p kaggle/androidcontrol_parse/build/run1
kaggle kernels output obadakraishan/a11ydebt-androidcontrol-run1 -p data/interim/androidcontrol/run1
uv run python scripts/compare_aissa.py androidcontrol data/interim/androidcontrol/run1 data/interim/aissa_reference
uv run a11ydebt summarize androidcontrol data/interim/androidcontrol/run1 --out data/interim/audit_androidcontrol_run1
```

## Corpus totals
| Quantity | AISSA | a11ydebt | Match |
|---|---:|---:|:-:|
| Shards / episodes / failed / truncated | 10 / 7,623 / 0 / 0 | 10 / 7,623 / 0 / 0 | yes |
| Screens (observations) | 49,892 | 49,892 | yes |
| Nodes | 11,002,225 | 11,002,225 | yes |
| Included (visible, positive area) | 6,831,063 | 6,831,063 | yes |
| Needs label: candidates / labelled | 1,462,544 / 837,536 | 1,462,544 / 837,536 | yes |
| **Label coverage** | **57.27%** | **57.27%** | yes |
| Icon-like: candidates / labelled | 194,529 / 122,074 | 194,529 / 122,074 | yes |
| **Icon-like coverage** | **62.75%** | **62.75%** | yes |
| Apps from resource ids (episodes with needs-label elements) | 700 | 700 | yes |

Across all episodes there are 701 apps. The extra one appears only in episodes with no
needs-label elements. Per-episode apps also equal AISSA's `androidcontrol_episode_apps()` for
7,623 of 7,623 episodes; 253 episodes have no usable resource id in both.

## Coverage by role (needs-label population, RQ1 Table 2)
| Role | Needs label | Labelled | Coverage | Match |
|---|---:|---:|---:|:-:|
| button | 108,037 | 78,066 | 72.26% | yes |
| image | 1,203,560 | 703,149 | 58.42% | yes |
| input | 24,402 | 6,640 | 27.21% | yes |
| other | 119,895 | 46,654 | 38.91% | yes |
| text | 6,650 | 3,027 | 45.52% | yes |

## Per shard (ReviewerChecks)
| Shard | Episodes | Needs label | Coverage | Match |
|---|---:|---:|---:|:-:|
| 00000 | 784 | 147,701 | 57.12% | yes |
| 00001 | 760 | 145,883 | 57.40% | yes |
| 00002 | 776 | 151,710 | 57.34% | yes |
| 00003 | 750 | 145,469 | 57.01% | yes |
| 00004 | 763 | 144,179 | 57.32% | yes |
| 00005 | 751 | 145,035 | 58.07% | yes |
| 00006 | 760 | 141,636 | 55.84% | yes |
| 00007 | 766 | 150,236 | 56.85% | yes |
| 00008 | 757 | 151,810 | 59.23% | yes |
| 00009 | 756 | 138,885 | 56.34% | yes |

## Episode and screen agreement
- **Episodes:** `n_observations`, `n_elements`, `n_included`, `n_needs_label`, `n_labelled`,
  `n_icon_like` and `n_icon_like_labelled` are equal for **7,623 of 7,623** episodes. a11ydebt has
  no extra episodes.
- **Screens:** the six counts are equal for **49,888 of 49,888** non-empty screens. The 4 screens
  that are absent from AISSA's node table have no nodes in a11ydebt either.

## All three populations (run 1)
| Population | Candidates | Labelled | Coverage | Screens with at least one unlabelled candidate |
|---|---:|---:|---:|---:|
| needs_label | 1,462,544 | 837,536 | 57.27% | 49,692 of 49,892 |
| icon_like | 194,529 | 122,074 | 62.75% | 20,779 of 49,892 |
| interactive_image (P01, new) | 133,266 | 78,469 | 58.88% | 15,569 of 49,892 |

## All 20 shards (run 1 + run 2): no AISSA counterpart
AISSA parsed only shards 00000 to 00009, so **nothing in this section can be checked against the
paper**. Run 2 (`obadakraishan/a11ydebt-androidcontrol-run2`, version 1, built from `3896724`,
the same bundled modules as run 1) parsed shards 00010 to 00019. It finished `complete` in
2,028 s on 4 CPUs, with 11.9 MB of output and 0 failed or truncated shards and 0 episode failures.

```bash
uv run a11ydebt summarize androidcontrol data/interim/androidcontrol --out data/interim/audit_androidcontrol_all20
uv run python scripts/check_androidcontrol_all20.py data/interim/androidcontrol \
    data/interim/audit_androidcontrol_all20 data/interim/audit_androidcontrol_run1 data/interim/aissa_reference
```

`check_androidcontrol_all20.py` passes every check:
- All 20 shards are present once, both runs are `complete`, and nothing failed or was truncated.
- There are **15,283** episodes (7,623 + 7,660), none in two shards, and no screen id twice.
- The run-1 rows inside the all-20 table are identical to run 1 and still add up to AISSA's
  totals.

| Quantity | All 20 shards | Run 1 (AISSA's 10) |
|---|---:|---:|
| Shards / episodes | 20 / 15,283 | 10 / 7,623 |
| Splits (train / validation / test episodes) | 13,603 / 137 / 1,543 | 6,769 / 71 / 783 |
| Screens (observations; screens with no nodes) | 99,131 (10) | 49,892 (4) |
| Nodes / included | 21,825,664 / 13,494,134 | 11,002,225 / 6,831,063 |
| Apps: over all episodes / over episodes with needs-label elements | 770 / 769 | 701 / 700 |
| Episodes with no identified app (with needs-label elements) | 490 (485) | 253 (251) |

| Population | Candidates | Labelled | Coverage | Screens with at least one unlabelled candidate |
|---|---:|---:|---:|---:|
| needs_label | 2,894,185 | 1,654,820 | 57.18% | 98,710 of 99,131 |
| icon_like | 390,697 | 243,562 | 62.34% | 41,572 of 99,131 |
| interactive_image | 266,281 | 156,403 | 58.74% | 31,027 of 99,131 |

| Role (needs label) | Candidates | Labelled | Coverage |
|---|---:|---:|---:|
| button | 218,529 | 156,460 | 71.60% |
| image | 2,383,470 | 1,389,033 | 58.28% |
| input | 49,004 | 13,090 | 26.71% |
| other | 230,038 | 89,759 | 39.02% |
| text | 13,144 | 6,478 | 49.28% |

Adding the second half of the corpus moves needs-label coverage by 0.09 points (57.27% to 57.18%)
and icon-like coverage by 0.41 points (62.75% to 62.34%). Cluster-bootstrap intervals for both
are in `docs/reproduction-bootstrap.md`.
