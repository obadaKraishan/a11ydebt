"""The Rico loader on three hand-built fixture screens (expected values computed by hand)."""

from __future__ import annotations

import pytest

from a11ydebt.rico import (
    find_screen_files,
    iter_screens,
    load_screen,
    parse_screen,
    read_ui_details,
)


def by_resource(screen, suffix):
    (node,) = [n for n in screen.nodes if n.resource_id.endswith(suffix)]
    return node


def test_finds_fixture_screens_in_numeric_order(rico_dir):
    assert [p.stem for p in find_screen_files(rico_dir)] == ["101", "102", "103"]
    assert [s.screen_id for s in iter_screens(rico_dir, limit=2)] == ["101", "102"]


def test_ui_details_maps_screens_to_apps(rico_dir):
    assert read_ui_details(rico_dir / "ui_details.csv") == {
        "101": "org.example.notes",
        "102": "org.example.notes",
        "103": "com.example.weather",
    }


def test_walk_is_preorder_with_parents_and_depths(rico_dir):
    screen = load_screen(rico_dir / "combined" / "101.json")
    assert len(screen.nodes) == 8
    assert [n.node_uid for n in screen.nodes] == list(range(8))
    assert [n.parent_uid for n in screen.nodes] == [-1, 0, 1, 1, 1, 1, 1, 1]
    assert [n.depth for n in screen.nodes] == [0, 1, 2, 2, 2, 2, 2, 2]
    assert screen.nodes[0].role == "container"  # PhoneWindow$DecorView
    assert (screen.width, screen.height) == (1440, 2560)


def test_null_children_are_skipped_and_empty_lists_are_leaves(rico_dir):
    screen = load_screen(rico_dir / "combined" / "103.json")
    assert len(screen.nodes) == 7  # root + 6 real children; the null entry is not a node


def test_inclusion_rule(rico_dir):
    s101 = load_screen(rico_dir / "combined" / "101.json")
    s103 = load_screen(rico_dir / "combined" / "103.json")
    assert by_resource(s101, "collapsed").included is False  # zero area
    assert by_resource(s101, "hidden").included is False  # not visible to user
    assert by_resource(s103, "inverted").included is False  # negative width
    assert by_resource(s103, "broken").included is False  # malformed bounds
    assert by_resource(s103, "refresh").included is True  # disabled still counts
    assert sum(n.included for n in s101.nodes) == 6
    assert sum(n.included for n in s103.nodes) == 5


def test_content_desc_encodings(rico_dir):
    s101 = load_screen(rico_dir / "combined" / "101.json")
    s102 = load_screen(rico_dir / "combined" / "102.json")
    s103 = load_screen(rico_dir / "combined" / "103.json")
    assert by_resource(s101, "logo").labelled is True  # ["App logo"]
    assert by_resource(s101, "nav").labelled is False  # [null]
    assert by_resource(s101, "search").labelled is False  # ["null"]
    assert by_resource(s102, "thumb").labelled is False  # [""]
    assert by_resource(s102, "drag_handle").labelled is False  # key missing
    assert by_resource(s103, "refresh").labelled is False  # whitespace
    assert by_resource(s103, "refresh").text == ""  # text "None" counts as absent


def test_population_flags_split_where_the_rules_differ(rico_dir):
    s102 = load_screen(rico_dir / "combined" / "102.json")
    thumb = by_resource(s102, "thumb")  # focusable, not clickable
    handle = by_resource(s102, "drag_handle")  # long-clickable only
    fab = by_resource(s102, "fab")
    save = by_resource(s102, "save")  # Button with text
    row = by_resource(s102, "row")  # clickable container

    assert (thumb.needs_label, thumb.icon_like, thumb.interactive_image) == (True, False, True)
    assert (handle.needs_label, handle.icon_like, handle.interactive_image) == (True, True, False)
    assert (fab.needs_label, fab.icon_like, fab.interactive_image) == (True, True, True)
    assert (save.needs_label, save.icon_like, save.interactive_image) == (False, False, False)
    assert (row.needs_label, row.icon_like, row.interactive_image) == (False, False, False)


def test_flagged_nodes(rico_dir):
    s101, s102, s103 = iter_screens(rico_dir)
    assert [n.resource_id.split("/")[-1] for n in s101.flagged()] == ["nav", "search"]
    assert [n.resource_id.split("/")[-1] for n in s102.flagged("interactive_image")] == ["thumb"]
    assert [n.resource_id.split("/")[-1] for n in s103.flagged("icon_like")] == ["refresh"]
    with pytest.raises(ValueError, match="unknown population"):
        s101.flagged("everything")


def test_app_comes_from_ui_details_then_activity_name(rico_dir):
    apps = {s.screen_id: s.app for s in iter_screens(rico_dir)}
    assert apps == {
        "101": "org.example.notes",
        "102": "org.example.notes",
        "103": "com.example.weather",
    }
    blob = {"activity_name": "com.foo.bar/.Main", "activity": {"root": {"class": "View"}}}
    assert parse_screen(blob, "9").app == "com.foo.bar"
    assert parse_screen(blob, "9", app="given").app == "given"


def test_missing_root_raises():
    with pytest.raises(ValueError, match=r"no activity\.root"):
        parse_screen({"activity": {}}, "1")
