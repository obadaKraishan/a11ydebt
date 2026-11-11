"""The codebook. Cases from the AISSA smoke tests are kept verbatim so the port cannot drift."""

from __future__ import annotations

import pytest

from a11ydebt import taxonomy as tx
from a11ydebt.taxonomy import LabelStatus as L
from a11ydebt.taxonomy import Role


@pytest.mark.parametrize(
    ("class_name", "expected"),
    [
        ("android.widget.ImageButton", Role.BUTTON),
        ("android.widget.ImageView", Role.IMAGE),
        ("androidx.appcompat.widget.AppCompatImageView", Role.IMAGE),
        ("com.google.android.material.floatingactionbutton.FloatingActionButton", Role.BUTTON),
        ("android.widget.EditText", Role.INPUT),
        ("android.widget.CheckBox", Role.INPUT),
        ("android.widget.TextView", Role.TEXT),
        ("android.widget.LinearLayout", Role.CONTAINER),
        ("androidx.recyclerview.widget.RecyclerView", Role.CONTAINER),
        ("android.webkit.WebView", Role.WEB),
        ("com.example.TotallyCustomThing", Role.OTHER),
        # additions
        ("com.example.weather.ui.WeatherIcon", Role.IMAGE),
        ("com.facebook.drawee.view.SimpleDraweeView", Role.IMAGE),
        ("android.widget.ToggleButton", Role.INPUT),
        ("", Role.OTHER),
        (None, Role.OTHER),
    ],
)
def test_role_classification(class_name, expected):
    assert tx.classify_role(class_name) == expected


def test_inner_class_names_are_normalised():
    assert tx.normalise_class("com.android.internal.policy.PhoneWindow$DecorView") == "decorview"


def test_ancestors_only_used_when_the_class_name_is_unknown():
    chain = ["android.widget.ImageView", "android.view.View", "java.lang.Object"]
    assert tx.classify_role("com.example.Thing") == Role.OTHER
    assert tx.classify_role("com.example.Thing", chain) == Role.IMAGE
    assert tx.classify_role("android.widget.TextView", chain) == Role.TEXT


def test_label_status_matrix():
    assert tx.label_status("image", "", "", False) == L.UNLABELLED
    assert tx.label_status("image", "Logo", "", False) == L.LABELLED
    assert tx.label_status("text", "", "Sign in", False) == L.NAMED_BY_TEXT
    assert tx.label_status("container", "", "", False) == L.NOT_APPLICABLE
    assert tx.label_status("web", "", "", True) == L.NOT_APPLICABLE
    assert tx.label_status("button", "", "", True) == L.UNLABELLED


def test_exempt_roles_never_need_a_label():
    for role in (Role.CONTAINER, Role.WEB):
        assert tx.needs_label(role, True, True, "") is False


def test_rico_content_desc_list_encoding():
    assert tx.is_named(["Search"]) is True
    assert tx.is_named([None]) is False
    assert tx.is_named([]) is False
    assert tx.is_named("none") is False
    assert tx.is_named("  ") is False
    assert tx.is_named(["null"]) is False


def test_zero_area_nodes_are_excluded():
    assert tx.in_analysis_population(True, 0, 0, 0, 0) is False
    assert tx.in_analysis_population(True, 10, 10, 5, 20) is False
    assert tx.in_analysis_population(False, 0, 0, 10, 10) is False
    assert tx.in_analysis_population(True, 0, 0, 10, 10) is True
    assert tx.in_analysis_population(True, 0, 0, 10, 10, enabled=False) is True
    strict = tx.in_analysis_population(True, 0, 0, 10, 10, enabled=False, require_enabled=True)
    assert strict is False


def test_icon_like_is_a_textless_tappable_graphic():
    assert tx.is_icon_like(Role.IMAGE, "", clickable=True) is True
    assert tx.is_icon_like(Role.IMAGE, "", clickable=False, long_clickable=True) is True
    assert tx.is_icon_like(Role.IMAGE, "", clickable=False) is False  # decorative image
    assert tx.is_icon_like(Role.BUTTON, "", clickable=False) is True  # buttons are interactive
    assert tx.is_icon_like(Role.BUTTON, "Save", clickable=True) is False
    assert tx.is_icon_like(Role.INPUT, "", clickable=True) is False


@pytest.mark.parametrize(
    ("class_name", "image_based"),
    [
        ("android.widget.ImageView", True),
        ("android.support.v7.widget.AppCompatImageButton", True),
        ("android.support.design.widget.FloatingActionButton", True),
        ("com.example.weather.ui.WeatherIcon", True),
        ("android.widget.Button", False),
        ("android.widget.TextView", False),
        ("android.widget.CheckBox", False),
    ],
)
def test_image_based(class_name, image_based):
    assert tx.is_image_based(class_name) is image_based


def test_interactive_image_rule():
    assert tx.is_interactive_image("android.widget.ImageView", clickable=True, focusable=False)
    assert tx.is_interactive_image("android.widget.ImageView", clickable=False, focusable=True)
    assert not tx.is_interactive_image("android.widget.ImageView", clickable=False, focusable=False)
    assert not tx.is_interactive_image("android.widget.Button", clickable=True, focusable=True)
