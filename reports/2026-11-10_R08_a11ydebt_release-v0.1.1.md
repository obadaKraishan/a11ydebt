# R08 · a11ydebt · release-v0.1.1
Date: 2026-11-10 · Prompt: prompts/2026-11-10_P08_a11ydebt_release-v0.1.1.md · From: Claude Code (executor) · To: planner (Claude app)

## 1. Summary (3 lines)
1. **a11ydebt v0.1.1 is released.**
   - `main` is now protected with reliacode's settings. Every change went through a PR: #2
     (the release) and #3 (the DOI record), both merged with merge commits on green CI.
   - The tag, the GitHub release and PyPI 0.1.1 are live; the upload ran after your approval.
   - Zenodo minted version DOI **10.5281/zenodo.24123117**. The concept DOI is unchanged.
2. **The count mismatch was a wording problem, not a bug.**
   - The planner's guess, that the no-app bucket was counted as an app, is wrong.
   - The report counted identified apps over all screens (701). The README counted clusters
     with a needs_label candidate (700 apps + 251 episodes = 951).
   - Both are now stated explicitly. The CSVs are byte-identical, and no number changed.
3. **Hub:**
   - The report-bundle rule is in CLAUDE.md and the report template, and
     `_shared/make_bundle.py` builds and scans the bundles.
   - STATUS.md has an Upcoming section.
   - **Still for you:** `rm ~/research/a11ydebt/RELEASE_APPROVED`. It was still present when I
     wrote this report.

