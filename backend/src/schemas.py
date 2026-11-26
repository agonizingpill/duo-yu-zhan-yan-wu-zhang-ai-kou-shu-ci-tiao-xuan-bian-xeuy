from datetime import date
from typing import Annotated
from unicodedata import normalize

from pydantic import BaseModel, Field, StringConstraints, field_validator

from src.enums import Channel, Language

Code = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^[A-Z][A-Z0-9-]{1,23}$")]
Brief = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)]


class SourceIn(BaseModel):
    code: Code
    title: Brief
    owner: Brief
    document_ref: Brief
    expires_on: date
    allow_recording: bool = False


class TermIn(BaseModel):
    code: Code
    source_code: Code
    language: Language
    show_cue: Brief
    spoken_text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=240)]
    bridge_words: Brief

    @field_validator("bridge_words", "spoken_text")
    @classmethod
    def require_readable(cls, value):
        value = normalize("NFKC", value).strip()
        if not any(character.isalnum() for character in value):
            raise ValueError("至少包含一个字母、汉字或数字")
        return value


class ScanIn(BaseModel):
    origin_code: Code
    target_language: Language


class PairIn(BaseModel):
    origin_code: Code
    target_code: Code
    scan_id: int | None = Field(default=None, gt=0)
    note: Brief


class EditionIn(BaseModel):
    code: Code
    show_title: Brief
    show_date: date
    target_language: Language
    channel: Channel


class CueOrderIn(BaseModel):
    origin_codes: list[Code] = Field(min_length=1, max_length=30)

    @field_validator("origin_codes")
    @classmethod
    def no_duplicates(cls, codes):
        if len(codes) != len(set(codes)):
            raise ValueError("同一原词只能在一份口述词单出现一次")
        return codes
