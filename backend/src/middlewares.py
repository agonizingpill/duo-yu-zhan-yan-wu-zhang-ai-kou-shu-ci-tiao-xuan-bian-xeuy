import logging
from time import monotonic
from uuid import uuid4

from fastapi.responses import JSONResponse

log = logging.getLogger("lexicon.requests")


async def trace(request, call_next):
    started = monotonic()
    request_id = uuid4().hex[:14]
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    log.info("%s %s %s %s %.3fs", request_id, request.method, request.url.path,
             response.status_code, monotonic() - started)
    return response


async def no_store(request, call_next):
    if request.headers.get("content-length", "0").isdigit() and int(request.headers.get("content-length", "0")) > 64_000:
        return JSONResponse({"detail": "当前提交超过 64 KB"}, status_code=413)
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response
