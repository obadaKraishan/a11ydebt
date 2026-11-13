"""The Space's single-screen audit: parsing both formats, scoring, limits and the report text.

The examples in space/examples/ are invented screens; the Rico fixtures are synthetic.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from a11ydebt.counts import count_screen
from a11ydebt.rico import load_screen

sa = pytest.importorskip("screen_audit")

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "space" / "examples"
FIXTURES = sorted((ROOT / "tests" / "fixtures" / "rico" / "combined").glob("*.json"))


def node(cls: str, bounds: str, **attrs: str) -> str:
    extra = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    return f'<node class="{cls}" bounds="{bounds}" {extra}/>'


def dump(*children: str, root: str = "android.widget.FrameLayout") -> bytes:
    inner = "".join(children)
    xml = (
        "<?xml version='1.0' encoding='UTF-8' standalone='yes' ?><hierarchy rotation=\"0\">"
        f'<node class="{root}" bounds="[0,0][1080,2000]">{inner}</node></hierarchy>'
    )
    return xml.encode()


def test_examples_agree_across_formats():
    xml = sa.audit_bytes((EXAMPLES / "recipe_screen.xml").read_bytes())
    rico = sa.audit_bytes((EXAMPLES / "recipe_screen.json").read_bytes())
    assert (xml.fmt, rico.fmt) == ("uiautomator_xml", "rico_json")
    for audit in (xml, rico):
        assert (audit.n_nodes, audit.n_included) == (17, 16)
        assert audit.candidates == {"needs_label": 8, "icon_like": 6}
        assert audit.labelled == {"needs_label": 2, "icon_like": 2}
    assert sa.flagged_rows(xml) == sa.flagged_rows(rico)
    assert [row[1] for row in sa.flagged_rows(xml)] == [
        "ImageButton",
        "AppCompatImageView",
        "ImageView",
        "ImageButton",
        "CheckBox",
        "FloatingActionButton",
    ]


def test_example_report_shows_no_element_text():
    audit = sa.audit_bytes((EXAMPLES / "recipe_screen.xml").read_bytes())
    shown = json.dumps([sa.flagged_rows(audit), sa.measure_rows(audit), sa.summary_text(audit)])
    for text in ("Lentil soup", "Serves 4", "Start cooking", "Search", "favourites", "ingredients"):
        assert text not in shown


@pytest.mark.parametrize("path", FIXTURES, ids=lambda p: p.name)
def test_rico_upload_counts_like_the_package(path):
    """The upload path gives the same numbers as the package's own loader and counter."""
    audit = sa.audit_bytes(path.read_bytes())
    counts = count_screen(load_screen(path))
    assert audit.n_nodes == counts.n_nodes
    assert audit.n_included == counts.n_included
    for pop in sa.POPULATIONS:
        assert audit.candidates[pop] == counts.candidates[pop]
        assert audit.labelled[pop] == counts.labelled[pop]


def test_bare_root_json_is_read():
    root = {
        "class": "android.widget.ImageButton",
        "bounds": [0, 0, 100, 100],
        "clickable": True,
        "visible-to-user": True,
    }
    audit = sa.audit_bytes(json.dumps(root).encode())
    assert audit.candidates["needs_label"] == 1 and audit.labelled["needs_label"] == 0


def test_appium_page_source_and_visibility():
    xml = (
        b"<hierarchy>"
        b'<android.widget.FrameLayout class="android.widget.FrameLayout" bounds="[0,0][100,100]">'
        b'<android.widget.ImageView class="android.widget.ImageView" bounds="[0,0][50,50]" '
        b'displayed="true" content-desc="Logo"/>'
        b'<android.widget.ImageView class="android.widget.ImageView" bounds="[50,0][100,50]" '
        b'displayed="false"/>'
        b'<android.widget.ImageButton bounds="[0,50][50,100]" clickable="true" '
        b'visible-to-user="true"/>'
        b"</android.widget.FrameLayout></hierarchy>"
    )
    audit = sa.audit_bytes(xml)
    assert audit.n_nodes == 4 and audit.n_included == 3  # displayed="false" is not counted
    assert audit.candidates["needs_label"] == 2 and audit.labelled["needs_label"] == 1
    # The button has no class attribute, so its tag supplies the class.
    assert [row[1] for row in sa.flagged_rows(audit)] == ["ImageButton"]


def test_several_windows_get_no_extra_node():
    xml = (
        "<hierarchy>"
        + node("android.widget.ImageView", "[0,0][10,10]")
        + node("android.widget.ImageButton", "[0,10][10,20]", clickable="true")
        + "</hierarchy>"
    ).encode()
    audit = sa.audit_bytes(xml)
    assert audit.n_nodes == 2 and audit.n_included == 2
    assert audit.candidates == {"needs_label": 2, "icon_like": 1}


