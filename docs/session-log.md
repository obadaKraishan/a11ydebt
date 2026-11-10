# Session log

Five lines per session: did / decided / next / open questions / usage notes.

## 2026-11-10 · S0 setup (prompt P01, report R01, both in ~/research/)
- **Did:** created the private repo; scaffolded uv, pydantic, ruff and pytest under Apache-2.0;
  added CLAUDE.md, the roadmap copy, licences and the changelog. Started copying Rico (66,261
  JSONs and two CSVs) to `/Volumes/Kraishan/research-data/a11ydebt/raw/rico`, to be symlinked
  into `data/raw/rico`.
- **Decided (Obada):** use the Kraishan AISSA pipeline data and reference outputs; port the AISSA
  codebook; ship three populations with the paper's needs_label as the default; keep the repo
  private.
- **Next:** S1, which covers the Rico loader, coverage() and fixture tests, and a full-corpus
  comparison against the AISSA numbers.
- **Open questions:** the paper's status and AISSA's blind-review rules, before the repo goes
  public.
- **Usage notes:** see R01.
