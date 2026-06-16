from __future__ import annotations

import csv
import io
from collections.abc import Generator, Iterable
from typing import Any

from fastapi.responses import StreamingResponse


def _csv_chunks(rows: Iterable[dict[str, Any]], columns: list[str], chunk_size: int = 500) -> Generator[str, None, None]:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    count = 0
    for row in rows:
        writer.writerow(row)
        count += 1
        if count >= chunk_size:
            yield buf.getvalue()
            buf.truncate(0)
            buf.seek(0)
            count = 0
    remaining = buf.getvalue()
    if remaining:
        yield remaining


class CSVStreamer:
    def stream(
        self,
        rows: Iterable[dict[str, Any]],
        columns: list[str],
        filename: str,
    ) -> StreamingResponse:
        return StreamingResponse(
            _csv_chunks(rows, columns),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
