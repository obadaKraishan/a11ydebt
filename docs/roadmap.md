# Roadmap: a11ydebt

**Accessibility-Debt Audit of GUI Agent Corpora**

> **Aim:** the first reproducible, cross-corpus measure of the accessibility debt built into the
> data behind GUI agents.

| At a glance | |
|---|---|
| First release | v0.1.0, before IEEE AISSA 2026 (Dec 8 to 10) |
| Depends on | The AISSA 2026 pipeline (accessibility-debt-agents), as the reference implementation |

**Design notes:** VLM decorative-icon judging is a v1.1 experiment behind a validation gate.
AndroidControl (Apache 2.0, about 50 GB) is parsed on Kaggle.

---

## 1. Goal and v1 scope

A pip-installable CLI, `a11ydebt audit rico|androidcontrol`, that reproduces the AISSA paper's content-description coverage numbers from raw data. It ships with a public audit table and a 2-page "how to audit your GUI corpus" note for AISSA.

- **v1 (by AISSA, Dec 8 to 10):** Rico and AndroidControl only.
- **v1.1:** AITW and AMEX loaders, plus the decorative-icon experiment.

## 2. Design decisions

- **The VLM decorative-icon judge is a v1.1 experiment** with a validation gate, not a v1 feature. No source verifies that small VLMs judge decorative icons reliably, so it has to earn its place.
- **AndroidControl is easy to get.** It is Apache 2.0 Google Research data at `gs://gresearch/android_control/` (GZIP TFRecords), with Hugging Face mirrors (about 50 GB as TFRecord, about 67 GB as Parquet). That is too big for a laptop, so Kaggle parses it.

## 3. Toolchain map

| Who | What it does |
|---|---|
| **Claude Code** | Parsers for Rico view hierarchies and AndroidControl TFRecords, coverage metrics, cluster bootstrap by app, CLI, tests, docs |
| **Local models** | None needed for v1. For v1.1 spot checks, a 3B to 4B VLM via Ollama on a handful of crops |
| **Kaggle T4x2** | Stream and parse AndroidControl, compute per-episode tables, write compact Parquet. Later, run Qwen2.5-VL or Qwen3-VL 7B (AWQ) as a first-pass decorative-vs-informative judge |
| **Hosted model (optional)** | None for v1. A Claude Haiku vision second opinion on a 300-crop validation set |

## 4. Build sessions

S1 to S4 make up v0.1.0; S5 to S7 come after AISSA.

| Session | Deliverable |
|---|---|
| S1 | Repo skeleton, Rico loader (start with the 150 MB semantic-annotation pack, then the 6 GB screenshots and hierarchies), coverage metric, tests against 20 hand-checked screens |
| S2 | AndroidControl reader as a Kaggle script kernel that outputs one Parquet row per UI node, with checkpointing |
| S3 | Cluster bootstrap CIs by app; reproduce the paper's tables; `a11ydebt report` writes Markdown and CSV |
| S4 | Packaging (pyproject, `pipx install a11ydebt`), README with AISSA citation, Zenodo DOI, **v0.1.0 tag** |
| S5 (after AISSA) | RICO-Semantics join (about 500k human annotations: 350k icon shape, 78k icon semantics, 66k label associations) to define "icon needs a label" |
| S6 | VLM judge on Kaggle over a stratified 300-crop sample, compared against the two paper authors' labels |
| S7 | AITW and AMEX loaders |

## 5. Kickoff prompt (S1)

The prompt that started the AI-assisted development in Claude Code:

```text
You are helping me turn my IEEE AISSA 2026 paper (content-description coverage in Rico and
AndroidControl) into a reproducible pip CLI called a11ydebt. Read CLAUDE.md. Plan mode first.
Session 1 scope: (a) package skeleton with uv, ruff, pytest; (b) a Rico loader that reads view
hierarchy JSON from a path I give (data/raw/rico/), walks nodes, and flags clickable image-like
nodes lacking content-desc; (c) a coverage() function returning counts and proportion per
screen and per app; (d) tests using 3 tiny fixture hierarchies you create. Do not download data
yourself; give me the exact download commands instead. Stop after tests pass.
```

## 6. Data, licensing and ethics

See `docs/licenses.md` for each dataset's terms as checked.

- **AndroidControl:** Apache 2.0.
- **Rico:** license listed as "unknown" on Hugging Face mirrors, so redistribute only derived statistics and IDs, never screenshots.
- **RICO-Semantics:** a Google Research dataset on GitHub; check its license file before redistributing labels.
- **No human subjects** are involved.

## 7. Quality checks

- Reproduce the paper's published numbers to within rounding.
- Unit tests on fixture hierarchies.
- Report second-coder agreement with Krippendorff's alpha.
- **VLM gate:** the VLM judge counts as a labeler only if alpha ≥ 0.80 against humans on n = 300 (binomial 95% CI about ±5.7 points). Otherwise it is a triage tool only.

## 8. Release checklist

The full steps are in `docs/release-checklist.md`.

- [ ] Version tag and Zenodo DOI
- [ ] CITATION.cff
- [ ] Data card stating what is not redistributed
- [ ] QR code on the AISSA slide linking to the repo

## 9. Timeline

| Week | Work |
|---|---|
| 1 (Nov 10 to 16) | S1 Rico loader |
| 2 | S2 AndroidControl on Kaggle |
| 3 | S3 bootstrap and tables |
| 4 (Dec 1 to 10) | S4 release v0.1 and **AISSA** |
| 5 to 6 | S5 RICO-Semantics join |
| 7 to 8 | S6 VLM judge experiment |
| 9 to 10 | S7 AITW and AMEX |

## 10. Risks and fallbacks

| Risk | Fallback |
|---|---|
| AndroidControl parsing too slow on Kaggle | Process the test split first |
| VLM judge unreliable | Report it as a negative finding; that is still a contribution |
| AISSA time crunch | Ship a Rico-only v0.1 |

---

## Sources

1. [Android-Control mirror (leosltl)](https://huggingface.co/datasets/leosltl/Android-Control)
2. [Android-Control mirror (smolagents)](https://huggingface.co/datasets/smolagents/android-control)
3. [AndroidControl paper (NeurIPS 2024 Datasets and Benchmarks)](https://proceedings.neurips.cc/paper_files/paper/2024/file/a79f3ef3b445fd4659f44648f7ea8ffd-Paper-Datasets_and_Benchmarks_Track.pdf)
4. [Rico dataset](https://interactionmining.org/rico)
5. [Rico on Hugging Face (license note)](https://huggingface.co/datasets/creative-graphic-design/Rico/blob/main/README.md)
6. [RICO-Semantics repository](https://github.com/google-research-datasets/rico_semantics)
7. [RICO-Semantics paper](https://arxiv.org/html/2210.02663v1)
