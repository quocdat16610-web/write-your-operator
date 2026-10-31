"""An animated walkthrough: run a small assembly program one instruction at a time, like a narrated video.

Animation files live in content/animations/<lesson id>.json:

    {"animations": [{
        "title": "...",
        "intro": "spoken before the first instruction",
        "code": ["_start:", "    mov eax, 7", ...],
        "init": {"eax": 5},                      # optional starting register values
        "show": ["eax", "ebx", "esp"],           # optional: registers to display (default: all)
        "notes": {"2": "text", "5": ["first time", "later times"]},   # keyed by 1-based code line
        "outro": "spoken after the last instruction"
    }]}

The machine state of every frame comes from core.x86sim, so the numbers are computed, not typed by hand.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPalette, QTextCursor, QTextFormat
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSlider,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.settings import AppSettings
from core.speech_text import Segment, plain_text, spoken_text
from core.x86sim import REGISTERS, STACK_TOP, Frame, signed, trace
from ui.lesson_renderer import rich
from ui.read_aloud import ReadAloudController

RETURN_MARK = 0xC0DE0000
CHANGED = QColor("#f2cc60")


def _hex(value: int) -> str:
    return f"0x{value:08X}"


def _describe(value: int) -> str:
    if value >> 16 == RETURN_MARK >> 16:
        return "địa chỉ quay về"
    return str(signed(value))


class AnimationDialog(QDialog):
    def __init__(self, animation: dict, settings: AppSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"🎬 {animation['title']}")
        self.resize(1080, 700)
        self.animation = animation
        self.code_lines: list[str] = animation["code"]
        self.frames: list[Frame] = trace("\n".join(self.code_lines), animation.get("init"))
        self._attach_notes()
        self.shown = [r for r in REGISTERS if r in animation.get("show", REGISTERS)]
        self.index = 0
        self.playing = False
        self._waiting_for_voice = False
        self.voice_failed = False

        self.reader = ReadAloudController(settings, self)
        self.reader.stopped.connect(self._on_voice_done)
        self.reader.error.connect(self._on_voice_error)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._advance)

        self._build()
        self._show_frame()

    # ---- data ----------------------------------------------------------
    def _attach_notes(self) -> None:
        notes = self.animation.get("notes", {})
        seen: dict[int, int] = {}
        for frame in self.frames:
            if frame.line is None:
                frame.note = self.animation.get("intro", "")
                continue
            note = notes.get(str(frame.line + 1), "")
            if isinstance(note, list):
                count = seen.get(frame.line, 0)
                note = note[min(count, len(note) - 1)] if note else ""
            seen[frame.line] = seen.get(frame.line, 0) + 1
            frame.note = note
        outro = self.animation.get("outro")
        if outro:
            last = self.frames[-1]
            self.frames.append(Frame(None, last.registers, last.flags, last.stack, set(), outro))

    # ---- layout --------------------------------------------------------
    def _build(self) -> None:
        mono = QFont("Consolas")
        mono.setStyleHint(QFont.Monospace)

        self.code_view = QPlainTextEdit("\n".join(self.code_lines))
        self.code_view.setReadOnly(True)
        self.code_view.setFont(mono)
        self.code_view.setLineWrapMode(QPlainTextEdit.NoWrap)

        self.reg_table = QTableWidget(len(self.shown), 3)
        self.reg_table.setHorizontalHeaderLabels(["Thanh ghi", "Hex", "Thập phân"])
        self.reg_table.verticalHeader().setVisible(False)
        self.reg_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.reg_table.setFont(mono)
        self.flags_label = QLabel()
        self.flags_label.setFont(mono)
        self.flags_label.setTextFormat(Qt.RichText)

        self.stack_table = QTableWidget(0, 3)
        self.stack_table.setHorizontalHeaderLabels(["Địa chỉ", "Giá trị", ""])
        self.stack_table.verticalHeader().setVisible(False)
        self.stack_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.stack_table.setFont(mono)
        self.stack_empty = QLabel("Stack đang trống (esp ở đáy).")
        self.stack_empty.setEnabled(False)
        for table in (self.reg_table, self.stack_table):
            table.horizontalHeader().setStretchLastSection(True)

        reg_box = QGroupBox("Thanh ghi")
        reg_layout = QVBoxLayout(reg_box)
        reg_layout.addWidget(self.reg_table)
        reg_layout.addWidget(self.flags_label)
        stack_box = QGroupBox("Stack (địa chỉ cao ở trên)")
        stack_layout = QVBoxLayout(stack_box)
        stack_layout.addWidget(self.stack_table)
        stack_layout.addWidget(self.stack_empty)

        right = QVBoxLayout()
        right.addWidget(reg_box, 3)
        right.addWidget(stack_box, 2)
        top = QHBoxLayout()
        code_box = QGroupBox("Code (dòng sáng = lệnh vừa chạy)")
        QVBoxLayout(code_box).addWidget(self.code_view)
        top.addWidget(code_box, 3)
        top.addLayout(right, 2)

        self.note_label = QLabel()
        self.note_label.setWordWrap(True)
        self.note_label.setTextFormat(Qt.RichText)
        self.note_label.setMinimumHeight(70)
        note_font = self.note_label.font()
        note_font.setPointSizeF(note_font.pointSizeF() * 1.25)
        self.note_label.setFont(note_font)

        self.first_button = QPushButton("⏮")
        self.first_button.clicked.connect(lambda: self._jump(0))
        self.prev_button = QPushButton("◀ Lùi")
        self.prev_button.clicked.connect(lambda: self._jump(self.index - 1))
        self.play_button = QPushButton("▶ Phát")
        self.play_button.clicked.connect(self._toggle_play)
        self.next_button = QPushButton("Tới ▶")
        self.next_button.clicked.connect(lambda: self._jump(self.index + 1))
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, len(self.frames) - 1)
        self.slider.valueChanged.connect(self._on_slider)
        self.step_label = QLabel()
        self.voice_check = QCheckBox("🔊 Thuyết minh")
        self.voice_check.setChecked(True)
        self.voice_check.toggled.connect(self._on_voice_toggled)

        controls = QHBoxLayout()
        for widget in (self.first_button, self.prev_button, self.play_button, self.next_button):
            controls.addWidget(widget)
        controls.addWidget(self.slider, 1)
        controls.addWidget(self.step_label)
        controls.addWidget(self.voice_check)

        layout = QVBoxLayout(self)
        layout.addLayout(top, 1)
        layout.addWidget(self.note_label)
        layout.addLayout(controls)

    # ---- rendering -----------------------------------------------------
    def _show_frame(self) -> None:
        frame = self.frames[self.index]
        self.slider.blockSignals(True)
        self.slider.setValue(self.index)
        self.slider.blockSignals(False)
        self.step_label.setText(f"Bước {self.index}/{len(self.frames) - 1}")
        self.note_label.setText(rich(frame.note))
        self._highlight_line(frame.line)

        for row, name in enumerate(self.shown):
            value = frame.registers[name]
            cells = [name, _hex(value), _describe(value)]
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                if name in frame.changed:
                    item.setBackground(CHANGED)
                    item.setForeground(QColor("#1f2328"))
                self.reg_table.setItem(row, col, item)
        self.reg_table.resizeColumnsToContents()

        flags = [f"<span style='background:{CHANGED.name()};color:#1f2328'>&nbsp;{name}={int(v)}&nbsp;</span>"
                 if name in frame.changed else f"{name}={int(v)}" for name, v in frame.flags.items()]
        self.flags_label.setText("Cờ: " + "&nbsp;&nbsp;".join(flags))

        esp, ebp = frame.registers["esp"], frame.registers["ebp"]
        self.stack_table.setRowCount(len(frame.stack))
        for row, (address, value) in enumerate(frame.stack):
            marks = [m for m, reg in (("◄ esp", esp), ("◄ ebp", ebp)) if reg == address]
            if ebp != STACK_TOP and 0 < address - ebp <= 16:  # ebp now points into the stack
                marks.append(f"[ebp + {address - ebp}]")
            cells = [_hex(address), f"{_describe(value)}", "  ".join(marks)]
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                if "stack" in frame.changed and address == esp:
                    item.setBackground(CHANGED)
                    item.setForeground(QColor("#1f2328"))
                self.stack_table.setItem(row, col, item)
        self.stack_table.resizeColumnsToContents()
        self.stack_empty.setVisible(not frame.stack)

        self.first_button.setEnabled(self.index > 0)
        self.prev_button.setEnabled(self.index > 0)
        self.next_button.setEnabled(self.index < len(self.frames) - 1)

    def _highlight_line(self, line: int | None) -> None:
        if line is None:
            self.code_view.setExtraSelections([])
            return
        block = self.code_view.document().findBlockByNumber(line)
        cursor = QTextCursor(block)
        selection = QTextEdit.ExtraSelection()
        selection.cursor = cursor
        color = QColor(self.palette().color(QPalette.Highlight))
        color.setAlpha(110)
        selection.format.setBackground(color)
        selection.format.setProperty(QTextFormat.FullWidthSelection, True)
        self.code_view.setExtraSelections([selection])
        self.code_view.setTextCursor(cursor)
        self.code_view.centerCursor()

    # ---- playback ------------------------------------------------------
    def _toggle_play(self) -> None:
        if self.playing:
            self._pause()
            return
        if self.index >= len(self.frames) - 1:
            self.index = 0
            self._show_frame()
        self.playing = True
        self.play_button.setText("⏸ Dừng")
        self._narrate_current()

    def _pause(self) -> None:
        self.playing = False
        self.play_button.setText("▶ Phát")
        self.timer.stop()
        self._waiting_for_voice = False
        self.reader.stop()

    def _narrate_current(self) -> None:
        note = self.frames[self.index].note
        if self.voice_check.isChecked() and not self.voice_failed and note:
            self._waiting_for_voice = True
            self.reader.start([Segment(spoken_text(plain_text(note)), note)], 1.0)
        else:
            self.timer.start(1500 + 45 * len(note))  # enough time to read it yourself

    def _advance(self) -> None:
        if not self.playing:
            return
        if self.index >= len(self.frames) - 1:
            self._pause()
            return
        self.index += 1
        self._show_frame()
        if self.frames[self.index].note:
            self._narrate_current()
        else:
            self.timer.start(350)

    def _on_voice_done(self) -> None:
        if self._waiting_for_voice and self.playing:
            self._waiting_for_voice = False
            self.timer.start(400)  # a short pause between sentences

    def _on_voice_error(self, message: str) -> None:
        self.voice_failed = True
        self.voice_check.setChecked(False)
        self.voice_check.setToolTip(message)
        self.note_label.setText(rich(self.frames[self.index].note)
                                + "<br><small>(Không phát được giọng đọc, chuyển sang tự chạy theo thời gian.)</small>")
        if self.playing:
            self._waiting_for_voice = False
            self.timer.start(1500)

    def _on_voice_toggled(self, enabled: bool) -> None:
        if enabled:
            self.voice_failed = False
        elif self._waiting_for_voice:
            self._waiting_for_voice = False
            self.reader.stop()
            if self.playing:
                self.timer.start(1200)

    def _jump(self, index: int) -> None:
        was_playing = self.playing
        self._pause()
        self.index = max(0, min(index, len(self.frames) - 1))
        self._show_frame()
        if was_playing:
            self._toggle_play()

    def _on_slider(self, value: int) -> None:
        self._jump(value)

    def done(self, result: int) -> None:
        self._pause()
        super().done(result)
