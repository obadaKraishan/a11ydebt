"""Rico view-hierarchy loader.

Reads the extracted Rico "UI Screenshots and View Hierarchies" release (``unique_uis.tar.gz``):
one ``<ui_number>.json`` per screen, usually under ``combined/``, plus ``ui_details.csv``, which
maps UI numbers to app packages. Each screen's tree is walked depth-first in the same order as
the AISSA parser (pre-order, children left to right), and every node gets the codebook flags
from :mod:`a11ydebt.taxonomy`.

Schema facts this relies on (verified against the full archive by the AISSA pipeline):

* The root is ``blob["activity"]["root"]``.
* ``children`` is absent on leaves, and a few child lists contain ``null``; those are skipped.
* ``content-desc`` is a list of length one, ``[None]`` when absent.
* ``bounds`` is ``[x1, y1, x2, y2]`` in absolute pixels; malformed bounds count as zero area.
* ``pointer`` is not unique, so node ids (``node_uid``) are assigned by traversal order.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from a11ydebt import taxonomy as tx
from a11ydebt.counts import POPULATIONS

__all__ = [
    "POPULATIONS",
    "RicoNode",
    "RicoScreen",
    "find_screen_files",
    "iter_screens",
    "load_screen",
    "parse_screen",
    "read_ui_details",
]


@dataclass(frozen=True, slots=True)
class RicoNode:
    """One view-hierarchy node with the codebook applied."""

    node_uid: int
    parent_uid: int
    depth: int
    class_name: str
    resource_id: str
    content_desc: str  # cleaned: "" when absent, [None], "null" or whitespace
    text: str  # cleaned the same way
    clickable: bool
    long_clickable: bool
    focusable: bool
    enabled: bool
    visible_to_user: bool
    bounds: tuple[int, int, int, int]
    role: str
    included: bool
    needs_label: bool
    icon_like: bool
    interactive_image: bool

    @property
    def labelled(self) -> bool:
        """The developer supplied a content description."""
        return bool(self.content_desc)

    def in_population(self, population: str) -> bool:
        if population not in POPULATIONS:
            raise ValueError(f"unknown population {population!r}; choose from {POPULATIONS}")
        return self.included and bool(getattr(self, population))

    def flagged(self, population: str = "needs_label") -> bool:
        """In the population and missing a content description: one unit of accessibility debt."""
        return self.in_population(population) and not self.labelled


@dataclass(frozen=True, slots=True)
class RicoScreen:
    """One Rico screen: its app, its root size and its flattened nodes in traversal order."""

    screen_id: str
    app: str
    activity_name: str
    width: int
    height: int
    nodes: tuple[RicoNode, ...]

    def flagged(self, population: str = "needs_label") -> list[RicoNode]:
        return [node for node in self.nodes if node.flagged(population)]


def _bounds(node: Mapping[str, Any]) -> tuple[int, int, int, int]:
    b = node.get("bounds") or [0, 0, 0, 0]
    try:
        return int(b[0]), int(b[1]), int(b[2]), int(b[3])
    except (TypeError, ValueError, IndexError):
        return 0, 0, 0, 0


def _make_node(node: Mapping[str, Any], uid: int, parent: int, depth: int) -> RicoNode:
    class_name = str(node.get("class") or "")
    text = tx.clean_text(str(node.get("text") or ""))
    clickable = bool(node.get("clickable"))
    long_clickable = bool(node.get("long-clickable"))
    focusable = bool(node.get("focusable"))
    enabled = bool(node.get("enabled"))
    visible = bool(node.get("visible-to-user"))
    x1, y1, x2, y2 = _bounds(node)
    role = tx.classify_role(class_name)
    return RicoNode(
        node_uid=uid,
        parent_uid=parent,
        depth=depth,
        class_name=class_name,
        resource_id=str(node.get("resource-id") or ""),
        content_desc=tx.clean_text(node.get("content-desc")),
        text=text,
        clickable=clickable,
        long_clickable=long_clickable,
        focusable=focusable,
        enabled=enabled,
        visible_to_user=visible,
        bounds=(x1, y1, x2, y2),
        role=role,
        included=tx.in_analysis_population(visible, x1, y1, x2, y2, enabled),
        needs_label=tx.needs_label(role, clickable, long_clickable, text),
        icon_like=tx.is_icon_like(role, text, clickable, long_clickable),
        interactive_image=tx.is_interactive_image(class_name, clickable, focusable),
    )


def parse_screen(blob: Mapping[str, Any], screen_id: str, app: str | None = None) -> RicoScreen:
    """Flatten one Rico screen. ``app`` defaults to the package in ``activity_name``."""
    activity = blob.get("activity")
    root = activity.get("root") if isinstance(activity, Mapping) else None
    if not isinstance(root, Mapping):
        raise ValueError(f"screen {screen_id}: no activity.root")
    activity_name = str(blob.get("activity_name") or "")
    if app is None:
        app = activity_name.split("/", 1)[0]
    rx1, ry1, rx2, ry2 = _bounds(root)

    nodes: list[RicoNode] = []
    stack: list[tuple[Mapping[str, Any], int, int]] = [(root, -1, 0)]
    while stack:
        node, parent, depth = stack.pop()
        uid = len(nodes)
        nodes.append(_make_node(node, uid, parent, depth))
        children = node.get("children") or []
        for child in reversed(children):
            if isinstance(child, Mapping):
                stack.append((child, uid, depth + 1))

    return RicoScreen(
        screen_id=screen_id,
        app=app,
        activity_name=activity_name,
        width=max(1, rx2 - rx1),
        height=max(1, ry2 - ry1),
        nodes=tuple(nodes),
    )


def load_screen(path: str | Path, app: str | None = None) -> RicoScreen:
    """Read and flatten one ``<ui_number>.json`` file."""
    path = Path(path)
    blob = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    return parse_screen(blob, path.stem, app)


def read_ui_details(path: str | Path) -> dict[str, str]:
    """Map Rico UI number -> app package from ``ui_details.csv``."""
    mapping: dict[str, str] = {}
    with Path(path).open(encoding="utf-8", errors="replace", newline="") as fh:
        for row in csv.DictReader(fh):
            uid = (row.get("UI Number") or "").strip()
            if uid:
                mapping[uid] = (row.get("App Package Name") or "").strip()
    return mapping


def _numeric_key(path: Path) -> tuple[int, int | str]:
    return (0, int(path.stem)) if path.stem.isdigit() else (1, path.stem)


def find_screen_files(rico_dir: str | Path) -> list[Path]:
    """Screen JSON files in ``rico_dir/combined/`` (or ``rico_dir`` itself), in numeric order."""
    root = Path(rico_dir)
    folder = root / "combined" if (root / "combined").is_dir() else root
    files = [p for p in folder.glob("*.json") if not p.name.startswith("._")]
    return sorted(files, key=_numeric_key)


def iter_screens(rico_dir: str | Path, limit: int | None = None) -> Iterator[RicoScreen]:
    """Yield parsed screens. Apps come from ``ui_details.csv`` when it is present."""
    root = Path(rico_dir)
    details = root / "ui_details.csv"
    apps = read_ui_details(details) if details.is_file() else {}
    files = find_screen_files(root)
    for path in files[:limit] if limit else files:
        yield load_screen(path, apps.get(path.stem))
