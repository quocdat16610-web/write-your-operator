"""Right-hand panel: welcome page, stage overview, or the selected lesson."""
from __future__ import annotations

import html
import re

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTextBrowser, QVBoxLayout, QWidget

from core.progress import STATUS_LABELS, ProgressStore, Status
from core.roadmap import (
    PHONE_REALITY_NOTE,
    lesson_by_id,
    previous_lesson,
    references_for,
    stage_by_number,
    videos_for,
)

WELCOME_HTML = """
<h1>MyOS Academy</h1>
<p>Chào mừng bạn! Ứng dụng này dạy bạn tự viết một hệ điều hành bằng C++,
từ kernel x86 đầu tiên đến ARM64, với bài học do Claude soạn riêng cho bạn.</p>
<h3>Bắt đầu</h3>
<ol>
  <li>Mở <b>Cài đặt</b> (Ctrl+,) và dán API key Anthropic.</li>
  <li>Chọn một <b>giai đoạn</b> bên trái để xem mục tiêu, bài tập lớn và tài liệu tham khảo.</li>
  <li>Chọn một <b>bài</b> rồi bấm <b>Bắt đầu học</b>. Bài sau mở khi bài trước xong
      (chuột phải để mở khóa thủ công).</li>
</ol>
"""


def rich(text: str) -> str:
    """Escape text for HTML and turn `backticks` into <code>."""
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", html.escape(text))


class LessonPanel(QWidget):
    progress_changed = Signal()

    def __init__(self, progress: ProgressStore) -> None:
        super().__init__()
        self.progress = progress
        self.lesson_id: str | None = None

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

        self.header = QWidget()
        header_layout = QVBoxLayout(self.header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addWidget(self.title_label)
        header_layout.addLayout(buttons)

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self.header)
        layout.addWidget(self.browser)
        self.show_welcome()

    # ---- Pages ---------------------------------------------------------
    def show_welcome(self) -> None:
        self.lesson_id = None
        self.header.hide()
        self.browser.setHtml(WELCOME_HTML)

    def show_stage(self, number: int) -> None:
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
        self.lesson_id = lesson_id
        self.header.show()
        self.refresh()

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

        if not unlocked:
            previous = previous_lesson(lesson.id)
            self.browser.setHtml(
                f"<h3>🔒 Bài này đang khóa</h3><p>Hoàn thành <b>Bài {previous.id}: {rich(previous.title)}</b> "
                "trước, hoặc bấm <b>Mở khóa thủ công</b> nếu bạn đã biết nội dung bài trước.</p>"
            )
            return
        self.browser.setHtml(
            f"<p>Thuộc <b>Giai đoạn {stage.number}: {rich(stage.title)}</b>. "
            f"Mục tiêu giai đoạn: {rich(stage.result)}.</p>"
            "<p><i>Nội dung bài học do Claude soạn sẽ hiện ở đây (Bước 3).</i></p>"
        )

    # ---- Actions -------------------------------------------------------
    def _change(self, status: Status) -> None:
        if self.lesson_id is not None:
            self.progress.set_status(self.lesson_id, status)
            self.progress_changed.emit()

    def _unlock(self) -> None:
        if self.lesson_id is not None:
            self.progress.unlock(self.lesson_id)
            self.progress_changed.emit()
