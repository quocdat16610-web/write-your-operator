"""Settings dialog: API key (keyring), model, voice, font size, theme."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core import credentials
from core.claude_client import list_models
from core.settings import EDGE_VOICES, KNOWN_MODELS, THEMES, TTS_ENGINES, AppSettings
from ui.workers import run_in_background


def _fill_combo(combo: QComboBox, items: dict[str, str], current: str) -> None:
    for value, label in items.items():
        combo.addItem(label, value)
    index = combo.findData(current)
    combo.setCurrentIndex(max(index, 0))


class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Cài đặt")
        self.setMinimumWidth(560)
        self.settings = settings

        layout = QVBoxLayout(self)
        layout.addWidget(self._build_api_group())
        layout.addWidget(self._build_model_group())
        layout.addWidget(self._build_voice_group())
        layout.addWidget(self._build_display_group())

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Lưu")
        buttons.button(QDialogButtonBox.Cancel).setText("Huỷ")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._refresh_key_status()

    # ---- API key -------------------------------------------------------
    def _build_api_group(self) -> QGroupBox:
        group = QGroupBox("API key Anthropic")
        form = QFormLayout(group)

        self.key_status = QLabel()
        form.addRow("Trạng thái:", self.key_status)

        self.key_edit = QLineEdit()
        self.key_edit.setEchoMode(QLineEdit.Password)
        self.key_edit.setPlaceholderText("sk-ant-… (để trống nếu giữ key đã lưu)")
        self.show_key_button = QPushButton("Hiện")
        self.show_key_button.setCheckable(True)
        self.show_key_button.toggled.connect(self._toggle_key_visibility)
        row = QHBoxLayout()
        row.addWidget(self.key_edit)
        row.addWidget(self.show_key_button)
        form.addRow("Key mới:", row)

        self.test_button = QPushButton("Kiểm tra key")
        self.test_button.clicked.connect(self._test_key)
        self.delete_button = QPushButton("Xoá key đã lưu")
        self.delete_button.clicked.connect(self._delete_key)
        actions = QHBoxLayout()
        actions.addWidget(self.test_button)
        actions.addWidget(self.delete_button)
        actions.addStretch()
        form.addRow(actions)

        note = QLabel("Key được lưu trong Windows Credential Manager, không lưu dạng chữ thường trong file.")
        note.setWordWrap(True)
        note.setEnabled(False)
        form.addRow(note)
        return group

    def _toggle_key_visibility(self, visible: bool) -> None:
        self.key_edit.setEchoMode(QLineEdit.Normal if visible else QLineEdit.Password)
        self.show_key_button.setText("Ẩn" if visible else "Hiện")

    def _refresh_key_status(self) -> None:
        try:
            key = credentials.get_api_key()
        except credentials.CredentialError as exc:
            self.key_status.setText(f"⚠️ {exc}")
            return
        if key:
            self.key_status.setText(f"✅ Đã lưu: {credentials.mask(key)}")
        else:
            self.key_status.setText("❌ Chưa có API key")
        self.delete_button.setEnabled(bool(key))

    def _key_to_test(self) -> str | None:
        typed = self.key_edit.text().strip()
        if typed:
            return typed
        try:
            return credentials.get_api_key()
        except credentials.CredentialError:
            return None

    def _test_key(self) -> None:
        key = self._key_to_test()
        if not key:
            QMessageBox.warning(self, "Thiếu API key", "Hãy dán API key vào ô 'Key mới' trước.")
            return
        self.test_button.setEnabled(False)
        self.test_button.setText("Đang kiểm tra…")
        run_in_background(list_models, key, on_success=self._on_test_ok, on_error=self._on_test_failed)

    def _on_test_ok(self, model_ids: list[str]) -> None:
        self._restore_test_button()
        self._merge_models(model_ids)
        QMessageBox.information(
            self, "Key hợp lệ", f"Kết nối thành công. Tài khoản dùng được {len(model_ids)} model."
        )

    def _on_test_failed(self, message: str) -> None:
        self._restore_test_button()
        QMessageBox.critical(self, "Kiểm tra thất bại", message)

    def _restore_test_button(self) -> None:
        self.test_button.setEnabled(True)
        self.test_button.setText("Kiểm tra key")

    def _delete_key(self) -> None:
        answer = QMessageBox.question(self, "Xoá API key", "Xoá API key khỏi Credential Manager?")
        if answer != QMessageBox.Yes:
            return
        try:
            credentials.delete_api_key()
        except credentials.CredentialError as exc:
            QMessageBox.critical(self, "Lỗi", str(exc))
        self._refresh_key_status()

    # ---- Model ---------------------------------------------------------
    def _build_model_group(self) -> QGroupBox:
        group = QGroupBox("Model Claude")
        form = QFormLayout(group)
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.addItems(KNOWN_MODELS)
        if self.settings.model not in KNOWN_MODELS:
            self.model_combo.addItem(self.settings.model)
        self.model_combo.setCurrentText(self.settings.model)
        form.addRow("Model:", self.model_combo)
        hint = QLabel("Bấm 'Kiểm tra key' để tải thêm các model tài khoản bạn dùng được.")
        hint.setEnabled(False)
        form.addRow(hint)
        return group

    def _merge_models(self, model_ids: list[str]) -> None:
        current = self.model_combo.currentText()
        existing = {self.model_combo.itemText(i) for i in range(self.model_combo.count())}
        for model_id in model_ids:
            if model_id not in existing:
                self.model_combo.addItem(model_id)
        self.model_combo.setCurrentText(current)

    # ---- Voice ---------------------------------------------------------
    def _build_voice_group(self) -> QGroupBox:
        group = QGroupBox("Giọng đọc")
        form = QFormLayout(group)
        self.engine_combo = QComboBox()
        _fill_combo(self.engine_combo, TTS_ENGINES, self.settings.tts_engine)
        form.addRow("Bộ đọc:", self.engine_combo)
        self.edge_voice_combo = QComboBox()
        _fill_combo(self.edge_voice_combo, EDGE_VOICES, self.settings.edge_voice)
        form.addRow("Giọng edge-tts:", self.edge_voice_combo)
        self.engine_combo.currentIndexChanged.connect(self._update_voice_widgets)
        self._update_voice_widgets()
        return group

    def _update_voice_widgets(self) -> None:
        self.edge_voice_combo.setEnabled(self.engine_combo.currentData() == "edge")

    # ---- Display -------------------------------------------------------
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

    # ---- Save ----------------------------------------------------------
    def accept(self) -> None:
        typed_key = self.key_edit.text().strip()
        if typed_key:
            if not typed_key.startswith("sk-ant-"):
                answer = QMessageBox.question(
                    self, "Key lạ", "Key Anthropic thường bắt đầu bằng 'sk-ant-'. Vẫn lưu?"
                )
                if answer != QMessageBox.Yes:
                    return
            try:
                credentials.set_api_key(typed_key)
            except credentials.CredentialError as exc:
                QMessageBox.critical(self, "Lỗi lưu key", str(exc))
                return

        model = self.model_combo.currentText().strip()
        if not model:
            QMessageBox.warning(self, "Thiếu model", "Hãy chọn hoặc nhập tên model.")
            return
        self.settings.model = model
        self.settings.tts_engine = self.engine_combo.currentData()
        self.settings.edge_voice = self.edge_voice_combo.currentData()
        self.settings.font_size = self.font_spin.value()
        self.settings.theme = self.theme_combo.currentData()
        super().accept()
