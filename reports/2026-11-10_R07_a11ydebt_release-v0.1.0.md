# R07 · a11ydebt · release-v0.1.0
Date: 2026-11-10 · Prompt: prompts/2026-11-10_P07_a11ydebt_release-v0.1.0.md · From: Claude Code (executor) · To: planner (Claude app)

## 1. Summary (3 lines)
1. **a11ydebt v0.1.0 is released.** The repo is public, the `v0.1.0` tag and GitHub release
   exist, PyPI serves 0.1.0 (uploaded through trusted publishing after Obada's approval), and
   Zenodo has minted concept DOI **10.5281/zenodo.24121869** and version DOI
   **10.5281/zenodo.24121870**.
2. **Before the flip, the tree was made public-safe.** CLAUDE.md and docs/roadmap.md were
   trimmed, the AI-use wording was updated (D2), and the prompts/reports line was added (D1c).
   The full-history scan found **nothing sensitive**; history was not changed.
3. **Every check passed:**
   - CI is green on 3.10 to 3.13 for every commit, and 113 tests pass.
   - All three `compare_aissa.py` checks reproduce AISSA exactly.
   - A clean `uv tool install a11ydebt` from PyPI prints `a11ydebt 0.1.0`.
   - The PyPI files are byte-identical to the local pre-flight build.
   - **Left for Obada:** delete `RELEASE_APPROVED`, and later add the paper DOI.

## 2. Done: what was built, with file paths
**Part A (before going public)**
- `CLAUDE.md` (D1a), in reliacode's style:
  - Removed: the advisor line, every `~/research` and `/Volumes` path, secrets and API-key
    handling, `RELEASE_APPROVED` and the hub gate, the hub prompts/reports/STATUS rules, the
    `_shared/llm_client.py` pointer, and "the repo stays PRIVATE".
  - Kept: the goal and reference numbers, the Rico rule, raw data read-only, the AISSA pipeline as
    a read-only reference (by name, no path), the taxonomy rule, no bulk work in a session, the
    provenance vocabulary and model licences, and small commits.
  - Also kept: the AI-use disclosure rule, never publishing without the maintainer's approval,
    and the coding, test, formatting, layout and command sections.
  - Local sessions still load the hub rules from `~/research/CLAUDE.md`.
- `docs/roadmap.md` (your answer during planning) is now a public software roadmap.
  - Dropped: "Prepared for", "Zero-Cash Edition", the cash and API-credit rows and cost section,
    "Feeds: TACCESS extension", "journal-extension tables", "What a grant adds", the 5 to 8
    hours/week line, the laptop and drive mentions, and the HF Space item (D5).
  - Kept: scope, design notes, toolchain, S1 to S7, the kickoff prompt, data and licensing, the
    quality checks with the VLM gate, the release items, timeline, risks and sources.
  - The hub keeps the full roadmap.
- `kaggle/androidcontrol_parse/README.md`: `cd ~/research/a11ydebt` became `# from the
  repository root`. This file ships in the sdist.
- `README.md`, AI-use disclosure:
  - D2 wording, word for word: "a11ydebt is developed with Claude Code, an AI coding assistant.
    The author directs the work, reviews the changes, and is responsible for the code and its
    correctness."
  - The trailer sentence and the "No language model produces any number" sentence are kept.
  - D1c line: "The prompts/ and reports/ folders hold the session-by-session record of the
    AI-assisted development."
- `.github/workflows/publish.yml`:
  - Trigger: `release: published`. Top level `contents: read`. One publish at a time, never
    cancelled.
  - Job **build**: checkout (`persist-credentials: false`), setup-uv, `uv build`, then a check
    that the release tag matches the built version (the tag comes in through `env`, never
    interpolated). It fails unless exactly the sdist and wheel are present, then uploads them as
    an artifact.
  - Job **publish**: `environment: pypi`, `id-token: write`, download-artifact, then
    `pypa/gh-action-pypi-publish` with no inputs. No secrets or tokens.
  - Every action is pinned to a full commit SHA with the exact version as a comment:

    | Action | Version | SHA |
    |---|---|---|
    | actions/checkout | v7.0.1 | `3d3c42e5…` |
    | astral-sh/setup-uv | v10.3.3 | `68559e99…` |
    | actions/upload-artifact | v7.0.2 | `cf430e03…` |
    | actions/download-artifact | v8.0.2 | `9000827c…` |
    | pypa/gh-action-pypi-publish | v1.14.3 | `7245906f…` |

  - Checked with zizmor 1.32.0 (auditor persona: no findings) and actionlint 1.7.12 (clean).
- `docs/release-checklist.md`:
  - Steps 6 and 8 use the trusted-publishing flow: no release assets, no token, and the
    environment commands.
  - The pre-flight adds `twine check --strict`, and the "what becomes public" item is marked
    decided.
  - Step 9, the HF Space, is "not for v0.1.0".

**Part B (release)**
- **GitHub environment `pypi`:**
  - Required reviewer: obadaKraishan (id 28910488), with `prevent_self_review: false`.
  - Custom deployment policy: tags matching `v*`. Read back from the API.
- **Release-prep commit:**
  - `.zenodo.json`: `related_identifiers` removed (D3).
  - `CITATION.cff`: `date-released: "2026-11-10"`.
  - `CHANGELOG.md`: `[0.1.0] - 2026-11-10`, and "The first release. …".
  - `README.md` and `docs/how-to-audit.md`: install from PyPI (section 6.5).
- **Tag, release and publish:** tag `v0.1.0` (annotated, on `515ffeb`), then the GitHub release
  (notes taken from the CHANGELOG [0.1.0] section, no assets). The publish workflow ran, and
  Obada approved the upload.
- **Post-release commit (`19340f7`):**
  - `CITATION.cff`: `doi` is the concept DOI, and `identifiers` holds the concept and version
    DOIs.
  - `README.md`: PyPI and DOI badges, `doi` in the software BibTeX entry, and one sentence on
    concept versus version DOI.
  - `CHANGELOG.md`: an `[Unreleased]` entry for these edits, plus link references.
  - `docs/release-checklist.md` and `docs/roadmap.md`: marked as released.
- **Session record:** `docs/session-log.md` (release entry), `~/research/STATUS.md`, and this
  report (hub copy in `~/research/reports/`).

## 3. Results: numbers, test results, comparison tables
### 3a. Release identifiers
| Item | Value |
|---|---|
| Public repo | <https://github.com/obadaKraishan/a11ydebt> (`visibility=public`; anonymous API HTTP 200) |
| Tag | `v0.1.0` (annotated object `0f66492`, commit `515ffeb`) |
| GitHub release | <https://github.com/obadaKraishan/a11ydebt/releases/tag/v0.1.0> (published 2026-11-10 23:37:38 UTC, no assets) |
| PyPI | <https://pypi.org/project/a11ydebt/0.1.0/> (uploaded 23:40:49 and 23:40:50 UTC) |
| Zenodo concept DOI | **10.5281/zenodo.24121869** (<https://doi.org/10.5281/zenodo.24121869>) |
| Zenodo version DOI | **10.5281/zenodo.24121870** (<https://doi.org/10.5281/zenodo.24121870>, record created 23:37:42 UTC) |
| Publish run | [42924918912](https://github.com/obadaKraishan/a11ydebt/actions/runs/42924918912): build success, upload success, approved by obadaKraishan (env `pypi`) |

### 3b. Workflow runs (CI, Python 3.10 to 3.13)
| Run | Commit | Result |
|---|---|---|
| [42917325728](https://github.com/obadaKraishan/a11ydebt/actions/runs/42917325728) | `12d93b6` P07 prompt | green |
| [42920270782](https://github.com/obadaKraishan/a11ydebt/actions/runs/42920270782) | `c464aa4` CLAUDE.md | green |
| [42920412245](https://github.com/obadaKraishan/a11ydebt/actions/runs/42920412245) | `468a79f` Kaggle README | cancelled (superseded by the next push) |
| [42920461977](https://github.com/obadaKraishan/a11ydebt/actions/runs/42920461977) | `f05d6af` D1c | green |
| [42920759049](https://github.com/obadaKraishan/a11ydebt/actions/runs/42920759049) | `4565e21` publish workflow + docs (end of Part A) | green |
| [42924798489](https://github.com/obadaKraishan/a11ydebt/actions/runs/42924798489) | `515ffeb` release prep (the tagged commit) | green |
| [42925746204](https://github.com/obadaKraishan/a11ydebt/actions/runs/42925746204) | `19340f7` DOIs | green |

### 3c. Pre-flight (step 6) and verification (step 8)
- `ruff check` and `ruff format --check` are clean, and **113 tests pass**.
- `compare_aissa.py rico`, `androidcontrol` and `bootstrap` all exit 0: "all AISSA quantities
  reproduced exactly" (twice) and "all AISSA intervals reproduced exactly".
- **Build:**
  - The wheel holds only `a11ydebt/` (11 modules) and its dist-info.
  - `twine check --strict` passes on both files.
  - Neither file contains a local path or the advisor's name.
- `cffconvert --validate` passes before and after the DOI commit.
- The PLACEHOLDER grep now finds only the paper DOI (`CITATION.cff:52`).
- **The PyPI files equal the local pre-flight build byte for byte:**

  | File | Size | SHA-256 |
  |---|---:|---|
  | `a11ydebt-0.1.0-py3-none-any.whl` | 43,131 B | `efeb8792f213508a7356198ef2d91c682c32defe267bd05e30c7bad7aa3b3f47` |
  | `a11ydebt-0.1.0.tar.gz` | 65,177 B | `0102dbe34a763196e496761ce14ebc1128ce6b36e40e8cbd668d35408042e625` |

  Both carry PEP 740 provenance attestations from trusted publishing.
- **Clean install:**
  - `uv tool install --no-cache --refresh a11ydebt==0.1.0` ran from PyPI into an isolated folder
    in the scratchpad, from outside the repo. `a11ydebt --version` prints `a11ydebt 0.1.0`, and
    the import path is the tool's own site-packages.
  - `audit rico` on the synthetic fixtures gives 3 screens, 2 apps and 27.27% needs-label, the
    same as R05.
- **The Zenodo record checks out:**
  - Software, Apache-2.0, open access, version 0.1.0, creator Kraishan, Obada.
  - `isSupplementTo` `https://github.com/obadaKraishan/a11ydebt/tree/v0.1.0`.
  - One file, `obadaKraishan/a11ydebt-v0.1.0.zip` (245,537 B).
  - Both DOIs resolve through doi.org, and the badge SVG serves.

### 3d. D1b full-history scan (before going public)
**Scope:**
- 44 commits, 118 unique text blobs (every version of every path ever committed) and all commit
  messages.
- On GitHub: 1 issue, 0 PRs, 0 milestones and 0 releases at the time.
- It ran under bash. Control strings ("Kraishan", "Jitkajornwanich") were found as expected, so
  the zero results are real.

| Category | Findings |
|---|---|
| Email addresses | **None in any file version.** In commit metadata: only `obada.kraishan@gmail.com` (author and committer of all commits), plus `noreply@anthropic.com` in 43 Co-Authored-By trailers. |
| People other than the two paper authors and cited authors | **One:** Kerk Kee (see the advisor row). Every other name is a cited dataset author (Deka, Huang, Franzen, Hibschman, Afergan, Li, Nichols, Kumar; Li, Bishop, Rawles, Campbell-Ajala, Tyamagundlu, Riva; Sunkara, Wang, Liu, Baechler, Hsiao, Chen, Sharma, Stout). The usernames are your own (obadaKraishan, obadakraishan, obadakr) and the dataset mirror hosts (leosltl, smolagents, creative-graphic-design). |
| Advisor mentions | `CLAUDE.md:1` "advisor: Dr. Kerk Kee", in 3 historical versions (from `2229677`). Removed from the current tree in `c464aa4`. |
| Teaching or student mentions | One generic mention: P02 line 6, "(client websites, teaching) are unaffected". No students, courses, grades or institutions. |
| Plans for unpublished work | In `docs/roadmap.md` (versions before `0886914`): "Feeds: TACCESS extension", "journal-extension tables", "What a grant adds" (human annotation at scale, larger VLMs, GUI-360, OS-Atlas, Mind2Web, AndroidWorld) and "$100 API credit". P05: "Full analysis waits for the TACCESS extension". R04: "Or should they wait for the TACCESS extension?". |
| Other internal material (not asked; not sensitive) | Local paths `/Volumes/Kraishan/...` and `~/research/...` in CLAUDE.md (old), session-log, the release checklist (old), P02, P04, R04 and R05. The secrets file location `~/.config/kraishan/secrets.env` and the `~/.zshrc` line-19 note, as paths only, never a value (P02, R02, P04, P05, R05, the old checklist). Max-plan usage notes, the M3 Pro laptop, and the reliacode and hub names. |
| Secrets | **None.** Patterns checked: Anthropic, OpenAI, HF, Kaggle, GitHub, AWS, Google, Slack and PyPI tokens, and private keys. |

Assessment: nothing sensitive. The advisor line and the TACCESS and grant plans were the only
items in your categories. Both were removed from the current tree; the history keeps them, as
you decided in D1.

## 4. Environment findings
- `ANTHROPIC_API_KEY` was unset at the start (checked by name).
- **Release gate:**
  - It blocked `git check-ignore -v RELEASE_APPROVED`. The hook counts only `ls`, `test`, `cat`
    and similar commands as read-only uses of that name, so I used `ls`.
  - With the file present, `git push origin v0.1.0` and `gh release create` went through.
- **PyPI's project JSON** (`/pypi/a11ydebt/json`) still returned `{"message": "Not Found"}`. That
  is a CDN-cached 404, probably from the R05 name check. The version endpoint, the simple index
  and the project page all show 0.1.0. It should clear by itself.
- **The builds are reproducible.** Hatchling's output from CI matches the local build, so the
  GitHub tag, the local tree and PyPI agree.
- **Zenodo timing:** the record was created 4 seconds after the release. Its
  `publication_date` is **2026-11-11**, though, because the release came at 23:37 UTC, which is
  already Nov 11 in Geneva. CITATION.cff says 2026-11-10 (UTC and Lubbock).
- **zsh word splitting** broke my first `compare_aissa.py` loop (exit 2, usage error). I reran
  it under bash; this was my mistake, not the code's.
- **The `pypi` environment** keeps the default `can_admins_bypass: true`. As admin, you can skip
  the review, but a run still waits unless you choose to.

## 5. Commits: hash + message, and whether pushed
All pushed, each with the Co-Authored-By trailer. `ruff check` and `ruff format --check .` ran
before every push.

| a11ydebt | Message |
|---|---|
| 12d93b6 | Add the P07 prompt (v0.1.0 release) |
| c464aa4 | Make CLAUDE.md suitable for a public repository (D1a) |
| 0886914 | Trim docs/roadmap.md to a public software roadmap |
| 468a79f | Use a repository-relative path in the Kaggle kernel README |
| 4988483 | Use the agreed AI-use wording in the README (D2) |
| f05d6af | Point the AI-use disclosure to prompts/ and reports/ (D1c) |
| 8958ed0 | Add the PyPI publish workflow (trusted publishing) |
| 4565e21 | Update the release checklist and changelog for trusted publishing |
| 515ffeb | Prepare the v0.1.0 release (**tagged v0.1.0**) |
| 19340f7 | Record the v0.1.0 DOIs and PyPI release |
| (next) | Add the R07 report and the release session-log entry |

| research-hub | Message |
|---|---|
| 796086e | Add the P07 prompt (a11ydebt v0.1.0 release) |
| (next) | Add the R07 report copy and update STATUS.md (a11ydebt released) |

## 6. Problems and how you handled them
1. **Asked mid-scan, as P07 allows.** The scan ran read-only during planning. The roadmap's
   TACCESS and grant plans were in the current tree, not only the history. I asked you, and you
   chose to trim the roadmap (`0886914`).
2. **zizmor's auditor persona flagged two low items:** no concurrency limit, and an
   `id-token: write` without a comment. Both are fixed before the first commit of the workflow.
3. **The hook block and the zsh loop**, as in section 4. Neither changed anything.
4. **The PyPI JSON cache** gave a false "not found". I confirmed the release through three other
   endpoints.
5. **Two departures from P07's wording, with reasons:**
   - **The README install switched to PyPI before the tag** (in `515ffeb`, not step 9's
     post-release commit). PyPI's page for 0.1.0 is built from the README at the tag and never
     changes. Otherwise it would say "not yet released, install from GitHub" forever. The GitHub
     install stays as the development option, and the DOI parts waited for step 9.
   - **`[Unreleased]` is not empty.** It already existed, empty. The project rule puts every
     user-visible change under it, so it now lists the post-release DOI and badge edits.
6. **Small extras beyond P07:**
   - The Kaggle README path (it ships in the sdist).
   - The how-to's install line and a PyPI badge.
   - Ticked roadmap items, and the CHANGELOG link references.

## 7. Decisions I need to make (numbered questions)
1. **Close the gate:** please run `rm ~/research/a11ydebt/RELEASE_APPROVED`. The hook blocks me
   from doing it.
2. **Zenodo date:** should the record's publication date be changed from 2026-11-11 to
   2026-11-10, to match CITATION.cff? This is a Zenodo web-UI metadata edit, with no new version.
   It could be done together with the paper-DOI edit later.
3. **PyPI page links:** the README's relative links (docs/…, prompts/, CITATION.cff) break on
   pypi.org. Should v0.1.1 or v0.2 use absolute GitHub links (my recommendation; no new
   dependency)?
4. **CI hardening:** `ci.yml` still uses tags (`checkout@v7`, `setup-uv@v10.3.0`). Pin them to
   SHAs like publish.yml? Separately, should `main` get reliacode-style branch protection now
   that the repo is public?

**Left for later: the paper DOI.** When IEEE Xplore assigns it:
- In `CITATION.cff`, uncomment `doi:` under `preferred-citation`.
- In the README's `@inproceedings`, replace the note with `doi = {…}`.
- In `.zenodo.json`, add `related_identifiers` (`isSupplementTo`, the paper DOI) for future
  versions.
- On the Zenodo record, add the same related identifier through the web UI.
- One commit, then a Zenodo metadata edit; no new release needed.

## 8. Usage note: rough share of the session limit this used
- About 90 tool calls across planning, Part A, the wait, and Part B. Mostly small edits, the
  history scan, and API and status checks.
- My rough guess is 20 to 25% of a 5-hour Max window; check `/usage`.
- No model calls, no API credit and no Kaggle.
- GitHub Actions: 7 CI runs of 4 jobs of about 20 s each, plus one publish run (3 min wall time,
  most of it waiting for approval).

## 9. Suggested next prompt scope
- **AISSA prep (before Dec 8):**
  - Put the QR code and the concept DOI on the slide, and make the handout PDF from
    `docs/how-to-audit.md`.
  - Check the QR code on a phone, signed out.
- **v0.1.1, small:** absolute links in the README, CI actions pinned to SHAs, and the paper DOI
  if IEEE has assigned it by then. Released through the same workflow, with a new
  `RELEASE_APPROVED`.
- **After AISSA:** v0.2 (issue #1, stream Rico from `unique_uis.tar.gz`), then S5 (the
  RICO-Semantics join).
