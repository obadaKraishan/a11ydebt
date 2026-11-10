# R05 · a11ydebt · packaging-S4
Date: 2026-11-10 · Prompt: prompts/2026-11-10_P05_a11ydebt_packaging-S4.md · From: Claude Code (executor) · To: planner (Claude app)

## 1. Summary (3 lines)
1. **S4 is done, and nothing was published:** no tag, no release, no Zenodo, no PyPI, no visibility change. `ANTHROPIC_API_KEY` was unset at the start.
2. **CI is green** on Python 3.10, 3.11, 3.12 and 3.13 for every commit after the first. The first run failed on a Linux-only floating-point detail in one test, which I fixed.
3. **The package is ready to release.** Version 0.1.0 (wheel 43 KB, sdist 65 KB) installs into a clean environment, all three commands run, and the sdist passes all tests on its own. Also done: the README rewrite, CITATION.cff (valid) and .zenodo.json with marked placeholders, the data card, `results/v0.1`, the how-to handout, the QR code and the release checklist.

## 2. Done: what was built, with file paths
- **CI (task 1):** `.github/workflows/ci.yml` is reliacode's workflow (`uv sync --locked`, ruff check, ruff format --check, pytest with coverage) on Python 3.10 to 3.13. `pytest-cov` is now a dev dependency.
- **Metadata (task 2):**
  - `pyproject.toml`: version 0.1.0, read from `src/a11ydebt/__init__.py`, so there is one source.
  - Keywords: accessibility, gui-agents, computer-use-agents, datasets, audit, content-description, rico, androidcontrol.
  - Classifiers: Alpha, Console, Science/Research, OS Independent, Python 3.10 to 3.13, and three Topic entries.
  - URLs: Homepage, Repository, Issues, Documentation (the README), Changelog.
  - The sdist is limited to src, tests, the Kaggle kernel and the top-level docs.
  - `tests/test_cli.py` checks that the metadata version equals `__version__`.
- **Report footnote (D1):** `src/a11ydebt/report.py` appends one footnote to every `report.md`, and `tests/test_report.py` checks it.
- **README (task 4):** rewritten (section 3c).
- **Citation (tasks 5 and 6):** `CITATION.cff`, `.zenodo.json`, and `tests/test_release_metadata.py`, which keeps version, title and licence consistent.
- **Data card (task 7):** `docs/data-card.md`.
- **Results (task 8):** `results/v0.1/` holds `report.md`, `coverage.csv` (9 rows), `roles.csv` (15), `screens_with_debt.csv` (9) and a `README.md` (contents, method, how to regenerate, provenance). Corpus-level aggregates only, with no identifiers; 8.9 KB of tables.
- **Handout (task 9):** `docs/how-to-audit.md`, 960 words, with a "For the slide" box that carries the D2 line.
- **QR code (task 10):** `docs/assets/qr-a11ydebt.png`, 444 × 444 px, 504 bytes, error correction M. It was made with `uvx segno` and checked by decoding it with zxing-cpp, which returns exactly `https://github.com/obadaKraishan/a11ydebt`. `docs/assets/README.md` records how it was made. No dependency was added.
- **Release checklist (task 11):** `docs/release-checklist.md` has pre-flight checks, then steps 1 to 10, with commands. None of it was run.
- **Changelog and log (task 12):** `CHANGELOG.md` gains a `## [0.1.0] - Unreleased` section, and `docs/session-log.md` an S4 entry. `~/research/STATUS.md` is updated.
- **Other:** the `.gitignore` comment no longer names a local drive path, because hatchling always ships that file in the sdist.

