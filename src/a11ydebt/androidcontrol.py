"""AndroidControl loader: TFRecord shards to episodes, one screen per step, flags per node.

Ports the parse logic of ``phase2_processing/02_parse_androidcontrol.py`` and
``src/a11ydebt/apps.py`` from accessibility-debt-agents (commit 97c0378, MIT; see NOTICE), and
keeps the rules that decide the counts unchanged:

* A screen is one step of an episode, ``f"{episode_id}_{step_index}"``. Its nodes are every node
  of every window in that step's AndroidAccessibilityForest, windows in forest order.
* A forest that fails to decode becomes an empty screen, and an episode that fails to decode is
  recorded as a failure and left out. A truncated shard yields every record it could read and
  sets ``ShardReader.truncated``.
* The codebook is ``a11ydebt.taxonomy``, applied exactly as for Rico. Roles come from the class name
  only, ``labelled`` means a non-empty content description, and ``included`` means visible to the
  user with positive area. The P01 ``interactive_image`` flag uses ``is_focusable``.
* An episode's app is the most frequent package among its nodes' resource ids
  (``<package>:id/<name>``), ignoring platform packages, with ties broken alphabetically. An
  episode with no usable resource id gets app "".

Standard library only, so the Kaggle kernel can bundle it.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from a11ydebt import taxonomy as tx
from a11ydebt.counts import POPULATIONS
from a11ydebt.tfrecord import TruncatedShardError, iter_records, parse_example, parse_forest

__all__ = [
    "SYSTEM_PACKAGES",
    "AcEpisode",
    "AcNode",
    "AcScreen",
    "ShardReader",
    "episode_app",
    "load_splits",
    "parse_episode",
]

#: Platform packages that appear on every device; never an episode's app (AISSA config.yaml).
SYSTEM_PACKAGES: frozenset[str] = frozenset(
    {
        "android",
        "com.android.systemui",
        "com.android.launcher3",
        "com.android.intentresolver",
        "com.android.permissioncontroller",
        "com.android.packageinstaller",
        "com.android.printspooler",
        "com.android.bips",
        "com.android.htmlviewer",
        "com.google.android.inputmethod.latin",
        "com.google.android.apps.nexuslauncher",
        "com.google.android.permissioncontroller",
        "com.google.android.packageinstaller",
        "com.google.android.gms",
        "com.google.android.ext.services",
        "com.google.android.settings.intelligence",
        "com.google.android.tts",
    }
)
_PACKAGE = re.compile(r"^([A-Za-z0-9_.]+):id/")


@dataclass(frozen=True, slots=True)
class AcNode:
    """One accessibility node with the codebook applied. ``node_uid`` is the window-local id."""

    window_index: int
    window_layer: int
    node_uid: int
    depth: int
    class_name: str
    resource_id: str
    content_desc: str  # cleaned: "" when absent or "null"
    text: str  # cleaned the same way
    hint_text: str
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
        return bool(self.content_desc)

    def in_population(self, population: str) -> bool:
        if population not in POPULATIONS:
            raise ValueError(f"unknown population {population!r}; choose from {POPULATIONS}")
        return self.included and bool(getattr(self, population))

    def flagged(self, population: str = "needs_label") -> bool:
        return self.in_population(population) and not self.labelled


@dataclass(frozen=True, slots=True)
class AcScreen:
    screen_id: str
    app: str
    episode_id: int
    step_index: int
    width: int
    height: int
    nodes: tuple[AcNode, ...]

    def flagged(self, population: str = "needs_label") -> list[AcNode]:
        return [node for node in self.nodes if node.flagged(population)]


@dataclass(frozen=True, slots=True)
class AcEpisode:
    episode_id: int
    split: str
    shard: str
    goal: str
    app: str
    n_actions: int
    screens: tuple[AcScreen, ...]


def _make_node(node: Any, window_index: int, window_layer: int) -> AcNode:
    class_name = node.class_name
    text = tx.clean_text(node.text)
    role = tx.classify_role(class_name)
    return AcNode(
        window_index=window_index,
        window_layer=window_layer,
        node_uid=node.unique_id,
        depth=node.depth,
        class_name=class_name,
        resource_id=node.view_id_resource_name,
        content_desc=tx.clean_text(node.content_description),
        text=text,
        hint_text=node.hint_text,
        clickable=node.is_clickable,
        long_clickable=node.is_long_clickable,
        focusable=node.is_focusable,
        enabled=node.is_enabled,
        visible_to_user=node.is_visible_to_user,
        bounds=(node.left, node.top, node.right, node.bottom),
        role=role,
        included=tx.in_analysis_population(
            node.is_visible_to_user, node.left, node.top, node.right, node.bottom, node.is_enabled
        ),
        needs_label=tx.needs_label(role, node.is_clickable, node.is_long_clickable, text),
        icon_like=tx.is_icon_like(role, text, node.is_clickable, node.is_long_clickable),
        interactive_image=tx.is_interactive_image(class_name, node.is_clickable, node.is_focusable),
    )


def episode_app(resource_ids: Iterator[str] | list[str]) -> str:
    """The dominant non-platform package among resource ids; "" when there is none."""
    counts: Counter[str] = Counter()
    for rid in resource_ids:
        match = _PACKAGE.match(rid or "")
        if match and match.group(1) not in SYSTEM_PACKAGES:
            counts[match.group(1)] += 1
    if not counts:
        return ""
    return min(counts.items(), key=lambda item: (-item[1], item[0]))[0]


def parse_episode(
    example: Mapping[str, list], split: str = "unknown", shard: str = ""
) -> AcEpisode:
    """Decode one tf.train.Example (as returned by ``parse_example``) into screens of nodes."""
    episode_id = int((example.get("episode_id") or [0])[0])
    goal = (example.get("goal") or [b""])[0].decode("utf-8", "replace")
    trees = example.get("accessibility_trees") or []
    widths = example.get("screenshot_widths") or []
    heights = example.get("screenshot_heights") or []

    steps: list[tuple[int, int, tuple[AcNode, ...]]] = []
    for step_index, blob in enumerate(trees):
        try:
            windows = parse_forest(blob)
        except Exception:  # a forest that will not decode is an empty screen, as in AISSA
            windows = []
        nodes = tuple(
            _make_node(node, window_index, window.layer)
            for window_index, window in enumerate(windows)
            for node in window.nodes
        )
        width = int(widths[step_index]) if step_index < len(widths) else 0
        height = int(heights[step_index]) if step_index < len(heights) else 0
        steps.append((width, height, nodes))

    app = episode_app([node.resource_id for _w, _h, nodes in steps for node in nodes])
    screens = tuple(
        AcScreen(
            screen_id=f"{episode_id}_{step_index}",
            app=app,
            episode_id=episode_id,
            step_index=step_index,
            width=width,
            height=height,
            nodes=nodes,
        )
        for step_index, (width, height, nodes) in enumerate(steps)
    )
    return AcEpisode(
        episode_id=episode_id,
        split=split,
        shard=shard,
        goal=goal,
        app=app,
        n_actions=len(example.get("actions") or []),
        screens=screens,
    )


def load_splits(path: str | Path) -> dict[int, str]:
    """Map episode id -> split ("train", "validation", "test") from AndroidControl's splits.json."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {int(episode_id): split for split, ids in data.items() for episode_id in ids}


class ShardReader:
    """Iterate the episodes of one shard. A truncated shard stops early and sets ``truncated``;
    an episode that fails to decode is skipped and listed in ``failures``."""

    def __init__(
        self, path: str | Path, splits: Mapping[int, str] | None = None, shard: str | None = None
    ) -> None:
        self.path = Path(path)
        self.shard = shard or self.path.name
        self.splits = splits or {}
        self.truncated = False
        self.records = 0
        self.failures: list[dict[str, str]] = []

    def __iter__(self) -> Iterator[AcEpisode]:
        records = iter_records(self.path)
        while True:
            try:
                blob = next(records)
            except StopIteration:
                return
            except TruncatedShardError:
                self.truncated = True
                return
            self.records += 1
            try:
                example = parse_example(blob)
                episode_id = int((example.get("episode_id") or [0])[0])
                yield parse_episode(example, self.splits.get(episode_id, "unknown"), self.shard)
            except Exception as exc:  # one bad episode must not stop a 2.5 GB shard
                self.failures.append(
                    {
                        "shard": self.shard,
                        "record": str(self.records),
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
