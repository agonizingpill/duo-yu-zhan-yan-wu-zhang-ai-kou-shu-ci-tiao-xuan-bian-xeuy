from enum import StrEnum


class Role(StrEnum):
    EDITOR = "editor"
    REVIEWER = "reviewer"
    READER = "reader"


class Language(StrEnum):
    ZH = "zh"
    EN = "en"
    JA = "ja"


class Channel(StrEnum):
    HEADSET = "headset"
    RECORDING = "recording"
