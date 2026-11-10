# a11ydebt

**Audit the accessibility debt in GUI-agent training corpora.** a11ydebt measures how many UI
elements that need a screen-reader label (an Android `content-desc`) actually have one, in the
corpora that computer-use agents are trained and evaluated on. It is the reproducible CLI behind
the IEEE AISSA 2026 paper *Trained on What Screen Readers Cannot Read: Accessibility Debt in the
GUI Corpora Behind Computer-Use Agents* (Kraishan and Jitkajornwanich).

> Status: pre-release (`0.1.0.dev0`), private. v0.1 targets Rico and AndroidControl.

## Quick start (development)
```bash
uv sync                      # Python 3.10+; installs pydantic, plus ruff and pytest for dev
uv run pytest                # tests use tiny synthetic fixtures, no data needed
uv run a11ydebt audit rico data/raw/rico --workers 8 --out data/interim/audit_rico
```

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
