# Licences: code, data and models

Adapted from `docs/DATA_LICENSES.md` in the AISSA pipeline (accessibility-debt-agents). Where that
file and other sources disagree, this project follows the stricter reading.

## Code
a11ydebt is Apache-2.0 (`LICENSE`). `src/a11ydebt/taxonomy.py` is ported from the MIT-licensed
AISSA pipeline, and `NOTICE` keeps that notice. The code licence does not cover any dataset.

## Datasets
| Dataset | Terms | May we redistribute? |
|---|---|---|
| **Rico** (Deka et al., UIST 2017) | University of Illinois research-use agreement, not an open licence (<https://www.interactionmining.org/archive/rico/copyright.txt>). Hugging Face mirrors list the licence as "unknown". | **No raw files.** Publish only aggregate statistics, screen and app identifiers, and checksums. |
| **AndroidControl** (Li et al., NeurIPS 2024 D&B) | Apache-2.0, Copyright 2024 The Google Research Authors | Yes, with attribution and the licence |
| **RICO-Semantics** (Sunkara et al., 2022) | CC BY-SA 4.0 | Yes, but anything derived from it must also be CC BY-SA 4.0, and Rico's terms still cover the underlying screens. |

### Rico in practice
| You may | You may not |
|---|---|
| Download it and analyse it | Commit it to git (`data/` is gitignored) |
| Publish aggregate statistics, such as coverage tables | Publish a derived dataset that contains Rico hierarchies or screenshots |
| Publish the parsing code | Attach raw Rico files to a submission or upload them to a public archive |
| Share file checksums so readers can verify their own copy | Use Rico screenshots in test fixtures (ours are synthetic) |

## Models (v1.1 decorative-icon judge)
Published outputs use Apache-2.0 or MIT models only, for example Qwen2.5-VL and Qwen3-VL. Llama
and Gemma 1 to 3 are fine for private exploration but not for published outputs. Record the
model name and licence in every LLM-touched row's provenance.

## Citations
- Deka, B., Huang, Z., Franzen, C., Hibschman, J., Afergan, D., Li, Y., Nichols, J., and Kumar, R.
  (2017). Rico: A Mobile App Dataset for Building Data-Driven Design Applications. UIST '17.
  <https://doi.org/10.1145/3126594.3126651>
- Li, W., Bishop, W., Li, A., Rawles, C., Campbell-Ajala, F., Tyamagundlu, D., and Riva, O. (2024).
  On the Effects of Data Scale on UI Control Agents. NeurIPS 2024 Datasets and Benchmarks.
  arXiv:2406.03679
- Sunkara, S., Wang, M., Liu, L., Baechler, G., Hsiao, Y.-C., Chen, J., Sharma, A., and Stout, J.
  (2022). Towards Better Semantic Understanding of Mobile Interfaces. arXiv:2210.02663
