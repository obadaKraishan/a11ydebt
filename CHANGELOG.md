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
- S2, AndroidControl:
  - `a11ydebt.counts`: one shared per-screen counting loop, stdlib only.
  - `a11ydebt.tfrecord`: the pure-Python TFRecord and protobuf readers, ported from AISSA.
  - `a11ydebt.androidcontrol`: episodes, screens per step, the codebook flags, and the episode app
    from the dominant resource-id package.
  - `a11ydebt.kaggle_outputs`: reads the Kaggle kernel's outputs.
- CLI: `a11ydebt audit androidcontrol SHARD...` and `a11ydebt summarize androidcontrol DIR`.
- `kaggle/androidcontrol_parse/`: a private CPU script kernel that downloads, verifies, parses and
  deletes one shard at a time. It writes per-screen Parquet and candidate-node Parquet, checkpoints
  each shard, resumes, and stops before Kaggle's 12-hour limit. It is built by `build_kernel.py`
  with pinned pyarrow and a pinned image. Run 1 covers AISSA's shards 00000-00009 and run 2
  covers 00010-00019.
- `scripts/aissa_androidcontrol_reference.py` records the shards and episode ids AISSA used.
  `scripts/compare_aissa.py androidcontrol` checks a run against AISSA.
- pyarrow 26.0.1 is a dev dependency, for the kernel tests and the scripts.
- S3, bootstrap and report:
  - `a11ydebt.bootstrap`: the cluster bootstrap of pooled coverage, ported from AISSA's
    ReviewerChecks (`cluster_bootstrap_rate`, `pct_ci`, the cluster rules), plus the Wilson
    interval. Apps are clusters, and an AndroidControl episode with no app is its own cluster.
    The defaults are 5,000 resamples and seed 20260908, both configurable. Resamples are drawn
    in blocks, bit-identical to AISSA's loop.
  - `a11ydebt.report` and the CLI `a11ydebt report [LABEL=]AUDIT_DIR ... [--out DIR]
    [--n-resamples N] [--seed S] [--conf C]`. It writes `report.md`, `coverage.csv`, `roles.csv`
    and `screens_with_debt.csv` (default `data/release/report/`). Coverage carries app-cluster
    and screen-cluster 95% intervals, and each interval has its own seeded generator.
  - `scripts/compare_aissa.py bootstrap` replays AISSA's shared-stream bootstrap and reproduces
    all four published `clustered_coverage` intervals and both `clustered_gap` intervals exactly.
  - `scripts/check_androidcontrol_all20.py`: sanity checks for the all-20-shard tables.
  - `docs/reproduction-bootstrap.md`, and an all-20 section in
    `docs/reproduction-androidcontrol.md`.
- numpy (>=1.26) is now a runtime dependency, for the bootstrap.

### Fixed
- `CorpusCoverage.n_apps` no longer counts screens without an identified app as an app.
- The Kaggle job's `run_summary.json` counts distinct apps across shards instead of summing
  per-shard counts.

### Changed
- `coverage()` and `screen_coverage()` accept any screen that follows `counts.ScreenLike`, so they
  work for both corpora. `POPULATIONS` moved to `a11ydebt.counts` and is re-exported from
  `a11ydebt.rico`.
- `scripts/compare_aissa.py` takes a corpus subcommand (`rico` or `androidcontrol`). The old
  two-argument Rico form still works.
