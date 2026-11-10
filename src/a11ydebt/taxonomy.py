"""The element taxonomy: the AISSA 2026 operational codebook, expressed as code.

Ported with unchanged semantics from ``src/a11ydebt/taxonomy.py`` in accessibility-debt-agents
(commit 97c0378, MIT; see NOTICE). Every published Rico and AndroidControl coverage number flows
from these rules, so a change here changes the paper's numbers. Any change needs a test, a
CHANGELOG entry and a re-run of ``scripts/compare_aissa.py``.

The module decides three things:

1. Which nodes count at all: the analysis population, ``in_analysis_population``.
2. What kind of element a node is: its role, ``classify_role``.
3. Whether an element needs a label and whether it has one: ``needs_label``, ``is_named`` and
   ``label_status``.

Roles come from the class name alone. AndroidControl trees have no superclass chain, so using
Rico's ``ancestors`` would make the cross-corpus comparison unfair. ``classify_role(name,
ancestors)`` exists only for the Rico robustness variant.

The P01 rule (``is_interactive_image``) is an addition and has no counterpart in the paper. It
flags an image-based node that is clickable or focusable.
"""

from __future__ import annotations

from collections.abc import Sequence

__all__ = [
    "ELEMENT_ROLES",
    "LABEL_STATUSES",
    "LabelStatus",
    "Role",
    "classify_role",
    "clean_text",
    "has_visible_text",
    "in_analysis_population",
    "is_floating_action_button",
    "is_icon_like",
    "is_image_based",
    "is_interactive",
    "is_interactive_image",
    "is_named",
    "label_status",
    "needs_label",
    "normalise_class",
    "positive_area",
]


class Role:
    """Element roles. Deliberately coarse so the categories stay reliable."""

    IMAGE = "image"  # ImageView and friends: cannot be read aloud without a label
    BUTTON = "button"  # Button, ImageButton, FloatingActionButton
    TEXT = "text"  # TextView and friends: self-naming when text is present
    INPUT = "input"  # EditText, CheckBox, RadioButton, Switch, SeekBar, Spinner
    CONTAINER = "container"  # layouts and list containers
    WEB = "web"  # WebView: contents are opaque to the view hierarchy
    OTHER = "other"


class LabelStatus:
    LABELLED = "labelled"  # has a non-empty content description
    UNLABELLED = "unlabelled"  # needs one and does not have one: the debt
    NAMED_BY_TEXT = "named_by_text"  # no content-desc but has visible text
    NOT_APPLICABLE = "not_applicable"  # decorative or structural; no label expected


ELEMENT_ROLES: tuple[str, ...] = (
    Role.IMAGE,
    Role.BUTTON,
    Role.TEXT,
    Role.INPUT,
    Role.CONTAINER,
    Role.WEB,
    Role.OTHER,
)
LABEL_STATUSES: tuple[str, ...] = (
    LabelStatus.LABELLED,
    LabelStatus.UNLABELLED,
    LabelStatus.NAMED_BY_TEXT,
    LabelStatus.NOT_APPLICABLE,
)


# ------------------------------------------------------------------ class-name matching


def normalise_class(class_name: str | None) -> str:
    """'android.widget.ImageButton' -> 'imagebutton'. Handles inner classes ('$')."""
    if not class_name:
        return ""
    name = str(class_name).strip()
    if "$" in name:
        name = name.split("$")[-1]
    if "." in name:
        name = name.rsplit(".", 1)[-1]
    return name.lower()


# Suffix rules, evaluated in order; first match wins, so specific entries come first. Suffixes
# (not exact names) make this work across AppCompat, Material, androidx and vendor classes.
_ROLE_RULES: tuple[tuple[str, str], ...] = (
    # inputs first: several of them end in -button or -view
    ("edittext", Role.INPUT),
    ("autocompletetextview", Role.INPUT),
    ("checkbox", Role.INPUT),
    ("radiobutton", Role.INPUT),
    ("togglebutton", Role.INPUT),
    ("switchcompat", Role.INPUT),
    ("switch", Role.INPUT),
    ("seekbar", Role.INPUT),
    ("ratingbar", Role.INPUT),
    ("spinner", Role.INPUT),
    ("numberpicker", Role.INPUT),
    ("datepicker", Role.INPUT),
    ("timepicker", Role.INPUT),
    ("searchview", Role.INPUT),
    # buttons
    ("floatingactionbutton", Role.BUTTON),
    ("imagebutton", Role.BUTTON),
    ("button", Role.BUTTON),
    # images
    ("imageview", Role.IMAGE),
    ("circleimageview", Role.IMAGE),
    ("photoview", Role.IMAGE),
    ("gifimageview", Role.IMAGE),
    ("simpledraweeview", Role.IMAGE),  # Facebook Fresco, very common in 2017 apps
    ("iconview", Role.IMAGE),
    ("icon", Role.IMAGE),
    # web
    ("webview", Role.WEB),
    # text
    ("textview", Role.TEXT),
    ("textclock", Role.TEXT),
    ("chronometer", Role.TEXT),
    # containers
    ("recyclerview", Role.CONTAINER),
    ("listview", Role.CONTAINER),
    ("gridview", Role.CONTAINER),
    ("scrollview", Role.CONTAINER),
    ("viewpager", Role.CONTAINER),
    ("viewgroup", Role.CONTAINER),
    ("layout", Role.CONTAINER),
    ("toolbar", Role.CONTAINER),
    ("actionbar", Role.CONTAINER),
    ("tablayout", Role.CONTAINER),
    ("decorview", Role.CONTAINER),
    ("drawerlayout", Role.CONTAINER),
    ("cardview", Role.CONTAINER),
)

