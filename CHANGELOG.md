# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Package skeleton: a uv project on Python 3.12 (supports >=3.10), hatchling build, pydantic,
  and ruff and pytest for development. Apache-2.0 `LICENSE` and a `NOTICE` for the ported AISSA
  codebook.
- Project docs: `CLAUDE.md`, `docs/roadmap.md`, `docs/licenses.md`, `docs/session-log.md`.
- `a11ydebt.taxonomy`: the AISSA 2026 codebook ported unchanged. It covers class-name roles,
  needs_label, icon_like and the inclusion rule (visible-to-user and positive area). It also adds
  the P01 `interactive_image` rule: an image-based node that is clickable or focusable.
- `a11ydebt.rico`: the Rico view-hierarchy loader. It walks the tree pre-order (same order as the
  AISSA parser), applies the codebook flags per node, and takes apps from `ui_details.csv`.
- `a11ydebt.coverage`: `coverage()` and `audit_rico()`. They return counts and proportions per
  screen, per app and for the corpus, for three populations, plus a needs_label split by role.
  Parsing can run in parallel, and parse failures are recorded instead of stopping the run.
- CLI: `a11ydebt audit rico PATH [--limit N] [--workers N] [--out DIR]`, which writes
  `screens.csv`, `apps.csv` and `summary.json`.
- `scripts/compare_aissa.py`: a dev-only exact comparison with the AISSA pipeline outputs.
- Tests: three synthetic fixture screens (not derived from Rico), 51 tests in total.
