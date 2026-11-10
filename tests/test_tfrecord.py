"""The TFRecord / protobuf reader, on synthetic shards written by tests/synthetic_tfrecord.py."""

from __future__ import annotations

import json

import pytest

from a11ydebt.tfrecord import (
    Node,
    TruncatedShardError,
    Window,
    iter_records,
    parse_example,
    parse_forest,
    resolve_click,
)
from synthetic_tfrecord import (
    BROKEN_FOREST,
    SNode,
    crc32c,
    encode_example,
    encode_forest,
    encode_window,
    standard_records,
    write_shard,
)


def test_crc32c_check_value():
    assert crc32c(b"123456789") == 0xE3069283  # the standard CRC-32C check value


def test_records_round_trip(tmp_path):
    records = standard_records()
    shard = write_shard(tmp_path / "shard", records)
    assert list(iter_records(shard)) == records


def test_truncated_shard_raises_after_the_good_records(tmp_path):
    shard = write_shard(tmp_path / "shard", standard_records(), truncate_last=True)
    reader = iter_records(shard)
    assert next(reader) == standard_records()[0]
    with pytest.raises(TruncatedShardError) as info:
        next(reader)
    assert info.value.records_read == 1


def test_parse_example_decodes_int64_and_bytes_lists():
    blob = encode_example(7, [b"a", b"b"], actions=[{"action_type": "click", "x": 1, "y": 2}])
    example = parse_example(blob)
    assert example["episode_id"] == [7]
    assert example["screenshot_widths"] == [1080, 1080]
    assert example["accessibility_trees"] == [b"a", b"b"]
    assert json.loads(example["actions"][0]) == {"action_type": "click", "x": 1, "y": 2}
    assert example["goal"] == [b"synthetic goal"]


def test_parse_forest_reads_windows_nodes_and_flags():
    forest = encode_forest(
        [
            encode_window(
                [
                    SNode(
                        3,
                        "android.widget.ImageButton",
                        (-5, -10, 100, 50),
                        desc="Menu",
                        rid="com.x:id/menu",
                        clickable=True,
                        focusable=True,
                        depth=2,
                        children=[4, 5],
                    ),
                ],
                layer=4,
                window_id=12,
                window_type=2,
            ),
            encode_window([SNode(0, "android.widget.TextView", text="Hi")]),
        ]
    )
    windows = parse_forest(forest)
    assert [w.layer for w in windows] == [4, 0]
    assert windows[0].window_id == 12
    assert windows[0].window_type == "TYPE_INPUT_METHOD"
    node = windows[0].nodes[0]
    assert (node.unique_id, node.class_name, node.content_description) == (
        3,
        "android.widget.ImageButton",
        "Menu",
    )
    assert (node.left, node.top, node.right, node.bottom) == (-5, -10, 100, 50)  # negatives survive
    assert (node.is_clickable, node.is_focusable, node.is_long_clickable) == (True, True, False)
    assert node.is_visible_to_user and node.is_enabled
    assert node.child_ids == [4, 5]
    assert node.depth == 2
    assert node.view_id_resource_name == "com.x:id/menu"
    assert windows[1].nodes[0].text == "Hi"


def test_a_corrupt_forest_raises():
    with pytest.raises(ValueError):
        parse_forest(BROKEN_FOREST)


# --- resolve_click, ported from the AISSA smoke tests


def _node(uid, box, clickable=False, visible=True, depth=0, children=()):
    return Node(
        unique_id=uid,
        left=box[0],
        top=box[1],
        right=box[2],
        bottom=box[3],
        is_clickable=clickable,
        is_visible_to_user=visible,
        depth=depth,
        child_ids=list(children),
    )


def test_resolve_click_prefers_the_deepest_node():
    window = Window(
        window_id=1,
        layer=0,
        nodes=[
            _node(0, (0, 0, 100, 100), clickable=True, depth=0, children=[1]),
            _node(1, (10, 10, 50, 50), clickable=True, depth=1),
        ],
    )
    node, _ = resolve_click([window], 20, 20)
    assert node.unique_id == 1


def test_resolve_click_prefers_the_topmost_window():
    low = Window(window_id=1, layer=0, nodes=[_node(0, (0, 0, 100, 100), clickable=True)])
    high = Window(window_id=2, layer=5, nodes=[_node(0, (0, 0, 100, 100), clickable=True)])
    _, window = resolve_click([low, high], 50, 50)
    assert window.window_id == 2


def test_resolve_click_walks_up_to_a_clickable_ancestor():
    parent = _node(0, (0, 0, 100, 100), clickable=True, depth=0, children=[1])
    child = _node(1, (10, 10, 50, 50), clickable=False, depth=1)
    node, _ = resolve_click([Window(window_id=1, nodes=[parent, child])], 30, 30)
    assert node.unique_id == 0


def test_resolve_click_ignores_invisible_nodes():
    window = Window(window_id=1, nodes=[_node(0, (0, 0, 100, 100), visible=False)])
    assert resolve_click([window], 50, 50) == (None, None)
