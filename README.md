# a11ydebt

**Audit the accessibility debt in GUI-agent training corpora.** a11ydebt measures how many UI
elements that need a screen-reader label (an Android `content-desc`) actually have one, in the
corpora that computer-use agents are trained and evaluated on. It is the reproducible CLI behind
the IEEE AISSA 2026 paper *Trained on What Screen Readers Cannot Read: Accessibility Debt in the
GUI Corpora Behind Computer-Use Agents* (Kraishan and Jitkajornwanich).

> Status: pre-release (`0.1.0.dev0`), private. v0.1 targets Rico and AndroidControl.

## Quick start (development)
```bash
uv sync                      # Python 3.10+; installs pydantic and numpy, plus ruff and pytest for dev
uv run pytest                # tests use tiny synthetic fixtures, no data needed
```

## Usage
There are three steps: audit a corpus, then (for AndroidControl on Kaggle) summarize, then report.

```bash
# 1. Audit: per-screen and per-app counts, written as screens.csv, apps.csv and summary.json
uv run a11ydebt audit rico data/raw/rico --workers 8 --out data/interim/audit_rico
uv run a11ydebt audit androidcontrol android_control-00000-of-00020 --splits splits.json \
    --out data/interim/audit_androidcontrol

# 2. The full AndroidControl corpus (about 50 GB) is parsed on Kaggle instead
#    (kaggle/androidcontrol_parse/); summarize turns the pulled outputs into the same tables
uv run a11ydebt summarize androidcontrol data/interim/androidcontrol \
    --out data/interim/audit_androidcontrol_all20

# 3. Report: Markdown and CSV tables with 95% cluster-bootstrap intervals
uv run a11ydebt report "Rico=data/interim/audit_rico" \
    "AndroidControl=data/interim/audit_androidcontrol_all20" --out data/release/report
```

`a11ydebt report` takes one or more audit folders, each optionally named `LABEL=FOLDER`. It
writes `report.md`, `coverage.csv`, `roles.csv` and `screens_with_debt.csv`. For each corpus the
tables cover:
- coverage for the three populations, with app-cluster and screen-cluster bootstrap intervals
  (the CSV adds the element-level Wilson interval);
- needs_label coverage by role;
- screens with at least one unlabelled element.

The defaults follow the AISSA paper: 5,000 resamples, seed 20260908, 95% intervals. Change them
with `--n-resamples`, `--seed` and `--conf`. App clusters are apps. On AndroidControl, an episode
with no identified app is its own cluster.

Both corpora reproduce the AISSA 2026 numbers exactly, including the published cluster-bootstrap
intervals (`docs/reproduction-rico.md`, `docs/reproduction-androidcontrol.md`,
`docs/reproduction-bootstrap.md`).

## Data
a11ydebt ships **no data**. Download Rico yourself under its research-use terms
(<https://interactionmining.org/rico>) and point the CLI at the folder that holds the
view-hierarchy JSON files (`combined/*.json`) and `ui_details.csv`. See `docs/licenses.md`
for what may and may not be redistributed.

## What it counts
Every count applies the AISSA 2026 codebook: roles come from class-name suffixes, and only
nodes that are visible to the user and have positive area are included.

| Population | Definition |
|---|---|
| `needs_label` (default) | Images, plus interactive elements with no visible text. Containers and web views are exempt. |
| `icon_like` | A tappable image or button with no visible text. This is the strictest unit. |
| `interactive_image` | An image-based node (ImageView family, ImageButton, FAB) that is clickable or focusable. |

## License
Apache-2.0 for the code (see `LICENSE` and `NOTICE`). The datasets have their own terms.
