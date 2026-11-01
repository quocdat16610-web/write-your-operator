"""Text-to-speech: edge-tts (Vietnamese neural voices, online) or pyttsx3 (Windows SAPI voices, offline).

Every paragraph is synthesised to an audio file and cached, so a lesson read once with edge-tts can be
replayed without a network connection.
"""
from __future__ import annotations

import asyncio
import hashlib
import sys
from pathlib import Path

from core.paths import app_data_dir


EDGE_BITRATE = 48_000  # edge-tts always returns audio-24khz-48kbitrate-mono-mp3 (constant bitrate)


class SpeechError(Exception):
    """Raised with a Vietnamese message the UI can show directly."""


def cache_path(engine: str, voice: str, speed: float, text: str) -> Path:
    folder = app_data_dir() / "audio"
    folder.mkdir(exist_ok=True)
    key = hashlib.sha1(f"{engine}|{voice}|{speed}|{text}".encode("utf-8")).hexdigest()
    return folder / f"{key}.{'mp3' if engine == 'edge' else 'wav'}"


def audio_duration(path: Path) -> float | None:
    """Length of a cached clip in seconds, or None if unknown."""
    try:
        if path.suffix == ".mp3":
            return path.stat().st_size * 8 / EDGE_BITRATE
        if path.suffix == ".wav":
            import wave
            with wave.open(str(path), "rb") as clip:
                return clip.getnframes() / clip.getframerate()
    except Exception:  # unreadable clip: fall back to the player's own end detection
        return None
    return None


def edge_rate(speed: float) -> str:
    return f"{round((speed - 1) * 100):+d}%"


def synthesize_edge(text: str, voice: str, speed: float, path: Path) -> None:
    if sys.version_info[:3] < (3, 9, 2):
        # Python 3.9.0/3.9.1: typing bug makes aiohttp/edge-tts fail with "unhashable type: 'list'".
        raise SpeechError(
            f"Python {sys.version.split()[0]} trên máy bạn có lỗi làm edge-tts không chạy được.\n"
            "Cách sửa: cài Python 3.12 từ python.org, rồi bấm đúp run.bat (nó tự tạo lại môi trường).\n"
            "Tạm thời có thể chọn bộ đọc pyttsx3 trong Cài đặt."
        )
    try:
        import edge_tts
    except ImportError as exc:
        raise SpeechError("Chưa cài edge-tts. Chạy lại run.bat để cài.") from exc
    partial = path.with_suffix(".part")
    try:
        asyncio.run(edge_tts.Communicate(text, voice, rate=edge_rate(speed)).save(str(partial)))
    except Exception as exc:  # network, DNS, service changes: all end up here
        partial.unlink(missing_ok=True)
        raise SpeechError(
            "Không tạo được giọng đọc online (edge-tts). Kiểm tra kết nối Internet, "
            f"hoặc chọn bộ đọc pyttsx3 trong Cài đặt.\nChi tiết: {exc}"
        ) from exc
    partial.replace(path)


def _is_vietnamese(voice) -> bool:
    languages = " ".join(str(lang) for lang in (getattr(voice, "languages", None) or []))
    return "vi" in languages.lower() or "vietnam" in f"{voice.name} {voice.id}".lower()


class Pyttsx3Speaker:
    """Owns one pyttsx3 engine. Create and use it on a single thread (SAPI is a COM object)."""

    def __init__(self) -> None:
        try:
            import comtypes  # Windows only; COM must be initialised on every thread that uses SAPI
            comtypes.CoInitialize()
        except ImportError:
            pass
        try:
            import pyttsx3
            self.engine = pyttsx3.Engine()  # not pyttsx3.init(): that shares one engine across threads
        except Exception as exc:
            raise SpeechError(f"Không khởi động được giọng đọc Windows (pyttsx3): {exc}") from exc

    def synthesize(self, text: str, voice_id: str, speed: float, path: Path) -> None:
        voices = self.engine.getProperty("voices")
        chosen = voice_id or next((v.id for v in voices if _is_vietnamese(v)), "")
        if chosen:
            self.engine.setProperty("voice", chosen)
        self.engine.setProperty("rate", int(175 * speed))
        self.engine.save_to_file(text, str(path))
        self.engine.runAndWait()
        if not path.exists():
            raise SpeechError("pyttsx3 không tạo được file âm thanh.")


def list_pyttsx3_voices() -> list[tuple[str, str]]:
    """(voice id, label) for every installed Windows voice; Vietnamese ones are marked."""
    try:
        import pyttsx3
        engine = pyttsx3.Engine()
        voices = engine.getProperty("voices")
    except Exception:
        return []
    return [(v.id, f"{v.name}{'  (tiếng Việt)' if _is_vietnamese(v) else ''}") for v in voices]
