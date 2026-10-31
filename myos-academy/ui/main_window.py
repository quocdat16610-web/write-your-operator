"""Main window: roadmap tree on the left with lesson status, lesson area on the right."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QSplitter

from core.progress import ProgressStore
from core.roadmap import ALL_LESSONS
from core.settings import AppSettings
from data.database import Database
from ui.lesson_panel import LessonPanel
from ui.roadmap_tree import RoadmapTree
from ui.settings_dialog import SettingsDialog
from ui.theme import apply_theme
from ui.workers import wait_for_all


class MainWindow(QMainWindow):
    def __init__(self, db: Database, settings: AppSettings) -> None:
        super().__init__()
        self.db = db
        self.settings = settings
        self.progress = ProgressStore(db)
        self.setWindowTitle("MyOS Academy")
        self.resize(1200, 780)

        self._build_menu()
        self._build_central()
        self._build_status_bar()
        self._refresh_status()

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&Tệp")
        settings_action = QAction("Cài đặt…", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)
        file_menu.addSeparator()
        quit_action = QAction("Thoát", self)
        quit_action.setShortcut(QKeySequence.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        toolbar = self.addToolBar("Chính")
        toolbar.setMovable(False)
        toolbar.addAction(settings_action)

    def _build_central(self) -> None:
        splitter = QSplitter(Qt.Horizontal)
        self.roadmap_tree = RoadmapTree(self.progress)
        self.lesson_panel = LessonPanel(self.progress)
        self.roadmap_tree.lesson_selected.connect(self.lesson_panel.show_lesson)
        self.roadmap_tree.stage_selected.connect(self.lesson_panel.show_stage)
        self.roadmap_tree.progress_changed.connect(self._on_progress_changed)
        self.lesson_panel.progress_changed.connect(self._on_progress_changed)
        splitter.addWidget(self.roadmap_tree)
        splitter.addWidget(self.lesson_panel)
        splitter.setSizes([380, 820])
        self.setCentralWidget(splitter)
        # Open the stage you are currently in, without selecting anything yet.
        current = self.progress.current_lesson()
        self.roadmap_tree.topLevelItem(current.stage).setExpanded(True)

    def _on_progress_changed(self) -> None:
        self.roadmap_tree.refresh()
        current = self.roadmap_tree.currentItem()
        if current is not None and current.data(0, Qt.UserRole)[0] == "stage":
            self.lesson_panel.show_stage(current.data(0, Qt.UserRole)[1])
        else:
            self.lesson_panel.refresh()
        self._refresh_status()

    def _build_status_bar(self) -> None:
        self.progress_label = QLabel()
        self.statusBar().addWidget(self.progress_label)

    def _refresh_status(self) -> None:
        done = self.progress.done_count()
        percent = round(100 * done / len(ALL_LESSONS))
        self.progress_label.setText(f"Tiến độ: {done}/{len(ALL_LESSONS)} bài ({percent}%)")

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == SettingsDialog.Accepted:
            self.settings.save(self.db)
            apply_theme(QApplication.instance(), self.settings.theme, self.settings.font_size)
            self._on_progress_changed()  # tree colours and code highlighting depend on the palette

    def closeEvent(self, event: QCloseEvent) -> None:
        wait_for_all()
        self.db.close()
        super().closeEvent(event)
