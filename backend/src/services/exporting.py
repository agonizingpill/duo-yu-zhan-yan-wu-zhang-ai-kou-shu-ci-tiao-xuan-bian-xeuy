import csv
from io import StringIO

from src.errors import conflict
from src.services.glossary import detail


def export_cell(value):
    text = str(value)
    if text.lstrip().startswith(("=", "+", "-", "@")) or text.startswith(("\t", "\r", "\n")):
        return "'" + text
    return text


def csv_text(db, code):
    edition = detail(db, code)
    if edition["status"] != "published":
        raise conflict("not_published", "词单发布后才可下载")
    stream = StringIO()
    writer = csv.writer(stream)
    writer.writerow(["顺序", "舞台提示", "原口述", "目标口述", "许可文件"])
    for cue in edition["cues"]:
        writer.writerow([export_cell(cue[key]) for key in (
            "position", "show_cue", "origin_snapshot", "target_snapshot", "license_snapshot"
        )])
    return "\ufeff" + stream.getvalue()
