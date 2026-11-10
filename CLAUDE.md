# a11ydebt (owner: Obada Kraishan, TTU CoMC; advisor: Dr. Kerk Kee)

## Goal
v0.1 by **Dec 1, 2026** (AISSA is Dec 8 to 10). It is a pip-installable CLI,
`a11ydebt audit rico|androidcontrol`, that reproduces the AISSA 2026 content-description
coverage numbers from raw data. The Rico references are needs-label coverage of 17.74%
(89,146/502,585) and icon-like coverage of 33.20% (42,341/127,552).

## Hard rules
- Hub rules in ~/research/CLAUDE.md apply here: prompts/ and reports/ naming, commit and push
  after each step, plan mode first, and the ask-before list.
- Never run bulk labeling or inference in this session. AndroidControl (about 50 GB) is parsed
  on Kaggle (`kaggle/<job>/`), and the v1.1 VLM judge runs on Kaggle too.
- Never print, log or commit secrets. `ANTHROPIC_API_KEY` must stay unset here.
- Never publish (Kaggle, HF, PyPI, Zenodo, git tag, GitHub release) without `RELEASE_APPROVED` in
  this repo's root, which only Obada creates. **The repo stays PRIVATE** until Obada confirms the
  paper's status and AISSA's blind-review rules.
- Every data item carries provenance: `human_written` | `llm_drafted_human_edited` |
  `llm_drafted_human_validated`, plus the model name and license if an LLM touched it.
- Published outputs use Apache-2.0 or MIT models unless docs/licenses.md says otherwise.
- Raw data is read-only. The AISSA pipeline at
  `/Volumes/Kraishan/AISSA26/code/accessibility-debt-agents` is a read-only reference; never
  write there.
- Rico is never committed or redistributed: no raw JSON and no screenshots. Publish only
  aggregate statistics, screen and app IDs, and checksums (see docs/licenses.md).
- `src/a11ydebt/taxonomy.py` is the paper's operational definition. Changing a rule changes every
  number, so any change needs a test, a CHANGELOG entry and a re-run of `scripts/compare_aissa.py`.

## Stack
Python 3.12 (supports >=3.10), uv, ruff, pytest, pydantic. The only runtime dependency is pydantic.
LLM calls (v1.1 only) go through `~/research/_shared/llm_client.py`.

## Layout
- `src/a11ydebt/`: taxonomy (codebook), rico (loader), coverage (metrics), cli
- `tests/`: synthetic fixtures in `tests/fixtures/rico/`, never real Rico
- `scripts/`: dev-only checks, such as `compare_aissa.py`
- `kaggle/<job>/` and `batch/`
- `data/{raw,interim,release}/`: never committed. `data/raw/rico` is a symlink to
  `/Volumes/Kraishan/research-data/a11ydebt/raw/rico`, so mount the drive first.
- `docs/`, `prompts/`, `reports/`

## Commands
```bash
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run a11ydebt audit rico data/raw/rico --workers 8 --out data/interim/audit_rico
uv run python scripts/compare_aissa.py rico data/interim/audit_rico data/interim/aissa_reference
# AndroidControl runs on Kaggle (see kaggle/androidcontrol_parse/README.md); poll rarely
uv run python kaggle/androidcontrol_parse/build_kernel.py kaggle/androidcontrol_parse/config_run1.json
kaggle kernels push -p kaggle/androidcontrol_parse/build/run1
kaggle kernels output obadakraishan/a11ydebt-androidcontrol-run1 -p data/interim/androidcontrol/run1
uv run python scripts/compare_aissa.py androidcontrol data/interim/androidcontrol/run1 data/interim/aissa_reference
```

## Definition of done (each session)
- Tests pass and ruff is clean.
- CHANGELOG.md is updated.
- docs/session-log.md gets 5 lines: did / decided / next / open questions / usage notes.
- A report is written to reports/ (or the hub's reports/ for cross-project prompts).
- ~/research/STATUS.md is updated.

## Context pointers
@docs/roadmap.md
@docs/licenses.md
