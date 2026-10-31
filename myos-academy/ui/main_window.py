"""Main window: roadmap tree on the left (filled in step 2), lesson area on the right."""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QTextBrowser,
    QTreeWidget,
    QTreeWidgetItem,
)

from core import credentials
from core.settings import AppSettings
from data.database import Database
from ui.settings_dialog import SettingsDialog
from ui.theme import apply_theme
from ui.workers import wait_for_all

WELCOME_HTML = """
<h1>MyOS Academy</h1>
<p>Chào mừng bạn! Ứng dụng này dạy bạn tự viết một hệ điều hành bằng C++,
từ kernel x86 đầu tiên đến ARM64, với bài học do Claude soạn riêng cho bạn.</p>
<h3>Bắt đầu</h3>
<ol>
  <li>Mở <b>Cài đặt</b> (Ctrl+,) và dán API key Anthropic.</li>
  <li>Bấm <b>Kiểm tra key</b> để chắc chắn key dùng được.</li>
  <li>Chọn một bài trong cây lộ trình bên trái (có từ Bước 2).</li>
</ol>
"""


class MainWindow(QMainWindow):
    def __init__(self, db: Database, settings: AppSettings) -> None:
        super().__init__()
        self.db = db
        self.settings = settings
        self.setWindowTitle("MyOS Academy")
        self.resize(1200, 780)

        self._build_menu()
        self._build_central()
        self._build_status_bar()
        self._refresh_status()

        # Ask for an API key once the window is visible.
        QTimer.singleShot(0, self._prompt_for_key_if_missing)

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
        self.roadmap_tree = QTreeWidget()
        self.roadmap_tree.setHeaderLabel("Lộ trình")
        QTreeWidgetItem(self.roadmap_tree, ["(Cây lộ trình sẽ có ở Bước 2)"])
        self.lesson_view = QTextBrowser()
        self.lesson_view.setOpenExternalLinks(True)
        self.lesson_view.setHtml(WELCOME_HTML)
        splitter.addWidget(self.roadmap_tree)
        splitter.addWidget(self.lesson_view)
        splitter.setSizes([320, 880])
        self.setCentralWidget(splitter)

    def _build_status_bar(self) -> None:
        self.key_label = QLabel()
        self.model_label = QLabel()
        self.statusBar().addWidget(self.key_label)
        self.statusBar().addPermanentWidget(self.model_label)

    def _refresh_status(self) -> None:
        try:
            has_key = bool(credentials.get_api_key())
        except credentials.CredentialError:
            has_key = False
        self.key_label.setText("API key: đã lưu ✅" if has_key else "API key: chưa có ❌")
        self.model_label.setText(f"Model: {self.settings.model}")

    def _prompt_for_key_if_missing(self) -> None:
        try:
            if credentials.get_api_key():
                return
        except credentials.CredentialError as exc:
            QMessageBox.warning(self, "Credential Manager", str(exc))
            return
        answer = QMessageBox.question(
            self, "Chưa có API key", "Bạn chưa nhập API key Anthropic. Mở Cài đặt ngay?"
        )
        if answer == QMessageBox.Yes:
            self.open_settings()

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == SettingsDialog.Accepted:
            self.settings.save(self.db)
            apply_theme(QApplication.instance(), self.settings.theme, self.settings.font_size)
        self._refresh_status()

    def closeEvent(self, event: QCloseEvent) -> None:
        wait_for_all()
        self.db.close()
        super().closeEvent(event)
