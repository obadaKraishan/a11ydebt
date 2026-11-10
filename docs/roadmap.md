# Roadmap 01 of 10: a11ydebt (Zero-Cash Edition)

**Accessibility-Debt Audit of GUI Agent Corpora** · Prepared for Obada Kraishan, November 2026

> **Why it will be cited:** The first reproducible, cross-corpus measure of the accessibility debt built into the data behind GUI agents.

| At a glance | |
|---|---|
| When | **First wave: start now** |
| Start | Start in week 1. AISSA (Dec 8 to 10) is the only hard external deadline in the portfolio. |
| Cash | $0 |
| API credit | $0 (optional few $) |
| Start | Week 1 |
| First release | Week 4, v0.1 |
| Depends on | Your AISSA pipeline |
| Feeds | TACCESS extension |

**What changed in this edition:** VLM decorative-icon judging moved to v1.1 behind a validation gate. AndroidControl (Apache 2.0, about 50 GB) is parsed on Kaggle.


---

## 1. Goal and v1 scope

A pip-installable CLI, `a11ydebt audit rico|androidcontrol`, that reproduces your AISSA content-description coverage numbers from raw data. It ships with a public audit table and a 2-page "how to audit your GUI corpus" note you can show at AISSA.

- **v1 (by AISSA, Dec 8 to 10):** Rico and AndroidControl only.
- **v1.1:** AITW and AMEX loaders, plus the decorative-icon experiment.

## 2. What changed

- **The VLM decorative-icon judge moved** from a v1 feature to a v1.1 experiment with a validation gate. No source verifies that small VLMs judge decorative icons reliably, so it has to earn its place.
- **AndroidControl is easier to get than assumed.** It is Apache 2.0 Google Research data at `gs://gresearch/android_control/` (GZIP TFRecords), with Hugging Face mirrors (about 50 GB as TFRecord, about 67 GB as Parquet). That is too big for your laptop, so Kaggle parses it.

## 3. Toolchain map

| Who | What it does |
|---|---|
| **Claude Code** (subscription) | Parsers for Rico view hierarchies and AndroidControl TFRecords, coverage metrics, cluster bootstrap by app, CLI, tests, docs |
| **Local models** (Kraishan drive) | None needed for v1. For v1.1 spot checks, a 3B to 4B VLM via Ollama on a handful of crops |
| **Kaggle T4x2** | Stream and parse AndroidControl, compute per-episode tables, write compact Parquet. Later, run Qwen2.5-VL or Qwen3-VL 7B (AWQ) as a first-pass decorative-vs-informative judge |
| **$100 API credit** | None for v1. Optional Haiku 5.5 vision second opinion on a 300-crop validation set |

## 4. Cost

| Item | Cost |
|---|---|
| Cash | **$0** |
| API credit | $0 for v1; a few dollars for the optional v1.1 second opinion |
| Kaggle GPU | A few hours for AndroidControl parsing |

## 5. Build sessions

| Session | Deliverable |
|---|---|
| S1 | Repo skeleton, Rico loader (start with the 150 MB semantic-annotation pack, then the 6 GB screenshots and hierarchies), coverage metric, tests against 20 hand-checked screens |
| S2 | AndroidControl reader as a Kaggle script kernel that outputs one Parquet row per UI node, with checkpointing |
| S3 | Cluster bootstrap CIs by app; reproduce the paper's tables; `a11ydebt report` writes Markdown and CSV |
| S4 | Packaging (pyproject, `pipx install a11ydebt`), README with AISSA citation, Zenodo DOI, **v0.1.0 tag** |
| S5 (after AISSA) | RICO-Semantics join (about 500k human annotations: 350k icon shape, 78k icon semantics, 66k label associations) to define "icon needs a label" |
| S6 | VLM judge on Kaggle over a stratified 300-crop sample, compared against your labels and Kulsawasd Jitkajornwanich's |
| S7 | AITW and AMEX loaders |

## 6. Kickoff prompt

Paste this into Claude Code in the new `a11ydebt` repo:

```text
You are helping me turn my IEEE AISSA 2026 paper (content-description coverage in Rico and
AndroidControl) into a reproducible pip CLI called a11ydebt. Read CLAUDE.md. Plan mode first.
Session 1 scope: (a) package skeleton with uv, ruff, pytest; (b) a Rico loader that reads view
hierarchy JSON from a path I give (data/raw/rico/), walks nodes, and flags clickable image-like
nodes lacking content-desc; (c) a coverage() function returning counts and proportion per
screen and per app; (d) tests using 3 tiny fixture hierarchies you create. Do not download data
yourself; give me the exact download commands instead. Stop after tests pass.
```

## 7. Data, licensing and ethics

- **AndroidControl:** Apache 2.0.
- **Rico:** license listed as "unknown" on Hugging Face mirrors, so redistribute only derived statistics and IDs, never screenshots.
- **RICO-Semantics:** a Google Research dataset on GitHub; check its license file before redistributing labels.
- **No human subjects** are involved.

## 8. Quality checks

- Reproduce your published numbers to within rounding.
- Unit tests on fixture hierarchies.
- Report second-coder agreement with Krippendorff's alpha.
- **VLM gate:** the VLM judge counts as a labeler only if alpha ≥ 0.80 against humans on n = 300 (binomial 95% CI about ±5.7 points). Otherwise it is a triage tool only.

## 9. Release checklist

- [ ] Version tag and Zenodo DOI
- [ ] CITATION.cff
- [ ] Data card stating what is not redistributed
- [ ] QR code on your AISSA slide linking to the repo
- [ ] Optional HF Space demo (ZeroGPU)

## 10. Timeline (5 to 8 hours/week)

| Week | Work |
|---|---|
| 1 (Nov 10 to 16) | S1 Rico loader |
| 2 | S2 AndroidControl on Kaggle |
| 3 | S3 bootstrap and tables |
| 4 (Dec 1 to 10) | S4 release v0.1 and **AISSA** |
| 5 to 6 | S5 RICO-Semantics join |
| 7 to 8 | S6 VLM judge experiment |
| 9 to 10 | S7 AITW and AMEX; journal-extension tables |

## 11. Risks and fallbacks

| Risk | Fallback |
|---|---|
| AndroidControl parsing too slow on Kaggle | Process the test split first |
| VLM judge unreliable | Report it as a negative finding; that is still a contribution |
| AISSA time crunch | Ship a Rico-only v0.1 |

## 12. What a grant adds

- Human annotation of decorative icons at scale
- Larger VLMs
- GUI-360, OS-Atlas, Mind2Web and AndroidWorld in the audit

---

## Sources

1. [Android-Control mirror (leosltl)](https://huggingface.co/datasets/leosltl/Android-Control)
2. [Android-Control mirror (smolagents)](https://huggingface.co/datasets/smolagents/android-control)
3. [AndroidControl paper (NeurIPS 2024 Datasets and Benchmarks)](https://proceedings.neurips.cc/paper_files/paper/2024/file/a79f3ef3b445fd4659f44648f7ea8ffd-Paper-Datasets_and_Benchmarks_Track.pdf)
4. [Rico dataset](https://interactionmining.org/rico)
5. [Rico on Hugging Face (license note)](https://huggingface.co/datasets/creative-graphic-design/Rico/blob/main/README.md)
6. [RICO-Semantics repository](https://github.com/google-research-datasets/rico_semantics)
7. [RICO-Semantics paper](https://arxiv.org/html/2210.02663v1)
