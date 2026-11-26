from fastapi import APIRouter, Depends

from src.auth import allow, current
from src.db import connect
from src.enums import Role
from src.queueing import wake
from src.schemas import PairIn, ScanIn
from src.services.candidates import queue_scan, scan_detail
from src.services.pairing import ACTIVE_PAIRS, approve

router = APIRouter(prefix="/matching", tags=["候选词与语种映射"])


@router.get("/scans")
def scans(user=Depends(current)):
    with connect() as db:
        return db.execute("SELECT * FROM candidate_scans ORDER BY id DESC LIMIT 50").fetchall()


@router.post("/scans", status_code=202)
def create_scan(form: ScanIn, user=Depends(allow(Role.EDITOR, Role.REVIEWER))):
    with connect() as db:
        scan = queue_scan(db, form, user["username"])
    wake(scan["id"])
    return scan


@router.get("/scans/{scan_id}")
def scan(scan_id: int, user=Depends(current)):
    with connect() as db:
        return scan_detail(db, scan_id)


@router.get("/pairs")
def pairs(origin_code: str | None = None, user=Depends(current)):
    with connect() as db:
        return db.execute(
            ACTIVE_PAIRS + " WHERE (%s::text IS NULL OR p.origin_code=%s) ORDER BY p.id DESC",
            (origin_code, origin_code),
        ).fetchall()


@router.post("/pairs", status_code=201)
def approve_pair(form: PairIn, user=Depends(allow(Role.REVIEWER))):
    with connect() as db:
        return approve(db, form, user["username"])