## 2. Done: what was built, with file paths
**Part A: protection, and PR [#2](https://github.com/obadaKraishan/a11ydebt/pull/2) (`release/0.1.1`, 10 commits)**
- **Branch protection** on `main`, set through `gh api` (read-back in section 3a).
- **a. README links:** all 16 relative links are absolute: `blob/main/...` for files,
  `tree/main/...` for `results/v0.1`, `prompts` and `reports`.
  - New `tests/test_docs.py` fails on any relative inline, reference or HTML link in README.md.
  - It requires at least 20 links, so a broken pattern can't pass vacuously.
  - It checks that every `blob/` target is a file and every `tree/` target is a folder.
- **b. Count consistency:**
  - `src/a11ydebt/report.py`: `CorpusReport.n_no_app` is counted with `bootstrap.cluster_key`
    (episodes on AndroidControl, screens elsewhere). Each corpus header now reads "N identified
    apps and M episodes (screens) with no identified app". The method note says the App
    clusters column counts only clusters with at least one candidate, so it can be smaller.
  - `tests/test_report.py` has two new tests: the AndroidControl fixture, and a Rico-style case
    with 0 and then 1 no-app screen.
  - README and `docs/how-to-audit.md` have the new wording; the how-to-audit column is renamed
    "App clusters (needs_label)", with the sentence you asked for, extended to AndroidControl.
  - `tests/test_docs.py` checks the README and how-to-audit counts against
    `results/v0.1/coverage.csv`, `screens_with_debt.csv` and the `report.md` headers.
  - `results/v0.1/` was regenerated (aggregates only), and the provenance lines in
    `results/v0.1/README.md` and `docs/data-card.md` were updated.
- **c. Software citation:** the how-to-audit Cite section adds the software after the paper,
  with concept DOI 10.5281/zenodo.24121869.
- **d. CI pins:**
  - `.github/workflows/ci.yml` pins `actions/checkout@3d3c42e5…` (v7.0.1) and
    `astral-sh/setup-uv@68559e99…` (v10.3.3), each SHA with its version in a comment. These are
    publish.yml's SHAs and the latest releases.
  - checkout gets `persist-credentials: false`.
  - New `.github/dependabot.yml`: github-actions, monthly, grouped, 7-day cooldown.
  - zizmor and actionlint are clean (3c).
- **e. Workflow docs:**
  - New `CONTRIBUTING.md`: issues (never attach Rico data), the branch, PR, green-CI and
    merge-commit workflow, tests and formatting, CHANGELOG and the taxonomy rule.
  - Its AI-assistance policy matches the README: disclose with the `Co-Authored-By` trailer or
    a PR note, own every line, and no model produces any number.
  - `CLAUDE.md` gains the protected-main rule, and the README's Development section links to
    CONTRIBUTING.
- **f.** `.gitignore`: `reports/bundles/`.
- **g. Version 0.1.1:**
  - `src/a11ydebt/__init__.py`, `CITATION.cff` (version and abstract; `date-released` stays
    2026-11-10), `.zenodo.json` (version and description; `tests/test_release_metadata.py`
    requires it), the README version line, BibTeX and results heading, and the how-to-audit
    version line.
  - `CHANGELOG.md` `[0.1.1] - 2026-11-10` with compare links.

**Part B: release**
- Pre-flight on `62c26f9` (3b), then annotated tag `v0.1.1` on that merge commit.
- [GitHub release a11ydebt 0.1.1](https://github.com/obadaKraishan/a11ydebt/releases/tag/v0.1.1):
  the CHANGELOG `[0.1.1]` notes, no files attached.
- [Publish run 42943321914](https://github.com/obadaKraishan/a11ydebt/actions/runs/42943321914):
  build at 02:03:43Z, then the upload waited for you and ran at 02:06:13Z.
- [PyPI 0.1.1](https://pypi.org/project/a11ydebt/0.1.1/).
- Post-release PR [#3](https://github.com/obadaKraishan/a11ydebt/pull/3) (`docs/0.1.1-doi`):
  - `CITATION.cff` identifiers add the 0.1.1 version DOI, and the README DOI sentence gives the
    0.1.1 and 0.1.0 DOIs.
  - A CHANGELOG `[Unreleased]` entry, and a one-paragraph v0.1.1 note in
    `docs/release-checklist.md`.
- The tag was not moved.

**Part C: hub** (`~/research`, direct commits as before)
- `CLAUDE.md`:
  - The bundle rule, with your wording, in "How we work".
  - The new-project rule now says the new repo's `.gitignore` covers `reports/bundles/`.
- `_shared/report_template.md`: section 10, Bundle.
- `_shared/CLAUDE-project-template.md`: the done-checklist mentions the bundle.
- Hub `.gitignore`: `reports/bundles/`.
- **New `_shared/make_bundle.py`** (stdlib only), so the rule is one command. I added it
  without being asked, because a scan that has to run every session should not be hand-rolled
  each time.
  - It writes report.md, prompt.md, git.txt (`git log --stat` and `git diff --stat` per repo
    range), ci.txt (`gh run list` since a time), results/ and MANIFEST.txt (size and SHA-256 per
    file, plus the resolved ranges).
  - It refuses secrets files, `.git`, venvs, caches, images, `.tfrecord`, archives, `data/raw/`
    and `/combined/` paths, and view-hierarchy JSON.
  - It runs a 13-pattern secret scan before zipping. A hit prints only the file, line and
    pattern name, and no zip is written.
  - It requires the zip path to be gitignored, and caps the zip at 10 MB.
  - `_shared/tests/test_make_bundle.py` has 21 tests. Fake tokens are built by concatenation.
    The whole `_shared/tests` suite gives 39 passed, 1 skipped. Commit `f84539f`'s message
    says 18 tests; the correct count is 21, and pushed history is not rewritten.
- `STATUS.md`: the Upcoming section with your exact schedule (reliacode S2a to JOSS, a11ydebt
  AISSA and v0.2, MansafBench), and the a11ydebt row.
- reliacode's `reports/` is already ignored, so it needs no change. mansafbench already ignores
  `reports/bundles/` (its `.gitignore` line 41).

## 3. Results: numbers, test results, comparison tables
### 3a. Branch protection on `main`, read back (identical to reliacode's, URLs stripped: `True`)
| Setting | Value |
|---|---|
| Required status checks | `Python 3.10`, `Python 3.11`, `Python 3.12`, `Python 3.13` (app 15368, GitHub Actions); strict: false |
| Enforce for admins | enabled |
| Required pull-request reviews | none |
| Force pushes / deletions | blocked / blocked |
| Linear history, signatures, conversation resolution, lock, fork syncing, block creations | all off |
| Merge methods (repo setting, unchanged, as in reliacode) | merge, squash and rebase all allowed; we use merge commits |

### 3b. Count consistency, recomputed from `data/interim/*/screens.csv`
| Corpus | Identified apps (all screens) | No-app episodes (all screens) | needs_label app clusters = apps + no-app episodes with a candidate |
|---|---:|---:|---:|
| Rico | 9,384 | 0 | 8,904 = 8,904 + 0 |
| AndroidControl, 10 shards | 701 | 253 | 951 = 700 + 251 |
| AndroidControl, all 20 shards | 770 | 490 | 1,254 = 769 + 485 |

- **The cause:** `coverage.py:172` already excludes app `""` from `n_apps`. The report header
  gave `n_apps` over all screens, while the README and the App clusters column count clusters
  with at least one needs_label candidate (AISSA's definition, as R04 said: 769 for 20 shards).
- The icon_like and interactive_image app clusters follow the same rule: 926 = 689 + 237 and
  905 = 678 + 227 on 10 shards.
- **The regeneration:** `coverage.csv`, `roles.csv` and `screens_with_debt.csv` are
  byte-identical. `report.md` differs only in the version and timestamp line, the method
  sentence and the three corpus headers.

### 3c. Checks
| Check | Result |
|---|---|
| pytest | 121 passed (113 at v0.1.0, plus 6 docs and 2 report tests) |
| ruff check, ruff format --check | clean before every push |
| zizmor 1.32.0 `--persona auditor`, online | first run: 1 medium (`dependabot-cooldown`), fixed; final: no findings |
| actionlint 1.7.12 | clean |
| `compare_aissa.py` rico, androidcontrol, bootstrap | exit 0; "all AISSA quantities reproduced exactly" (twice) and "all AISSA intervals reproduced exactly" |
| `uv build` to a fresh folder, wheel contents | `a11ydebt/` (11 files) and `a11ydebt-0.1.1.dist-info` (6) only |
| `twine check --strict` | PASSED for the sdist and the wheel |
| PLACEHOLDER grep | only `CITATION.cff:52`, the paper-DOI comment; none in `.zenodo.json` |
| `cffconvert --validate` | valid (schema 1.2.0), before and after PR #3 |

### 3d. Release verification (step 6)
| Check | Result |
|---|---|
| PyPI JSON | version 0.1.1; releases 0.1.0 and 0.1.1 |
| PyPI files vs the local pre-flight build | byte-identical: wheel 43,786 B (`298394f5…`), sdist 69,249 B (`85a5e4aa…`) |
| Clean install (scratch `UV_TOOL_DIR`, `--no-cache`) | `a11ydebt 0.1.1`; your global tool was not touched |
| PyPI project page README, opened in Chrome | "Version 0.1.1, released on 2026-11-10". The README body has 38 links: 0 relative, 18 into the repo |
| Three README links clicked on the PyPI page | `tree/main/results/v0.1` (folder listing), `blob/main/docs/how-to-audit.md`, `blob/main/CONTRIBUTING.md`: all open on GitHub, HTTP 200 |
| Zenodo | 0.1.1: **10.5281/zenodo.24123117** (`a11ydebt-v0.1.1.zip`). Concept **10.5281/zenodo.24121869** is unchanged and resolves to 0.1.1. 0.1.0 is still 10.5281/zenodo.24121870 |

### 3e. Workflow runs (all succeeded)
| Run | Workflow | Event | Commit |
|---|---|---|---|
| [42941591821](https://github.com/obadaKraishan/a11ydebt/actions/runs/42941591821) | CI | PR #2 | `f8fde38` (first run with the pinned ci.yml) |
| [42941654635](https://github.com/obadaKraishan/a11ydebt/actions/runs/42941654635) | CI | PR #2 | `0bb9138` |
| [42941845360](https://github.com/obadaKraishan/a11ydebt/actions/runs/42941845360) | CI | PR #2 | `fd9265d` (merged head) |
| [42941976716](https://github.com/obadaKraishan/a11ydebt/actions/runs/42941976716) | CI | push, main | `62c26f9` (merge of #2, tagged v0.1.1) |
| [42941986712](https://github.com/obadaKraishan/a11ydebt/actions/runs/42941986712) | Dependabot Updates | dynamic | `62c26f9`: no updates, no PR |
| [42943321914](https://github.com/obadaKraishan/a11ydebt/actions/runs/42943321914) | Publish to PyPI | release | `62c26f9` |
| [42944122597](https://github.com/obadaKraishan/a11ydebt/actions/runs/42944122597) | CI | PR #3 | `b1c7866` |
| [42944198653](https://github.com/obadaKraishan/a11ydebt/actions/runs/42944198653) | CI | push, main | `eb4a473` (merge of #3) |

The R08 report PR adds two more CI runs. They are listed in the bundle's `ci.txt`.

## 4. Environment findings
- **Session start:** `ANTHROPIC_API_KEY` was unset (checked by name). `RELEASE_APPROVED` was
  absent; you created it at 20:02 local.
- **Release gate:** the hook let the tag push and the release through once the file existed.
  Branch protection does not affect tags.
- **PyPI serves a JavaScript "Client Challenge"** to curl, so the project page can't be checked
  from the shell. I used Claude in Chrome: one tab, closed afterwards.
  - On GitHub, Chrome allowed one screenshot, then refused JavaScript and further screenshots.
  - The page titles and URLs (and curl's HTTP 200) confirmed the other two links.
- **uv does not rebuild the editable install** when only the dynamic `__version__` changes. The
  local metadata said 0.1.0 until `uv sync --reinstall-package a11ydebt`. CI builds fresh and
  was not affected.
- **Another session was working in the hub at the same time.** `68c4d8b` added the P09 prompt
  (MansafBench S1) and the mansafbench ignore line. I pulled before every hub commit, and there
  were no conflicts. The hub range in the bundle therefore includes that commit.
- **Dependabot is active.** Its first run on `main` found every action current.
- **UTC dates:** the release ran after midnight UTC. PyPI uploads and the Zenodo record are dated
  2026-11-11, while CITATION.cff and CHANGELOG say 2026-11-10, as you decided for 0.1.0 (D2).

## 5. Commits: hash + message, and whether pushed
All are pushed. a11ydebt commits reached `main` only through PRs.

| Repo | Commit | Message |
|---|---|---|
| a11ydebt | `f095d0a` | Add the P08 prompt (v0.1.1, protected main, report bundles) |
| a11ydebt | `0276b20` | Ignore reports/bundles/ (local session evidence bundles) |
| a11ydebt | `7a4139b` | Make every README link absolute, for PyPI's project page |
| a11ydebt | `654b71d` | Report header: identified apps and no-app episodes, stated separately |
| a11ydebt | `372c3fd` | Docs: say which app count each number is, and test it against results/v0.1 |
| a11ydebt | `a174978` | how-to-audit: cite the software (concept DOI) after the paper |
| a11ydebt | `69776bc` | Pin CI actions to commit SHAs and add Dependabot for github-actions |
| a11ydebt | `f8fde38` | Add CONTRIBUTING.md and the protected-main rule |
| a11ydebt | `0bb9138` | Version 0.1.1 |
| a11ydebt | `fd9265d` | Regenerate results/v0.1 with the 0.1.1 report header |
| a11ydebt | `62c26f9` | Merge pull request #2 (tag `v0.1.1`) |
| a11ydebt | `9762489` | Record the 0.1.1 version DOI (10.5281/zenodo.24123117) |
| a11ydebt | `b1c7866` | Release checklist: note that v0.1.1 used the same steps |
| a11ydebt | `eb4a473` | Merge pull request #3: record the a11ydebt 0.1.1 version DOI |
| a11ydebt | (next) | Add the R08 report and the session-log entry, then the merge of its PR |
| hub | `408243f` | Add the P08 prompt (a11ydebt v0.1.1, protected main, report bundles) |
| hub | `f84539f` | Add _shared/make_bundle.py: build and scan a session's report bundle |
| hub | `d723311` | Add the report-bundle rule (CLAUDE.md, report template) and ignore reports/bundles/ |
| hub | `64b17bb` | STATUS.md: add the Upcoming schedule (reliacode, a11ydebt, MansafBench) |
| hub | (next) | Add the R08 report copy and update STATUS.md (a11ydebt 0.1.1) |

## 6. Problems and how you handled them
1. **A commit was pushed while a test failed locally.** I had piped pytest into `tail` in a
   `&&` chain, which hid pytest's exit status.
   - The failure was the stale editable metadata (section 4), not the code. CI was green on that
     commit (`0bb9138`), so nothing broken reached `main`.
   - Since then, every check captures pytest's exit code directly.
2. **The planner's hypothesis was wrong** (section 3b). I fixed the wording rather than the
   counting. That matches the prompt's goal, and no number changed.
3. **`gh pr merge --match-head-commit` needs the full SHA.** The first merge call failed
   harmlessly and merged nothing. The retry with the full SHA worked.
4. **zizmor flagged `dependabot-cooldown`.** I added a 7-day cooldown before committing.
5. **I didn't delete `dist/` for the build**, because of the hub's "ask before deleting" rule.
   The checklist's `rm -rf dist && uv build` became a build into a fresh scratch folder. The
   0.1.0 files are still in `dist/` (decision 2).
6. **The PyPI page check** needed a real browser (section 4). The first Zenodo concept-record
   query lacked `-L` and returned a redirect; the rerun with `-L` and the doi.org resolution
   agree.

## 7. Decisions I need to make (numbered questions)
1. **Please delete `RELEASE_APPROVED`** (D1): `rm ~/research/a11ydebt/RELEASE_APPROVED`. I don't
   touch it.
2. **May I delete `a11ydebt/dist/`?** It is gitignored and holds the 0.1.0 build files. Or
   should the release checklist build into a fresh folder from now on?
3. **The `audit` CLI line** (`cli.py:58`) still prints "N apps" for identified apps. For v0.2,
   should it say "identified apps" too, to match the report? It is a one-line change plus a test
   update.
4. **Bundles hold full local paths** (scratch and home directory) in some logs. That's fine
   while they stay local. Should `make_bundle.py` redact `$HOME` in case a bundle is ever
   shared?

## 8. Usage note: rough share of the session limit this used
- No model calls, no Kaggle use, and no API spend.
- GitHub Actions: six CI runs, one Dependabot run and one publish run. The two R08 PR runs come
  after this report.
- One Chrome tab for about a minute.
- I can't see the plan's usage meter. By the number of tool calls, I'd estimate a medium to
  large session, on the order of a third to a half of a session limit.

## 9. Suggested next prompt scope
- **reliacode S2a** (backend adapter, #1) on 2026-11-17, as scheduled in STATUS.md's Upcoming
  section, building its R-bundle with `_shared/make_bundle.py`.
- **For a11ydebt, nothing until AISSA** apart from the slide (QR code and the concept DOI).
  After AISSA: the paper DOI in CITATION.cff, `.zenodo.json` and the README, then v0.2 (issue
  #1). Fold decision 3 in there.

## 10. Bundle
- **Path:** `a11ydebt/reports/bundles/R08_a11ydebt_bundle.zip`. It is gitignored, never
  committed or published, and built with `_shared/make_bundle.py`.
- **Size and SHA-256:** printed in the final message.
- **Commit ranges:** a11ydebt `1310374..main` after the R08 PR merge. Hub `3a3517d..main` after
  the R08 copy, which includes the other session's `68c4d8b`.
- **Contents:**
  - `report.md` (this file), `prompt.md` (P08), `MANIFEST.txt`, `git.txt`
  - `ci.txt`: every a11ydebt workflow run since 01:30Z, with IDs, commits and results.
  - `results/r08_results/`: the count check, protection read-back (a11ydebt and reliacode),
    zizmor and actionlint logs, regeneration log and CSV diff, pre-flight and build logs, PyPI,
    clean-install, README-link and Zenodo checks, and the hub test log.
  - `results/v0.1/`: the aggregate tables.
  - `results/release_notes_0.1.1.md`.
- **Never inside:** raw data, per-screen CSVs, screenshots, view hierarchies, secrets, venvs or
  caches. The secret-pattern scan ran over every file before zipping (the result is in
  `MANIFEST.txt`).
