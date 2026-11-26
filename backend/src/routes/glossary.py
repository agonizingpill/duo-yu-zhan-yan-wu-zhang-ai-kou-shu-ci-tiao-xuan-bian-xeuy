from fastapi import APIRouter, Depends
from fastapi.responses import Response
from psycopg.errors import UniqueViolation

from src.auth import allow, current
from src.db import connect
from src.enums import Role
from src.errors import conflict
from src.read_models import EditionView
from src.schemas import CueOrderIn, EditionIn
from src.services import glossary
from src.services.exporting import csv_text

router = APIRouter(prefix="/glossaries", tags=["演出词单"])


@router.get("", response_model=list[EditionView])
def list_editions(user=Depends(current)):
    with connect() as db:
        return db.execute(glossary.EDITION_INDEX + " ORDER BY e.show_date,e.code").fetchall()


@router.post("", status_code=201, response_model=EditionView)
def create_edition(form: EditionIn, user=Depends(allow(Role.EDITOR))):
    try:
        with connect() as db:
            return glossary.create(db, form, user["username"])
    except UniqueViolation:
        raise conflict("duplicate_edition", "词单编号已使用")


@router.get("/{code}")
def edition_detail(code: str, user=Depends(current)):
    with connect() as db:
        return glossary.detail(db, code)


@router.put("/{code}/order")
def put_order(code: str, form: CueOrderIn, user=Depends(allow(Role.EDITOR))):
    with connect() as db:
        return glossary.arrange(db, code, form, user["username"])


@router.post("/{code}/publish")
def publish_edition(code: str, user=Depends(allow(Role.REVIEWER))):
    with connect() as db:
        return glossary.publish(db, code, user["username"])


@router.get("/{code}/export")
def edition_csv(code: str, user=Depends(current)):
    with connect() as db:
        content = csv_text(db, code)
    return Response(content, media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="{code}.csv"'})
