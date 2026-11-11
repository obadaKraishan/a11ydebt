"""Per-screen counting shared by the CLI and the Kaggle kernel. Standard library only.

A screen is anything with ``screen_id``, ``app`` and ``nodes``. A node is anything carrying the
codebook flags ``included``, ``labelled``, ``needs_label``, ``icon_like``, ``interactive_image`` and
``role``. Rico and AndroidControl nodes both qualify, so both corpora are counted by the same loop.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Protocol

__all__ = ["LABEL_ROLES", "POPULATIONS", "NodeLike", "ScreenCounts", "ScreenLike", "count_screen"]

#: The populations a11ydebt counts. All of them require ``included`` (visible, positive area).
#:   needs_label        the paper's primary denominator (AISSA "label coverage")
#:   icon_like          the paper's strictest denominator (a tappable graphic with no text)
#:   interactive_image  an a11ydebt addition: an image-based node that is clickable or focusable
POPULATIONS: tuple[str, ...] = ("needs_label", "icon_like", "interactive_image")

#: Roles that can need a label (containers and web views are exempt), in report order.
LABEL_ROLES: tuple[str, ...] = ("button", "image", "input", "other", "text")


class NodeLike(Protocol):
    @property
    def included(self) -> bool: ...
    @property
    def labelled(self) -> bool: ...
    @property
    def needs_label(self) -> bool: ...
    @property
    def icon_like(self) -> bool: ...
    @property
    def interactive_image(self) -> bool: ...
    @property
    def role(self) -> str: ...


class ScreenLike(Protocol):
    @property
    def screen_id(self) -> str: ...
    @property
    def app(self) -> str: ...
    @property
    def nodes(self) -> Sequence[NodeLike]: ...


def _zeros() -> dict[str, int]:
    return dict.fromkeys(POPULATIONS, 0)


@dataclass
class ScreenCounts:
    """Counts for one screen, over included nodes only (``n_nodes`` counts every node)."""

    n_nodes: int = 0
    n_included: int = 0
    candidates: dict[str, int] = field(default_factory=_zeros)
    labelled: dict[str, int] = field(default_factory=_zeros)
    role_candidates: dict[str, int] = field(default_factory=dict)  # needs_label, by role
    role_labelled: dict[str, int] = field(default_factory=dict)


def count_screen(screen: ScreenLike) -> ScreenCounts:
    counts = ScreenCounts(n_nodes=len(screen.nodes))
    for node in screen.nodes:
        if not node.included:
            continue
        counts.n_included += 1
        has_label = int(node.labelled)
        for population in POPULATIONS:
            if getattr(node, population):
                counts.candidates[population] += 1
                counts.labelled[population] += has_label
        if node.needs_label:
            counts.role_candidates[node.role] = counts.role_candidates.get(node.role, 0) + 1
            counts.role_labelled[node.role] = counts.role_labelled.get(node.role, 0) + has_label
    return counts
