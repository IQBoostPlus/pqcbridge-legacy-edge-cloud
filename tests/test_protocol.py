"""Baseline tests for the JSON-lines protocol framing
(serialization/deserialization, size limit, malformed input).

Updated for P04 (F-15 decision): a message truncated at EOF is now
reported as "mid-message", distinct from an oversized message.
"""
import io

import pytest

from common import protocol


def _stream(data: bytes):
    return io.BufferedReader(io.BytesIO(data))


def test_read_message_round_trip():
    original = {"type": "hello", "device_id": "dev-01"}
    parsed = protocol.read_message(_stream(protocol.encode_message(original)))
    assert parsed == original


def test_read_message_rejects_invalid_json():
    with pytest.raises(protocol.ProtocolError):
        protocol.read_message(_stream(b"not json\n"))


def test_read_message_rejects_non_object():
    with pytest.raises(protocol.ProtocolError):
        protocol.read_message(_stream(b"[1,2,3]\n"))


def test_read_message_rejects_oversized_messages():
    with pytest.raises(protocol.ProtocolError, match="maximum allowed size"):
        protocol.read_message(
            _stream(b"x" * (protocol.MAX_MESSAGE_BYTES + 10)))


def test_read_message_detects_truncated_message():
    # content without a trailing newline at EOF: not oversized, truncated
    with pytest.raises(protocol.ProtocolError, match="mid-message"):
        protocol.read_message(_stream(b'{"type": "hello"'))


def test_read_message_detects_clean_disconnect():
    with pytest.raises(protocol.ConnectionClosedError):
        protocol.read_message(_stream(b""))


def test_read_message_accepts_multiple_messages_in_sequence():
    stream = _stream(protocol.encode_message({"type": "a"})
                     + protocol.encode_message({"type": "b"}))
    assert protocol.read_message(stream)["type"] == "a"
    assert protocol.read_message(stream)["type"] == "b"


def test_b64_round_trip():
    assert protocol.b64d(protocol.b64e(b"\x00\x01\xfe\xff")) == b"\x00\x01\xfe\xff"


def test_b64_rejects_malformed():
    with pytest.raises(protocol.ProtocolError):
        protocol.b64d("!!!not-base64!!!")


def test_parse_reading_bytes_rejects_missing_fields():
    with pytest.raises(protocol.ProtocolError):
        protocol.parse_reading_bytes(b'{"device_id": "dev-01"}')


def test_parse_reading_bytes_rejects_missing_sequence():
    # P04 (F-05): every reading must carry a sequence for replay
    # protection; this is a documented protocol change from P01.
    with pytest.raises(protocol.ProtocolError):
        protocol.parse_reading_bytes(
            b'{"device_id": "dev-01", "timestamp": "2026-01-01T00:00:00+00:00",'
            b' "temperature_c": 21.5}')


def test_parse_reading_bytes_accepts_valid_reading():
    reading = protocol.parse_reading_bytes(
        b'{"device_id": "dev-01", "timestamp": "2026-01-01T00:00:00+00:00",'
        b' "temperature_c": 21.5, "sequence": 3}')
    assert reading["device_id"] == "dev-01"
    assert reading["sequence"] == 3
