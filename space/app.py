"""a11ydebt on Hugging Face Spaces: explore the accessibility debt in two GUI-agent corpora, or
audit one screen of your own with the same rules.

The Explore tab reads the per-screen statistics in ``data/`` (ids and counts only; see
``build_stats.py``). The Audit tab reads one uploaded view hierarchy in memory, deletes Gradio's
temporary copy straight away, and keeps nothing. There is no logging of content, no run
history and no analytics.
"""

from __future__ import annotations

import contextlib
import os
import time

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")

from pathlib import Path

import gradio as gr
import pandas as pd

import charts
import explore_stats as ex
import published
import screen_audit as sa

HERE = Path(__file__).resolve().parent
STATS = ex.load_stats(HERE / "data")
EXAMPLES = {
    "xml": HERE / "examples" / "recipe_screen.xml",
    "json": HERE / "examples" / "recipe_screen.json",
}
REPO = "https://github.com/obadaKraishan/a11ydebt"
PYPI = "https://pypi.org/project/a11ydebt/"
DOI = "https://doi.org/10.5281/zenodo.24121869"
DATASET = "https://huggingface.co/datasets/obadakr/a11ydebt-stats"
PRIVACY = (
    "**Privacy:** your file is read in memory, audited and dropped. The temporary copy the "
    "upload makes is deleted as soon as it has been read. Nothing is logged or stored, and the "
    "app keeps no run history and has no analytics."
)
LIMITS = (
    "a11ydebt reports **label coverage** (content descriptions). It is not a full "
    "accessibility audit: it does not check contrast, touch-target size, focus order, labels "
    "taken from a nearby view, or whether a label is meaningful."
)


def pct(value: float | None, digits: int = 2) -> str:
    return "n/a" if value is None else f"{100 * value:.{digits}f}%"


# ------------------------------------------------------------------ Explore


def _card(corpus: str) -> charts.Card:
    h = ex.headline(STATS, corpus)
    need, icon = h["needs_label"], h["icon_like"]
    low, high = published.APP_CLUSTER_CI[corpus]["needs_label"]
    return charts.Card(
        title=ex.CORPUS_LABELS[corpus],
        css="s1" if corpus == "rico" else "s2",
        big=pct(need["coverage"]),
        big_caption="of the elements that need a label have one",
        meta=(
            f"{need['labelled']:,} of {need['candidates']:,} elements · "
            f"95% CI {100 * low:.2f} to {100 * high:.2f}%"
        ),
        facts=[
            ("Icon-like coverage", f"{pct(icon['coverage'])} of {icon['candidates']:,}"),
            (
                "Screens with at least one unlabelled element",
                f"{pct(need['share_of_screens_with_debt'], 1)} of {h['screens']:,}",
            ),
            ("Elements counted (visible, with a size)", f"{h['n_included']:,}"),
        ],
    )


def headline_html(ac: str = "ac10") -> str:
    note = (
        "Intervals are 95% app-cluster bootstrap intervals from a11ydebt's published tables. "
        "The paper's sample is AndroidControl shards 00000 to 00009; all 20 shards are a "
        "robustness extension that is not in the paper."
    )
    return charts.headline_cards([_card("rico"), _card(ac)], note=note)


def _pair(rows_rico, rows_ac, ac: str) -> list[charts.Series]:
    def series(rows, corpus, css):
        return charts.Series(
            name=ex.CORPUS_LABELS[corpus],
            tag=ex.SHORT_LABELS[corpus],
            css=css,
            values=[share for _, _, share in rows],
            labels=[f"{100 * share:.1f}%" for _, _, share in rows],
            cells=[f"{n:,} screens ({100 * share:.1f}%)" for _, n, share in rows],
        )

    return [series(rows_rico, "rico", "s1"), series(rows_ac, ac, "s2")]


def _screens_note(population: str, ac: str, min_candidates: int) -> str:
    def n(corpus: str) -> int:
        return sum(
            count
            for _, count, _ in ex.coverage_distribution(STATS, corpus, population, min_candidates)
        )

    floor = max(1, int(min_candidates))
    what = "element" if floor == 1 else "elements"
    return (
        f"Share of screens with at least {floor} {what} in the measure: "
        f"Rico {n('rico'):,} screens, AndroidControl {n(ac):,}."
    )


