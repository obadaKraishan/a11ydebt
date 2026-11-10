"""Write small synthetic AndroidControl shards for tests (never real data).

Encodes AndroidAccessibilityForest protobufs and tf.train.Example records on the wire format the
reader in ``a11ydebt.tfrecord`` decodes, and frames them as a GZIP TFRecord file with real masked
CRC32C checksums.
"""

from __future__ import annotations

import gzip
import json
import struct
from dataclasses import dataclass, field
from pathlib import Path

# ------------------------------------------------------------------ protobuf encoding


def varint(value: int) -> bytes:
    value &= (1 << 64) - 1  # negatives as 64-bit two's complement, like protobuf int32/int64
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def key(field_no: int, wire: int) -> bytes:
    return varint((field_no << 3) | wire)


def f_varint(field_no: int, value: int) -> bytes:
    return key(field_no, 0) + varint(value)


def f_bytes(field_no: int, value: bytes | str) -> bytes:
    data = value.encode("utf-8") if isinstance(value, str) else value
    return key(field_no, 2) + varint(len(data)) + data


@dataclass
class SNode:
    """A synthetic AndroidAccessibilityNodeInfo."""

    uid: int
    cls: str
    bounds: tuple[int, int, int, int] = (0, 0, 100, 100)
    desc: str = ""
    text: str = ""
    hint: str = ""
    rid: str = ""
    clickable: bool = False
    long_clickable: bool = False
    focusable: bool = False
    enabled: bool = True
    visible: bool = True
    depth: int = 0
    children: list[int] = field(default_factory=list)

    def encode(self) -> bytes:
        rect = b"".join(f_varint(i + 1, v) for i, v in enumerate(self.bounds))
        out = f_varint(1, self.uid) + f_bytes(2, rect) + f_bytes(3, self.cls)
        for no, value in ((4, self.desc), (5, self.hint), (7, self.text), (10, self.rid)):
            if value:
                out += f_bytes(no, value)
        for no, flag in (
            (14, self.clickable),
            (16, self.enabled),
            (17, self.focusable),
            (19, self.long_clickable),
            (23, self.visible),
        ):
            if flag:
                out += f_varint(no, 1)
        if self.children:
            out += f_bytes(25, b"".join(varint(c) for c in self.children))  # packed
        return out + f_varint(27, self.depth)


def encode_window(
    nodes: list[SNode], layer: int = 0, window_id: int = 1, window_type: int = 1
) -> bytes:
    tree = b"".join(f_bytes(1, n.encode()) for n in nodes)
    rect = b"".join(f_varint(i + 1, v) for i, v in enumerate((0, 0, 1080, 2400)))
    return (
        f_bytes(1, rect)
        + f_varint(3, window_id)
        + f_varint(4, layer)
        + f_varint(6, window_type)
        + f_bytes(11, tree)
    )


def encode_forest(windows: list[bytes]) -> bytes:
    return b"".join(f_bytes(1, w) for w in windows)


def _feature_bytes(values: list[bytes]) -> bytes:
    return f_bytes(1, b"".join(f_bytes(1, v) for v in values))  # Feature.bytes_list


def _feature_int64(values: list[int]) -> bytes:
    return f_bytes(3, f_bytes(1, b"".join(varint(v) for v in values)))  # Feature.int64_list, packed


def encode_example(
    episode_id: int,
    forests: list[bytes],
    actions: list[dict] | None = None,
    goal: str = "synthetic goal",
) -> bytes:
    actions = actions or []
    features = {
        "episode_id": _feature_int64([episode_id]),
        "goal": _feature_bytes([goal.encode()]),
        "screenshot_widths": _feature_int64([1080] * len(forests)),
        "screenshot_heights": _feature_int64([2400] * len(forests)),
        "accessibility_trees": _feature_bytes(forests),
        "actions": _feature_bytes([json.dumps(a).encode() for a in actions]),
        "step_instructions": _feature_bytes([b"step"] * len(actions)),
    }
    entries = b"".join(
        f_bytes(1, f_bytes(1, name) + f_bytes(2, value)) for name, value in features.items()
    )
    return f_bytes(1, entries)  # Example.features


