"""Settings dialog: voice, font size, theme."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.settings import EDGE_VOICES, THEMES, TTS_ENGINES, AppSettings
from core.tts import list_pyttsx3_voices


def _fill_combo(combo: QComboBox, items: dict[str, str], current: str) -> None:
    for value, label in items.items():
        combo.addItem(label, value)
    index = combo.findData(current)
    combo.setCurrentIndex(max(index, 0))


class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Cài đặt")
        self.setMinimumWidth(480)
        self.settings = settings

        layout = QVBoxLayout(self)
        layout.addWidget(self._build_voice_group())
        layout.addWidget(self._build_display_group())

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Lưu")
        buttons.button(QDialogButtonBox.Cancel).setText("Huỷ")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _build_voice_group(self) -> QGroupBox:
        group = QGroupBox("Giọng đọc")
        form = QFormLayout(group)
        self.engine_combo = QComboBox()
        _fill_combo(self.engine_combo, TTS_ENGINES, self.settings.tts_engine)
        form.addRow("Bộ đọc:", self.engine_combo)
        self.edge_voice_combo = QComboBox()
        _fill_combo(self.edge_voice_combo, EDGE_VOICES, self.settings.edge_voice)
        form.addRow("Giọng edge-tts:", self.edge_voice_combo)

        self.windows_voice_combo = QComboBox()
        self.windows_voice_combo.addItem("Tự chọn giọng tiếng Việt nếu có", "")
        voices = list_pyttsx3_voices()
        for voice_id, label in voices:
            self.windows_voice_combo.addItem(label, voice_id)
        self.windows_voice_combo.setCurrentIndex(
            max(self.windows_voice_combo.findData(self.settings.pyttsx3_voice), 0))
        form.addRow("Giọng Windows:", self.windows_voice_combo)

        has_vietnamese = any("tiếng Việt" in label for _, label in voices)
        note = QLabel(
            "edge-tts: giọng tiếng Việt tự nhiên, cần Internet; đoạn đã nghe được lưu lại để nghe offline.\n"
            "pyttsx3: chạy offline bằng giọng có sẵn của Windows."
            + ("" if has_vietnamese else
               " Máy bạn chưa có giọng tiếng Việt cho pyttsx3, nên nó sẽ đọc tiếng Việt bằng giọng tiếng Anh "
               "(rất khó nghe). Nên dùng edge-tts.")
        )
        note.setWordWrap(True)
        note.setEnabled(False)
        form.addRow(note)

        self.engine_combo.currentIndexChanged.connect(self._update_voice_widgets)
        self._update_voice_widgets()
        return group

    def _update_voice_widgets(self) -> None:
        edge = self.engine_combo.currentData() == "edge"
        self.edge_voice_combo.setEnabled(edge)
        self.windows_voice_combo.setEnabled(not edge)

    def _build_display_group(self) -> QGroupBox:
        group = QGroupBox("Hiển thị")
        form = QFormLayout(group)
        self.font_spin = QSpinBox()
        self.font_spin.setRange(8, 24)
        self.font_spin.setSuffix(" pt")
        self.font_spin.setValue(self.settings.font_size)
        form.addRow("Cỡ chữ:", self.font_spin)
        self.theme_combo = QComboBox()
        _fill_combo(self.theme_combo, THEMES, self.settings.theme)
        form.addRow("Giao diện:", self.theme_combo)
        return group

    def accept(self) -> None:
        self.settings.tts_engine = self.engine_combo.currentData()
        self.settings.edge_voice = self.edge_voice_combo.currentData()
        self.settings.pyttsx3_voice = self.windows_voice_combo.currentData()
        self.settings.font_size = self.font_spin.value()
        self.settings.theme = self.theme_combo.currentData()
        super().accept()
