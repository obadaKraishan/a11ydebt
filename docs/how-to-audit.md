# How to audit your GUI corpus with a11ydebt

*A two-page practical note. a11ydebt 0.1.0 · <https://github.com/obadaKraishan/a11ydebt>
(QR code: [assets/qr-a11ydebt.png](assets/qr-a11ydebt.png))*

## Why audit
Computer-use agents learn to operate phones from corpora of recorded screens. A screen reader can
announce a button or an icon only if the app gave it a label, its `content-desc`. When labels are
missing, the corpus teaches agents on screens that blind users cannot operate. It also misses
the text an accessibility-tree agent would read. An audit puts a number on that gap, which we
call *accessibility debt*, before you train on a corpus or benchmark with it.

## What gets counted: three populations
a11ydebt looks at every element that is **visible on screen and has a size** (hidden and
zero-size elements are skipped). It then asks whether the element needs a label, and if so,
whether it has one.

- **needs_label: anything a screen reader would have to name.** That is every image, plus every
  button, input or tappable element that shows no text of its own. Layout containers and web
  views are exempt. This is the paper's main measure.
- **icon_like: tappable graphics with no text.** These are icons and image buttons with no
  visible text, such as a magnifying glass, a heart or a hamburger menu. If one has no label, a
  blind user hears only "button". This is the strictest measure.
- **interactive_image: images you can tap or focus.** This means ImageViews, ImageButtons and
  floating action buttons that are clickable or focusable. It is new in a11ydebt and not in the
  paper.

**Coverage** is labelled / candidates, pooled over the whole corpus. Debt is 1 minus coverage.

## The commands
```bash
pipx install "git+https://github.com/obadaKraishan/a11ydebt.git"

# 1. Audit: per-screen and per-app counts (screens.csv, apps.csv, summary.json)
a11ydebt audit rico path/to/rico --workers 8 --out audit_rico
a11ydebt audit androidcontrol android_control-00000-of-00020 --splits splits.json --out audit_ac

# 2. For all of AndroidControl (about 50 GB), run the Kaggle kernel instead, then:
a11ydebt summarize androidcontrol kaggle_outputs/ --out audit_ac

# 3. Report: Markdown and CSV tables with 95% confidence intervals
a11ydebt report "Rico=audit_rico" "AndroidControl=audit_ac" --out report
```
For Rico, point the tool at the folder that holds `combined/*.json` and `ui_details.csv`. For
any other corpus, write a loader that yields screens whose nodes carry the codebook flags. The
counting, bootstrap and report code needs no changes.

## Reading the intervals: screens or apps?
Elements are not independent. Screens of the same app share a design system and a developer,
and the same habits about labelling. So a11ydebt reports two cluster-bootstrap intervals, each
from 5,000 resamples:

- **Screen clusters** resample whole screens. This captures variation from screen to screen
  within the corpus, and it is narrow because there are tens of thousands of screens.
- **App clusters** resample whole apps. This captures variation from app to app, which is the
  real unit of developer behaviour. **Cite this one** when you generalise about "apps in this
  corpus". It is wider, and it gets much wider when the corpus has few apps.

If the screen interval is tight but the app interval is wide, a few large apps drive the
estimate. On AndroidControl, an episode whose app cannot be identified becomes its own cluster,
so no data is dropped. The CSV also gives the element-level Wilson interval, which treats
elements as independent. It is too narrow; report it only for comparison.

## Worked numbers (IEEE AISSA 2026)
| Corpus | needs_label coverage [app-cluster 95% CI] | icon_like coverage [app-cluster 95% CI] | Apps (clusters) |
|---|---:|---:|---:|
| Rico (2017), 66,261 screens | **17.74%** [17.12, 18.37] | **33.20%** [31.96, 34.47] | 8,904 |
| AndroidControl (2024), 10 shards, 49,892 screens | **57.27%** [55.66, 58.84] | **62.75%** [57.76, 67.39] | 951 |

Here is how to read these:
- **Rico** labels fewer than one in five elements that need a label.
- **AndroidControl** labels a little over half.
- **The gap** is 39.5 points; in the paper, its app-cluster interval is [37.81, 41.21]. It is
  large and certain.
- **AndroidControl's icon-like interval** is about ten points wide. With about 1,000 apps,
  icon labelling varies a great deal between apps, so read that estimate with more caution than
  the needs-label one.
- **Screen-cluster intervals** (for example 57.27% [56.99, 57.53]) would hide that.

**Robustness extension (not in the paper):** all 20 AndroidControl shards (15,283 episodes,
99,131 screens) give 57.18% [55.69, 58.65] needs-label coverage, which is within the 10-shard
interval.

*Intervals use independent seeds. The paper's Table I intervals come from one shared random
stream and differ by at most 0.02 points. `scripts/compare_aissa.py bootstrap` reproduces them
exactly.*

## Five pitfalls
1. **Report the denominator.** "57% coverage" means nothing without the population and the
   count (1,462,544 needs-label elements).
2. **Cluster by app.** Element-level intervals look precise and are wrong.
3. **Keep the inclusion rule fixed.** Counting invisible or zero-size nodes changes the numbers.
   a11ydebt's rule is the paper's codebook, and changing it requires a re-run of the comparison
   against AISSA.
4. **A content description is not the whole accessible name.** Android can also fall back on
   hint text or a nearby label. These counts measure the `content-desc` field itself.
5. **Don't redistribute the corpus.** Rico's terms allow aggregate statistics and identifiers
   only. a11ydebt never writes screenshots, and its published tables are aggregates.

## For the slide
> **a11ydebt**: `pipx install` → `a11ydebt audit` → `a11ydebt report`. It reproduces AISSA 2026
> exactly. Rico 17.74% vs AndroidControl 57.27% needs-label coverage (app-cluster 95% CIs
> [17.12, 18.37] and [55.66, 58.84]). Robustness extension, not in the paper: all 20 AndroidControl
> shards give 57.18% [55.69, 58.65]. Scan the QR code for the repo.

**Cite:** Kraishan, O., and Jitkajornwanich, K. (2026). *Trained on What Screen Readers Cannot
Read: Accessibility Debt in the GUI Corpora Behind Computer-Use Agents.* IEEE AISSA 2026.