def test_zero_area_and_bad_bounds_are_not_counted():
    audit = sa.audit_bytes(
        dump(
            node("android.widget.ImageView", "[0,0][0,10]"),
            node("android.widget.ImageView", "not bounds"),
            node("android.widget.ImageView", "[0,0][10,10]"),
        )
    )
    assert audit.n_nodes == 4 and audit.n_included == 2  # the root and one image
    assert audit.candidates["needs_label"] == 1


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (b"", "empty"),
        (b"   \n", "empty"),
        (b"PK\x03\x04binary", "not a view hierarchy"),
        (b"{not json", "malformed"),
        (b"[1, 2]", "not a view hierarchy"),
        (b'{"screens": [1, 2]}', "activity.root"),
        (b'{"activity": {}}', "activity.root"),
        (b"<hierarchy><node", "malformed"),
        (b"<html><body>hi</body></html>", "not a uiautomator dump"),
        (b'<!DOCTYPE x [<!ENTITY a "aaaa">]><hierarchy/>', "DOCTYPE"),
        (b"[" * 100_000 + b"]" * 100_000, "not a view hierarchy"),
        (b"{" + b'"a":{' * 50_000 + b"}" * 50_001, "malformed"),
    ],
)
def test_unreadable_uploads_get_a_clear_error(data, message):
    with pytest.raises(sa.AuditError, match=message):
        sa.audit_bytes(data)


def test_size_cap():
    with pytest.raises(sa.AuditError, match="larger than"):
        sa.audit_bytes(b"{" + b" " * sa.MAX_BYTES + b"}")


def test_node_cap(monkeypatch):
    monkeypatch.setattr(sa, "MAX_NODES", 3)
    many = dump(*(node("android.widget.TextView", "[0,0][1,1]") for _ in range(5)))
    with pytest.raises(sa.AuditError, match="more than 3 nodes"):
        sa.audit_bytes(many)


def test_byte_order_mark_and_leading_space():
    data = b"\xef\xbb\xbf  \n" + (EXAMPLES / "recipe_screen.json").read_bytes()
    assert sa.audit_bytes(data).candidates["needs_label"] == 8


def test_summary_when_nothing_needs_a_label():
    audit = sa.audit_bytes(dump(node("android.widget.TextView", "[0,0][10,10]", text="Hello")))
    text = sa.summary_text(audit)
    assert (
        "coverage is not defined" in text and "not the same as the screen being accessible" in text
    )
    assert sa.measure_rows(audit)[-1] == ["Coverage", "n/a", "n/a"]


def test_summary_singular_and_all_labelled():
    one = sa.audit_bytes(
        dump(
            node(
                "android.widget.ImageButton", "[0,0][10,10]", clickable="true", content_desc="Back"
            )
        )
    )
    text = sa.summary_text(one)
    assert "**1 element needs a label**" in text and "1 has a content description" in text
    assert "Every element that needs a label has one." in text
    assert "label coverage is 100.0%" in text
    assert "Of the 1 icon-like element" in text and "1 is labelled" in text


def test_summary_compares_with_the_corpora():
    audit = sa.audit_bytes((EXAMPLES / "recipe_screen.xml").read_bytes())
    text = sa.summary_text(audit)
    assert "label coverage is 25.0%" in text
    assert "Rico 17.74%" in text and "AndroidControl 57.27%" in text
    assert "6 elements have no name" in text and "**33.3%**" in text


def test_measure_rows():
    audit = sa.audit_bytes((EXAMPLES / "recipe_screen.json").read_bytes())
    assert sa.measure_rows(audit) == [
        ["In the measure", 8, 6],
        ["Labelled", 2, 2],
        ["Unlabelled", 6, 4],
        ["Coverage", "25.0%", "33.3%"],
    ]
    assert len(sa.MEASURE_HEADERS) == 3


def test_flagged_rows_are_class_bounds_and_ids():
    audit = sa.audit_bytes((EXAMPLES / "recipe_screen.xml").read_bytes())
    first = sa.flagged_rows(audit)[0]
    assert dict(zip(sa.FLAGGED_HEADERS, first, strict=True)) == {
        "#": 4,
        "Class": "ImageButton",
        "Bounds": "[0,63][147,210]",
        "Size": "147 x 147",
        "Role": "button",
        "View id": "nav_back",
        "Icon-like": "yes",
    }
