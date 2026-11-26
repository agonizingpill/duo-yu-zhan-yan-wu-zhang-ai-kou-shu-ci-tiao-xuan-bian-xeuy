from src.audit import record
from src.errors import missing

TERM_INDEX = """
SELECT t.*, r.title AS source_title, r.expires_on, r.revoked_at
FROM cue_terms t JOIN source_rights r ON r.code=t.source_code
"""
SOURCE_INDEX = """
SELECT r.*, (SELECT count(*) FROM cue_terms t WHERE t.source_code=r.code) AS term_count
FROM source_rights r
"""


def source(db, code, *, lock=False):
    sql = "SELECT * FROM source_rights WHERE code=%s"
    row = db.execute(sql + (" FOR UPDATE" if lock else ""), (code,)).fetchone()
    if row is None:
        raise missing("许可", code)
    return row


def term(db, code):
    row = db.execute(TERM_INDEX + " WHERE t.code=%s", (code,)).fetchone()
    if row is None:
        raise missing("词条", code)
    return row


def add_source(db, form, actor):
    db.execute(
        """INSERT INTO source_rights (code,title,owner,document_ref,expires_on,allow_recording)
        VALUES (%(code)s,%(title)s,%(owner)s,%(document_ref)s,%(expires_on)s,%(allow_recording)s)""",
        form.model_dump(),
    )
    record(db, actor, "register_rights", form.code, document=form.document_ref)
    return db.execute(SOURCE_INDEX + " WHERE r.code=%s", (form.code,)).fetchone()


def revoke(db, code, actor):
    row = source(db, code, lock=True)
    if row["revoked_at"] is None:
        db.execute("UPDATE source_rights SET revoked_at=now() WHERE code=%s", (code,))
        record(db, actor, "revoke_rights", code)
    return db.execute(SOURCE_INDEX + " WHERE r.code=%s", (code,)).fetchone()


def add_term(db, form, actor):
    source(db, form.source_code)
    db.execute(
        """INSERT INTO cue_terms (code,source_code,language,show_cue,spoken_text,bridge_words)
        VALUES (%(code)s,%(source_code)s,%(language)s,%(show_cue)s,%(spoken_text)s,%(bridge_words)s)""",
        form.model_dump(),
    )
    record(db, actor, "register_term", form.code, source=form.source_code)
    return term(db, form.code)
