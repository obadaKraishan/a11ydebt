# Session log

Five lines per session: did / decided / next / open questions / usage notes.

## 2026-11-10 · S0 setup (prompt P01, report R01, both in ~/research/)
- **Did:** created the private repo; scaffolded uv, pydantic, ruff and pytest under Apache-2.0;
  added CLAUDE.md, the roadmap copy, licences and the changelog. Copied Rico (66,261 JSONs,
  16.44 GB, plus two CSVs) to `/Volumes/Kraishan/research-data/a11ydebt/raw/rico`, verified it
  (names, sizes and CSV checksums match; source unchanged) and symlinked it as `data/raw/rico`.
- **Decided (Obada):** use the Kraishan AISSA pipeline data and reference outputs; port the AISSA
  codebook; ship three populations with the paper's needs_label as the default; keep the repo
  private.
- **Next:** S1, which covers the Rico loader, coverage() and fixture tests, and a full-corpus
  comparison against the AISSA numbers.
- **Open questions:** the paper's status and AISSA's blind-review rules, before the repo goes
  public.
- **Usage notes:** see R01.

## 2026-11-10 · S1 build (prompt P01, report R01, both in ~/research/)
- **Did:**
  - Ported the AISSA codebook (`taxonomy.py`). Added the Rico loader (`rico.py`), `coverage()`
    and `audit_rico()` (`coverage.py`), the CLI `a11ydebt audit rico` and
    `scripts/compare_aissa.py`. There are three synthetic fixtures and 51 tests, and ruff is clean.
  - The full Rico run (66,261 screens, 417 s, 8 workers) reproduces every AISSA number exactly:
    17.74% needs-label, 33.20% icon-like, the role table, all 66,261 screens and all 9,384 apps
    (docs/reproduction-rico.md).
- **Decided:**
  - Ship three populations, with needs_label as the default (Obada).
  - Roles come from the class name only, as in the paper.
  - The P01 interactive_image population comes out at 33.29% coverage (35,217/105,780).
- **Next:** S2 is the AndroidControl reader as a Kaggle script kernel (port the AISSA TFRecord and
  protobuf reader). S3 adds the cluster bootstrap by app and `a11ydebt report`.
- **Open questions:**
  - Enable the release hook?
  - Paper status and AISSA rules before the repo goes public.
  - Stream Rico from `unique_uis.tar.gz`, so users skip the 16 GB extraction?
- **Usage notes:** one long session covered P01 (hub, S0 and S1). The Rico audit is deterministic
  local parsing with no model calls. The only LLM call was a 1-prompt local Ollama smoke test.

