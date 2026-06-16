"""Unit tests for CSVStreamer."""

import io

import pytest

from app.services.csv_streamer import CSVStreamer, _csv_chunks


def test_csv_chunks_header_included():
    rows = [{"a": 1, "b": 2}]
    chunks = list(_csv_chunks(rows, ["a", "b"]))
    full = "".join(chunks)
    assert "a,b" in full
    assert "1,2" in full


def test_csv_chunks_splits_at_chunk_size():
    rows = [{"a": i} for i in range(10)]
    chunks = list(_csv_chunks(rows, ["a"], chunk_size=3))
    # 10 rows / 3 per chunk = 4 chunks
    assert len(chunks) >= 3


def test_csv_chunks_column_ordering():
    rows = [{"z": 1, "a": 2, "m": 3}]
    columns = ["a", "m", "z"]
    full = "".join(_csv_chunks(rows, columns))
    header_line = full.splitlines()[0]
    assert header_line == "a,m,z"


def test_streamer_returns_streaming_response():
    from fastapi.responses import StreamingResponse  # noqa: PLC0415
    streamer = CSVStreamer()
    resp = streamer.stream([{"x": 1}], ["x"], "test.csv")
    assert isinstance(resp, StreamingResponse)


def test_streamer_content_disposition_header():
    streamer = CSVStreamer()
    resp = streamer.stream([], ["x"], "my_report.csv")
    assert resp.headers["content-disposition"] == 'attachment; filename="my_report.csv"'
