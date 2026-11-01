"""Right-hand panel: welcome page, stage overview, or the selected lesson."""
from __future__ import annotations

import html

from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QColor, QCursor, QDesktopServices, QGuiApplication, QPalette, QTextCursor, QTextFormat
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QTextEdit,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from core.lesson_content import content_root, load_animations, load_lesson
from core.progress import STATUS_LABELS, ProgressStore, Status
from core.roadmap import (
    PHONE_REALITY_NOTE,
    ALL_LESSONS,
    lesson_by_id,
    previous_lesson,
    references_for,
    stage_by_number,
    videos_for,
)
from core.settings import SPEEDS, AppSettings
from core.speech_text import Segment, lecture_segments, summary_segments
from ui.lesson_renderer import RenderedLesson, render_lesson, rich
from ui.animation_dialog import AnimationDialog
from ui.read_aloud import ReadAloudController

WELCOME_HTML = """
<h1>MyOS Academy</h1>
<p>Chào mừng bạn! Ứng dụng này dạy bạn tự viết một hệ điều hành bằng C++,
từ kernel x86 đầu tiên đến ARM64. Bài học được soạn sẵn trong app: không cần mạng, không cần API key.</p>
<h3>Bắt đầu</h3>
<ol>
  <li>Chọn một <b>giai đoạn</b> bên trái để xem mục tiêu, bài tập lớn và tài liệu tham khảo.</li>
  <li>Chọn một <b>bài</b> rồi bấm <b>Bắt đầu học</b>. Bài sau mở khi bài trước xong
      (chuột phải để mở khóa thủ công).</li>
</ol>
"""


