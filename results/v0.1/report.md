# a11ydebt coverage report

a11ydebt 0.1.0 · generated 2026-11-10T21:57:57+00:00

Coverage is pooled: labelled / candidates. The 95% intervals are the percentile intervals of 5,000 cluster-bootstrap resamples (seed 20260908). Each interval has its own generator seeded with the seed.[^seeds] App clusters are apps; on AndroidControl, an episode with no identified app is its own cluster. Screen clusters are screens. Only clusters with at least one candidate are resampled.

## Rico

Dataset `rico` from `data/raw/rico`: 66,261 screens, 9,384 apps, 6,371,389 nodes (2,862,639 included: visible, positive area).

**Coverage with 95% cluster-bootstrap intervals**

| Population | Candidates | Labelled | Coverage % | 95% CI, app clusters | App clusters | 95% CI, screen clusters | Screen clusters |
|---|---:|---:|---:|---:|---:|---:|---:|
| needs_label | 502,585 | 89,146 | 17.74 | [17.12, 18.37] | 8,904 | [17.49, 17.98] | 60,637 |
| icon_like | 127,552 | 42,341 | 33.20 | [31.96, 34.47] | 7,332 | [32.68, 33.68] | 42,990 |
| interactive_image | 105,780 | 35,217 | 33.29 | [31.97, 34.66] | 6,775 | [32.76, 33.84] | 38,925 |

**needs_label by role**

| Role | Candidates | Labelled | Coverage % |
|---|---:|---:|---:|
| button | 76,461 | 34,619 | 45.28 |
| image | 302,202 | 29,063 | 9.62 |
| input | 29,416 | 646 | 2.20 |
| other | 92,964 | 24,755 | 26.63 |
| text | 1,542 | 63 | 4.09 |

**Screens with at least one unlabelled element**

| Population | Screens with candidates | Screens with ≥1 unlabelled | % of all screens | % of screens with candidates |
|---|---:|---:|---:|---:|
| needs_label | 60,637 | 56,941 | 85.93 | 93.90 |
| icon_like | 42,990 | 25,949 | 39.16 | 60.36 |
| interactive_image | 38,925 | 23,048 | 34.78 | 59.21 |

## AndroidControl, 10 shards (the paper's sample)

Dataset `androidcontrol` from `data/interim/androidcontrol/run1`: 49,892 screens, 701 apps, 11,002,225 nodes (6,831,063 included: visible, positive area).

**Coverage with 95% cluster-bootstrap intervals**

| Population | Candidates | Labelled | Coverage % | 95% CI, app clusters | App clusters | 95% CI, screen clusters | Screen clusters |
|---|---:|---:|---:|---:|---:|---:|---:|
| needs_label | 1,462,544 | 837,536 | 57.27 | [55.66, 58.84] | 951 | [56.99, 57.53] | 49,745 |
| icon_like | 194,529 | 122,074 | 62.75 | [57.76, 67.39] | 926 | [62.20, 63.30] | 39,955 |
| interactive_image | 133,266 | 78,469 | 58.88 | [53.50, 64.15] | 905 | [58.25, 59.51] | 36,429 |

**needs_label by role**

| Role | Candidates | Labelled | Coverage % |
|---|---:|---:|---:|
| button | 108,037 | 78,066 | 72.26 |
| image | 1,203,560 | 703,149 | 58.42 |
| input | 24,402 | 6,640 | 27.21 |
| other | 119,895 | 46,654 | 38.91 |
| text | 6,650 | 3,027 | 45.52 |

**Screens with at least one unlabelled element**

| Population | Screens with candidates | Screens with ≥1 unlabelled | % of all screens | % of screens with candidates |
|---|---:|---:|---:|---:|
| needs_label | 49,745 | 49,692 | 99.60 | 99.89 |
| icon_like | 39,955 | 20,779 | 41.65 | 52.01 |
| interactive_image | 36,429 | 15,569 | 31.21 | 42.74 |

## AndroidControl, all 20 shards (robustness extension, not in the paper)

Dataset `androidcontrol` from `data/interim/androidcontrol`: 99,131 screens, 770 apps, 21,825,664 nodes (13,494,134 included: visible, positive area).

**Coverage with 95% cluster-bootstrap intervals**

| Population | Candidates | Labelled | Coverage % | 95% CI, app clusters | App clusters | 95% CI, screen clusters | Screen clusters |
|---|---:|---:|---:|---:|---:|---:|---:|
| needs_label | 2,894,185 | 1,654,820 | 57.18 | [55.69, 58.65] | 1,254 | [56.98, 57.37] | 98,848 |
| icon_like | 390,697 | 243,562 | 62.34 | [57.07, 67.03] | 1,225 | [61.95, 62.74] | 79,658 |
| interactive_image | 266,281 | 156,403 | 58.74 | [53.20, 64.05] | 1,191 | [58.30, 59.18] | 72,557 |

**needs_label by role**

| Role | Candidates | Labelled | Coverage % |
|---|---:|---:|---:|
| button | 218,529 | 156,460 | 71.60 |
| image | 2,383,470 | 1,389,033 | 58.28 |
| input | 49,004 | 13,090 | 26.71 |
| other | 230,038 | 89,759 | 39.02 |
| text | 13,144 | 6,478 | 49.28 |

**Screens with at least one unlabelled element**

| Population | Screens with candidates | Screens with ≥1 unlabelled | % of all screens | % of screens with candidates |
|---|---:|---:|---:|---:|
| needs_label | 98,848 | 98,710 | 99.58 | 99.86 |
| icon_like | 79,658 | 41,572 | 41.94 | 52.19 |
| interactive_image | 72,557 | 31,027 | 31.30 | 42.76 |

[^seeds]: Intervals use independent seeds. The AISSA 2026 paper's shared-stream intervals (Table I) are reproduced exactly by `scripts/compare_aissa.py bootstrap`; see [docs/reproduction-bootstrap.md](https://github.com/obadaKraishan/a11ydebt/blob/main/docs/reproduction-bootstrap.md).
