"""Play one audio file at a time.

PySide6-Essentials has no QtMultimedia, so on Windows we use MCI (winmm.dll, part of every Windows),
which plays both mp3 and wav. Elsewhere (development on Linux/macOS) a command-line player is used if
one is installed.
"""
from __future__ import annotations

import shutil
import sys

from PySide6.QtCore import QObject, QProcess, QTimer, Signal

from core.tts import SpeechError

ALIAS = "myos_tts"


def _mci(command: str) -> str:
    import ctypes

    winmm = ctypes.windll.winmm
    buffer = ctypes.create_unicode_buffer(256)
    error = winmm.mciSendStringW(command, buffer, 255, 0)
    if error:
        message = ctypes.create_unicode_buffer(256)
        winmm.mciGetErrorStringW(error, message, 255)
        raise SpeechError(f"Lỗi phát âm thanh (MCI): {message.value}")
    return buffer.value


class AudioPlayer(QObject):
    finished = Signal()  # the file played to the end (not emitted by stop())

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._windows = sys.platform == "win32"
        self._open = False
        self._timer = QTimer(self)
        self._timer.setInterval(150)
        self._timer.timeout.connect(self._poll)
        self._process: QProcess | None = None

    def play(self, path: str) -> None:
        self.stop()
        if self._windows:
            _mci(f'open "{path}" type mpegvideo alias {ALIAS}')
            self._open = True
            _mci(f"play {ALIAS}")
            self._timer.start()
            return
        player = shutil.which("ffplay") or shutil.which("mpg123") or shutil.which("paplay")
        if player is None:
            QTimer.singleShot(1000, self.finished.emit)  # nothing to play with: just move on
            return
        args = ["-nodisp", "-autoexit", "-loglevel", "quiet", path] if player.endswith("ffplay") else [path]
        self._process = QProcess(self)
        self._process.finished.connect(self._on_process_finished)
        self._process.start(player, args)

    def stop(self) -> None:
        self._timer.stop()
        if self._open:
            try:
                _mci(f"close {ALIAS}")
            except SpeechError:
                pass
            self._open = False
        if self._process is not None:
            process, self._process = self._process, None
            process.finished.disconnect(self._on_process_finished)
            process.kill()
            process.waitForFinished(1000)

    def _poll(self) -> None:
        try:
            mode = _mci(f"status {ALIAS} mode")
        except SpeechError:
            mode = "stopped"
        if mode == "stopped":
            self.stop()
            self.finished.emit()

    def _on_process_finished(self) -> None:
        self._process = None
        self.finished.emit()
