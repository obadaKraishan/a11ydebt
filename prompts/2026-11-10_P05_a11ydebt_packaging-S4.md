# P05 · a11ydebt Session 4: packaging and release prep (no release)
Date: 2026-11-10 · From: planner (Claude app) · To: Claude Code (executor)
Start a FRESH session from ~/research/a11ydebt. Follow ~/research/CLAUDE.md: save this prompt first (a11ydebt/prompts/ and a hub copy), check ANTHROPIC_API_KEY is unset (stop if set), plan mode, small commits pushed after each step, run `ruff check` AND `ruff format --check .` before every push, report at the end.

## Answers to R04 decisions
D1 Keep per-interval seeding in `a11ydebt report`. Add one footnote to the report Markdown and to the README: intervals use independent seeds; the paper's shared-stream intervals (Table I) are reproduced exactly by `scripts/compare_aissa.py bootstrap`, see docs/reproduction-bootstrap.md. No --aissa-stream flag.
D2 Show the all-20 AndroidControl result as a clearly labeled robustness extension ("not in the paper"): one line in the how-to note and in the slide material. The paper's 10-shard numbers stay the headline. Full analysis waits for the TACCESS extension.
D3 numpy as a hard runtime dependency is fine.
D4 Yes: S4 is packaging and release prep only. No tag, no GitHub release, no Zenodo, no PyPI, no visibility change. The paper is accepted (oral) and the camera-ready is done; I will create RELEASE_APPROVED myself when I am ready.

## Tasks
1. CI: add GitHub Actions (ruff check, ruff format --check, pytest) on Python 3.10 to 3.13, mirroring reliacode's workflow.
2. pyproject metadata: version 0.1.0 (not tagged), description, author Obada Kraishan, license Apache-2.0, keywords (accessibility, GUI agents, computer-use agents, datasets, audit), classifiers, project URLs (repository, issues, documentation pointing at the GitHub README for now).
3. Build and verify: `uv build`, then install the wheel into a clean environment (uv tool install or pipx) and run `a11ydebt --help`, `a11ydebt audit rico` on the test fixtures, and `a11ydebt report` on a tiny fixture audit. Confirm the wheel contains no data, fixtures beyond what tests need, or secrets. Report the wheel and sdist sizes and file lists.
4. README rewrite for a first-time visitor: what it is and why (one paragraph), install (from GitHub for now; PyPI later), quickstart for Rico and for AndroidControl via the Kaggle kernel, a results table (Rico vs AndroidControl, three populations, app-cluster CIs) with the D1 footnote, "How to cite" (the AISSA paper first, then the software), license, NOTICE/provenance, and an "AI-use disclosure" section matching reliacode's wording.
5. CITATION.cff: software entry for a11ydebt 0.1.0 with a preferred-citation block for the AISSA paper ("Trained on What Screen Readers Cannot Read: Accessibility Debt in the GUI Corpora Behind Computer-Use Agents", Obada Kraishan and Kulsawasd Jitkajornwanich, IEEE AISSA 2026). Use clearly marked placeholders for the paper DOI and the software DOI. Validate it (cffconvert via uvx).
6. .zenodo.json prepared (creators, title, description, license, keywords, related identifiers placeholder) but not used yet.
7. docs/data-card.md: what the audit tables contain, sources and licenses (Rico: license unknown, so only derived statistics and IDs; AndroidControl: Apache 2.0), what is never redistributed (screenshots, raw view hierarchies), how to regenerate everything, and provenance.
8. results/v0.1/: commit only the aggregate report tables (coverage, roles, screens-with-debt summaries) as small CSV and Markdown. No per-screen or per-node tables.
9. docs/how-to-audit.md: a 2-page practical note "How to audit your GUI corpus with a11ydebt": the three populations in plain words, the commands, how to read screen- vs app-cluster intervals, and the worked numbers (Rico, AndroidControl 10 shards, plus the all-20 robustness line from D2). Write it so I can turn it into a handout.
10. docs/assets/qr-a11ydebt.png: a QR code for https://github.com/obadaKraishan/a11ydebt (generate with a dev-only tool via uvx; do not add a runtime dependency).
11. docs/release-checklist.md: the exact steps that need RELEASE_APPROVED, in order: make the repo public (I run the command), tag v0.1.0, GitHub release (Zenodo trigger), add DOI badge and fill CITATION.cff, optional PyPI publish, optional HF Space. Include the commands but do not run them.
12. Update CHANGELOG (0.1.0 unreleased section), docs/session-log.md, and STATUS.md.

Stop after task 12.

## Report
Usual template. Include: CI status, wheel/sdist sizes and contents, the README results table, the CITATION.cff validation output, and anything that blocks a release.
