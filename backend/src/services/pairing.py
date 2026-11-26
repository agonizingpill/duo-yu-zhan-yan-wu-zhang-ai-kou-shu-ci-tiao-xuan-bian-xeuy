from src.audit import record
from src.errors import conflict
from src.services.catalogue import term
from src.services.rights import hold_licenses, objection

ACTIVE_PAIRS = """
SELECT p.*, a.spoken_text AS origin_text, b.spoken_text AS target_text,
       a.source_code AS origin_license, b.source_code AS target_license,
       r.expires_on, r.revoked_at
FROM approved_pairs p JOIN cue_terms a ON a.code=p.origin_code
JOIN cue_terms b ON b.code=p.target_code JOIN source_rights r ON r.code=b.source_code
"""


def approve(db, form, actor):
    db.execute("SELECT code FROM cue_terms WHERE code=%s FOR UPDATE", (form.origin_code,))
    origin, target = term(db, form.origin_code), term(db, form.target_code)
    if not origin["active"] or not target["active"] or origin["language"] == target["language"]:
        raise conflict("invalid_pair", "原词与译词必须启用，且分属不同语种")
    if form.scan_id is not None:
        proposed = db.execute(
            """SELECT 1 FROM proposed_pairs p JOIN candidate_scans s ON s.id=p.scan_id
            WHERE s.status='ready' AND s.id=%s AND s.origin_code=%s AND p.target_code=%s""",
            (form.scan_id, form.origin_code, form.target_code),
        ).fetchone()
        if proposed is None:
            raise conflict("scan_mismatch", "该译词不属于指定原词的候选扫描")
    from datetime import date
    from src.enums import Channel

    rights = hold_licenses(db, [origin["source_code"], target["source_code"]])
    denied = [
        source_code for source_code, license in rights.items()
        if objection(license, date.today(), Channel.HEADSET)
    ]
    if denied:
        raise conflict("rights_inactive", "原词或译词的当前许可失效", sources=denied)
    previous = db.execute(
        """UPDATE approved_pairs SET status='superseded'
        WHERE origin_code=%s AND target_language=%s AND status='active' RETURNING id""",
        (form.origin_code, target["language"]),
    ).fetchone()
    row = db.execute(
        """INSERT INTO approved_pairs (origin_code,target_code,target_language,scan_id,note,approver)
        VALUES (%s,%s,%s,%s,%s,%s) RETURNING id""",
        (form.origin_code, form.target_code, target["language"], form.scan_id, form.note, actor),
    ).fetchone()
    record(db, actor, "approve_pair", form.origin_code,
           new_pair=row["id"], superseded=previous["id"] if previous else None)
    return db.execute(ACTIVE_PAIRS + " WHERE p.id=%s", (row["id"],)).fetchone()