def distribution_html(population: str, ac: str, min_candidates: int) -> tuple[str, str]:
    note = _screens_note(population, ac, min_candidates)
    cov = charts.bar_chart(
        title="How much of each screen is labelled?",
        caption=f"{ex.POPULATION_LABELS[population]}. {note}",
        categories=ex.COVERAGE_BINS,
        series=_pair(
            ex.coverage_distribution(STATS, "rico", population, min_candidates),
            ex.coverage_distribution(STATS, ac, population, min_candidates),
            ac,
        ),
        table_headers=["Coverage on the screen", "Rico", "AndroidControl"],
    )
    unl = charts.bar_chart(
        title="Unlabelled elements per screen",
        caption=f"{ex.POPULATION_LABELS[population]}. The same screens as above.",
        categories=[label for label, _, _ in ex.UNLABELLED_BINS],
        series=_pair(
            ex.unlabelled_distribution(STATS, "rico", population, min_candidates),
            ex.unlabelled_distribution(STATS, ac, population, min_candidates),
            ac,
        ),
        table_headers=["Unlabelled elements", "Rico", "AndroidControl"],
    )
    return cov, unl


def roles_html(ac: str) -> str:
    def series(corpus: str, css: str) -> charts.Series:
        counts = [published.ROLE_COUNTS[corpus][role] for role in published.ROLES]
        return charts.Series(
            name=ex.CORPUS_LABELS[corpus],
            tag=ex.SHORT_LABELS[corpus],
            css=css,
            values=[lab / cand for cand, lab in counts],
            labels=[f"{100 * lab / cand:.1f}%" for cand, lab in counts],
            cells=[f"{lab:,} of {cand:,} ({100 * lab / cand:.1f}%)" for cand, lab in counts],
        )

    return charts.bar_chart(
        title="Label coverage by element role",
        caption=(
            "Needs-label coverage per role, from the class name (the paper's Table 2). "
            "Containers and web views never need a label."
        ),
        categories=list(published.ROLES),
        series=[series("rico", "s1"), series(ac, "s2")],
        scale=1.0,
        table_headers=["Role", "Rico", "AndroidControl"],
    )


def top_table(dataset: str, population: str, ac: str, min_candidates: int):
    corpus = "rico" if dataset == "rico" else ac
    rows = ex.top_debt(STATS, corpus, population, min_candidates, n=25)
    frame = pd.DataFrame(rows, columns=ex.TOP_HEADERS[dataset])
    return frame, ex.LOOKUP[dataset]


def refresh(population: str, ac: str, min_candidates: int, dataset: str):
    cov, unl = distribution_html(population, ac, min_candidates)
    frame, lookup = top_table(dataset, population, ac, min_candidates)
    return headline_html(ac), cov, unl, roles_html(ac), frame, lookup


# ------------------------------------------------------------------ Audit


def _empty_tables():
    return (
        pd.DataFrame(columns=sa.MEASURE_HEADERS),
        pd.DataFrame(columns=sa.FLAGGED_HEADERS),
    )


def _report(data: bytes, source: str):
    try:
        audit = sa.audit_bytes(data)
    except sa.AuditError as exc:
        measures, flagged = _empty_tables()
        return f"**Could not audit {source}.** {exc}", measures, flagged
    summary = sa.summary_text(audit)
    measures = pd.DataFrame(sa.measure_rows(audit), columns=sa.MEASURE_HEADERS)
    flagged = pd.DataFrame(sa.flagged_rows(audit), columns=sa.FLAGGED_HEADERS)
    return summary, measures, flagged


def _forget(path: str) -> None:
    """Delete the temporary copy of an upload, and its folder if that is now empty.

    Gradio's File component (type="filepath") also leaves an empty placeholder file in the
    cache folder for every upload. Those hold no content; empty ones older than a minute are
    removed too, so the folder does not record when uploads happened. The age check keeps an
    upload that another visitor is still sending safe.
    """
    folder = os.path.dirname(path)
    for remove, target in ((os.remove, path), (os.rmdir, folder)):
        with contextlib.suppress(OSError):
            remove(target)
    cache = os.path.dirname(folder)
    cutoff = time.time() - 60
    try:
        with os.scandir(cache) as entries:
            for entry in entries:
                if not (entry.name.startswith("tmp") and entry.is_file(follow_symlinks=False)):
                    continue
                info = entry.stat(follow_symlinks=False)
                if info.st_size == 0 and info.st_mtime < cutoff:
                    os.remove(entry.path)
    except OSError:
        pass