## 3. Results: numbers, test results, comparison tables
### 3a. Tests and CI
- **Local:** 113 tests pass (111 before, plus 2 metadata tests), and ruff check and format are clean.
- **Local matrix:** with uv-managed Pythons, 3.10, 3.11, 3.12 and 3.13 each passed 110 of 110 when the workflow was added, with 94% coverage.
- **GitHub Actions:**
  - The latest run, [42910845243](https://github.com/obadaKraishan/a11ydebt/actions/runs/42910845243) on `735c4fe`, passed on all four versions.
  - All 12 runs from `a7c27eb` onwards are green.
  - The single red run is `8612a92`, the commit that added CI (section 6.1).

### 3b. Wheel and sdist (final build, from `735c4fe`)
| Artifact | Size | Files | SHA-256 |
|---|---:|---:|---|
| `a11ydebt-0.1.0-py3-none-any.whl` | 43,123 B (119,704 B unpacked) | 17 | `a84853e885bbd46afcb0bbdaa82812f912de12beb4d6446235e82c3fe9c2ccd9` |
| `a11ydebt-0.1.0.tar.gz` | 64,871 B | 42 | `8510f6c4e7c4da32d99585fec3499c9907bacbf81ec03f8258ffd0fa136b60ea` |

- **Wheel:**
  - `a11ydebt/`: `__init__`, androidcontrol, bootstrap, cli, counts, coverage, kaggle_outputs, report, rico, taxonomy, tfrecord (11 modules).
  - `a11ydebt-0.1.0.dist-info/`: METADATA, WHEEL, entry_points.txt, RECORD, `licenses/LICENSE` and `licenses/NOTICE`.
- **Sdist:**
  - The same 11 modules under `src/a11ydebt/`.
  - `tests/`: 11 test modules, `conftest.py`, `synthetic_tfrecord.py`, and the synthetic fixtures `tests/fixtures/rico/{ui_details.csv, combined/101.json, 102.json, 103.json}` (about 9 KB).
  - `kaggle/androidcontrol_parse/`: `job.py`, `build_kernel.py`, `config_run1.json`, `config_run2.json`, `README.md` and `.gitignore`, plus `kaggle/.gitkeep`.
  - Top level: CHANGELOG.md, CITATION.cff, LICENSE, NOTICE, README.md, `.gitignore`, pyproject.toml and PKG-INFO.
- **Scans of both artifacts:**
  - No secrets (Anthropic, HF and Kaggle key patterns, private keys).
  - No local paths (`/Users/`, `/Volumes/`) and no email addresses.
  - No data: the only CSV is the 151-byte synthetic fixture `ui_details.csv`, which the tests need.
- **Clean-install check:**
  - The wheel went in through `uv tool install` into an isolated tool folder, run from outside the repo; the import path was the tool's own site-packages.
  - `a11ydebt --help` and `--version` (0.1.0) work.
  - `audit rico` on the fixtures gives 3 screens, 2 apps and 27.27% needs-label.
  - `audit androidcontrol` on a synthetic shard gives 3 screens and 33.33%.
  - `report` on the fixture audits writes all four files, with the footnote.
  - `summarize` without pyarrow fails cleanly ("needs pyarrow", exit 2).
- **Sdist self-test:** unpacked into a fresh Python 3.12 venv with pytest and pyarrow, **111 of 111** tests passed. That was before the 2 metadata tests existed; they skip where CITATION.cff or .zenodo.json is absent.

### 3c. README results table (as committed)
Label coverage, with 95% app-cluster bootstrap intervals[^seeds]. AndroidControl is the paper's 10 shards.

| Population | Rico: candidates | Rico: coverage % [95% CI] | AndroidControl: candidates | AndroidControl: coverage % [95% CI] |
|---|---:|---:|---:|---:|
| needs_label | 502,585 | **17.74** [17.12, 18.37] | 1,462,544 | **57.27** [55.66, 58.84] |
| icon_like | 127,552 | **33.20** [31.96, 34.47] | 194,529 | **62.75** [57.76, 67.39] |
| interactive_image | 105,780 | 33.29 [31.97, 34.66] | 133,266 | 58.88 [53.50, 64.15] |

[^seeds]: Intervals use independent seeds. The paper's shared-stream intervals (Table I) are reproduced exactly by `scripts/compare_aissa.py bootstrap`; see docs/reproduction-bootstrap.md.

The same footnote ends every `report.md`. The all-20 result appears only in `results/v0.1`, the how-to and the slide box, each time labelled "robustness extension, not in the paper": **57.18% [55.69, 58.65]**.

### 3d. CITATION.cff validation output
```text
$ uvx cffconvert --validate -i CITATION.cff
Citation metadata are valid according to schema version 1.2.0.
```
- `cffconvert` 2.0.0 exits 0.
- Its BibTeX and APA conversions render only the software entry; that tool ignores `preferred-citation`, which is a known limitation. GitHub's "Cite this repository" box uses `preferred-citation`, so it shows the paper.
- `.zenodo.json` parses as JSON, and its version, title and licence match CITATION.cff (tested).

## 4. Environment findings
- **API key:** `[ -n "${ANTHROPIC_API_KEY+x}" ]` printed `unset` at the start.
- **GitHub Actions:** runs on this private repo, about 20 s per job.
- **Platform rounding:** `x ** 0.5` rounds differently in glibc and macOS libm, so the Wilson bound for 0 labelled is 0.0 on macOS and 2.8e-17 on Linux. The bootstrap is unaffected: integer sums and one IEEE division give the same result on every platform.
- **Python 3.10 and 3.11:** installed through uv (`uv python install`, about 40 MB each) for the local matrix.
- **Release gate:** it blocked `uv publish --help` and `gh release create --help`, because it matches the command text, help flags included. That is the hook working as designed. I stopped probing publishing commands, and the checklist asks you to confirm those flags with `--help` at release time.
- **PyPI:** `a11ydebt` returns 404 on both PyPI and TestPyPI, so the name is not registered today.

## 5. Commits: hash + message, and whether pushed
Every commit carries the Co-Authored-By trailer. Each was pushed right after it was made, with `ruff check` and `ruff format --check .` run before every push.

| a11ydebt | Message | CI |
|---|---|---|
| 2abe727 | Add the P05 prompt (S4 packaging and release prep) | (before CI) |
| 8612a92 | Add CI: ruff and pytest on Python 3.10 to 3.13 | **failed** (section 6.1) |
| a7c27eb | Allow for libm rounding in the Wilson zero-bound test | green |
| d5267b3 | Set version 0.1.0 and complete the package metadata | green |
| 5b21b77 | Add the independent-seeds footnote to report.md (D1) | green |
| 98db33a | Ship the Kaggle kernel in the sdist so its tests run | green |
| 5bc2c4d | Rewrite the README for first-time visitors | green |
| 1e5c4c2 | Add CITATION.cff and .zenodo.json (prepared, not used yet) | green |
| 5fd19d4 | Add results/v0.1: the aggregate report tables | green |
| 6611841 | Add the data card; correct the provenance line in results/v0.1 | green |
| c19c80b | Add docs/how-to-audit.md, a two-page handout | green |
| c387c69 | Add the QR code for the repository (docs/assets/qr-a11ydebt.png) | green |
| b1045fd | Add docs/release-checklist.md (steps that need RELEASE_APPROVED) | green |
| 735c4fe | Update the changelog (0.1.0, unreleased) and the session log for S4 | green |
| (next commit) | Add the R05 report | |

| research-hub | Message |
|---|---|
| 43e5497 | Add the P05 prompt (a11ydebt S4 packaging) |
| (next commit) | Add the R05 report copy and update STATUS.md |

## 6. Problems and how you handled them
1. **The first CI run failed on all four versions.** `test_wilson_interval` asserted `wilson_ci(0, 10)[0] == 0.0`, but on Linux the value is 2.8e-17 (section 4). The port stays faithful to AISSA's formula, and the test now allows 1e-12. This failed only in CI because the local matrix ran on macOS.
2. **The sdist could not run its own tests.** `tests/test_kaggle_job.py` imports `kaggle/androidcontrol_parse/`. Running the tests from the unpacked sdist exposed this, and I added `kaggle/` to the sdist.
3. **Hatchling always ships `.gitignore`;** its `exclude` setting doesn't apply. That file named a local drive path, so I reworded the comment instead.
4. **I wrote one wrong line and fixed it a commit later.** The first `results/v0.1/README.md` said "`provenance: human_written` code". The code is AI-assisted. The line now says no language model produced or edited any number.
5. **Overclaims I caught and narrowed:**
   - The README first said it reproduces "every coverage number and interval" in the paper. The paper's RQ3 numbers (touched versus background) are not computed by a11ydebt, so it now says "corpus coverage numbers (overall and by role) and its cluster-bootstrap intervals".
   - The how-to claimed `content-desc` is what "most agent pipelines read". It now says only what is counted.
6. **DOI placeholders.** A fake DOI that passes validation could slip into a release, so neither file has one:
   - `CITATION.cff` carries commented `# PLACEHOLDER` lines.
   - `.zenodo.json` has a `PLACEHOLDER: ...` string, which Zenodo would reject rather than publish.
   - The checklist greps for `PLACEHOLDER` before release.
7. **Slide material (D2).** There is no slides task in P05, so the D2 line went into a "For the slide" box at the end of `docs/how-to-audit.md`.

## 7. Decisions I need to make (numbered questions)
1. **What becomes public with the repo?**
   - The git history includes `prompts/`, `reports/`, `CLAUDE.md`, `docs/roadmap.md` and `docs/session-log.md`. They hold local paths (`/Volumes/Kraishan/...`) and internal planning notes.
   - The full-history scan found **no secrets and no data files**.
   - **Option 1, keep (my recommendation):** it is the clearest record of AI-assisted work.
   - **Option 2, scrub before going public:** this needs a history rewrite, which counts as deleting, so it is your call.
2. **AI-use disclosure wording.** I matched reliacode: "The author ... reviews every change before it is committed." In this workflow, Claude Code commits during a session, and you review afterwards. Keep the sentence, or change it to, for example, "reviews every change, and is responsible for..."?
3. **Paper DOI at release time.** If IEEE Xplore has not assigned it by the release, release without it: delete the `.zenodo.json` related-identifier entry and keep the CITATION.cff line commented. OK?
4. **Software authorship.** CITATION.cff and `.zenodo.json` list only you as the software's author, with Kulsawasd Jitkajornwanich on the paper. Is that right?
5. **PyPI and the HF Space at v0.1.0?** The name is free today. The Space needs a design first. Both are optional steps 8 and 9 in the checklist.

**What blocks a release** (in checklist order):
- `RELEASE_APPROVED` does not exist (by design).
- Decision 1 above, then the visibility change, which you run.
- The Zenodo GitHub switch must be turned on after the repo is public and before the release.
- The CHANGELOG and `date-released` must be set.
- The paper DOI is unknown (decision 3).

Until the repo is public, the README's `pipx install git+https://...` and the QR code work only for people with access.

## 8. Usage note: rough share of the session limit this used
I can't read the meter. This was a fresh session of about 60 tool calls, mostly documents (README, data card, how-to, checklist, citation files) plus small code changes. My rough guess is 15 to 20% of a 5-hour Max window; check `/usage`. There were no model calls and no Kaggle runs. CI used about 13 runs × 4 jobs × 20 s of GitHub Actions time.

## 9. Suggested next prompt scope
- **No prompt needed for the release itself.** You run `docs/release-checklist.md` once decisions 1 to 4 are settled and `RELEASE_APPROVED` exists. If you want, a short P06 can do the final metadata commit (step 4) and the DOI fill-in (step 7) around your steps.
- **AISSA prep (Dec 8 to 10):** turn `docs/how-to-audit.md` into the handout PDF and put the QR code and the D2 line on the slide. Only after the repo is public should the QR code be printed.
- **After AISSA:** v0.2, with issue #1 (stream Rico from `unique_uis.tar.gz`), then S5 (the RICO-Semantics join for "icon needs a label").
