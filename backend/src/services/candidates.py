from src.audit import record
from src.errors import conflict, missing
from src.services.catalogue import term
from src.services.embedding import rank_candidates


def queue_scan(db, form, actor):
    origin = term(db, form.origin_code)
    if not origin["active"] or origin["language"] == form.target_language:
        raise conflict("invalid_languages", "请选择启用的原词以及不同的目标语种")
    row = db.execute(
        """INSERT INTO candidate_scans (origin_code,target_language) VALUES (%s,%s)
        ON CONFLICT (origin_code,target_language) WHERE status='queued' DO NOTHING RETURNING *""",
        (form.origin_code, form.target_language),
    ).fetchone()
    if row:
        record(db, actor, "queue_candidate_scan", row["id"], origin=form.origin_code)
        return row
    return db.execute(
        "SELECT * FROM candidate_scans WHERE origin_code=%s AND target_language=%s ORDER BY id DESC LIMIT 1",
        (form.origin_code, form.target_language),
    ).fetchone()


def scan_detail(db, scan_id):
    scan = db.execute("SELECT * FROM candidate_scans WHERE id=%s", (scan_id,)).fetchone()
    if scan is None:
        raise missing("候选扫描", scan_id)
    scan["origin"] = term(db, scan["origin_code"])
    scan["pairs"] = db.execute(
        """SELECT p.*, t.spoken_text, t.show_cue, t.source_code, r.expires_on, r.revoked_at
        FROM proposed_pairs p JOIN cue_terms t ON t.code=p.target_code
        JOIN source_rights r ON r.code=t.source_code WHERE p.scan_id=%s ORDER BY p.rank""",
        (scan_id,),
    ).fetchall()
    return scan


def calculate_one(db):
    scan = db.execute(
        "SELECT * FROM candidate_scans WHERE status='queued' ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED"
    ).fetchone()
    if scan is None:
        return False
    origin = term(db, scan["origin_code"])
    targets = db.execute(
        "SELECT * FROM cue_terms WHERE language=%s AND active ORDER BY code", (scan["target_language"],)
    ).fetchall()
    try:
        ranking, metrics = rank_candidates(origin, targets)
    except ValueError as error:
        db.execute(
            "UPDATE candidate_scans SET status='failed',error=%s,completed_at=now() WHERE id=%s",
            (str(error), scan["id"]),
        )
        return True
    with db.cursor() as cursor:
        cursor.executemany(
            "INSERT INTO proposed_pairs (scan_id,target_code,rank,similarity) VALUES (%s,%s,%s,%s)",
            ((scan["id"], code, rank, score) for rank, (code, score) in enumerate(ranking, 1)),
        )
    db.execute(
        """UPDATE candidate_scans
        SET status='ready',dimensions=%(dimensions)s,vocabulary_size=%(vocabulary_size)s,
        explained_variance=%(explained_variance)s,fingerprint=%(fingerprint)s,completed_at=now()
        WHERE id=%(id)s""",
        metrics | {"id": scan["id"]},
    )
    record(db, "worker", "rank_candidates", scan["id"], proposals=len(ranking), **metrics)
    return True
