from src.audit import recent_for, record
from src.errors import conflict, missing
from src.services.catalogue import term
from src.services.rights import hold_licenses, objection

EDITION_INDEX = """
SELECT e.*, (SELECT count(*) FROM glossary_cues c WHERE c.edition_code=e.code) AS cue_count
FROM glossary_editions e
"""
EDITION_CUES = """
SELECT c.*, o.spoken_text AS origin_text, o.show_cue, o.source_code AS origin_license,
    p.id AS current_pair_id, t.code AS target_code, t.spoken_text AS target_text,
    t.source_code AS target_license
FROM glossary_cues c JOIN cue_terms o ON o.code=c.origin_code
LEFT JOIN approved_pairs p ON (c.pair_id IS NOT NULL AND c.pair_id=p.id)
    OR (c.pair_id IS NULL AND p.origin_code=c.origin_code AND p.target_language=%s AND p.status='active')
LEFT JOIN cue_terms t ON t.code=p.target_code
WHERE c.edition_code=%s ORDER BY c.position
"""


def get_edition(db, code, *, lock=False):
    row = db.execute(
        EDITION_INDEX + " WHERE e.code=%s" + (" FOR UPDATE OF e" if lock else ""),
        (code,),
    ).fetchone()
    if row is None:
        raise missing("词单", code)
    return row


def create(db, form, actor):
    db.execute(
        """INSERT INTO glossary_editions (code,show_title,show_date,target_language,channel)
        VALUES (%(code)s,%(show_title)s,%(show_date)s,%(target_language)s,%(channel)s)""",
        form.model_dump(),
    )
    record(db, actor, "open_edition", form.code, channel=form.channel)
    return get_edition(db, form.code)


def require_draft(edition):
    if edition["status"] != "draft":
        raise conflict("edition_frozen", "已发布词单已冻结，请另建版本")


def arrange(db, code, form, actor):
    edition = get_edition(db, code, lock=True)
    require_draft(edition)
    for origin_code in form.origin_codes:
        origin = term(db, origin_code)
        if not origin["active"] or origin["language"] == edition["target_language"]:
            raise conflict("invalid_origin", f"{origin_code} 不可作为此词单的原词")
    db.execute("DELETE FROM glossary_cues WHERE edition_code=%s", (code,))
    with db.cursor() as cursor:
        cursor.executemany(
            "INSERT INTO glossary_cues (edition_code,position,origin_code) VALUES (%s,%s,%s)",
            ((code, position, item) for position, item in enumerate(form.origin_codes, 1)),
        )
    record(db, actor, "arrange_cues", code, origins=form.origin_codes)
    return detail(db, code)


def alternatives(db, edition, cue, origin_license):
    if objection(origin_license, edition["show_date"], edition["channel"]):
        return []
    options = db.execute(
        """SELECT DISTINCT ON (t.code) t.code,t.spoken_text,p.similarity,p.scan_id,r.expires_on,r.revoked_at,r.allow_recording
        FROM candidate_scans s JOIN proposed_pairs p ON p.scan_id=s.id
        JOIN cue_terms t ON t.code=p.target_code JOIN source_rights r ON r.code=t.source_code
        WHERE s.origin_code=%s AND s.target_language=%s AND s.status='ready' AND t.active
          AND (%s::text IS NULL OR t.code<>%s)
        ORDER BY t.code,s.id DESC""",
        (cue["origin_code"], edition["target_language"], cue["target_code"], cue["target_code"]),
    ).fetchall()
    return [
        {"code": row["code"], "spoken_text": row["spoken_text"], "similarity": row["similarity"],
         "scan_id": row["scan_id"]}
        for row in sorted(options, key=lambda row: -row["similarity"])
        if not objection(row, edition["show_date"], edition["channel"])
    ][:3]


def inspect_cues(db, edition, cues):
    codes = [cue[key] for cue in cues for key in ("origin_license", "target_license") if cue[key]]
    rights = hold_licenses(db, codes)
    blocked = []
    for cue in cues:
        problems = []
        if cue["current_pair_id"] is None:
            problems.append("缺少已审核目标语映射")
        for key in ("origin_license", "target_license"):
            if cue[key] is None:
                continue
            if reason := objection(rights[cue[key]], edition["show_date"], edition["channel"]):
                problems.append(f"{cue[key]} · {reason}")
        if problems:
            blocked.append({"origin_code": cue["origin_code"], "target_code": cue["target_code"],
                            "reasons": problems,
                            "alternatives": alternatives(db, edition, cue, rights[cue["origin_license"]])})
    return blocked


def detail(db, code):
    edition = get_edition(db, code)
    cues = db.execute(EDITION_CUES, (edition["target_language"], code)).fetchall()
    if edition["status"] == "published":
        for cue in cues:
            cue["origin_text"] = cue["origin_snapshot"]
            cue["target_text"] = cue["target_snapshot"]
    return edition | {
        "cues": cues,
        "blocked": inspect_cues(db, edition, cues) if edition["status"] == "draft" else [],
        "history": recent_for(db, code),
    }


def publish(db, code, actor):
    edition = get_edition(db, code, lock=True)
    require_draft(edition)
    db.execute(
        """SELECT t.code FROM cue_terms t JOIN glossary_cues c ON c.origin_code=t.code
        WHERE c.edition_code=%s ORDER BY t.code FOR SHARE OF t""", (code,)
    ).fetchall()
    rows = db.execute(EDITION_CUES, (edition["target_language"], code)).fetchall()
    if not rows:
        raise conflict("empty_edition", "请安排至少一个要口述的词条")
    if blocked := inspect_cues(db, edition, rows):
        raise conflict("glossary_blocked", "词单有待补审或失效许可", blocked=blocked)
    with db.cursor() as cursor:
        cursor.executemany(
            """UPDATE glossary_cues SET pair_id=%s,origin_snapshot=%s,target_snapshot=%s,license_snapshot=%s
            WHERE edition_code=%s AND position=%s""",
            ((row["current_pair_id"], row["origin_text"], row["target_text"],
              row["origin_license"] + " / " + row["target_license"], code, row["position"])
             for row in rows),
        )
    db.execute(
        """UPDATE glossary_editions SET status='published',published_by=%s,published_at=now()
        WHERE code=%s""", (actor, code)
    )
    record(db, actor, "publish_edition", code, count=len(rows))
    return detail(db, code)
