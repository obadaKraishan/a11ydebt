# P07 · a11ydebt v0.1.0 release
Date: 2026-11-10 · From: planner (Claude app) · To: Claude Code (executor)
Run in a FRESH session from ~/research/a11ydebt AFTER P06 has finished. Follow ~/research/CLAUDE.md: save this prompt first (a11ydebt/prompts/ and a hub copy), check ANTHROPIC_API_KEY is unset, plan mode, small commits pushed after each step, run `ruff check` and `ruff format --check .` before every push, report at the end. Follow docs/release-checklist.md where it applies.

## Answers to R05 decisions
D1 Keep the history; no rewrite. Before going public: (a) make CLAUDE.md public-safe in the current tree, with the same rule as reliacode (remove the advisor line, ~/research paths, secrets paths and hub-internal rules; keep coding, test, formatting and AI-use rules); (b) scan the full history and report, by category, anything personal: email addresses, names of people other than the two paper authors and cited authors, advisor mentions, teaching or student mentions, and plans for unpublished work. Do not change history. If anything looks sensitive, stop and ask me. (c) Add one line under the README's AI-use disclosure: prompts/ and reports/ hold the session-by-session record of the AI-assisted development.
D2 AI-use wording becomes: "a11ydebt is developed with Claude Code, an AI coding assistant. The author directs the work, reviews the changes, and is responsible for the code and its correctness."
D3 Yes. If the paper DOI is not assigned at release time, release without it: remove the .zenodo.json related-identifier placeholder entry and keep the CITATION.cff line commented. We add the DOI later with a CITATION.cff commit and an edit to the Zenodo record's metadata.
D4 Yes: I am the sole software author; Kulsawasd Jitkajornwanich is credited through the paper (preferred-citation).
D5 PyPI: yes at v0.1.0, through PyPI trusted publishing from GitHub Actions (no token anywhere). HF Space: no; revisit after AISSA.

## Part A: before the repo is public (no RELEASE_APPROVED needed)
1. Apply D1a, D1c and D2 (separate commits).
2. Run the D1b history scan and put the results in the report. Stop and ask if anything looks sensitive.
3. Add .github/workflows/publish.yml: on `release: published`, build with uv and upload with pypa/gh-action-pypi-publish through trusted publishing (`permissions: id-token: write`, `environment: pypi`). Pin every action to an exact version. No secrets or tokens.
4. Push, confirm CI is green, then STOP and give me these steps, with the exact commands and paths:
   a. `gh repo edit obadaKraishan/a11ydebt --visibility public --accept-visibility-change-consequences`
   b. Zenodo: sign in with GitHub and turn on obadaKraishan/a11ydebt in the GitHub integration page.
   c. PyPI: add a pending trusted publisher (project a11ydebt, owner obadaKraishan, repository a11ydebt, workflow publish.yml, environment pypi).
   d. Create RELEASE_APPROVED (tell me the exact path and command the hook checks).
   Wait until I confirm all four.

## Part B: release (after I confirm)
5. Check that the repo is public and RELEASE_APPROVED exists. Create the GitHub environment `pypi` via gh api with me (obadaKraishan) as the required reviewer, so the PyPI upload waits for my click.
6. Run the checklist's pre-flight (including the PLACEHOLDER grep). Apply D3 as needed. Set the CHANGELOG [0.1.0] date and CITATION.cff date-released to today. Commit, push, confirm CI is green.
7. Create an annotated tag v0.1.0, push it, and create the GitHub release with notes from the CHANGELOG. Tell me when the publish workflow is waiting for my approval.
8. After I approve, verify: the publish workflow is green; pypi.org/project/a11ydebt shows 0.1.0; a clean `uv tool install a11ydebt` from PyPI runs `a11ydebt --version`; Zenodo has minted the DOIs (concept and version; if Zenodo is slow, check again later in the session).
9. Post-release commit: DOI badge in the README (concept DOI), CITATION.cff `doi` (concept DOI) with the version DOI under identifiers, README install section switched to PyPI (`uv tool install a11ydebt` or `pipx install a11ydebt`), and a new empty [Unreleased] section in the CHANGELOG. Validate CITATION.cff again.
10. Tell me to delete RELEASE_APPROVED so the gate closes again. Update docs/session-log.md and ~/research/STATUS.md.

Stop after task 10.

## Report
Usual template. Include: the history scan results, the public URL, tag, release URL, PyPI URL, Zenodo concept and version DOIs, workflow run links, and anything left for later (paper DOI).
