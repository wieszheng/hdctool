from __future__ import annotations

from hdctool.channel_handshake import MAX_CONNECTKEY_SIZE, ChannelHandShake


def test_deserialize_reads_banner_and_channel_id() -> None:
    banner = b"OHOS HDC\x00\x00\x00\x00"
    channel = (0xAABBCCDD).to_bytes(4, "big")
    buf = banner + channel
    hs = ChannelHandShake()
    hs.deserialize(buf)
    assert hs.banner == banner
    assert hs.channel_id == 0xAABBCCDD


def test_serialize_joins_banner_and_zero_padded_key() -> None:
    hs = ChannelHandShake()
    hs.banner = b"x" * 12
    hs.connect_key = "k1"
    out = hs.serialize()
    assert len(out) == 12 + MAX_CONNECTKEY_SIZE
    assert out.startswith(b"x" * 12)
    assert out[12:14] == b"k1"
