import os

from fastapi import Request
from fastapi.responses import Response, FileResponse

# Size of a partial response served when the client's Range header doesn't
# bound the end of the range (e.g. "bytes=0-") — browsers follow up with
# further ranged requests as needed, so we don't need to load the whole file.
_CHUNK_SIZE = 1024 * 1024


def range_response(request: Request, file_path: str, media_type: str) -> Response:
    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("range")
    if not range_header:
        return FileResponse(file_path, media_type=media_type)

    try:
        _, _, range_spec = range_header.partition("=")
        start_str, _, end_str = range_spec.partition("-")
        start = int(start_str) if start_str else 0
        end = min(int(end_str), file_size - 1) if end_str else min(start + _CHUNK_SIZE - 1, file_size - 1)
    except ValueError:
        start, end = 0, min(_CHUNK_SIZE - 1, file_size - 1)

    if start >= file_size or start > end:
        return Response(status_code=416, headers={"Content-Range": f"bytes */{file_size}"})

    length = end - start + 1
    with open(file_path, "rb") as f:
        f.seek(start)
        chunk = f.read(length)

    return Response(
        content=chunk,
        status_code=206,
        media_type=media_type,
        headers={
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(length),
        },
    )
