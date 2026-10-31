"""Run blocking work (e.g. text-to-speech) on a background QThread so the UI never freezes."""
from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import QObject, QThread, Signal, Slot


class _Registry(QObject):
    """Holds Python references to running threads/workers; lives on the UI thread."""

    def __init__(self) -> None:
        super().__init__()
        self.active: list[tuple[QThread, QObject]] = []

    @Slot()
    def sweep(self) -> None:
        self.active = [(t, w) for t, w in self.active if not t.isFinished()]


_registry: _Registry | None = None


def _get_registry() -> _Registry:
    global _registry
    if _registry is None:
        _registry = _Registry()
    return _registry


class Worker(QObject):
    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, fn: Callable[..., Any], *args: Any) -> None:
        super().__init__()
        self._fn = fn
        self._args = args

    @Slot()
    def run(self) -> None:
        try:
            result = self._fn(*self._args)
        except Exception as exc:  # report every failure to the UI instead of crashing
            self.failed.emit(str(exc))
        else:
            self.succeeded.emit(result)


def run_in_background(
    fn: Callable[..., Any],
    *args: Any,
    on_success: Callable[[Any], None],
    on_error: Callable[[str], None],
) -> QThread:
    """Call fn(*args) on a new thread. Callbacks must be methods of a QObject (they run on the UI thread)."""
    thread = QThread()
    worker = Worker(fn, *args)
    worker.moveToThread(thread)

    thread.started.connect(worker.run)
    worker.succeeded.connect(on_success)
    worker.failed.connect(on_error)
    worker.succeeded.connect(thread.quit)
    worker.failed.connect(thread.quit)

    registry = _get_registry()
    registry.active.append((thread, worker))
    thread.finished.connect(registry.sweep)

    thread.start()
    return thread


def wait_for_all(timeout_ms: int = 3000) -> None:
    """Called on app exit so no thread is destroyed while still running."""
    for thread, _ in list(_get_registry().active):
        thread.quit()
        thread.wait(timeout_ms)
