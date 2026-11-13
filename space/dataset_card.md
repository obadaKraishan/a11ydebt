---
license: cc-by-4.0
pretty_name: a11ydebt per-screen statistics
size_categories:
  - 100K<n<1M
tags:
  - accessibility
  - android
  - gui-agents
  - mobile-ui
  - rico
  - androidcontrol
configs:
  - config_name: default
    data_files:
      - split: rico
        path: data/rico.parquet
      - split: androidcontrol
        path: data/androidcontrol.parquet
---

# a11ydebt per-screen statistics

How many of the elements on each screen of two GUI-agent corpora need a screen-reader label,
and how many have one. One row per screen, for every screen of **Rico** (2017, 66,261 screens)
and every step of **AndroidControl** (2024, 99,131 screens in 20 shards). The rows hold
identifiers and counts only: no screenshots, no view hierarchies, no UI text, no class names and
no app names.

The counts apply the operational codebook of the IEEE AISSA 2026 paper *Trained on What Screen
Readers Cannot Read: Accessibility Debt in the GUI Corpora Behind Computer-Use Agents*, as
implemented in the [a11ydebt](https://github.com/obadaKraishan/a11ydebt) package. The
[a11ydebt Space](https://huggingface.co/spaces/obadakr/a11ydebt) is built on this data.

```python
from datasets import load_dataset

rico = load_dataset("obadakr/a11ydebt-stats", split="rico")
androidcontrol = load_dataset("obadakr/a11ydebt-stats", split="androidcontrol")
```

## Fields
| Column | Type | Meaning |
|---|---|---|
| `dataset` | string | `rico` or `androidcontrol` |
| `screen_id` | string | Rico: the UI number (`combined/<screen_id>.json`). AndroidControl: `<episode_id>_<step_index>` |
| `episode_id` | int64 | AndroidControl episode id; empty for Rico |
| `step_index` | int32 | AndroidControl step within the episode (index into `accessibility_trees`); empty for Rico |
| `shard` | int16 | AndroidControl shard number, 0 to 19 (`android_control-000NN-of-00020`); empty for Rico |
| `in_paper_sample` | bool | In the paper's sample: every Rico screen, and AndroidControl shards 0 to 9 |
| `n_nodes` | int32 | Nodes in the screen's tree |
| `n_included` | int32 | Nodes that count: visible to the user and with positive area |
| `needs_label_candidates` | int32 | Included elements that need a label: images, and interactive elements with no visible text (containers and web views are exempt) |
| `needs_label_labelled` | int32 | Of those, the ones with a non-empty content description |
| `needs_label_unlabelled` | int32 | Candidates minus labelled: the screen's accessibility debt |
| `needs_label_coverage` | float64 | Labelled / candidates; empty when there are no candidates |
| `icon_like_candidates` | int32 | Included elements that are a tappable image or button with no visible text (the paper's strictest measure) |
| `icon_like_labelled` | int32 | Of those, the ones with a content description |
| `icon_like_unlabelled` | int32 | Candidates minus labelled |
| `icon_like_coverage` | float64 | Labelled / candidates; empty when there are none |

`needs_label` is the paper's primary measure and `icon_like` its strictest. a11ydebt also counts
an `interactive_image` population, which is not in the paper and is left out here.

## Corpus totals
These sums of the rows equal the paper's Table 1 for Rico and AndroidControl's 10 shards.

| Split, rows | Elements counted | Needs a label | Labelled | Coverage | Icon-like | Icon-like coverage |
|---|---:|---:|---:|---:|---:|---:|
| `rico`, all 66,261 | 2,862,639 | 502,585 | 89,146 | 17.74% | 127,552 | 33.20% |
| `androidcontrol`, the 49,892 with `in_paper_sample` | 6,831,063 | 1,462,544 | 837,536 | 57.27% | 194,529 | 62.75% |
| `androidcontrol`, all 99,131 | 13,494,134 | 2,894,185 | 1,654,820 | 57.18% | 390,697 | 62.34% |

Share of screens with at least one unlabelled element that needs a label: Rico 85.9%
(56,941), AndroidControl 99.6% (49,692 in the paper's sample; 98,710 of all 99,131). The
app-cluster bootstrap intervals need each screen's app, which this dataset leaves out; they are
in a11ydebt's published tables (`results/v0.1/coverage.csv` in the repository).

## How it was computed
1. **Rico.** `a11ydebt audit rico <rico folder> --workers 8 --out audit_rico`, over the
   `unique_uis.tar.gz` view hierarchies and `ui_details.csv`.
2. **AndroidControl.** The free Kaggle CPU kernel in `kaggle/androidcontrol_parse/`, run 1 for
   shards 00000 to 00009 and run 2 for 00010 to 00019. It verifies each shard's checksum and
   writes per-screen tables (`screens/*.parquet`).
3. **This dataset.** `python space/build_stats.py --rico audit_rico/screens.csv
   --androidcontrol run1/screens run2/screens --out data`. The script reads only the id and
   count columns, refuses the kernel's node tables, and fails if any string column holds anything
   but a dataset name or an id.

The runs used a11ydebt 0.1.0 before its release; the codebook and counting code are unchanged
in the released 0.1.1, whose aggregate tables are byte-identical to these runs'. Every row was
also checked against the package's own per-screen tables, screen by screen. Parsing is
deterministic, so a rerun gives the same rows.

**Provenance.** Every value is computed by code from the source corpora. No language model and
no human annotation produced or edited any row.

## Looking a screen up
The ids let you find a screen in your own copy of the corpus, which you obtain under its terms:

- **Rico:** `combined/<screen_id>.json` (and `<screen_id>.jpg`) in `unique_uis.tar.gz`.
- **AndroidControl:** open shard `android_control-000NN-of-00020` (NN is `shard`), find the
  record whose `episode_id` matches, and read `accessibility_trees[step_index]`.

## Limits
- **Content descriptions only.** Coverage counts a non-empty `content-desc`. It does not count
  other ways Android can name an element, such as hint text or a label from a nearby view, and it
  does not judge whether a label is meaningful.
- **Roles come from the class name alone**, as in the paper.
- **Small denominators.** A screen's coverage over one or two candidates is a coarse number;
  filter on the candidate counts when you compare screens.
- **Snapshots.** Rico is a 2017 crawl of Android apps and AndroidControl was released in 2024.
  Neither is a random sample of the apps people use today.
- **Not a full accessibility audit.** Contrast, touch-target size and focus order are not
  measured.

## Licences
- **These statistics:** [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Please
  credit the paper and the software (below), and the two source corpora.
- **Rico** (Deka et al., UIST 2017) is distributed by the University of Illinois under its own
  research-use terms (<https://www.interactionmining.org/archive/rico/copyright.txt>), which
  are not an open licence. This dataset contains none of Rico's files, screenshots, hierarchies
  or text; Rico's terms still govern the underlying data, which you must obtain from its source.
- **AndroidControl** (Li et al., NeurIPS 2024 Datasets and Benchmarks) is Apache-2.0, Copyright
  2024 The Google Research Authors.
- **The code** that produced the rows (a11ydebt) is Apache-2.0.

## Citation
```bibtex
@inproceedings{kraishan2026trained,
  title     = {Trained on What Screen Readers Cannot Read: Accessibility Debt in the {GUI}
               Corpora Behind Computer-Use Agents},
  author    = {Kraishan, Obada and Jitkajornwanich, Kulsawasd},
  booktitle = {IEEE AISSA 2026},
  year      = {2026},
  note      = {To appear}
}

@software{kraishan2026a11ydebt,
  author  = {Kraishan, Obada},
  title   = {a11ydebt: Audit Accessibility Debt in GUI-Agent Corpora},
  year    = {2026},
  url     = {https://github.com/obadaKraishan/a11ydebt},
  doi     = {10.5281/zenodo.24121869}
}
```

Please also cite the source corpora:

- Deka, B., Huang, Z., Franzen, C., Hibschman, J., Afergan, D., Li, Y., Nichols, J., and Kumar, R.
  (2017). Rico: A Mobile App Dataset for Building Data-Driven Design Applications. UIST '17.
  <https://doi.org/10.1145/3126594.3126651>
- Li, W., Bishop, W., Li, A., Rawles, C., Campbell-Ajala, F., Tyamagundlu, D., and Riva, O. (2024).
  On the Effects of Data Scale on UI Control Agents. NeurIPS 2024 Datasets and Benchmarks.
  arXiv:2406.03679
