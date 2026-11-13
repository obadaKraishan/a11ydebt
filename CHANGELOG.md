# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- `space/`: a Gradio app for Hugging Face Spaces, outside the package. "Explore the debt" shows
  the corpus numbers, the spread of per-screen coverage, coverage by role and the screens with
  the most unlabelled elements (ids only). "Audit your own screen" applies the codebook to one
  uploaded Rico view-hierarchy JSON or Android `uiautomator dump` XML, read in memory and not
  kept. `space/build_stats.py` builds the per-screen statistics it reads (ids and counts only,
  with a guard against any text column), and `space/dataset_card.md` documents them. The app
  depends on the released a11ydebt 0.1.1 and Gradio 6.31.0; the package itself is unchanged.
  Its tests run in CI (`pythonpath = ["space"]` for pytest) and skip where `space/` is absent.

### Removed
- Removed internal development notes and the roadmap from the repository: `prompts/`,
  `reports/`, `CLAUDE.md`, `docs/session-log.md` and `docs/roadmap.md` are no longer tracked
  and are now gitignored, and the README no longer has an AI-use section or links to those
  folders. The git history and the 0.1.0 and 0.1.1 archives still contain them.

### Changed
- After the 0.1.1 release: `CITATION.cff` lists the 0.1.1 version DOI
  (10.5281/zenodo.24123117) next to the 0.1.0 one, and the README's DOI sentence gives both.
  The concept DOI, 10.5281/zenodo.24121869, is unchanged and now resolves to 0.1.1.
- `CONTRIBUTING.md` states the AI-assistance rules for contributors on their own, the release
  checklist lists plain maintainer steps, and the docs and code comments call the
  `interactive_image` population by its name instead of an internal session number. No number
  changes.

## [0.1.1] - 2026-11-10
Documentation and CI fixes after the first release. No coverage number or interval changes.

### Added
- `CONTRIBUTING.md`: issues (never attach Rico data), the branch and pull-request
  workflow on the protected `main`, tests and formatting, and the AI-assistance policy. The
  README's Development section links to it.

### Changed
- After the 0.1.0 release: the README has PyPI and Zenodo DOI badges, and its software BibTeX
  entry carries the concept DOI. `CITATION.cff` gains `doi` (the concept DOI,
  10.5281/zenodo.24121869) and `identifiers` (the 0.1.0 version DOI, 10.5281/zenodo.24121870).
  The paper DOI follows once IEEE Xplore assigns it.
- `a11ydebt report`: each corpus header gives identified apps and the app clusters with no
  identified app separately, for example "701 identified apps and 253 episodes with no
  identified app" on AndroidControl, instead of "701 apps". The method note adds that the App
  clusters column counts only the clusters with at least one candidate in that population (951
  needs_label clusters = 700 apps + 251 episodes). No number changes. `CorpusReport` gains
  `n_no_app`.
- CI pins every action to a full commit SHA, with the exact version in a comment, as
  `publish.yml` does: `actions/checkout` v7.0.1 (now with `persist-credentials: false`) and
  `astral-sh/setup-uv` v10.3.3. A new `.github/dependabot.yml` proposes action updates once a
  month, grouped, after a 7-day cooldown. zizmor 1.32.0 (auditor persona) and actionlint
  1.7.12 report nothing.

### Fixed
- Every README link is absolute (`https://github.com/obadaKraishan/a11ydebt/blob/main/...` for
  files, `.../tree/main/...` for folders), so the links work on PyPI's project page.
  `tests/test_docs.py` fails if the README gains a relative link.
- The README and `docs/how-to-audit.md` say which app count they give: AndroidControl's 10
  shards have 701 identified apps and 253 episodes with no identified app, and needs_label has
  951 app clusters (700 apps and 251 episodes with a candidate). Rico has 9,384 apps and 8,904
  needs_label app clusters. The how-to-audit column is now "App clusters (needs_label)".
  `tests/test_docs.py` checks these counts against `results/v0.1/`.
- `docs/how-to-audit.md` cites the software after the paper, with the concept DOI
  10.5281/zenodo.24121869.

## [0.1.0] - 2026-11-10
The first release. It audits Rico and AndroidControl and reproduces the corpus coverage numbers
and cluster-bootstrap intervals of the IEEE AISSA 2026 paper exactly.

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
- S4, packaging and release prep:
  - CI (`.github/workflows/ci.yml`) runs ruff check, ruff format --check and pytest with coverage
    on Python 3.10 to 3.13, mirroring reliacode. pytest-cov is a dev dependency.
  - Package metadata: version 0.1.0, read from `a11ydebt/__init__.py`, plus keywords,
    classifiers and project URLs. The sdist holds src, tests, the Kaggle kernel and the top-level
    docs.
  - `CITATION.cff` (validated with cffconvert 2.0.0) is the software entry, with the AISSA 2026
    paper as preferred-citation. `.zenodo.json` holds the Zenodo archive metadata. The paper DOI
    is a marked, commented placeholder until IEEE Xplore assigns it.
    `tests/test_release_metadata.py` keeps their versions in step.
  - `results/v0.1/`: the aggregate report tables for Rico, AndroidControl 10 shards and
    AndroidControl all 20 shards (a robustness extension, not in the paper).
  - Docs: `docs/data-card.md`, `docs/how-to-audit.md` (a two-page handout),
    `docs/release-checklist.md`, and `docs/assets/qr-a11ydebt.png` (made with segno through uvx).
  - `report.md` ends with a footnote on independent seeds (decision D1).
- Release:
  - `.github/workflows/publish.yml` uploads to PyPI through trusted publishing (no token) when a
    GitHub release is published. The upload waits for the maintainer's approval in the `pypi`
    environment, the build checks that the tag matches the package version, and every action is
    pinned to a full commit SHA.

### Fixed
- `CorpusCoverage.n_apps` no longer counts screens without an identified app as an app.
- The Kaggle job's `run_summary.json` counts distinct apps across shards instead of summing
  per-shard counts.

### Changed
- The README is rewritten for first-time visitors: install, quickstarts, the results table, how
  to cite, provenance, and the AI-use disclosure.
- `tests/test_bootstrap.py`: the Wilson zero-bound test allows for libm rounding (Linux gives
  about 3e-17).
- `coverage()` and `screen_coverage()` accept any screen that follows `counts.ScreenLike`, so they
  work for both corpora. `POPULATIONS` moved to `a11ydebt.counts` and is re-exported from
  `a11ydebt.rico`.
- `scripts/compare_aissa.py` takes a corpus subcommand (`rico` or `androidcontrol`). The old
  two-argument Rico form still works.
- Before going public: `CLAUDE.md` keeps only the project's own rules, `docs/roadmap.md` is a
  public software roadmap, and the README's AI-use disclosure says the author directs the work,
  reviews the changes and is responsible for the code. It also points to `prompts/` and
  `reports/`, the record of the AI-assisted development.
- `docs/release-checklist.md` uses the trusted-publishing workflow and attaches no files to the
  GitHub release.

[Unreleased]: https://github.com/obadaKraishan/a11ydebt/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/obadaKraishan/a11ydebt/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/obadaKraishan/a11ydebt/releases/tag/v0.1.0
