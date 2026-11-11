# a11ydebt

[![CI](https://github.com/obadaKraishan/a11ydebt/actions/workflows/ci.yml/badge.svg)](https://github.com/obadaKraishan/a11ydebt/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/a11ydebt.svg)](https://pypi.org/project/a11ydebt/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24121869.svg)](https://doi.org/10.5281/zenodo.24121869)

**Measure the accessibility debt in the GUI corpora behind computer-use agents.** Agents that
operate phones learn from large corpora of recorded screens. A screen reader can only announce a
button or an icon if the app gave it a label (an Android `content-desc`), and many apps don't.
a11ydebt counts, for every element that needs a label, whether it has one. It reports the
coverage per screen, per app and per corpus, with app-level cluster-bootstrap confidence
intervals. It is the reproducible tool behind the IEEE AISSA 2026 paper *Trained on What Screen
Readers Cannot Read: Accessibility Debt in the GUI Corpora Behind Computer-Use Agents*
(Kraishan and Jitkajornwanich). From the raw data, it reproduces the paper's corpus coverage
numbers (overall and by role) and its cluster-bootstrap intervals exactly.

> Version 0.1.0, released on 2026-11-10. It supports Rico and AndroidControl, and needs Python
> 3.10 or later.

## Install
From PyPI:
```bash
uv tool install a11ydebt
# or
pipx install a11ydebt
```
For the latest development version, install from GitHub instead:
`uv tool install "git+https://github.com/obadaKraishan/a11ydebt.git"`.

The runtime dependencies are pydantic and numpy. `a11ydebt summarize`, which reads the Kaggle
kernel's Parquet outputs, also needs pyarrow: `pipx inject a11ydebt pyarrow`, or
`uv tool install --with pyarrow ...`.

## Quickstart: Rico
1. Download Rico from <https://interactionmining.org/rico>, under its research-use terms. You
   need *UI Screenshots and View Hierarchies* (`unique_uis.tar.gz`, 6.5 GB) and the UI metadata
   file `ui_details.csv`. Unpack the archive (about 16 GB) to get `combined/*.json`, and put
   `ui_details.csv` next to `combined/`. The checksums are in
   [docs/reproduction-rico.md](https://github.com/obadaKraishan/a11ydebt/blob/main/docs/reproduction-rico.md).
2. Audit and report:
   ```bash
   a11ydebt audit rico path/to/rico --workers 8 --out audit_rico   # about 6 minutes on 8 cores
   a11ydebt report "Rico=audit_rico" --out report
   ```
   `audit` writes `screens.csv`, `apps.csv` and `summary.json`. `report` writes `report.md`,
   `coverage.csv`, `roles.csv` and `screens_with_debt.csv`.

## Quickstart: AndroidControl
AndroidControl (Apache-2.0) is 20 GZIP TFRecord shards, about 50 GB in all, at
`https://storage.googleapis.com/gresearch/android_control/`.

- **One shard, locally (2.5 GB):**
  ```bash
  curl -O https://storage.googleapis.com/gresearch/android_control/android_control-00000-of-00020
  curl -O https://storage.googleapis.com/gresearch/android_control/splits.json
  a11ydebt audit androidcontrol android_control-00000-of-00020 --splits splits.json --out audit_ac
  ```
- **The full corpus, on a free Kaggle CPU kernel** (from a clone of this repo, with the Kaggle CLI
  set up). First set `kernel_id` in `kaggle/androidcontrol_parse/config_run1.json` to
  `<your-kaggle-username>/a11ydebt-androidcontrol-run1`. The kernel downloads, verifies, parses and
  deletes one shard at a time, and returns about 12 MB of Parquet per 10 shards
  ([kaggle/androidcontrol_parse/README.md](https://github.com/obadaKraishan/a11ydebt/blob/main/kaggle/androidcontrol_parse/README.md)).
  ```bash
  uv run python kaggle/androidcontrol_parse/build_kernel.py kaggle/androidcontrol_parse/config_run1.json
  kaggle kernels push -p kaggle/androidcontrol_parse/build/run1
  kaggle kernels output <your-kaggle-username>/a11ydebt-androidcontrol-run1 -p kaggle_out/run1
  a11ydebt summarize androidcontrol kaggle_out --out audit_ac
  a11ydebt report "Rico=audit_rico" "AndroidControl=audit_ac" --out report
  ```
  `config_run1.json` covers shards 00000 to 00009 (the paper's 10), and `config_run2.json` covers
  00010 to 00019.

## What it counts
Every count applies the AISSA 2026 codebook (`src/a11ydebt/taxonomy.py`). Roles come from
class names, and only nodes that are visible to the user and have positive area are included.

| Population | Definition |
|---|---|
| `needs_label` (the paper's primary measure) | Images, plus interactive elements with no visible text. Containers and web views are exempt. |
| `icon_like` (the paper's strictest measure) | A tappable image or button with no visible text. |
| `interactive_image` (new in a11ydebt) | An image-based node (ImageView family, ImageButton, FAB) that is clickable or focusable. |

## Results (v0.1.0)
Label coverage, with 95% app-cluster bootstrap intervals[^seeds]. AndroidControl is the
paper's 10 shards. Full tables: [results/v0.1/](https://github.com/obadaKraishan/a11ydebt/tree/main/results/v0.1).

| Population | Rico: candidates | Rico: coverage % [95% CI] | AndroidControl: candidates | AndroidControl: coverage % [95% CI] |
|---|---:|---:|---:|---:|
| needs_label | 502,585 | **17.74** [17.12, 18.37] | 1,462,544 | **57.27** [55.66, 58.84] |
| icon_like | 127,552 | **33.20** [31.96, 34.47] | 194,529 | **62.75** [57.76, 67.39] |
| interactive_image | 105,780 | 33.29 [31.97, 34.66] | 133,266 | 58.88 [53.50, 64.15] |

Rico has 66,261 screens from 9,384 apps. The AndroidControl sample has 49,892 screens from 7,623
episodes: 701 identified apps, and 253 episodes with no identified app. An app cluster counts
only if it has at least one candidate, so needs_label has 8,904 app clusters on Rico and 951 on
AndroidControl (700 apps, plus 251 no-app episodes, each its own cluster). The point estimates
equal the paper's exactly. The interactive_image row is not in the paper.

[^seeds]: Intervals use independent seeds. The paper's shared-stream intervals (Table I) are
    reproduced exactly by `scripts/compare_aissa.py bootstrap`; see
    [docs/reproduction-bootstrap.md](https://github.com/obadaKraishan/a11ydebt/blob/main/docs/reproduction-bootstrap.md).

## Reproducing the paper
- Rico: [docs/reproduction-rico.md](https://github.com/obadaKraishan/a11ydebt/blob/main/docs/reproduction-rico.md). All 66,261 screens and 9,384 apps
  equal the AISSA pipeline's counts.
- AndroidControl: [docs/reproduction-androidcontrol.md](https://github.com/obadaKraishan/a11ydebt/blob/main/docs/reproduction-androidcontrol.md). All
  10 shards, 7,623 episodes and 49,888 non-empty screens are equal.
- Intervals: [docs/reproduction-bootstrap.md](https://github.com/obadaKraishan/a11ydebt/blob/main/docs/reproduction-bootstrap.md). All six published
  cluster-bootstrap intervals match, with bit-identical draws.
- A practical guide: [docs/how-to-audit.md](https://github.com/obadaKraishan/a11ydebt/blob/main/docs/how-to-audit.md).

`scripts/compare_aissa.py` checks a run against copies of the AISSA pipeline's outputs. It is a
development tool and is not part of the package.

## Data
a11ydebt ships **no data**. Rico's terms forbid redistributing its files, so this repository
publishes only aggregate statistics. AndroidControl is Apache-2.0. See
[docs/data-card.md](https://github.com/obadaKraishan/a11ydebt/blob/main/docs/data-card.md) for what the tables contain and how to regenerate them, and
[docs/licenses.md](https://github.com/obadaKraishan/a11ydebt/blob/main/docs/licenses.md) for each dataset's terms.

## How to cite
Please cite the paper. If you use the software, cite it as well. [CITATION.cff](https://github.com/obadaKraishan/a11ydebt/blob/main/CITATION.cff)
carries both entries.

```bibtex
@inproceedings{kraishan2026trained,
  title     = {Trained on What Screen Readers Cannot Read: Accessibility Debt in the {GUI}
               Corpora Behind Computer-Use Agents},
  author    = {Kraishan, Obada and Jitkajornwanich, Kulsawasd},
  booktitle = {IEEE AISSA 2026},
  year      = {2026},
  note      = {DOI to be added when IEEE Xplore assigns one}
}

@software{kraishan2026a11ydebt,
  author  = {Kraishan, Obada},
  title   = {a11ydebt: Audit Accessibility Debt in GUI-Agent Corpora},
  version = {0.1.0},
  year    = {2026},
  url     = {https://github.com/obadaKraishan/a11ydebt},
  doi     = {10.5281/zenodo.24121869}
}
```
The software DOI [10.5281/zenodo.24121869](https://doi.org/10.5281/zenodo.24121869) covers every
version. Version 0.1.0 alone is
[10.5281/zenodo.24121870](https://doi.org/10.5281/zenodo.24121870).

## Development
```bash
uv sync                                          # Python 3.10+, with ruff, pytest and pyarrow for dev
uv run pytest                                    # synthetic fixtures only, no data needed
uv run ruff check . && uv run ruff format --check .
```
CI runs the same checks on Python 3.10 to 3.13. `main` is protected: every change goes through a
pull request, merged once CI is green. See
[CONTRIBUTING.md](https://github.com/obadaKraishan/a11ydebt/blob/main/CONTRIBUTING.md).

## License and provenance
The code is Apache-2.0 ([LICENSE](https://github.com/obadaKraishan/a11ydebt/blob/main/LICENSE)). The codebook, the AndroidControl reader and the
cluster bootstrap are ported from the MIT-licensed AISSA pipeline (accessibility-debt-agents).
[NOTICE](https://github.com/obadaKraishan/a11ydebt/blob/main/NOTICE) lists every ported file and keeps the MIT notice. The datasets have their own
terms ([docs/licenses.md](https://github.com/obadaKraishan/a11ydebt/blob/main/docs/licenses.md)).

## AI-use disclosure
a11ydebt is developed with [Claude Code](https://claude.com/claude-code), an AI coding assistant.
The author directs the work, reviews the changes, and is responsible for the code and its
correctness. Commits made with Claude Code carry a `Co-Authored-By: Claude` trailer, so the
history shows which changes were AI-assisted. No language model produces any number in the
audit: the counts come from deterministic parsing, and the intervals from a seeded bootstrap.

The [prompts/](https://github.com/obadaKraishan/a11ydebt/tree/main/prompts) and [reports/](https://github.com/obadaKraishan/a11ydebt/tree/main/reports) folders hold the session-by-session record of
the AI-assisted development.
