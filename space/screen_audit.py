"""Audit one uploaded screen with the a11ydebt codebook: parse it, count it, describe it.

Pure functions, no Gradio, so the tests run without the app. Two formats are read:

* a **Rico view hierarchy** (JSON with ``activity.root``, or a bare root node), the format
  ``a11ydebt audit rico`` reads;
* an **Android ``uiautomator dump``** (XML, ``<hierarchy><node .../></hierarchy>``), also the
  Appium page-source variant whose tags are class names.

The XML is converted to the Rico shape and both go through ``a11ydebt.rico.parse_screen`` from
the released package, so an uploaded screen is counted by exactly the rules behind the paper.
Nothing here writes a file or logs content: the bytes come in, a report goes out.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, replace
from typing import Any

from a11ydebt.rico import RicoScreen, parse_screen

MAX_BYTES = 10 * 1024 * 1024
MAX_NODES = 100_000
POPULATIONS = ("needs_label", "icon_like")
FORMAT_NAMES = {
    "rico_json": "Rico view hierarchy (JSON)",
    "uiautomator_xml": "uiautomator dump (XML)",
}
#: The paper's corpus coverage, for comparison in the report (needs_label, icon_like).
CORPUS_COVERAGE = {
    "Rico (2017)": {"needs_label": 89_146 / 502_585, "icon_like": 42_341 / 127_552},
    "AndroidControl (2024)": {"needs_label": 837_536 / 1_462_544, "icon_like": 122_074 / 194_529},
}
SUPPORTED = (
    "Upload a Rico view-hierarchy JSON file or the XML from "
    "`adb shell uiautomator dump` (or Appium's page source)."
)

_BOUNDS = re.compile(r"\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]")
_TRUE = {"true", "1"}


class AuditError(ValueError):
    """A problem with the upload, worded for the person who uploaded it."""


@dataclass(frozen=True)
class FlaggedElement:
    """An element that needs a label and has none: one unit of accessibility debt."""

    order: int  # position in the traversal, 1-based, top of the tree first
    class_name: str
    role: str
    bounds: tuple[int, int, int, int]
    resource_id: str
    icon_like: bool

    @property
    def short_class(self) -> str:
        return self.class_name.rsplit(".", 1)[-1].split("$")[-1] or "(no class)"

    @property
    def bounds_text(self) -> str:
        x1, y1, x2, y2 = self.bounds
        return f"[{x1},{y1}][{x2},{y2}]"

    @property
    def size_text(self) -> str:
        x1, y1, x2, y2 = self.bounds
        return f"{x2 - x1} x {y2 - y1}"


@dataclass(frozen=True)
class ScreenAudit:
    fmt: str
    n_nodes: int
    n_included: int
    candidates: dict[str, int]
    labelled: dict[str, int]
    flagged: tuple[FlaggedElement, ...]

    def unlabelled(self, population: str) -> int:
        return self.candidates[population] - self.labelled[population]

    def coverage(self, population: str) -> float | None:
        cand = self.candidates[population]
        return self.labelled[population] / cand if cand else None


# ------------------------------------------------------------------ format detection


def _decode(data: bytes) -> str:
    return data.decode("utf-8", errors="replace").lstrip("﻿").lstrip()


def detect_format(data: bytes) -> str:
    """``rico_json`` or ``uiautomator_xml``, judged from the content, not the file name."""
    if not data or not data.strip():
        raise AuditError("The file is empty. " + SUPPORTED)
    head = _decode(data[:512])
    if head.startswith("{"):
        return "rico_json"
    if head.startswith("<"):
        return "uiautomator_xml"
    raise AuditError("This file is not a view hierarchy this tool can read. " + SUPPORTED)


# ------------------------------------------------------------------ parsing


def _bare_root(blob: dict[str, Any]) -> bool:
    return "class" in blob and ("bounds" in blob or "children" in blob)


def parse_rico_json(data: bytes) -> RicoScreen:
    try:
        blob = json.loads(_decode(data))
    except (ValueError, RecursionError) as exc:
        raise AuditError(
            "The JSON could not be read: it is malformed or too deeply nested."
        ) from exc
    if not isinstance(blob, dict):
        raise AuditError("The JSON is not a Rico view hierarchy. " + SUPPORTED)
    if "activity" not in blob and _bare_root(blob):
        blob = {"activity": {"root": blob}}
    try:
        return parse_screen(blob, "upload", app="")
    except (ValueError, TypeError, AttributeError) as exc:
        raise AuditError(
            "The JSON has no `activity.root` node, so it is not a Rico view hierarchy. " + SUPPORTED
        ) from exc


def _flag(attrs: dict[str, str], name: str, default: bool = False) -> bool:
    value = attrs.get(name)
    return default if value is None else value.strip().lower() in _TRUE


def _xml_node(elem: ET.Element) -> dict[str, Any]:
    """One uiautomator node in the Rico JSON shape that ``parse_screen`` reads."""
    attrs = elem.attrib
    match = _BOUNDS.fullmatch(attrs.get("bounds", "").replace(" ", ""))
    bounds = [int(v) for v in match.groups()] if match else [0, 0, 0, 0]
    class_name = attrs.get("class") or ("" if elem.tag == "node" else elem.tag)
    # The AOSP dumper writes only nodes that are visible to the user; Appium marks them.
    visible = _flag(attrs, "visible-to-user", _flag(attrs, "displayed", True))
    return {
        "class": class_name,
        "text": attrs.get("text", ""),
        "content-desc": [attrs.get("content-desc") or None],
        "resource-id": attrs.get("resource-id", ""),
        "clickable": _flag(attrs, "clickable"),
        "long-clickable": _flag(attrs, "long-clickable"),
        "focusable": _flag(attrs, "focusable"),
        "enabled": _flag(attrs, "enabled", True),
        "visible-to-user": visible,
        "bounds": bounds,
        "children": [],
    }


def uiautomator_to_rico(data: bytes) -> tuple[dict[str, Any], bool]:
    """Convert a uiautomator (or Appium) XML dump to a Rico screen blob.

    Returns the blob and whether a synthetic root was added (a dump with several top-level
    windows); that root is dropped again after parsing so it is never counted.
    """
    head = data[:4096].lower()
    if b"<!doctype" in head or b"<!entity" in data.lower():
        raise AuditError("XML with a DOCTYPE or entities is not accepted. " + SUPPORTED)
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise AuditError("The XML could not be read: it is malformed.") from exc

    tops: list[dict[str, Any]] = []
    count = 0
    # Iterative walk, so a deeply nested dump cannot exhaust the stack.
    stack: list[tuple[ET.Element, list[dict[str, Any]]]] = [
        (child, tops) for child in reversed(list(root))
    ]
    if root.tag != "hierarchy":
        stack = [(root, tops)]
    while stack:
        elem, siblings = stack.pop()
        if "bounds" in elem.attrib:
            node = _xml_node(elem)
            siblings.append(node)
            count += 1
            if count > MAX_NODES:
                raise AuditError(f"The dump has more than {MAX_NODES:,} nodes.")
            target = node["children"]
        else:
            target = siblings  # a wrapper element: its children belong to the parent
        stack.extend((child, target) for child in reversed(list(elem)))

    if not tops:
        raise AuditError(
            "The XML has no `<node>` elements with `bounds`, so it is not a uiautomator dump. "
            + SUPPORTED
        )
    if len(tops) == 1:
        return {"activity_name": "", "activity": {"root": tops[0]}}, False
    synthetic = {
        "class": "",
        "visible-to-user": False,
        "bounds": [0, 0, 0, 0],
        "content-desc": [None],
        "children": tops,
    }
    return {"activity_name": "", "activity": {"root": synthetic}}, True


def parse_upload(data: bytes) -> tuple[RicoScreen, str]:
    """Parse an upload into a screen, with the codebook applied. Raises AuditError."""
    if len(data) > MAX_BYTES:
        raise AuditError(f"The file is larger than {MAX_BYTES // (1024 * 1024)} MB.")
    fmt = detect_format(data)
    if fmt == "rico_json":
        screen = parse_rico_json(data)
    else:
        blob, synthetic = uiautomator_to_rico(data)
        screen = parse_screen(blob, "upload", app="")
        if synthetic:
            screen = replace(screen, nodes=screen.nodes[1:])
    if len(screen.nodes) > MAX_NODES:
        raise AuditError(f"The screen has more than {MAX_NODES:,} nodes.")
    return screen, fmt


# ------------------------------------------------------------------ scoring


def score(screen: RicoScreen, fmt: str) -> ScreenAudit:
    """The paper's measures for one screen, over included nodes (visible, positive area)."""
    candidates = dict.fromkeys(POPULATIONS, 0)
    labelled = dict.fromkeys(POPULATIONS, 0)
    flagged: list[FlaggedElement] = []
    n_included = 0
    for order, node in enumerate(screen.nodes, start=1):
        if not node.included:
            continue
        n_included += 1
        for population in POPULATIONS:
            if getattr(node, population):
                candidates[population] += 1
                labelled[population] += int(node.labelled)
        if node.flagged("needs_label"):
            flagged.append(
                FlaggedElement(
                    order=order,
                    class_name=node.class_name,
                    role=node.role,
                    bounds=node.bounds,
                    resource_id=node.resource_id,
                    icon_like=node.icon_like,
                )
            )
    return ScreenAudit(
        fmt=fmt,
        n_nodes=len(screen.nodes),
        n_included=n_included,
        candidates=candidates,
        labelled=labelled,
        flagged=tuple(flagged),
    )


