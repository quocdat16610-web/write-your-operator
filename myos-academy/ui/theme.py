"""Light/dark palettes and global font size."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


def _dark_palette() -> QPalette:
    p = QPalette()
    base, window, text = QColor("#1e1f22"), QColor("#2b2d31"), QColor("#e6e6e6")
    p.setColor(QPalette.Window, window)
    p.setColor(QPalette.WindowText, text)
    p.setColor(QPalette.Base, base)
    p.setColor(QPalette.AlternateBase, window)
    p.setColor(QPalette.Text, text)
    p.setColor(QPalette.Button, window)
    p.setColor(QPalette.ButtonText, text)
    p.setColor(QPalette.ToolTipBase, base)
    p.setColor(QPalette.ToolTipText, text)
    p.setColor(QPalette.PlaceholderText, QColor("#8a8a8a"))
    p.setColor(QPalette.Highlight, QColor("#4c8bf5"))
    p.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    p.setColor(QPalette.Link, QColor("#7aa7ff"))
    p.setColor(QPalette.Disabled, QPalette.Text, QColor("#6b6b6b"))
    p.setColor(QPalette.Disabled, QPalette.ButtonText, QColor("#6b6b6b"))
    return p


def is_dark(theme: str) -> bool:
    if theme == "system":
        return QApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
    return theme == "dark"


def apply_theme(app: QApplication, theme: str, font_size: int) -> None:
    app.setStyle("Fusion")
    app.setPalette(_dark_palette() if is_dark(theme) else app.style().standardPalette())
    font = app.font()
    font.setPointSize(font_size)
    app.setFont(font)
