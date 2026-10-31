"""Left-hand tree: 10 stages, each with its lessons and their status."""
from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QAction, QBrush, QPalette
from PySide6.QtWidgets import QMenu, QTreeWidget, QTreeWidgetItem

from core.progress import ProgressStore, Status
from core.roadmap import STAGES, lesson_by_id

ROLE = Qt.UserRole
STATUS_ICONS = {Status.NOT_STARTED: "○", Status.IN_PROGRESS: "◐", Status.DONE: "✅"}
LOCK_ICON = "🔒"


class RoadmapTree(QTreeWidget):
    lesson_selected = Signal(str)
    stage_selected = Signal(int)
    progress_changed = Signal()

    def __init__(self, progress: ProgressStore) -> None:
        super().__init__()
        self.progress = progress
        self.setHeaderLabel("Lộ trình")
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)
        self.currentItemChanged.connect(self._on_current_changed)

        self._stage_items: dict[int, QTreeWidgetItem] = {}
        self._lesson_items: dict[str, QTreeWidgetItem] = {}
        for stage in STAGES:
            stage_item = QTreeWidgetItem(self)
            stage_item.setData(0, ROLE, ("stage", stage.number))
            font = stage_item.font(0)
            font.setBold(True)
            stage_item.setFont(0, font)
            self._stage_items[stage.number] = stage_item
            for lesson in stage.lessons:
                lesson_item = QTreeWidgetItem(stage_item)
                lesson_item.setData(0, ROLE, ("lesson", lesson.id))
                lesson_item.setToolTip(0, f"Bài {lesson.id}: {lesson.title}")
                self._lesson_items[lesson.id] = lesson_item
        self.refresh()

    def refresh(self) -> None:
        dim = QBrush(self.palette().color(QPalette.Disabled, QPalette.Text))
        normal = QBrush(self.palette().color(QPalette.Text))
        for stage in STAGES:
            done = self.progress.done_count(stage.lessons)
            self._stage_items[stage.number].setText(
                0, f"Giai đoạn {stage.number} · {stage.title} ({done}/{len(stage.lessons)})"
            )
            for lesson in stage.lessons:
                item = self._lesson_items[lesson.id]
                unlocked = self.progress.is_unlocked(lesson.id)
                icon = STATUS_ICONS[self.progress.status(lesson.id)] if unlocked else LOCK_ICON
                item.setText(0, f"{icon}  {lesson.id}  {lesson.title}")
                item.setForeground(0, normal if unlocked else dim)

    def select_lesson(self, lesson_id: str) -> None:
        item = self._lesson_items[lesson_id]
        item.parent().setExpanded(True)
        self.setCurrentItem(item)

    def _on_current_changed(self, current: QTreeWidgetItem | None, _previous) -> None:
        if current is None:
            return
        kind, key = current.data(0, ROLE)
        if kind == "stage":
            self.stage_selected.emit(key)
        else:
            self.lesson_selected.emit(key)

    def _show_menu(self, pos: QPoint) -> None:
        item = self.itemAt(pos)
        if item is None or item.data(0, ROLE)[0] != "lesson":
            return
        lesson = lesson_by_id(item.data(0, ROLE)[1])
        menu = QMenu(self)
        if not self.progress.is_unlocked(lesson.id):
            menu.addAction(self._action(menu, "Mở khóa thủ công", lambda: self.progress.unlock(lesson.id)))
        else:
            for status, label in ((Status.IN_PROGRESS, "Đánh dấu: đang học"),
                                  (Status.DONE, "Đánh dấu: đã xong"),
                                  (Status.NOT_STARTED, "Đặt lại: chưa học")):
                action = self._action(menu, label, lambda s=status: self.progress.set_status(lesson.id, s))
                action.setEnabled(self.progress.status(lesson.id) != status)
                menu.addAction(action)
        menu.exec(self.viewport().mapToGlobal(pos))

    def _action(self, menu: QMenu, text: str, change) -> QAction:
        action = QAction(text, menu)

        def run() -> None:
            change()
            self.progress_changed.emit()

        action.triggered.connect(run)
        return action
