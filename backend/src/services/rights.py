from datetime import date

from src.enums import Channel


def hold_licenses(db, codes):
    return {
        row["code"]: row
        for row in db.execute(
            "SELECT * FROM source_rights WHERE code=ANY(%s) ORDER BY code FOR SHARE",
            (list(set(codes)),),
        ).fetchall()
    }


def objection(source, event_date, channel):
    if source["revoked_at"] is not None:
        return "许可已撤销"
    if source["expires_on"] < max(event_date, date.today()):
        return f"许可于 {source['expires_on'].isoformat()} 到期，无法覆盖演出日期"
    if channel == Channel.RECORDING and not source["allow_recording"]:
        return "许可仅覆盖现场耳机口述，不能用于回放录制"
    return None
