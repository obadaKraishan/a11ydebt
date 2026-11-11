# Data card: a11ydebt v0.1 audit tables

a11ydebt produces **counts**, not a dataset of UI content. It reads GUI corpora that you download
yourself, applies the AISSA 2026 codebook to every UI element, and writes tables of how many
elements need a screen-reader label and how many have one. This card describes those tables,
what this repository publishes, what it never redistributes, and how to regenerate everything.

## What the tables contain
**Published in this repository: `results/v0.1/`.** These are corpus-level aggregates only, for
Rico, AndroidControl (10 shards) and AndroidControl (all 20 shards).

| File | One row per | Columns |
|---|---|---|
| `coverage.csv` | corpus × population | candidates, labelled, coverage, element-level Wilson 95% CI, app-cluster and screen-cluster 95% bootstrap CIs, cluster counts, resamples, seed, level |
| `roles.csv` | corpus × role | needs_label candidates, labelled, coverage |
| `screens_with_debt.csv` | corpus × population | screens, screens with candidates, screens with at least one unlabelled element, and both shares |
| `report.md` | | The same three tables in Markdown, with the method note |

**Written locally by the CLI and never committed** (`data/` is gitignored):

| File | One row per | Contains identifiers? |
|---|---|---|
| `screens.csv` (`audit`, `summarize`) | screen | Yes: the Rico screen id or the AndroidControl `episode_step`, plus the app package. Counts per population. |
| `apps.csv` | app | Yes: the app package. Counts and screens with debt per population. |
| `summary.json` | corpus | No: totals, the role breakdown, inclusion rule, failures, version. |
| Kaggle `screens/*.parquet` | AndroidControl screen | Yes: ids, split, app and counts. |
| Kaggle `nodes/*.parquet` | candidate node | Yes: ids, class name, role, resource id, content description, text, hint text and the codebook flags. |

No table contains screenshots or rendered pixels. Only the Kaggle node table contains UI text.

## Sources and licences
| Corpus | Source | Licence | What a11ydebt may publish |
|---|---|---|---|
| **Rico** (Deka et al., UIST 2017) | <https://interactionmining.org/rico>: `unique_uis.tar.gz` (66,261 view hierarchies) and `ui_details.csv` | University of Illinois research-use terms; Hugging Face mirrors list it as "unknown". It is not an open licence. | **Derived statistics and identifiers only:** aggregate tables, screen and app ids, and file checksums. |
| **AndroidControl** (Li et al., NeurIPS 2024 D&B) | `https://storage.googleapis.com/gresearch/android_control/`: 20 GZIP TFRecord shards, about 50 GB | Apache-2.0, Copyright 2024 The Google Research Authors | Redistribution is allowed with attribution and the licence. v0.1 still publishes aggregates only. |
| RICO-Semantics | Not used in v0.1 | CC BY-SA 4.0 | |

Full terms and citations: [docs/licenses.md](licenses.md).

## Never redistributed
- Rico screenshots, Rico view-hierarchy JSON, and any table derived from them that holds UI text
  or layout.
- AndroidControl TFRecord shards, screenshots and accessibility trees. Their licence would allow
  it, but a11ydebt is an audit tool, not a mirror.
- Node-level tables from either corpus.
- Test fixtures derived from real data. The fixtures are synthetic: three hand-built Rico-format
  screens in `tests/fixtures/rico/`, and TFRecord shards that `tests/synthetic_tfrecord.py`
  generates.

The package (wheel and sdist) contains code, synthetic test fixtures and documentation only.

## How to regenerate everything
1. **Rico.** Download it under its terms, unpack `unique_uis.tar.gz`, and check the archive and
   `ui_details.csv` against the SHA-256 values in [reproduction-rico.md](reproduction-rico.md).
   Then run `a11ydebt audit rico <folder> --workers 8 --out audit_rico` (about 6 minutes on 8 cores).
2. **AndroidControl.** Run the Kaggle CPU kernel in `kaggle/androidcontrol_parse/`: run 1 covers
   shards 00000 to 00009 and run 2 covers 00010 to 00019. The kernel verifies each shard's bytes
   and checksum before it parses it. Then run `a11ydebt summarize androidcontrol <pulled outputs>
   --out audit_ac`. A single shard can also be audited locally with `a11ydebt audit
   androidcontrol`.
3. **Tables.** Run `a11ydebt report "Rico=audit_rico" "AndroidControl=audit_ac"`.

The commands that produced `results/v0.1/` are listed in
[results/v0.1/README.md](../results/v0.1/README.md). Parsing is deterministic, and every interval
is seeded, so a rerun gives identical numbers.

## Provenance
- **Rules:** the codebook (`src/a11ydebt/taxonomy.py`) is ported unchanged from the MIT-licensed
  AISSA pipeline (see `NOTICE`). Changing a rule changes every number, so a change needs a test,
  a changelog entry and a re-run of `scripts/compare_aissa.py`.
- **Checks:** the Rico and AndroidControl (10 shards) numbers equal the AISSA pipeline's, screen by
  screen and episode by episode. The paper's six cluster-bootstrap intervals are reproduced
  exactly ([reproduction-rico.md](reproduction-rico.md),
  [reproduction-androidcontrol.md](reproduction-androidcontrol.md),
  [reproduction-bootstrap.md](reproduction-bootstrap.md)).
- **No LLM in the data path:** no language model labelled, generated or edited any data item, so
  no item records an LLM model or licence. (The v1.1
  decorative-icon experiment would add LLM-judged items, with model and licence recorded per row.)
- **Versions:** the tables in `results/v0.1/` came from a11ydebt 0.1.0, Kaggle runs 1 and 2
  (bundled from commit `3896724`), seed 20260908 and 5,000 resamples. a11ydebt 0.1.1
  regenerated `report.md` (its header now separates identified apps from no-app episodes); the
  CSVs are byte-identical.

## Known limitations
- **Content description only.** Coverage counts a non-empty `content-desc`. It does not count
  every way Android can compute an accessible name, such as hint text or a label from a nearby
  view. The AISSA pipeline's reviewer checks (Check 4) test hint text as a label.
- **Roles from the class name only,** as in the paper.
- **AndroidControl apps** come from the dominant resource-id package of each episode. 490 of the
  15,283 episodes have no identifiable app, and each becomes its own cluster.
- **Rico is a 2017 snapshot** of Android apps, and AndroidControl was released in 2024. Neither
  is a random sample of the apps people use today.
