"""Read a list of paragraphs aloud: synthesise on a background thread, play on the UI thread.

The next paragraph is synthesised while the current one plays, so there is no gap between them.
Each start/stop bumps a generation number; results from an older generation are ignored.
"""
from __future__ import annotations

import queue
import threading
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal

from core import tts
from core.settings import AppSettings
from core.speech_text import Segment
from ui.audio_player import AudioPlayer

PREFETCH = 3  # paragraphs synthesised ahead of the one playing


@dataclass(frozen=True)
class _Job:
    generation: int
    index: int
    text: str
    engine: str
    voice: str
    speed: float


class _Bridge(QObject):
    """Created on the UI thread; signals emitted from the worker thread arrive there queued."""

    ready = Signal(int, int, str)  # generation, index, audio path
    failed = Signal(int, str)  # generation, message


class _SynthThread(threading.Thread):
    def __init__(self, bridge: _Bridge, current_generation) -> None:
        super().__init__(name="tts", daemon=True)  # daemon: never blocks closing the app
        self.jobs: queue.Queue[_Job] = queue.Queue()
        self.bridge = bridge
        self.current_generation = current_generation
        self._pyttsx3: tts.Pyttsx3Speaker | None = None

    def run(self) -> None:
        while True:
            job = self.jobs.get()
            if job.generation != self.current_generation():
                continue  # the user stopped or restarted: skip stale work
            try:
                path = tts.cache_path(job.engine, job.voice, job.speed, job.text)
                if not path.exists():
                    if job.engine == "edge":
                        tts.synthesize_edge(job.text, job.voice, job.speed, path)
                    else:
                        if self._pyttsx3 is None:
                            self._pyttsx3 = tts.Pyttsx3Speaker()
                        self._pyttsx3.synthesize(job.text, job.voice, job.speed, path)
            except Exception as exc:  # anything at all: the loop must keep running
                self.bridge.failed.emit(job.generation, str(exc) or repr(exc))
                continue
            self.bridge.ready.emit(job.generation, job.index, str(path))


class ReadAloudController(QObject):
    segment_started = Signal(int)
    buffering = Signal(int)  # waiting for paragraph <index> to finish downloading
    stopped = Signal()  # finished the list, or stop() was called
    error = Signal(str)

    def __init__(self, settings: AppSettings, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.generation = 0
        self.segments: list[Segment] = []
        self.index = -1
        self.speed = 1.0
        self._paths: dict[int, str] = {}
        self._requested: set[int] = set()
        self._playing = False

        self._bridge = _Bridge(self)
        self._bridge.ready.connect(self._on_ready)
        self._bridge.failed.connect(self._on_failed)
        self._thread = _SynthThread(self._bridge, lambda: self.generation)
        self._thread.start()
        self.player = AudioPlayer(self)
        self.player.finished.connect(self._on_played)

    @property
    def active(self) -> bool:
        return self.index >= 0

    def start(self, segments: list[Segment], speed: float, start_index: int = 0) -> None:
        self._reset()
        if not segments:
            self.stopped.emit()
            return
        self.segments, self.speed, self.index = segments, speed, start_index
        self._request_ahead()

    def set_speed(self, speed: float) -> None:
        """Restart the current paragraph at the new speed."""
        if self.active:
            self.start(self.segments, speed, self.index)
        self.speed = speed

    def stop(self) -> None:
        was_active = self.active
        self._reset()
        if was_active:
            self.stopped.emit()

    def _reset(self) -> None:
        self.generation += 1
        self.player.stop()
        self._playing = False
        self.index = -1
        self._paths.clear()
        self._requested.clear()

    def _voice(self) -> str:
        return self.settings.edge_voice if self.settings.tts_engine == "edge" else self.settings.pyttsx3_voice

    def _request_ahead(self) -> None:
        for index in range(self.index, min(self.index + PREFETCH + 1, len(self.segments))):
            if index not in self._requested:
                self._requested.add(index)
                self._thread.jobs.put(_Job(self.generation, index, self.segments[index].spoken,
                                           self.settings.tts_engine, self._voice(), self.speed))

    def _on_ready(self, generation: int, index: int, path: str) -> None:
        if generation != self.generation:
            return
        self._paths[index] = path
        if index == self.index and not self._playing:
            self._play_current()

    def _play_current(self) -> None:
        self._playing = True
        self.segment_started.emit(self.index)
        try:
            self.player.play(self._paths[self.index])
        except tts.SpeechError as exc:
            self.error.emit(str(exc))
            self.stop()
            return
        self._request_ahead()

    def _on_played(self) -> None:
        self._playing = False
        self.index += 1
        if self.index >= len(self.segments):
            self.stop()
        elif self.index in self._paths:
            self._play_current()
        else:
            self.buffering.emit(self.index)
            self._request_ahead()  # wait for _on_ready

    def _on_failed(self, generation: int, message: str) -> None:
        if generation == self.generation:
            self.error.emit(message)
            self.stop()
