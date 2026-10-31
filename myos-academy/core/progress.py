"""Lesson status (not started / in progress / done) and sequential unlocking."""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from core.roadmap import ALL_LESSONS, Lesson, previous_lesson
from data.database import Database


class Status(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    DONE = "done"


STATUS_LABELS = {
    Status.NOT_STARTED: "Chưa học",
    Status.IN_PROGRESS: "Đang học",
    Status.DONE: "Xong",
}


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class ProgressStore:
    def __init__(self, db: Database) -> None:
        self.conn = db.conn

    def _row(self, lesson_id: str):
        return self.conn.execute(
            "SELECT status, manually_unlocked FROM lesson_progress WHERE lesson_id = ?", (lesson_id,)
        ).fetchone()

    def status(self, lesson_id: str) -> Status:
        row = self._row(lesson_id)
        return Status(row["status"]) if row else Status.NOT_STARTED

    def set_status(self, lesson_id: str, status: Status) -> None:
        now = _now()
        started = now if status != Status.NOT_STARTED else None
        completed = now if status == Status.DONE else None
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO lesson_progress (lesson_id, status, started_at, completed_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(lesson_id) DO UPDATE SET
                    status       = excluded.status,
                    started_at   = COALESCE(lesson_progress.started_at, excluded.started_at),
                    completed_at = excluded.completed_at,
                    updated_at   = excluded.updated_at
                """,
                (lesson_id, status.value, started, completed, now),
            )

    def unlock(self, lesson_id: str) -> None:
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO lesson_progress (lesson_id, manually_unlocked, updated_at) VALUES (?, 1, ?)
                ON CONFLICT(lesson_id) DO UPDATE SET manually_unlocked = 1, updated_at = excluded.updated_at
                """,
                (lesson_id, _now()),
            )

    def is_unlocked(self, lesson_id: str) -> bool:
        """Open if it is the first lesson, was unlocked by hand, was already started, or the previous one is done."""
        previous = previous_lesson(lesson_id)
        if previous is None:
            return True
        row = self._row(lesson_id)
        if row and (row["manually_unlocked"] or row["status"] != Status.NOT_STARTED):
            return True
        return self.status(previous.id) == Status.DONE

    def done_count(self, lessons: tuple[Lesson, ...] = ALL_LESSONS) -> int:
        return sum(1 for lesson in lessons if self.status(lesson.id) == Status.DONE)

    def current_lesson(self) -> Lesson:
        """First lesson that is not done yet (the one to study next)."""
        for lesson in ALL_LESSONS:
            if self.status(lesson.id) != Status.DONE:
                return lesson
        return ALL_LESSONS[-1]