def audit_bytes(data: bytes) -> ScreenAudit:
    screen, fmt = parse_upload(data)
    return score(screen, fmt)


# ------------------------------------------------------------------ report


def pct(value: float | None, digits: int = 1) -> str:
    return "n/a" if value is None else f"{100 * value:.{digits}f}%"


def _plural(n: int, one: str, many: str | None = None) -> str:
    return f"{n:,} {one if n == 1 else (many or one + 's')}"


def summary_text(audit: ScreenAudit) -> str:
    """A short plain-language summary, in Markdown."""
    need = audit.candidates["needs_label"]
    icon = audit.candidates["icon_like"]
    lines = [
        f"**Read as:** {FORMAT_NAMES[audit.fmt]}. "
        f"{_plural(audit.n_nodes, 'element')} in the file, "
        f"{audit.n_included:,} of them visible and with a size (the ones the paper counts)."
    ]
    if need == 0:
        lines.append(
            "Nothing on this screen needs a content description under the paper's rules, so "
            "coverage is not defined here. That is not the same as the screen being accessible."
        )
        return "\n\n".join(lines)
    missing = audit.unlabelled("needs_label")
    rico = CORPUS_COVERAGE["Rico (2017)"]["needs_label"]
    ac = CORPUS_COVERAGE["AndroidControl (2024)"]["needs_label"]
    verb = "needs" if need == 1 else "need"
    lines.append(
        f"**{_plural(need, 'element')} {verb} a label** for a screen reader (images, and controls "
        f"with no visible text). {audit.labelled['needs_label']:,} "
        f"{'has' if audit.labelled['needs_label'] == 1 else 'have'} a content description, "
        f"so **label coverage is {pct(audit.coverage('needs_label'))}** "
        f"(the paper's corpora: Rico {pct(rico, 2)}, AndroidControl {pct(ac, 2)})."
    )
    if missing:
        lines.append(
            f"{_plural(missing, 'element')} {'has' if missing == 1 else 'have'} no name. "
            'A screen reader such as TalkBack announces a control like that as just "Unlabelled, '
            'button", or skips an image entirely. They are listed below by class and bounds.'
        )
    else:
        lines.append("Every element that needs a label has one.")
    if icon:
        lines.append(
            f"Of the {_plural(icon, 'icon-like element')} (a tappable image or button with no "
            f"text), {audit.labelled['icon_like']:,} "
            f"{'is' if audit.labelled['icon_like'] == 1 else 'are'} labelled: "
            f"**{pct(audit.coverage('icon_like'))}**."
        )
    return "\n\n".join(lines)


#: Columns are the paper's two measures; rows are the counts. Three columns fit on a phone.
MEASURE_HEADERS = ["Elements", "Needs a label", "Icon-like"]


def measure_rows(audit: ScreenAudit) -> list[list[object]]:
    return [
        ["In the measure", *(audit.candidates[p] for p in POPULATIONS)],
        ["Labelled", *(audit.labelled[p] for p in POPULATIONS)],
        ["Unlabelled", *(audit.unlabelled(p) for p in POPULATIONS)],
        ["Coverage", *(pct(audit.coverage(p)) for p in POPULATIONS)],
    ]


FLAGGED_HEADERS = ["#", "Class", "Bounds", "Size", "Role", "View id", "Icon-like"]


def flagged_rows(audit: ScreenAudit) -> list[list[object]]:
    """The unlabelled elements by class and bounds. No text is shown: these elements have no
    content description and, by the codebook, no visible text. The view id comes from the
    uploaded file itself."""
    return [
        [
            el.order,
            el.short_class,
            el.bounds_text,
            el.size_text,
            el.role,
            el.resource_id.split(":id/", 1)[-1] if el.resource_id else "",
            "yes" if el.icon_like else "",
        ]
        for el in audit.flagged
    ]
