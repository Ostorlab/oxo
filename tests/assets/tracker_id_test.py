"""Unit tests for TrackerId asset."""

from ostorlab.agent.message import serializer
from ostorlab.assets import tracker_id


def testAssetToProto_whenTrackerId_generatesProto():
    asset = tracker_id.TrackerId(id="a1b2c3", source="reverse_search")
    raw = asset.to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.tracker_id", raw)
    assert unraw.id == "a1b2c3"
    assert unraw.source == "reverse_search"