# Used only for the Rico-only robustness variant.
_ANCESTOR_RULES: tuple[tuple[str, str], ...] = (
    ("android.widget.EditText", Role.INPUT),
    ("android.widget.CompoundButton", Role.INPUT),
    ("android.widget.AbsSeekBar", Role.INPUT),
    ("android.widget.AbsSpinner", Role.INPUT),
    ("android.widget.ImageButton", Role.BUTTON),
    ("android.widget.Button", Role.BUTTON),
    ("android.widget.ImageView", Role.IMAGE),
    ("android.webkit.WebView", Role.WEB),
    ("android.widget.TextView", Role.TEXT),
    ("android.widget.AdapterView", Role.CONTAINER),
    ("android.view.ViewGroup", Role.CONTAINER),
)


def classify_role(class_name: str | None, ancestors: Sequence[str] | None = None) -> str:
    """Assign an element role from the class name.

    Pass ``ancestors`` ONLY for the Rico-only robustness variant; the primary analysis uses
    the class name alone so both corpora are classified from identical information.
    """
    key = normalise_class(class_name)
    if key:
        for suffix, role in _ROLE_RULES:
            if key.endswith(suffix):
                return role
    if ancestors:
        for ancestor, role in _ANCESTOR_RULES:
            if ancestor in ancestors:
                return role
    return Role.OTHER


def is_floating_action_button(class_name: str | None) -> bool:
    return normalise_class(class_name).endswith("floatingactionbutton")


# ------------------------------------------------------------------ label logic


def clean_text(value: object) -> str:
    """Normalise a text-ish field to a stripped string; Rico's ``[None]`` and literal
    'none'/'null'/'nan' strings count as absent."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        value = value[0] if value else None
        if value is None:
            return ""
    text = str(value).strip()
    if text.lower() in {"none", "null", "nan", ""}:
        return ""
    return text


def is_interactive(clickable: bool, long_clickable: bool = False, role: str | None = None) -> bool:
    """An element a user can act on, and therefore one a screen reader must name."""
    if bool(clickable) or bool(long_clickable):
        return True
    return role in {Role.INPUT, Role.BUTTON}


def has_visible_text(text: object) -> bool:
    return bool(clean_text(text))


def is_named(content_desc: object) -> bool:
    """True when a developer supplied a content description."""
    return bool(clean_text(content_desc))


def needs_label(role: str, clickable: bool, long_clickable: bool, text: object) -> bool:
    """Does this element require a content description?

    Yes when it is image-bearing or interactive AND carries no visible text of its own.
    Containers, plain text views and web views are exempt.
    """
    if role in {Role.CONTAINER, Role.WEB}:
        return False
    if has_visible_text(text):
        return False
    if role == Role.IMAGE:
        return True
    return is_interactive(clickable, long_clickable, role)


def label_status(
    role: str,
    content_desc: object,
    text: object,
    clickable: bool,
    long_clickable: bool = False,
) -> str:
    """The study's dependent variable; ``unlabelled`` is the accessibility debt."""
    if is_named(content_desc):
        return LabelStatus.LABELLED
    if needs_label(role, clickable, long_clickable, text):
        return LabelStatus.UNLABELLED
    if has_visible_text(text):
        return LabelStatus.NAMED_BY_TEXT
    return LabelStatus.NOT_APPLICABLE


def is_icon_like(role: str, text: object, clickable: bool, long_clickable: bool = False) -> bool:
    """The strictest unit: a tappable graphic (image or button role) with no visible text."""
    if role not in {Role.IMAGE, Role.BUTTON}:
        return False
    if has_visible_text(text):
        return False
    return is_interactive(clickable, long_clickable, role)


# ------------------------------------------------------------------ P01 rule (a11ydebt addition)

_IMAGE_BUTTON_SUFFIXES = ("imagebutton", "floatingactionbutton")


def is_image_based(class_name: str | None) -> bool:
    """ImageView-family classes (role image) plus ImageButton and FloatingActionButton.

    A plain text ``Button`` is not image-based even though it shares the button role.
    """
    return classify_role(class_name) == Role.IMAGE or normalise_class(class_name).endswith(
        _IMAGE_BUTTON_SUFFIXES
    )


def is_interactive_image(class_name: str | None, clickable: bool, focusable: bool) -> bool:
    """P01: an image-based node that is clickable or focusable (long-click alone does not count)."""
    return is_image_based(class_name) and (bool(clickable) or bool(focusable))


# ------------------------------------------------------------------ analysis population


def positive_area(x1: float, y1: float, x2: float, y2: float) -> bool:
    """48.7% of Rico nodes have zero or negative area, and some of them are still flagged
    visible-to-user, so area is checked separately from visibility."""
    try:
        return (float(x2) - float(x1)) > 0 and (float(y2) - float(y1)) > 0
    except (TypeError, ValueError):
        return False


def in_analysis_population(
    visible_to_user: bool,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    enabled: bool = True,
    require_enabled: bool = False,
) -> bool:
    """The inclusion rule for every count: visible-to-user and positive area. ``require_enabled``
    is off by default and exercised only in the sensitivity analysis."""
    if not bool(visible_to_user):
        return False
    if not positive_area(x1, y1, x2, y2):
        return False
    return not (require_enabled and not bool(enabled))
