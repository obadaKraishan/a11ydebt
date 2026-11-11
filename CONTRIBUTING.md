# Contributing to a11ydebt

Thank you for helping. a11ydebt is small, and it reproduces published numbers, so every change
is kept small, tested and easy to review.

## Issues
- **Bugs:** give the a11ydebt version (`a11ydebt --version`), the command you ran, the corpus,
  and the output or traceback.
- **Never attach Rico data:** no view-hierarchy JSON and no screenshots, not even one screen.
  Rico's terms forbid redistributing it. Describe the problem, or share a synthetic hierarchy
  that shows it. AndroidControl is Apache-2.0, but a screen id is still easier to review than
  an upload.
- **Ideas:** open an issue first for a new corpus loader or a change to the counting rules, so
  we can agree on the approach before you write code.

## Branches and pull requests
`main` is protected. Every change, including the maintainer's, goes through a pull request:
1. Branch from `main` (for example `fix/report-header` or `docs/cite-software`).
2. Make small commits with clear messages.
3. Open a pull request. CI must pass on Python 3.10, 3.11, 3.12 and 3.13.
4. The pull request is merged with a merge commit. Force pushes to `main` are blocked, and its
   history is never rewritten.

## Tests and formatting
```bash
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check .
```
- Tests use synthetic fixtures only (`tests/fixtures/`), never real corpus data.
- Every user-visible change adds a line to `CHANGELOG.md` under `[Unreleased]`.
- `src/a11ydebt/taxonomy.py` is the AISSA 2026 paper's operational definition. Changing a rule
  changes every number, so the change needs a test, a CHANGELOG entry, and a re-run of
  `scripts/compare_aissa.py` against the AISSA reference outputs.
- A new runtime dependency needs a reason in the CHANGELOG. The current ones are pydantic and
  numpy.

## AI assistance
AI-assisted contributions are welcome on these terms:
- **Disclose it.** Keep the assistant's `Co-Authored-By:` trailer on the commits, or say in the
  pull request which parts were AI-assisted.
- **Own it.** You have read and understood every line you submit, and you are responsible for
  its correctness.
- **No model output in the numbers.** No language model produces any count or interval in the
  audit. The counts come from deterministic parsing, and the intervals from a seeded bootstrap.

## Licence
By contributing, you agree that your contribution is licensed under Apache-2.0, the licence of
this repository.
