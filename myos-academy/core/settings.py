"""User preferences, persisted in the settings table."""
from __future__ import annotations

from dataclasses import dataclass, fields

from data.database import Database

TTS_ENGINES = {
    "edge": "edge-tts (giọng tiếng Việt, cần mạng)",
    "pyttsx3": "pyttsx3 (giọng Windows, offline)",
}
EDGE_VOICES = {
    "vi-VN-HoaiMyNeural": "Hoài My (nữ)",
    "vi-VN-NamMinhNeural": "Nam Minh (nam)",
}

SPEEDS = {"0.75": "0.75×", "1.0": "1×", "1.25": "1.25×", "1.5": "1.5×"}

THEMES = {"system": "Theo hệ thống", "light": "Sáng", "dark": "Tối"}


@dataclass
class AppSettings:
    tts_engine: str = "edge"
    edge_voice: str = "vi-VN-HoaiMyNeural"
    pyttsx3_voice: str = ""
    speech_speed: str = "1.0"
    font_size: int = 11
    theme: str = "system"

    @classmethod
    def load(cls, db: Database) -> "AppSettings":
        result = cls()
        for field in fields(cls):
            raw = db.get_setting(field.name)
            if raw is None:
                continue
            default = getattr(result, field.name)
            try:
                value = int(raw) if isinstance(default, int) else raw
            except ValueError:
                continue
            setattr(result, field.name, value)
        return result

    def save(self, db: Database) -> None:
        for field in fields(self):
            db.set_setting(field.name, str(getattr(self, field.name)))
