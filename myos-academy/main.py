"""Entry point: python main.py"""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from core.paths import database_path
from core.settings import AppSettings
from data.database import Database
from ui.main_window import MainWindow
from ui.theme import apply_theme


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("MyOS Academy")
    app.setOrganizationName("MyOSAcademy")

    db = Database(database_path())
    settings = AppSettings.load(db)
    apply_theme(app, settings.theme, settings.font_size)

    window = MainWindow(db, settings)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
