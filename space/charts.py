"""HTML for the explorer: headline cards and paired horizontal bar charts.

Plain HTML and CSS, no script, so the charts follow the app's light or dark theme, work on a
phone, and read in a screen reader. Each chart has a legend, a direct series label on its first
row, a tooltip on every bar, and its numbers as a table. Series colours are categorical slots 1
(blue) and 2 (orange), validated for colour-vision deficiency on both surfaces. All text here is
the app's own; nothing comes from a corpus.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from html import escape

CSS = """
.ad-root {
  --ad-s1: #2a78d6; --ad-s2: #eb6834;
  --ad-surface: #fcfcfb; --ad-grid: #e4e2dc; --ad-track: #f0efec;
  color: var(--body-text-color);
}
.dark .ad-root {
  --ad-s1: #3987e5; --ad-s2: #d95926;
  --ad-surface: #1a1a19; --ad-grid: #3a3a37; --ad-track: #262624;
}
.ad-root .s1 { background: var(--ad-s1); }
.ad-root .s2 { background: var(--ad-s2); }
.ad-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
  gap: .75rem; }
.ad-card { background: var(--ad-surface); border: 1px solid var(--ad-grid); border-radius: 12px;
  padding: 1rem 1.1rem; }
.ad-card h3 { margin: 0 0 .35rem; font-size: 1rem; font-weight: 600; display: flex;
  align-items: center; gap: .5rem; }
.ad-big { font-size: 2.4rem; line-height: 1.1; font-weight: 700; margin: .1rem 0 0;
  font-variant-numeric: tabular-nums; }
.ad-cap { margin: .1rem 0 .4rem; color: var(--body-text-color-subdued); font-size: .9rem; }
.ad-meta { margin: 0 0 .6rem; font-size: .85rem; color: var(--body-text-color-subdued);
  font-variant-numeric: tabular-nums; }
.ad-facts { margin: 0; display: grid; gap: .35rem; }
.ad-facts div { display: flex; justify-content: space-between; gap: .75rem;
  border-top: 1px solid var(--ad-grid); padding-top: .35rem; }
.ad-facts dt { font-size: .85rem; color: var(--body-text-color-subdued); }
.ad-facts dd { margin: 0; font-weight: 600; font-variant-numeric: tabular-nums; text-align: right;
  white-space: nowrap; }
.ad-note { font-size: .85rem; color: var(--body-text-color-subdued); margin: .6rem 0 0; }
.ad-swatch { display: inline-block; width: .8rem; height: .8rem; border-radius: 3px; flex: none; }
.ad-chart { margin: 0; background: var(--ad-surface); border: 1px solid var(--ad-grid);
  border-radius: 12px; padding: 1rem 1.1rem; }
.ad-chart figcaption { margin-bottom: .5rem; }
.ad-chart figcaption strong { display: block; font-size: 1rem; }
.ad-chart figcaption span { font-size: .85rem; color: var(--body-text-color-subdued); }
.ad-legend { display: flex; flex-wrap: wrap; gap: .4rem 1rem; margin: 0 0 .5rem; padding: 0;
  list-style: none; font-size: .85rem; }
.ad-legend li { display: flex; align-items: center; gap: .4rem; }
.ad-row { display: grid; grid-template-columns: minmax(5.25rem, 7.5rem) 1fr; gap: .75rem;
  align-items: center; padding: .3rem 0; border-top: 1px solid var(--ad-grid); }