def audit_upload(path: str | None):
    if not path:
        measures, flagged = _empty_tables()
        return "Upload a file, or try the example.", measures, flagged, None
    try:
        size = os.path.getsize(path)
        if size > sa.MAX_BYTES:
            measures, flagged = _empty_tables()
            return (
                f"**The file is larger than {sa.MAX_BYTES // 2**20} MB.**",
                measures,
                flagged,
                None,
            )
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError:
        measures, flagged = _empty_tables()
        return "**The upload could not be read.** Please upload it again.", measures, flagged, None
    finally:
        _forget(path)
    summary, measures, flagged = _report(data, "this file")
    del data
    return summary, measures, flagged, None


def audit_example(kind: str):
    data = EXAMPLES[kind].read_bytes()
    summary, measures, flagged = _report(data, "the example")
    name = "uiautomator XML" if kind == "xml" else "Rico JSON"
    return (
        f"*The example is an invented recipe screen ({name}).*\n\n{summary}",
        measures,
        flagged,
    )


# ------------------------------------------------------------------ About

ABOUT = f"""
## About

### What is accessibility debt?
A screen reader can only announce an image or an icon-only button if the app gave it a text
label, which on Android is a content description. Accessibility debt is the share of elements
that need such a label and have none, and the GUI corpora that train computer-use agents carry a
great deal of it.

### Links
- Code: [{REPO.removeprefix("https://")}]({REPO})
- Package: [pypi.org/project/a11ydebt]({PYPI}) (`pipx install a11ydebt`)
- Software DOI (all versions): [10.5281/zenodo.24121869]({DOI})
- The per-screen data behind the Explore tab: [obadakr/a11ydebt-stats]({DATASET})

### How to cite
Kraishan, O. and Jitkajornwanich, K. (2026). *Trained on What Screen Readers Cannot Read:
Accessibility Debt in the GUI Corpora Behind Computer-Use Agents.* IEEE AISSA 2026, to appear.

Kraishan, O. (2026). *a11ydebt: Audit Accessibility Debt in GUI-Agent Corpora.* Software.
[doi:10.5281/zenodo.24121869]({DOI})

### What the numbers mean
An element **needs a label** if it is an image, or an interactive element with no visible text,
and it is visible with a size; containers and web views are exempt. It is **icon-like** if it is
a tappable image or button with no text. **Coverage** is the share of those elements that have a
non-empty content description. Rico (Deka et al., 2017) is used under its research-use terms, so
only ids and counts are shown here; AndroidControl (Li et al., 2024) is Apache-2.0.

### Privacy
{PRIVACY}

### Limits
{LIMITS}
"""

INTRO = (
    "How many of the buttons and images in the screens that train phone-using AI agents can a "
    "screen reader name? Explore two corpora, or audit one screen of your own."
)
AUDIT_HELP = f"""
Upload **one** view hierarchy: a Rico JSON file, or the XML from Android's `uiautomator dump`
(Appium's page source works too), up to {sa.MAX_BYTES // 2**20} MB. To get one from a phone or
emulator with USB debugging on:

```
adb shell uiautomator dump /sdcard/window_dump.xml
adb pull /sdcard/window_dump.xml
```

{PRIVACY}
"""

APP_CSS = """
.gradio-container { max-width: min(1100px, 100vw) !important; margin: 0 auto; }
/* Flex items default to min-width: auto, so one wide table would widen the whole page on a
   phone. With min-width 0 the table scrolls inside its own frame instead. */
.gradio-container, .gradio-container .main, .gradio-container main.contain,
.gradio-container .tabs, .gradio-container .tabitem, .gradio-container .tab-container {
  min-width: 0 !important;
}
#ad-title h1 { margin-bottom: .25rem; }
#ad-intro p { color: var(--body-text-color-subdued); margin-top: 0; }
#ad-about { border-top: 1px solid var(--border-color-primary); margin-top: 1rem;
  padding-top: .5rem; }
.prose :not(pre) > code { white-space: pre-wrap; overflow-wrap: anywhere; }
.prose pre { overflow-x: auto; max-width: 100%; }
@media (max-width: 560px) {
  .tab-container button { padding: .35rem .5rem !important; font-size: .9rem !important; }
}
"""

