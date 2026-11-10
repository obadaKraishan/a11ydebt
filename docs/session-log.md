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
