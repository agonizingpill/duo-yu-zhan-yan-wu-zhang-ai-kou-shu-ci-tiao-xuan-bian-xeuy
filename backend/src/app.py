import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from psycopg import OperationalError
from redis import RedisError

from scripts.seed_demo import seed
from src.auth import router as auth
from src.config import settings
from src.db import connect, migrate
from src.middlewares import no_store, trace
from src.queueing import client
from src.routes import candidates, catalogue, glossary

log = logging.getLogger("lexicon.app")


@asynccontextmanager
async def lifespan(app):
    migrate()
    if settings.seed_demo:
        try:
            seed()
        except Exception:
            log.exception("演示词条导入失败")
    yield


app = FastAPI(title="浮桥口述词页", lifespan=lifespan)
app.middleware("http")(trace)
app.middleware("http")(no_store)
for router in (auth, catalogue.router, candidates.router, glossary.router):
    app.include_router(router)


@app.exception_handler(RequestValidationError)
async def validation_error(request, error):
    issues = [{"field": ".".join(str(part) for part in issue["loc"][1:]),
               "message": issue["msg"]} for issue in error.errors()]
    return JSONResponse({"detail": {"message": "请检查表单字段", "fields": issues}}, status_code=422)


@app.get("/healthz")
def health():
    try:
        with connect() as db:
            db.execute("SELECT 1 FROM source_rights LIMIT 1")
        client.ping()
    except (OperationalError, RedisError):
        raise HTTPException(503, "词库暂不可用")
    return {"status": "healthy", "db": "connected", "redis": "connected"}
