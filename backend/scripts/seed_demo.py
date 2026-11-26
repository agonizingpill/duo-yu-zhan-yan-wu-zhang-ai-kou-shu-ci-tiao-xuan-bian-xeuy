import json

from scripts.seed_data import SOURCES, TERMS
from src.db import connect, migrate


def seed():
    with connect() as db:
        db.execute("SELECT pg_advisory_xact_lock(107801)")
        with db.cursor() as cursor:
            cursor.executemany(
                """INSERT INTO source_rights (code,title,owner,document_ref,expires_on,allow_recording)
                VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (code) DO NOTHING""", SOURCES
            )
            cursor.executemany(
                """INSERT INTO cue_terms (code,source_code,language,show_cue,spoken_text,bridge_words)
                VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (code) DO NOTHING""", TERMS
            )
        db.execute(
            """INSERT INTO glossary_editions (code,show_title,show_date,target_language,channel)
            VALUES ('FB-WINTER','灯下潮汐 · 冬季展演','2026-12-18','en','recording')
            ON CONFLICT (code) DO NOTHING"""
        )
        db.execute(
            """INSERT INTO glossary_cues (edition_code,position,origin_code)
            SELECT 'FB-WINTER', sample.position, sample.code
            FROM (VALUES (1,'ZH-WATER'),(2,'ZH-LANTERN')) AS sample(position,code)
            WHERE NOT EXISTS (SELECT 1 FROM glossary_cues WHERE edition_code='FB-WINTER')
            ON CONFLICT DO NOTHING"""
        )
        db.execute(
            """INSERT INTO approved_pairs (origin_code,target_code,target_language,note,approver)
            SELECT sample.origin_code,sample.target_code,'en','上次走台复核','seed'
            FROM (VALUES ('ZH-WATER','EN-WATER-OLD'),('ZH-LANTERN','EN-LANTERN'))
            AS sample(origin_code,target_code)
            WHERE NOT EXISTS (SELECT 1 FROM approved_pairs p WHERE p.origin_code=sample.origin_code AND p.target_language='en')
            """
        )
        return db.execute(
            """SELECT (SELECT count(*) FROM source_rights) AS sources,
            (SELECT count(*) FROM cue_terms) AS terms,(SELECT count(*) FROM glossary_editions) AS editions,
            (SELECT count(*) FROM glossary_cues) AS cue_slots,(SELECT count(*) FROM approved_pairs) AS mappings"""
        ).fetchone()


if __name__ == "__main__":
    migrate()
    print(json.dumps(seed(), sort_keys=True, ensure_ascii=False))
