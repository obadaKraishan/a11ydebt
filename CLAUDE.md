# a11ydebt

Guidance for AI coding assistants (such as Claude Code) working in this repository. People
should start with the [README](README.md).

## Goal
A pip-installable CLI, `a11ydebt audit rico|androidcontrol`, that reproduces the IEEE AISSA 2026
content-description coverage numbers from raw data. The Rico references are needs-label coverage
of 17.74% (89,146/502,585) and icon-like coverage of 33.20% (42,341/127,552). v0.1.0 comes before
AISSA (Dec 8 to 10, 2026); see `docs/roadmap.md`.

## Rules
- **The repository is public.** Never commit secrets, API keys, credentials or data.
- **Rico is never committed or redistributed:** no raw JSON and no screenshots. Publish only
  aggregate statistics, screen and app IDs, and checksums (see `docs/licenses.md`).
- **Raw data is read-only.** Copy what you need and never modify the originals. The AISSA paper's
  original pipeline (accessibility-debt-agents) is a read-only reference; never write to it.
- **`src/a11ydebt/taxonomy.py` is the paper's operational definition.** Changing a rule changes
  every number, so any change needs a test, a CHANGELOG entry and a re-run of
  `scripts/compare_aissa.py`.
- **No bulk work in an assistant session.** Never run bulk labeling or model inference locally.
  AndroidControl (about 50 GB) is parsed on Kaggle (`kaggle/androidcontrol_parse/`), and the
  planned v1.1 VLM judge runs on Kaggle too.
- **Provenance.** Every data item carries `provenance`: `human_written`,
  `llm_drafted_human_edited` or `llm_drafted_human_validated`, plus the model name and licence if
  a language model touched it. Published outputs use Apache-2.0 or MIT models unless
  `docs/licenses.md` says otherwise.
- **Small, real, incremental commits** with clear messages, pushed as they are made. No code
  dumps, no backdating, no squashing, no force pushes.
- **`main` is protected** (since 2026-11-10). CI must pass on Python 3.10, 3.11, 3.12 and 3.13,
  admins included; force pushes and deletion are blocked. Every change goes on a branch and
  through a pull request, merged with a merge commit (`gh pr merge --merge`) once CI is green.
  Never push to `main` directly. See `CONTRIBUTING.md`.
- **AI use is disclosed.** Commits made with an AI assistant keep their `Co-Authored-By:`
  trailer, and the README's AI-use disclosure must stay accurate.
- **Never publish** (PyPI, Zenodo, Kaggle, Hugging Face, git tags, GitHub releases) without the
  maintainer's explicit approval.

## Coding conventions
- Python >=3.10 (develop on 3.12), uv, hatchling. The runtime dependencies are pydantic and
  numpy; a new one needs a reason in the CHANGELOG.
- Ruff with line length 100.
- Language-model calls (v1.1 only) go through one OpenAI-compatible client.

## Tests and formatting
- `uv run pytest` must pass.
- Before every push, run `uv run ruff check .` and `uv run ruff format --check .`.
- Tests use synthetic fixtures (`tests/fixtures/rico/`), never real Rico data.
- Every user-visible change gets a line in `CHANGELOG.md` under `[Unreleased]`, and each working
  session adds five lines to `docs/session-log.md`: did, decided, next, open questions and usage
  notes.

## Layout
- `src/a11ydebt/`: taxonomy (codebook), rico and androidcontrol (loaders), coverage (metrics),
  bootstrap (cluster CIs), report (tables), cli
- `tests/`: synthetic fixtures in `tests/fixtures/rico/`
- `scripts/`: dev-only checks, such as `compare_aissa.py`
- `kaggle/<job>/`: Kaggle script kernels
- `data/{raw,interim,release}/`: never committed. `data/raw/rico` is a symlink to a local copy of
  Rico outside the repository.
- `docs/`; `prompts/` and `reports/`, the session-by-session record of the AI-assisted
  development
- `.github/workflows/`: `ci.yml` (ruff and pytest on Python 3.10 to 3.13)

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
uv run a11ydebt summarize androidcontrol data/interim/androidcontrol --out data/interim/audit_androidcontrol_all20
uv run python scripts/check_androidcontrol_all20.py data/interim/androidcontrol data/interim/audit_androidcontrol_all20 data/interim/audit_androidcontrol_run1 data/interim/aissa_reference
uv run python scripts/compare_aissa.py bootstrap data/interim/audit_rico data/interim/audit_androidcontrol_run1 data/interim/aissa_reference
uv run a11ydebt report "Rico=data/interim/audit_rico" "AndroidControl, 10 shards (AISSA)=data/interim/audit_androidcontrol_run1" "AndroidControl, all 20 shards=data/interim/audit_androidcontrol_all20"
gh run list --limit 3          # CI status
```

## Context pointers
@docs/roadmap.md
@docs/licenses.md
