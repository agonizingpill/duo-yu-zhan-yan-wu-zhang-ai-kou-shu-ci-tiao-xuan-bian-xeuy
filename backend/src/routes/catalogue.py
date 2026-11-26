from fastapi import APIRouter, Depends
from psycopg.errors import UniqueViolation

from src.auth import allow, current
from src.db import connect
from src.enums import Language, Role
from src.errors import conflict
from src.read_models import SourceView, TermView
from src.schemas import SourceIn, TermIn
from src.services import catalogue

router = APIRouter(prefix="/catalogue", tags=["词库许可"])


@router.get("/sources", response_model=list[SourceView])
def sources(user=Depends(current)):
    with connect() as db:
        return db.execute(catalogue.SOURCE_INDEX + " ORDER BY r.code").fetchall()


@router.post("/sources", status_code=201, response_model=SourceView)
def create_source(form: SourceIn, user=Depends(allow(Role.EDITOR))):
    try:
        with connect() as db:
            return catalogue.add_source(db, form, user["username"])
    except UniqueViolation:
        raise conflict("duplicate_rights", "许可编号或授权凭证已登记")


@router.post("/sources/{code}/revoke", response_model=SourceView)
def revoke_source(code: str, user=Depends(allow(Role.REVIEWER))):
    with connect() as db:
        return catalogue.revoke(db, code, user["username"])


@router.get("/terms", response_model=list[TermView])
def terms(language: Language | None = None, user=Depends(current)):
    with connect() as db:
        return db.execute(
            catalogue.TERM_INDEX + " WHERE (%s::text IS NULL OR t.language=%s) ORDER BY t.code",
            (language, language),
        ).fetchall()


@router.post("/terms", status_code=201, response_model=TermView)
def create_term(form: TermIn, user=Depends(allow(Role.EDITOR))):
    try:
        with connect() as db:
            return catalogue.add_term(db, form, user["username"])
    except UniqueViolation:
        raise conflict("duplicate_term", "该编号或来源下的相同口述已登记")