THEME = gr.themes.Base(
    primary_hue=gr.themes.colors.blue,
    neutral_hue=gr.themes.colors.stone,
    font=("ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto", "sans-serif"),
    font_mono=("ui-monospace", "SFMono-Regular", "Menlo", "Consolas", "monospace"),
).set(
    body_background_fill="#f6f5f2",
    body_background_fill_dark="#121211",
    block_background_fill="#fcfcfb",
    block_background_fill_dark="#1a1a19",
)

POP_CHOICES = [(ex.POPULATION_LABELS[p], p) for p in ex.POPULATIONS]
AC_CHOICES = [("The paper's 10 shards", "ac10"), ("All 20 shards", "ac20")]

with gr.Blocks(
    title="a11ydebt: accessibility debt explorer", analytics_enabled=False, delete_cache=(300, 300)
) as demo:
    gr.Markdown("# a11ydebt", elem_id="ad-title")
    gr.Markdown(INTRO, elem_id="ad-intro")
    with gr.Tabs():
        with gr.Tab("Explore the debt"):
            headline = gr.HTML(headline_html("ac10"))
            with gr.Row(equal_height=False):
                population = gr.Radio(
                    POP_CHOICES, value="needs_label", label="Measure", min_width=260
                )
                ac = gr.Radio(
                    AC_CHOICES, value="ac10", label="AndroidControl sample", min_width=260
                )
                min_cand = gr.Slider(
                    1,
                    20,
                    value=1,
                    step=1,
                    min_width=260,
                    label="Only screens with at least this many elements in the measure",
                )
            first_cov, first_unl = distribution_html("needs_label", "ac10", 1)
            cov_chart = gr.HTML(first_cov)
            unl_chart = gr.HTML(first_unl)
            role_chart = gr.HTML(roles_html("ac10"))
            gr.Markdown(
                "### Highest-debt screens\nThe 25 screens with the most unlabelled elements in "
                "the measure, ties broken by lower coverage. Ids and counts only."
            )
            top_dataset = gr.Radio(
                [("Rico", "rico"), ("AndroidControl", "androidcontrol")],
                value="rico",
                label="Corpus",
            )
            first_top, first_lookup = top_table("rico", "needs_label", "ac10", 1)
            top = gr.Dataframe(first_top, interactive=False, wrap=False, max_height=520)
            lookup = gr.Markdown(first_lookup)
            gr.Markdown(
                'Label quality (for example a description that only says "button") needs the '
                "label text, which this data does not carry; the paper's reviewer checks cover "
                "it. " + LIMITS
            )

            inputs = [population, ac, min_cand, top_dataset]
            outputs = [headline, cov_chart, unl_chart, role_chart, top, lookup]
            # One documented endpoint; the other triggers run the same function privately.
            population.change(refresh, inputs, outputs, api_name="explore", show_progress="hidden")
            for control in (ac, top_dataset):
                control.change(
                    refresh, inputs, outputs, api_visibility="private", show_progress="hidden"
                )
            min_cand.release(
                refresh, inputs, outputs, api_visibility="private", show_progress="hidden"
            )

        with gr.Tab("Audit your own screen"):
            gr.Markdown(AUDIT_HELP)
            upload = gr.File(
                label="View hierarchy (.json or .xml)",
                file_types=[".json", ".xml"],
                type="filepath",
            )
            with gr.Row():
                ex_xml = gr.Button("Try the example (uiautomator XML)", variant="primary")
                ex_json = gr.Button("Try the example (Rico JSON)")
            summary = gr.Markdown()
            measures = gr.Dataframe(
                pd.DataFrame(columns=sa.MEASURE_HEADERS),
                interactive=False,
                wrap=True,
                label="The paper's two measures, for this screen",
                column_widths=["40%", "30%", "30%"],
            )
            flagged = gr.Dataframe(
                pd.DataFrame(columns=sa.FLAGGED_HEADERS),
                interactive=False,
                wrap=False,
                max_height=520,
                label="Elements that need a label and have none",
            )
            report = [summary, measures, flagged]
            upload.upload(audit_upload, upload, [*report, upload], api_name="audit")
            ex_xml.click(lambda: audit_example("xml"), None, report, api_name="example_xml")
            ex_json.click(lambda: audit_example("json"), None, report, api_name="example_json")

    gr.Markdown(ABOUT, elem_id="ad-about")


if __name__ == "__main__":
    demo.launch(
        theme=THEME,
        css=charts.CSS + APP_CSS,
        max_file_size=sa.MAX_BYTES,
        footer_links=["api", "gradio", "settings"],
        run_history=False,
        enable_monitoring=False,
    )
