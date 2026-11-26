from psycopg.types.json import Jsonb


def record(db, actor, event, key, **detail):
    db.execute(
        "INSERT INTO change_ledger (actor,operation,entity_key,detail) VALUES (%s,%s,%s,%s)",
        (actor, event, str(key), Jsonb(detail)),
    )


def recent_for(db, code):
    return db.execute(
        "SELECT event_time,actor,operation,detail FROM change_ledger WHERE entity_key=%s "
        "ORDER BY id DESC LIMIT 12", (code,)
    ).fetchall()
