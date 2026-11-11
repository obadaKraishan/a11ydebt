# P08 · a11ydebt v0.1.1 (docs fixes, pinned CI, branch protection) and report bundles
Date: 2026-11-10 · From: planner (Claude app) · To: Claude Code (executor)
Start a FRESH session from ~/research/a11ydebt (type /clear first). Follow ~/research/CLAUDE.md: save this prompt first (a11ydebt/prompts/ and a hub copy), check ANTHROPIC_API_KEY is unset, plan mode, run `ruff check` and `ruff format --check .` before every push, report at the end. RELEASE_APPROVED must NOT exist at the start; if it does, stop and tell me.

## Answers to R07 decisions
D1 RELEASE_APPROVED is deleted after every release; I run the rm myself.
D2 Leave the Zenodo publication date (2026-11-11) for now.
D3 Yes: absolute GitHub links in everything that renders on PyPI.
D4 Yes: pin ci.yml actions to SHAs, and protect main with reliacode's settings.

## Part A: protection and the v0.1.1 changes (no RELEASE_APPROVED needed)
1. Branch protection on main via gh api, the same as reliacode: required checks Python 3.10, 3.11, 3.12 and 3.13; enforce for admins; no required reviewers; no force pushes; no deletion. Read it back. From now on every a11ydebt change goes through a branch and a PR, merged with a merge commit when CI is green.
2. On branch `release/0.1.1`, one PR with small commits:
   a. README: replace every relative link with an absolute one (files: https://github.com/obadaKraishan/a11ydebt/blob/main/..., folders: .../tree/main/...), because PyPI renders the README without the repo. Add a test that fails if README.md contains a relative Markdown link.
   b. Count consistency (found in the planner's review; verify everything from the data or the committed CSVs, do not use the planner's arithmetic):
      - README says the AndroidControl sample has "951 app clusters (700 apps, plus 251 episodes with no identified app)", but results/v0.1/report.md says "49,892 screens, 701 apps" (and "770 apps" for all 20 shards, where R04 said 769 by the AISSA definition). Find the cause (probably the no-app bucket counted as an app). Make the report header state identified apps and no-app episodes separately, regenerate results/v0.1 (aggregates only; the coverage numbers must not change), and add a test.
      - docs/how-to-audit.md: the "Apps (clusters)" column shows 8,904 for Rico while the README says 9,384 apps. Rename the column to "App clusters (needs_label)" and add one sentence: clusters are apps with at least one candidate (Rico has 9,384 apps; 8,904 have a needs-label candidate).
   c. docs/how-to-audit.md "Cite": after the paper, add the software with the concept DOI 10.5281/zenodo.24121869.
   d. ci.yml: pin every action to a full commit SHA with the exact version in a comment, as in publish.yml. Add .github/dependabot.yml for github-actions, monthly, so the pins stay current. Run zizmor and actionlint.
   e. Add CONTRIBUTING.md (short: issues, the branch and PR workflow, tests and formatting, the AI-assistance policy matching the README) and the protected-main rule in CLAUDE.md.
   f. Add `reports/bundles/` to .gitignore (see Part C).
   g. Version 0.1.1: `__init__`, CITATION.cff (version, date-released today), CHANGELOG [0.1.1], README version line.
   Open the PR, wait for green CI, merge with a merge commit.
3. STOP and tell me to run `touch ~/research/a11ydebt/RELEASE_APPROVED` in my own terminal. Wait for my confirmation.

## Part B: release (after I confirm)
4. Pre-flight on main from docs/release-checklist.md: tests, `compare_aissa.py` rico, androidcontrol and bootstrap, build, `twine check --strict`, PLACEHOLDER grep.
5. Annotated tag v0.1.1 on the merged main commit, push it, and create the GitHub release with the CHANGELOG notes. Tell me when the PyPI upload is waiting for my approval.
6. After I approve: verify PyPI shows 0.1.1; a clean `uv tool install a11ydebt==0.1.1` prints 0.1.1; on the PyPI project page, open three README links and confirm they work; Zenodo has a new version DOI and the concept DOI is unchanged.
7. Post-release PR: add the 0.1.1 version DOI to CITATION.cff identifiers and to the README DOI sentence, plus an [Unreleased] entry. Merge when green.
8. Tell me to run `rm ~/research/a11ydebt/RELEASE_APPROVED`.

## Part C: hub housekeeping (hub commits)
9. Report bundles, a new standing rule. Add it to ~/research/CLAUDE.md and to the hub report template:
   With every report, write `reports/bundles/RNN_<project>_bundle.zip` in the repo the session worked in (gitignored; never committed or published). It holds: `report.md` and `prompt.md`; `MANIFEST.txt` (every file with size and SHA-256, plus the session's commit range); `git.txt` (`git log --stat` for the session's commits and `git diff --stat <start>..<end>`); `ci.txt` (CI and workflow run IDs, commits, results); `results/` (every table, CSV, JSON summary or log the report cites; aggregates only unless a prompt asks for more). Never include raw data, screenshots, view hierarchies, secrets (.env, tokens, secrets.env, kaggle.json), venvs or caches. Keep it under 10 MB, and run the secret-pattern scan over the files before zipping. reliacode's reports/ is already gitignored, so it needs no change.
10. Add an "Upcoming" section to ~/research/STATUS.md so future sessions can recall the schedule:
    reliacode: S2a backend adapter #1 on 2026-11-17; S2b cost ledger #2 on 2026-11-20; S3 reliability #3 on 2026-11-24; S4 PPI #4 on 2026-12-01 (light); S5 exporter #5 on 2026-12-15; S6a docs #6 on 2026-12-22; S6b case studies #7 #8 on 2026-12-29; S7 v0.1.0 on 2027-01-05; monthly minor releases 2027-02-02, 03-02, 04-06; JOSS paper draft 2027-04-27; JOSS submission opens 2027-05-11.
    a11ydebt: AISSA talk 2026-12-08 to 10; after AISSA, check IEEE Xplore for the paper DOI, then v0.2 (issue #1).
    MansafBench: starts this week (HRPP email, S1 schema).
11. Build this session's bundle (R08) by the new rule.

Stop after task 11.

## Report
Usual template, plus the bundle. Include: the protection settings read back, PR links, the count-consistency finding and fix, the release URL, PyPI URL, the new version DOI, and workflow run links.