# ------------------------------------------------------------------ TFRecord framing

_CRC_TABLE = []
for _i in range(256):
    _c = _i
    for _ in range(8):
        _c = (_c >> 1) ^ 0x82F63B78 if _c & 1 else _c >> 1
    _CRC_TABLE.append(_c)


def crc32c(data: bytes) -> int:
    crc = 0xFFFFFFFF
    for byte in data:
        crc = _CRC_TABLE[(crc ^ byte) & 0xFF] ^ (crc >> 8)
    return crc ^ 0xFFFFFFFF


def masked_crc(data: bytes) -> int:
    crc = crc32c(data)
    return (((crc >> 15) | (crc << 17)) + 0xA282EAD8) & 0xFFFFFFFF


def frame(record: bytes) -> bytes:
    header = struct.pack("<Q", len(record))
    return (
        header
        + struct.pack("<I", masked_crc(header))
        + record
        + struct.pack("<I", masked_crc(record))
    )


def write_shard(path: Path, records: list[bytes], truncate_last: bool = False) -> Path:
    """Write a GZIP TFRecord shard. ``truncate_last`` cuts the final record's payload short."""
    data = b"".join(frame(r) for r in records)
    if truncate_last and records:
        data = data[: len(data) - len(records[-1]) // 2 - 4]
    path.write_bytes(gzip.compress(data))
    return path


# ------------------------------------------------------------------ the standard test shard

BROKEN_FOREST = b"\x0f\xff"  # field 1 with wire type 7: the reader raises, as on corrupt data


def standard_records() -> list[bytes]:
    """Two episodes whose counts the tests check by hand (see tests/test_androidcontrol.py)."""
    app_window = encode_window(
        [
            SNode(0, "android.widget.FrameLayout", (0, 0, 1080, 2400), children=[1, 2, 3, 4, 5]),
            SNode(
                1,
                "android.widget.ImageButton",
                (0, 0, 120, 120),
                rid="com.example.shop:id/menu",
                clickable=True,
                focusable=True,
                depth=1,
            ),
            SNode(
                2,
                "android.widget.ImageView",
                (120, 0, 360, 120),
                desc="Logo",
                rid="com.example.shop:id/logo",
                depth=1,
            ),
            SNode(3, "android.widget.TextView", (360, 0, 700, 120), text="Deals", depth=1),
            SNode(
                4,
                "android.widget.Button",
                (700, 0, 960, 120),
                desc="Search",
                clickable=True,
                depth=1,
            ),
            SNode(
                5,
                "android.widget.ImageView",
                (960, 0, 1080, 120),
                clickable=True,
                visible=False,
                depth=1,
            ),
        ],
        layer=1,
        window_id=10,
    )
    keyboard_window = encode_window(
        [
            SNode(
                0,
                "android.view.View",
                (0, 1800, 120, 1900),
                clickable=True,
                rid="com.google.android.inputmethod.latin:id/key",
            )
        ],
        layer=2,
        window_id=11,
        window_type=2,
    )
    news_window = encode_window(
        [
            SNode(
                0,
                "android.widget.ImageView",
                (0, 0, 300, 300),
                focusable=True,
                rid="com.example.news:id/thumb",
            ),
            SNode(
                1,
                "android.widget.EditText",
                (0, 300, 1080, 420),
                hint="Search news",
                clickable=True,
                rid="com.example.news:id/query",
            ),
            SNode(2, "android.widget.ImageView", (10, 10, 10, 50), clickable=True),
        ]
    )
    return [
        encode_example(
            7,
            [encode_forest([app_window, keyboard_window]), BROKEN_FOREST],
            actions=[{"action_type": "click", "x": 10, "y": 10}],
        ),
        encode_example(9, [encode_forest([news_window])]),
    ]