## 2026-11-10 · S2 AndroidControl on Kaggle (prompt P02, report R02, both in ~/research/)
- **Did:**
  - Ported AISSA's TFRecord and protobuf reader (`tfrecord.py`) and its AndroidControl parse logic
    (`androidcontrol.py`), and added the shared counter (`counts.py`).
  - Built the private CPU Kaggle kernel (`kaggle/androidcontrol_parse/`), `summarize
    androidcontrol` and `compare_aissa.py androidcontrol`. 80 tests pass.
  - Run 1 (AISSA's shards 00000-00009, 20.6 min, 12.1 MB) reproduces AISSA exactly: 57.27%
    needs-label, 62.75% icon-like, the role table, 10 shards, 7,623 episodes, 49,888 screens and
    700 apps (docs/reproduction-androidcontrol.md). The Rico regression run is still exact after
    the counter refactor.
- **Decided:**
  - AISSA's app count is over episodes with needs-label elements (700); 701 over all episodes.
  - `n_apps` excludes the unknown app.
  - Run 2 (shards 00010-00019) was started and not waited on.
- **Next:** pull run 2 and build all-20-shard totals. S3 adds the cluster bootstrap by app
  (port AISSA's `bootstrap.py`) and `a11ydebt report`.
- **Open questions:** whether to stream Rico from `unique_uis.tar.gz` for users. The run 2 results
  are pending.
- **Usage notes:** Kaggle did the 25 GB of downloads and parsing. Local work was the code, the
  tests, and a 7-minute Rico regression run. Polling ran in background loops.

## 2026-11-10 · S3 bootstrap and report (prompt P04, report R04, both in a11ydebt/)
- **Did:**
  - Part A: HF token files set to 600, `README_HF_CACHE_LAYOUT.md` written on the drive, and
    issue #1 opened (Rico tar.gz streaming, labelled v0.2).
  - Pulled run 2 (0 failed or truncated shards) and built the all-20 tables: 15,283 episodes,
    57.18% needs-label, 62.34% icon-like. The run-1 subset still equals AISSA.
  - Ported AISSA's cluster bootstrap (`a11ydebt.bootstrap`) and added `a11ydebt report`. The
    replay reproduces all six AISSA intervals exactly, with bit-identical draws. 110 tests pass.
- **Decided:**
  - AISSA's `bootstrap.py` is an import shim, so the port is from ReviewerChecks.
  - numpy becomes a runtime dependency.
  - `report` seeds each interval with its own generator. That differs from the paper's shared
    stream by up to 0.02 points, and `compare_aissa.py bootstrap` gives the exact paper numbers.
- **Next:** S4, packaging (pyproject metadata, `pipx install`), the README citation, CITATION.cff,
  and the release checklist. No tag or upload until `RELEASE_APPROVED`.
- **Open questions:**
  - Should `report` print the paper's exact intervals (shared stream) instead?
  - Should the all-20 numbers go into the AISSA talk?
  - Paper status and blind-review rules, before the repo goes public.
- **Usage notes:** Kaggle did run 2 (2,028 s of CPU). Local work was the code, a 6-minute Rico
  re-audit and an 11-second report. There were no model calls.

## 2026-11-10 · S4 packaging and release prep (prompt P05, report R05, both in a11ydebt/)
- **Did:**
  - CI on Python 3.10 to 3.13 is green.
  - Version 0.1.0 with full metadata; the wheel and sdist build, install and run cleanly (the
    sdist passes all tests on its own).
  - README rewrite; CITATION.cff (valid) and .zenodo.json with marked placeholders.
  - New docs: data card, results/v0.1 aggregates, the two-page how-to, the QR code and the
    release checklist.
- **Decided (Obada, R04):**
  - D1: per-interval seeds plus a footnote. D2: all 20 shards shown only as a robustness
    extension.
  - D3: numpy is a hard dependency. D4: no release in S4.
  - Also: DOI placeholders are comments (CFF) or an invalid string (Zenodo), never fake DOIs.
- **Next:** Obada runs `docs/release-checklist.md` once `RELEASE_APPROVED` exists. After AISSA:
  v0.2 (issue #1, Rico tar.gz streaming), then S5 (the RICO-Semantics join).
- **Open questions:**
  - Should prompts/, reports/ and the local paths stay in the public history?
  - Is the PyPI name available?
  - Confirm the AI-use wording for this repo's workflow.
- **Usage notes:** no model calls and no Kaggle use. CI and local matrix runs took seconds each.

## 2026-11-10 · v0.1.0 release (prompt P07, report R07, both in a11ydebt/)
- **Did:**
  - Made the tree public-safe: CLAUDE.md and docs/roadmap.md trimmed; the AI-use wording updated.
  - Scanned the full history for personal material; nothing sensitive.
  - Added the trusted-publishing workflow; Obada made the repo public.
  - Tagged and released v0.1.0, now on PyPI (approved by Obada) and Zenodo (concept DOI
    10.5281/zenodo.24121869, version DOI 10.5281/zenodo.24121870).
- **Decided (Obada, R05 and this session):**
  - D1: keep the history, trim the tree. D2: the new AI-use wording. D3: release without the
    paper DOI.
  - D4: sole software author. D5: PyPI yes, HF Space no.
  - Also: the README install switched to PyPI before the tag, because PyPI's 0.1.0 page is
    built from it.
- **Next:** delete RELEASE_APPROVED. Add the paper DOI once IEEE Xplore assigns it. After AISSA:
  v0.2 (issue #1), then S5.
- **Open questions:**
  - Zenodo dates the record 2026-11-11 (CET), while CITATION.cff says 2026-11-10.
  - README links are relative, so they break on PyPI's project page.
- **Usage notes:** no model calls and no Kaggle use. Seven CI runs (one cancelled when
  superseded) plus one publish run (3 min, including the wait for approval).
