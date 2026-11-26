from datetime import date, datetime

from pydantic import BaseModel

from src.enums import Channel, Language


class SourceView(BaseModel):
    code: str
    title: str
    owner: str
    document_ref: str
    expires_on: date
    allow_recording: bool
    revoked_at: datetime | None
    term_count: int


class TermView(BaseModel):
    code: str
    source_code: str
    source_title: str
    language: Language
    show_cue: str
    spoken_text: str
    bridge_words: str
    active: bool
    expires_on: date
    revoked_at: datetime | None


class EditionView(BaseModel):
    code: str
    show_title: str
    show_date: date
    target_language: Language
    channel: Channel
    status: str
    published_at: datetime | None
    published_by: str | None
    cue_count: int
