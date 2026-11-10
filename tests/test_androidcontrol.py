"""The AndroidControl loader on the synthetic standard shard. Expected counts were done by hand.

Episode 7, step 0 (two windows):
  app window (layer 1): FrameLayout root; ImageButton menu (clickable, no desc); ImageView "Logo";
  TextView "Deals"; Button desc "Search" (clickable, no text); ImageView, clickable but invisible.
  keyboard window (layer 2): View, clickable, no text, resource id of the system keyboard.
Episode 7, step 1: a corrupt forest, so an empty screen.
Episode 9, step 0: ImageView thumb (focusable only); EditText with hint only; zero-area ImageView.
"""

from __future__ import annotations

import json

import pytest

from a11ydebt.androidcontrol import ShardReader, episode_app, load_splits
from a11ydebt.counts import count_screen
from a11ydebt.coverage import audit_androidcontrol, coverage
from synthetic_tfrecord import standard_records, write_shard


@pytest.fixture
def shard(tmp_path):
    return write_shard(tmp_path / "android_control-00000-of-00001", standard_records())


@pytest.fixture
def episodes(shard):
    return list(ShardReader(shard, splits={7: "train", 9: "test"}))


def by_rid(screen, suffix):
    (node,) = [n for n in screen.nodes if n.resource_id.endswith(suffix)]
    return node


def test_episodes_screens_splits_and_apps(episodes):
    ep7, ep9 = episodes
    assert (ep7.episode_id, ep7.split, ep7.app, ep7.n_actions) == (
        7,
        "train",
        "com.example.shop",
        1,
    )
    assert (ep9.episode_id, ep9.split, ep9.app, ep9.n_actions) == (9, "test", "com.example.news", 0)
    assert [s.screen_id for s in ep7.screens] == ["7_0", "7_1"]
    assert [s.screen_id for s in ep9.screens] == ["9_0"]
    assert ep7.shard == "android_control-00000-of-00001"


def test_nodes_come_from_every_window(episodes):
    screen = episodes[0].screens[0]
    assert len(screen.nodes) == 7
    key = by_rid(screen, "inputmethod.latin:id/key")
    assert (key.window_index, key.window_layer, key.role) == (1, 2, "other")


def test_a_corrupt_forest_is_an_empty_screen(episodes):
    assert episodes[0].screens[1].nodes == ()


def test_codebook_flags(episodes):
    s70, s90 = episodes[0].screens[0], episodes[1].screens[0]
    menu, logo = by_rid(s70, "shop:id/menu"), by_rid(s70, "shop:id/logo")
    search = next(n for n in s70.nodes if n.content_desc == "Search")
    hidden = next(n for n in s70.nodes if not n.visible_to_user)
    thumb, query = by_rid(s90, "news:id/thumb"), by_rid(s90, "news:id/query")
    tiny = next(n for n in s90.nodes if n.resource_id == "")

    assert (menu.needs_label, menu.icon_like, menu.interactive_image, menu.labelled) == (
        True,
        True,
        True,
        False,
    )
    assert (logo.needs_label, logo.icon_like, logo.interactive_image, logo.labelled) == (
        True,
        False,
        False,
        True,
    )
    assert (search.needs_label, search.icon_like, search.interactive_image) == (True, True, False)
    assert (thumb.needs_label, thumb.icon_like, thumb.interactive_image) == (True, False, True)
    assert (query.role, query.needs_label, query.labelled) == (
        "input",
        True,
        False,
    )  # a hint is not a label
    assert hidden.included is False and tiny.included is False


def test_counts_per_screen(episodes):
    c70, c71, c90 = (count_screen(s) for s in (*episodes[0].screens, *episodes[1].screens))
    assert (c70.n_nodes, c70.n_included) == (7, 6)
    assert c70.candidates == {"needs_label": 4, "icon_like": 2, "interactive_image": 1}
    assert c70.labelled == {"needs_label": 2, "icon_like": 1, "interactive_image": 0}
    assert c70.role_candidates == {"button": 2, "image": 1, "other": 1}
    assert c70.role_labelled == {"button": 1, "image": 1, "other": 0}
    assert (c71.n_nodes, c71.n_included, c71.candidates["needs_label"]) == (0, 0, 0)
    assert (c90.n_nodes, c90.n_included) == (3, 2)
    assert c90.candidates == {"needs_label": 2, "icon_like": 0, "interactive_image": 1}
    assert c90.labelled == {"needs_label": 0, "icon_like": 0, "interactive_image": 0}


def test_corpus_report(episodes):
    report = coverage([s for ep in episodes for s in ep.screens], dataset="androidcontrol")
    corpus = report.corpus
    assert (corpus.n_screens, corpus.n_apps, corpus.n_nodes, corpus.n_included) == (3, 2, 10, 8)
    pops = {p: (c.candidates, c.labelled) for p, c in corpus.populations.items()}
    assert pops == {"needs_label": (6, 2), "icon_like": (2, 1), "interactive_image": (2, 0)}
    roles = {r: (c.candidates, c.labelled) for r, c in corpus.needs_label_by_role.items()}
    assert roles == {"button": (2, 1), "image": (2, 1), "input": (1, 0), "other": (1, 0)}


def test_truncated_shard_keeps_what_it_read(tmp_path):
    shard = write_shard(tmp_path / "cut", standard_records(), truncate_last=True)
    reader = ShardReader(shard)
    assert [ep.episode_id for ep in reader] == [7]
    assert reader.truncated is True


def test_an_undecodable_episode_is_recorded_and_skipped(tmp_path):
    shard = write_shard(tmp_path / "bad", [b"\x0f\xff", *standard_records()])
    reader = ShardReader(shard)
    assert [ep.episode_id for ep in reader] == [7, 9]
    assert len(reader.failures) == 1
    assert reader.failures[0]["record"] == "1"


def test_episode_app_ignores_platform_packages_and_breaks_ties_alphabetically():
    ids = ["b.app:id/x", "a.app:id/y", "android:id/z", "com.android.systemui:id/q", "no-package"]
    assert episode_app(ids) == "a.app"
    assert episode_app(["com.google.android.gms:id/x"]) == ""
    assert episode_app([]) == ""


def test_load_splits(tmp_path):
    path = tmp_path / "splits.json"
    path.write_text(json.dumps({"train": [1, 2], "test": [3]}), encoding="utf-8")
    assert load_splits(path) == {1: "train", 2: "train", 3: "test"}


def test_audit_androidcontrol_over_shards(shard, tmp_path):
    cut = write_shard(tmp_path / "cut", standard_records(), truncate_last=True)
    report = audit_androidcontrol([shard, cut])
    assert report.dataset == "androidcontrol"
    assert report.corpus.n_screens == 3 + 2  # the cut shard still yields episode 7
    assert [f.error.split(":")[0] for f in report.failures] == ["TruncatedShard"]
