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

Run 2 covers shards 00010 to 00019 (`obadakraishan/a11ydebt-androidcontrol-run2`) and extends the
audit to all 20 shards. It has no AISSA counterpart.