.ad-cat { font-size: .85rem; font-variant-numeric: tabular-nums; }
.ad-bars { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.ad-line { display: flex; align-items: center; gap: .4rem; min-height: 16px; }
.ad-bar { display: block; height: 10px; border-radius: 0 4px 4px 0; flex: none; }
.ad-val { font-size: .8rem; color: var(--body-text-color-subdued);
  font-variant-numeric: tabular-nums; white-space: nowrap; }
.ad-table { margin-top: .6rem; font-size: .85rem; }
.ad-table summary { cursor: pointer; color: var(--body-text-color-subdued); }
.ad-table table { width: 100%; border-collapse: collapse; margin-top: .4rem; }
.ad-table th, .ad-table td { text-align: right; padding: .2rem .4rem;
  border-bottom: 1px solid var(--ad-grid); font-variant-numeric: tabular-nums; }
.ad-table th:first-child, .ad-table td:first-child { text-align: left; }
@media (forced-colors: active) {
  .ad-bar { forced-color-adjust: none; border: 1px solid CanvasText; }
}
"""


@dataclass(frozen=True)
class Series:
    name: str  # shown in the legend and the table header
    tag: str  # the short direct label on the first row
    css: str  # "s1" or "s2"
    values: Sequence[float]  # bar lengths, in the chart's scale
    labels: Sequence[str]  # the text at the end of each bar
    cells: Sequence[str]  # the table cell (and tooltip) for each category


def _width(value: float, scale: float) -> str:
    frac = 0.0 if scale <= 0 else max(0.0, min(1.0, value / scale))
    # The value label takes up to about 7rem; the bar uses the rest of the line.
    return f"calc((100% - 7.5rem) * {frac:.4f})"


def bar_chart(
    title: str,
    caption: str,
    categories: Sequence[str],
    series: Sequence[Series],
    scale: float | None = None,
    table_headers: Sequence[str] | None = None,
) -> str:
    """Paired horizontal bars, one row per category, one bar per series."""
    top = scale if scale is not None else max((v for s in series for v in s.values), default=0)
    out = [
        '<figure class="ad-root ad-chart">',
        f"<figcaption><strong>{escape(title)}</strong><span>{escape(caption)}</span></figcaption>",
        '<ul class="ad-legend" aria-label="Legend">',
        *(
            f'<li><span class="ad-swatch {s.css}" aria-hidden="true"></span>{escape(s.name)}</li>'
            for s in series
        ),
        "</ul>",
    ]
    for i, category in enumerate(categories):
        out.append(f'<div class="ad-row"><div class="ad-cat">{escape(category)}</div>')
        out.append('<div class="ad-bars">')
        for s in series:
            value = s.values[i]
            label = f"{s.tag}: {s.labels[i]}" if i == 0 else s.labels[i]
            min_width = "2px" if value > 0 else "0"
            out.append(
                f'<div class="ad-line" title="{escape(f"{s.name}, {category}: {s.cells[i]}")}">'
                f'<span class="ad-bar {s.css}" aria-hidden="true" '
                f'style="width:{_width(value, top)};min-width:{min_width}"></span>'
                f'<span class="ad-val">{escape(label)}</span></div>'
            )
        out.append("</div></div>")
    headers = table_headers or ["", *(s.name for s in series)]
    out.append('<details class="ad-table"><summary>Show the numbers as a table</summary><table>')
    out.append("<thead><tr>" + "".join(f"<th>{escape(h)}</th>" for h in headers) + "</tr></thead>")
    out.append("<tbody>")
    for i, category in enumerate(categories):
        cells = "".join(f"<td>{escape(s.cells[i])}</td>" for s in series)
        out.append(f"<tr><td>{escape(category)}</td>{cells}</tr>")
    out.append("</tbody></table></details></figure>")
    return "\n".join(out)


@dataclass(frozen=True)
class Card:
    title: str
    css: str
    big: str
    big_caption: str
    meta: str
    facts: Sequence[tuple[str, str]]


def headline_cards(cards: Sequence[Card], note: str = "") -> str:
    out = ['<div class="ad-root">', '<div class="ad-cards">']
    for card in cards:
        out.append(f'<section class="ad-card" aria-label="{escape(card.title)}">')
        out.append(
            f'<h3><span class="ad-swatch {card.css}" aria-hidden="true"></span>'
            f"{escape(card.title)}</h3>"
        )
        out.append(f'<p class="ad-big">{escape(card.big)}</p>')
        out.append(f'<p class="ad-cap">{escape(card.big_caption)}</p>')
        out.append(f'<p class="ad-meta">{escape(card.meta)}</p>')
        out.append('<dl class="ad-facts">')
        for term, value in card.facts:
            out.append(f"<div><dt>{escape(term)}</dt><dd>{escape(value)}</dd></div>")
        out.append("</dl></section>")
    out.append("</div>")
    if note:
        out.append(f'<p class="ad-note">{escape(note)}</p>')
    out.append("</div>")
    return "\n".join(out)