class LessonPanel(QWidget):
    progress_changed = Signal()

    settings_changed = Signal()  # e.g. reading speed, so the main window can save it

    def __init__(self, progress: ProgressStore, settings: AppSettings) -> None:
        super().__init__()
        self.progress = progress
        self.settings = settings
        self.segments: list[Segment] = []
        self._highlight_from = 0
        self.lesson_id: str | None = None
        self.revealed_hints: set[int] = set()
        self.rendered: RenderedLesson | None = None

        self.title_label = QLabel()
        font = self.title_label.font()
        font.setPointSizeF(font.pointSizeF() * 1.4)
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setWordWrap(True)
        self.status_label = QLabel()

        self.start_button = QPushButton("Bắt đầu học")
        self.start_button.clicked.connect(lambda: self._change(Status.IN_PROGRESS))
        self.done_button = QPushButton("Đánh dấu đã xong")
        self.done_button.clicked.connect(lambda: self._change(Status.DONE))
        self.unlock_button = QPushButton("Mở khóa thủ công")
        self.unlock_button.clicked.connect(self._unlock)

        buttons = QHBoxLayout()
        buttons.addWidget(self.status_label)
        buttons.addStretch()
        for button in (self.unlock_button, self.start_button, self.done_button):
            buttons.addWidget(button)

        self.lecture_button = QPushButton("🎓 Nghe giảng")
        self.lecture_button.setToolTip("Đọc to mục tiêu, lý thuyết và lỗi hay gặp (bỏ qua code và bảng)")
        self.lecture_button.clicked.connect(lambda: self._read(lecture_segments))
        self.summary_button = QPushButton("🎧 Nghe tóm tắt")
        self.summary_button.setToolTip("Đọc phần Bản nghe")
        self.summary_button.clicked.connect(lambda: self._read(summary_segments))
        self.stop_button = QPushButton("⏹ Dừng")
        self.stop_button.clicked.connect(self._stop_reading)
        self.speed_combo = QComboBox()
        for value, label in SPEEDS.items():
            self.speed_combo.addItem(label, value)
        self.speed_combo.setCurrentIndex(max(self.speed_combo.findData(settings.speech_speed), 0))
        self.speed_combo.currentIndexChanged.connect(self._on_speed_changed)
        self.reading_label = QLabel()
        self.animation_button = QPushButton("🎬 Xem hoạt hình")
        self.animation_button.setToolTip("Xem CPU chạy từng lệnh: thanh ghi và stack thay đổi, có thuyết minh")
        self.animation_button.clicked.connect(self._open_animation)

        audio = QHBoxLayout()
        for widget in (self.animation_button, self.lecture_button, self.summary_button, self.stop_button,
                       QLabel("Tốc độ:"), self.speed_combo, self.reading_label):
            audio.addWidget(widget)
        audio.addStretch()

        self.header = QWidget()
        header_layout = QVBoxLayout(self.header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addWidget(self.title_label)
        header_layout.addLayout(buttons)
        header_layout.addLayout(audio)

        self.reader = ReadAloudController(settings, self)
        self.reader.segment_started.connect(self._on_segment_started)
        self.reader.buffering.connect(self._on_buffering)
        self.reader.stopped.connect(self._on_reading_stopped)
        self.reader.error.connect(self._on_reading_error)

        self.browser = QTextBrowser()
        self.browser.setOpenLinks(False)  # every link goes through _on_link
        self.browser.setSearchPaths([str(content_root())])  # so <img src="images/x.png"> resolves
        self.browser.anchorClicked.connect(self._on_link)

        layout = QVBoxLayout(self)
        layout.addWidget(self.header)
        layout.addWidget(self.browser)
        self._on_reading_stopped()
        self.show_welcome()

    # ---- Pages ---------------------------------------------------------
    def show_welcome(self) -> None:
        self.reader.stop()
        self.lesson_id = None
        self.header.hide()
        self.browser.setHtml(WELCOME_HTML)

    def show_stage(self, number: int) -> None:
        self.reader.stop()
        self.lesson_id = None
        self.header.hide()
        stage = stage_by_number(number)
        done = self.progress.done_count(stage.lessons)

        parts = [f"<h1>Giai đoạn {stage.number}: {rich(stage.title)}</h1>",
                 f"<p>Tiến độ: <b>{done}/{len(stage.lessons)}</b> bài · Thời gian ước tính: "
                 f"<b>{rich(stage.duration)}</b> (khoảng 1 giờ mỗi ngày)</p>",
                 "<table border='1' cellpadding='6' cellspacing='0' width='100%'>",
                 f"<tr><th align='left' width='28%'>Kết quả cuối giai đoạn</th><td>{rich(stage.result)}</td></tr>",
                 f"<tr><th align='left'>Lý thuyết chính</th><td>{rich(stage.theory)}</td></tr>",
                 f"<tr><th align='left'>Bài tập lớn</th><td>{rich(stage.big_exercise)}</td></tr>",
                 "</table>",
                 "<h3>Các bài</h3><ul>"]
        for lesson in stage.lessons:
            status = STATUS_LABELS[self.progress.status(lesson.id)]
            locked = "" if self.progress.is_unlocked(lesson.id) else " 🔒"
            parts.append(f"<li><b>{lesson.id}</b> {rich(lesson.title)} · <i>{status}</i>{locked}</li>")
        parts.append("</ul>")

        if stage.number == 9:
            parts.append(f"<h3>⚠️ Sự thật về “OS cho điện thoại”</h3><p>{rich(PHONE_REALITY_NOTE)}</p>")

        videos = videos_for(stage.number)
        if videos:
            parts.append("<h3>Video tham khảo</h3>"
                         "<p>Mở trang tìm kiếm YouTube (không có link video cố định). "
                         "Video tiếng Anh, bật phụ đề tự dịch nếu cần. "
                         "Nên xem <b>sau</b> khi đọc lý thuyết của bài.</p><ul>")
            for video in videos:
                parts.append(f"<li><a href='{html.escape(video.url)}'>🔎 {html.escape(video.query)}</a>"
                             f": {rich(video.note)}</li>")
            parts.append("</ul>")

        parts.append("<h3>Tài liệu tham khảo</h3><ul>")
        for ref in references_for(stage.number):
            name = (f"<a href='{html.escape(ref.url)}'>{html.escape(ref.name)}</a>"
                    if ref.url else html.escape(ref.name))
            parts.append(f"<li>{name}: {rich(ref.note)}</li>")
        parts.append("</ul>")
        self.browser.setHtml("".join(parts))

    def show_lesson(self, lesson_id: str) -> None:
        if lesson_id != self.lesson_id:
            self.reader.stop()
        self.lesson_id = lesson_id
        self.revealed_hints = set()
        self.header.show()
        self.refresh()
        self.browser.verticalScrollBar().setValue(0)

    def refresh(self) -> None:
        if self.lesson_id is None:
            return
        lesson = lesson_by_id(self.lesson_id)
        stage = stage_by_number(lesson.stage)
        unlocked = self.progress.is_unlocked(lesson.id)
        status = self.progress.status(lesson.id)

        self.title_label.setText(f"Bài {lesson.id}: {lesson.title}")
        self.status_label.setText(f"Trạng thái: <b>{STATUS_LABELS[status] if unlocked else 'Đang khóa 🔒'}</b>")
        self.unlock_button.setVisible(not unlocked)
        self.start_button.setVisible(unlocked and status == Status.NOT_STARTED)
        self.done_button.setVisible(unlocked and status != Status.DONE)

        has_content = unlocked and load_lesson(lesson.id) is not None
        for widget in (self.lecture_button, self.summary_button, self.speed_combo):
            widget.setEnabled(has_content)
        self.animation_button.setVisible(unlocked and bool(load_animations(lesson.id)))

        if not unlocked:
            previous = previous_lesson(lesson.id)
            self.browser.setHtml(
                f"<h3>🔒 Bài này đang khóa</h3><p>Hoàn thành <b>Bài {previous.id}: {rich(previous.title)}</b> "
                "trước, hoặc bấm <b>Mở khóa thủ công</b> nếu bạn đã biết nội dung bài trước.</p>"
            )
            return
        source = load_lesson(lesson.id)
        if source is None:
            self.rendered = None
            self.browser.setHtml(
                f"<p>Thuộc <b>Giai đoạn {stage.number}: {rich(stage.title)}</b>. "
                f"Mục tiêu giai đoạn: {rich(stage.result)}.</p>"
                "<p><i>Bài này chưa được soạn. Nó sẽ có trong bản cập nhật tới của app.</i></p>"
            )
            return
        dark = QGuiApplication.palette().color(QPalette.Base).lightness() < 128
        self.rendered = render_lesson(source, self.revealed_hints, dark)
        scroll = self.browser.verticalScrollBar().value()
        self.browser.setHtml(self.rendered.html + self._next_lesson_html(lesson.id))
        self.browser.verticalScrollBar().setValue(scroll)

    def _next_lesson_html(self, lesson_id: str) -> str:
        index = [lesson.id for lesson in ALL_LESSONS].index(lesson_id)
        if index + 1 >= len(ALL_LESSONS):
            return "<hr><p><b>🎉 Đây là bài cuối của lộ trình.</b></p>"
        following = ALL_LESSONS[index + 1]
        return (f"<hr><p>Học xong thì bấm <b>Đánh dấu đã xong</b> để mở "
                f"<b>Bài {following.id}: {rich(following.title)}</b>.</p>")

    def _on_link(self, url: QUrl) -> None:
        scheme, target = url.scheme(), url.path()
        if scheme == "copy" and self.rendered is not None:
            QGuiApplication.clipboard().setText(self.rendered.code_blocks[int(target)].code)
            QToolTip.showText(QCursor.pos(), "Đã copy vào clipboard")
        elif scheme == "hint":
            self.revealed_hints.add(int(target))
            self.refresh()
        elif scheme in ("http", "https"):
            QDesktopServices.openUrl(url)

    # ---- Animations ----------------------------------------------------
    def _open_animation(self) -> None:
        animations = load_animations(self.lesson_id) if self.lesson_id else []
        if len(animations) == 1:
            self._play_animation(animations[0])
        elif animations:
            menu = QMenu(self)
            for animation in animations:
                menu.addAction(animation["title"], lambda a=animation: self._play_animation(a))
            menu.exec(self.animation_button.mapToGlobal(self.animation_button.rect().bottomLeft()))

    def _play_animation(self, animation: dict) -> None:
        self.reader.stop()
        AnimationDialog(animation, self.settings, self).exec()

    # ---- Read aloud ----------------------------------------------------
    def _read(self, make_segments) -> None:
        source = load_lesson(self.lesson_id) if self.lesson_id else None
        if source is None:
            return
        self.segments = make_segments(source)
        self._highlight_from = 0
        self.stop_button.setEnabled(True)
        self.reading_label.setText("Đang chuẩn bị giọng đọc…")
        self.reader.start(self.segments, float(self.speed_combo.currentData()))

    def _stop_reading(self) -> None:
        self.reader.stop()

    def _on_speed_changed(self) -> None:
        self.settings.speech_speed = self.speed_combo.currentData()
        self.settings_changed.emit()
        self.reader.set_speed(float(self.settings.speech_speed))

    def _on_segment_started(self, index: int) -> None:
        self.reading_label.setText(f"Đang đọc đoạn {index + 1}/{len(self.segments)}")
        self._highlight(self.segments[index].anchor)

    def _on_buffering(self, index: int) -> None:
        self.reading_label.setText(f"Đang tải giọng đọc đoạn {index + 1}… (cần Internet)")

    def _on_reading_stopped(self) -> None:
        self.stop_button.setEnabled(False)
        self.reading_label.setText("")
        self.browser.setExtraSelections([])

    def _on_reading_error(self, message: str) -> None:
        QMessageBox.warning(self, "Giọng đọc", message)

    def _highlight(self, anchor: str) -> None:
        """Highlight the on-screen paragraph that starts with the text being read, and scroll to it."""
        document = self.browser.document()
        found = QTextCursor()
        for length in (60, 30, 15):  # long prefixes first; short ones survive small formatting differences
            found = document.find(anchor[:length], self._highlight_from)
            if not found.isNull():
                break
        if found.isNull():
            return
        self._highlight_from = found.selectionStart()
        found.movePosition(QTextCursor.StartOfBlock)
        found.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
        selection = QTextEdit.ExtraSelection()
        selection.cursor = found
        color = QColor(self.palette().color(QPalette.Highlight))
        color.setAlpha(90)
        selection.format.setBackground(color)
        selection.format.setProperty(QTextFormat.FullWidthSelection, True)
        self.browser.setExtraSelections([selection])
        caret = QTextCursor(found)
        caret.clearSelection()
        self.browser.setTextCursor(caret)
        self.browser.ensureCursorVisible()

    # ---- Actions -------------------------------------------------------
    def _change(self, status: Status) -> None:
        if self.lesson_id is not None:
            self.progress.set_status(self.lesson_id, status)
            self.progress_changed.emit()

    def _unlock(self) -> None:
        if self.lesson_id is not None:
            self.progress.unlock(self.lesson_id)
            self.progress_changed.emit()
