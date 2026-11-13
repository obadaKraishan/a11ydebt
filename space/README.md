---
title: a11ydebt
emoji: 🔎
colorFrom: blue
colorTo: gray
sdk: gradio
sdk_version: 6.31.0
python_version: "3.12"
app_file: app.py
suggested_hardware: cpu-basic
pinned: false
license: apache-2.0
short_description: Accessibility debt in the screens behind GUI agents
datasets:
  - obadakr/a11ydebt-stats
tags:
  - accessibility
  - android
  - gui-agents
  - screen-readers
---

# a11ydebt: accessibility debt explorer

Computer-use agents that operate phones learn from large corpora of recorded screens. A screen
reader can only announce an image or an icon-only button if the app gave it a label (an
Android content description), and many apps do not. This app shows how much of that labelling
is missing in two such corpora, Rico (2017) and AndroidControl (2024), and lets you check one
screen of your own with the same rules.

- **Explore the debt:** the corpus numbers from the IEEE AISSA 2026 paper, the spread of label
  coverage across screens, coverage by element role, and the screens with the most unlabelled
  elements (ids only).
- **Audit your own screen:** upload one Rico view-hierarchy JSON file or the XML from
  `adb shell uiautomator dump`. You get the paper's two measures for that screen and the
  unlabelled elements by class and bounds.

**Privacy.** An uploaded file is read in memory, audited and dropped. The temporary copy the
upload makes is deleted as soon as it has been read. Nothing is logged or stored, and the app
keeps no run history and has no analytics.

**Limits.** a11ydebt reports label coverage (content descriptions). It is not a full
accessibility audit: it does not check contrast, touch-target size, focus order, labels taken
from a nearby view, or whether a label is meaningful.

## Data
The Explore tab reads [obadakr/a11ydebt-stats](https://huggingface.co/datasets/obadakr/a11ydebt-stats):
one row per screen, with screen ids and counts only. No screenshots, view hierarchies or UI text
from either corpus are included. The rows are built from a11ydebt's audit tables by
`build_stats.py`.

## Run it locally
From a clone of [the repository](https://github.com/obadaKraishan/a11ydebt), with the two
Parquet files in `space/data/`:

```bash
cd space
pip install gradio==6.31.0 -r requirements.txt
python app.py
```

## Code and citation
- Code: <https://github.com/obadaKraishan/a11ydebt> (Apache-2.0)
- Package: <https://pypi.org/project/a11ydebt/>
- Software DOI (all versions): [10.5281/zenodo.24121869](https://doi.org/10.5281/zenodo.24121869)
- Paper: Kraishan, O. and Jitkajornwanich, K. (2026). *Trained on What Screen Readers Cannot
  Read: Accessibility Debt in the GUI Corpora Behind Computer-Use Agents.* IEEE AISSA 2026, to
  appear.
