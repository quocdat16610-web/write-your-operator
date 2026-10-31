"""Draw the lesson diagrams into content/images/*.png.

Run from the myos-academy folder:  python tools/make_diagrams.py
The PNGs are committed, so the app itself never needs Pillow.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "content" / "images"
SCALE = 2  # draw at 2x so images stay sharp on high-DPI screens
WIDTH = 720

FONT_DIRS = [Path("C:/Windows/Fonts"), Path("/usr/share/fonts/truetype/dejavu")]
SANS = ["segoeui.ttf", "DejaVuSans.ttf"]
SANS_BOLD = ["segoeuib.ttf", "DejaVuSans-Bold.ttf"]
MONO = ["consola.ttf", "DejaVuSansMono.ttf"]

BG, BORDER, TEXT, MUTED = "#ffffff", "#d0d7de", "#1f2328", "#59636e"
BLUE, BLUE_BG = "#0969da", "#ddf4ff"
GREEN, GREEN_BG = "#1a7f37", "#dafbe1"
ORANGE, ORANGE_BG = "#bc4c00", "#fff1e5"
PURPLE, PURPLE_BG = "#8250df", "#fbefff"
GRAY_BG = "#f6f8fa"


def font(names: list[str], size: int) -> ImageFont.FreeTypeFont:
    for folder in FONT_DIRS:
        for name in names:
            path = folder / name
            if path.exists():
                return ImageFont.truetype(str(path), size * SCALE)
    raise SystemExit(f"Không tìm thấy font {names}")


class Canvas:
    def __init__(self, height: int) -> None:
        self.image = Image.new("RGB", (WIDTH * SCALE, height * SCALE), BG)
        self.draw = ImageDraw.Draw(self.image)
        self.draw.rounded_rectangle([0, 0, WIDTH * SCALE - 1, height * SCALE - 1], 14 * SCALE,
                                    outline=BORDER, width=2 * SCALE)

    def box(self, x, y, w, h, fill=GRAY_BG, outline=BORDER, radius=8, width=2) -> None:
        self.draw.rounded_rectangle([x * SCALE, y * SCALE, (x + w) * SCALE, (y + h) * SCALE],
                                    radius * SCALE, fill=fill, outline=outline, width=width * SCALE)

    def text(self, x, y, value, size=15, color=TEXT, kind="sans", anchor="la") -> None:
        face = font({"sans": SANS, "bold": SANS_BOLD, "mono": MONO}[kind], size)
        self.draw.text((x * SCALE, y * SCALE), value, fill=color, font=face, anchor=anchor)

    def arrow(self, x1, y1, x2, y2, color=MUTED, width=2) -> None:
        self.draw.line([x1 * SCALE, y1 * SCALE, x2 * SCALE, y2 * SCALE], fill=color, width=width * SCALE)
        import math
        angle = math.atan2(y2 - y1, x2 - x1)
        size = 9
        left = (x2 - size * math.cos(angle - 0.45), y2 - size * math.sin(angle - 0.45))
        right = (x2 - size * math.cos(angle + 0.45), y2 - size * math.sin(angle + 0.45))
        self.draw.polygon([(x2 * SCALE, y2 * SCALE), (left[0] * SCALE, left[1] * SCALE),
                           (right[0] * SCALE, right[1] * SCALE)], fill=color)

    def save(self, name: str) -> None:
        OUT.mkdir(parents=True, exist_ok=True)
        self.image.save(OUT / name, optimize=True)
        print("wrote", OUT / name)


def compile_pipeline() -> None:
    c = Canvas(250)
    c.text(24, 20, "Từ C++ đến mã máy", 18, kind="bold")
    rows = [
        ("C++", "int x = 5 + 3;", BLUE, BLUE_BG),
        ("Assembly", "mov eax, 5      add eax, 3", PURPLE, PURPLE_BG),
        ("Mã máy (byte)", "B8 05 00 00 00   83 C0 03", GREEN, GREEN_BG),
    ]
    for i, (label, code, color, fill) in enumerate(rows):
        y = 58 + i * 64
        c.box(24, y, 150, 40, fill=fill, outline=color)
        c.text(99, y + 20, label, 15, color, "bold", "mm")
        c.box(190, y, 506, 40, fill=GRAY_BG)
        c.text(206, y + 20, code, 16, TEXT, "mono", "lm")
        if i < 2:
            c.arrow(99, y + 42, 99, y + 62)
            c.text(112, y + 52, "g++ dịch" if i == 0 else "nasm dịch", 12, MUTED, anchor="lm")
    c.save("asm-pipeline.png")


def registers() -> None:
    c = Canvas(380)
    c.text(24, 20, "Thanh ghi: 8 \"tờ giấy nháp\" 32 bit trong CPU", 18, kind="bold")
    regs = [("eax", "tính toán, giá trị trả về", BLUE, BLUE_BG), ("ebx", "dữ liệu chung", BLUE, BLUE_BG),
            ("ecx", "biến đếm vòng lặp", BLUE, BLUE_BG), ("edx", "dữ liệu chung", BLUE, BLUE_BG),
            ("esi", "địa chỉ nguồn", PURPLE, PURPLE_BG), ("edi", "địa chỉ đích", PURPLE, PURPLE_BG),
            ("esp", "đỉnh stack", ORANGE, ORANGE_BG), ("ebp", "đáy khung stack", ORANGE, ORANGE_BG)]
    for i, (name, role, color, fill) in enumerate(regs):
        col, row = i % 2, i // 2
        x, y = 24 + col * 340, 56 + row * 46
        c.box(x, y, 70, 36, fill=fill, outline=color)
        c.text(x + 35, y + 18, name, 16, color, "mono", "mm")
        c.text(x + 82, y + 18, role, 14, TEXT, anchor="lm")
    y = 250
    c.text(24, y, "Dùng từng phần của eax:", 15, kind="bold")
    c.box(24, y + 28, 336, 40, fill=GRAY_BG)
    c.text(192, y + 48, "16 bit trên", 14, MUTED, anchor="mm")
    c.box(360, y + 28, 168, 40, fill=BLUE_BG, outline=BLUE)
    c.text(444, y + 48, "ah (8 bit)", 14, BLUE, "mono", "mm")
    c.box(528, y + 28, 168, 40, fill=BLUE_BG, outline=BLUE)
    c.text(612, y + 48, "al (8 bit)", 14, BLUE, "mono", "mm")
    c.draw.line([360 * SCALE, (y + 80) * SCALE, 696 * SCALE, (y + 80) * SCALE], fill=BLUE, width=2 * SCALE)
    c.text(528, y + 92, "ax = 16 bit thấp", 14, BLUE, "mono", "mm")
    c.draw.line([24 * SCALE, (y + 20) * SCALE, 696 * SCALE, (y + 20) * SCALE], fill=TEXT, width=2 * SCALE)
    c.text(360, y + 10, "eax = 32 bit", 14, TEXT, "mono", "mm")
    c.save("asm-registers.png")


def memory_brackets() -> None:
    c = Canvas(300)
    c.text(24, 20, "Có ngoặc vuông và không có ngoặc vuông", 18, kind="bold")
    c.text(24, 52, "Giả sử ebx = 0x2000, và trong RAM ở địa chỉ 0x2000 đang có số 99", 14, MUTED)
    c.box(24, 86, 300, 44, fill=GREEN_BG, outline=GREEN)
    c.text(174, 108, "mov eax, ebx", 18, GREEN, "mono", "mm")
    c.text(24, 146, "chép con số trong ebx", 14)
    c.text(24, 168, "→ eax = 0x2000", 16, GREEN, "mono")
    c.box(396, 86, 300, 44, fill=ORANGE_BG, outline=ORANGE)
    c.text(546, 108, "mov eax, [ebx]", 18, ORANGE, "mono", "mm")
    c.text(396, 146, "dùng ebx làm địa chỉ, đọc RAM ở đó", 14)
    c.text(396, 168, "→ eax = 99", 16, ORANGE, "mono")
    # RAM strip
    c.text(24, 214, "RAM:", 14, MUTED, "bold")
    cells = [("0x1FF8", "0"), ("0x1FFC", "7"), ("0x2000", "99"), ("0x2004", "0")]
    for i, (addr, value) in enumerate(cells):
        x = 80 + i * 150
        highlight = addr == "0x2000"
        c.box(x, 206, 140, 40, fill=ORANGE_BG if highlight else GRAY_BG, outline=ORANGE if highlight else BORDER)
        c.text(x + 70, 226, value, 16, ORANGE if highlight else TEXT, "mono", "mm")
        c.text(x + 70, 262, addr, 12, MUTED, "mono", "mm")
    c.save("asm-memory.png")


def loop_flow() -> None:
    c = Canvas(430)
    c.text(24, 20, "Vòng lặp = cmp + lệnh nhảy", 18, kind="bold")
    steps = [("xor eax, eax", "tổng = 0"), ("mov ecx, 1", "i = 1"),
             ("add eax, ecx", "tổng += i"), ("inc ecx", "i += 1"), ("cmp ecx, 10", "so sánh i với 10")]
    for i, (code, meaning) in enumerate(steps):
        y = 56 + i * 58
        loop_body = i >= 2
        c.box(60, y, 230, 40, fill=PURPLE_BG if loop_body else GRAY_BG, outline=PURPLE if loop_body else BORDER)
        c.text(175, y + 20, code, 16, TEXT, "mono", "mm")
        c.text(306, y + 20, meaning, 14, MUTED, anchor="lm")
        if i < len(steps) - 1:
            c.arrow(175, y + 40, 175, y + 56)
    y = 56 + 5 * 58
    c.arrow(175, y - 18, 175, y - 2)
    c.box(60, y, 230, 44, fill=ORANGE_BG, outline=ORANGE)
    c.text(175, y + 22, "jle .loop", 16, ORANGE, "mono", "mm")
    # back edge
    c.draw.line([(60 * SCALE, (y + 22) * SCALE), (36 * SCALE, (y + 22) * SCALE),
                 (36 * SCALE, (56 + 2 * 58 + 20) * SCALE)], fill=ORANGE, width=2 * SCALE)
    c.arrow(36, 56 + 2 * 58 + 20, 58, 56 + 2 * 58 + 20, ORANGE)
    c.text(306, y + 12, "i <= 10: nhảy lên làm tiếp", 14, ORANGE, anchor="lm")
    c.text(306, y + 34, "i = 11: đi tiếp xuống dưới", 14, GREEN, anchor="lm")
    c.arrow(175, y + 44, 175, y + 70, GREEN)
    c.text(190, y + 62, "thoát vòng, eax = 55", 14, GREEN, anchor="lm")
    c.save("asm-loop.png")


def stack_push_pop() -> None:
    c = Canvas(340)
    c.text(24, 20, "Stack như chồng đĩa: push đặt lên, pop lấy ra", 18, kind="bold")
    states = [("ban đầu", []), ("push 10", ["10"]), ("push 20", ["10", "20"]), ("pop eax → 20", ["10"])]
    for i, (title, items) in enumerate(states):
        x = 24 + i * 172
        c.text(x + 75, 60, title, 15, kind="bold", anchor="mm")
        base = 280
        c.draw.line([x * SCALE, base * SCALE, (x + 150) * SCALE, base * SCALE], fill=MUTED, width=2 * SCALE)
        for j, value in enumerate(items):
            y = base - (j + 1) * 46
            c.box(x + 10, y, 130, 40, fill=BLUE_BG, outline=BLUE)
            c.text(x + 75, y + 20, value, 16, BLUE, "mono", "mm")
        top = base - len(items) * 46
        c.text(x + 75, top - 16, "▲ esp", 13, ORANGE, "mono", "mm")
    c.text(24, 300, "Trên x86, stack mọc xuống địa chỉ thấp: push giảm esp đi 4, pop tăng esp lên 4.", 14, MUTED)
    c.save("asm-stack.png")


def call_frame() -> None:
    c = Canvas(380)
    c.text(24, 20, "Khung stack khi C++ gọi add_numbers(30, 12)", 18, kind="bold")
    c.text(24, 50, "địa chỉ cao", 13, MUTED)
    rows = [("b = 12", "[ebp + 12]", "người gọi đẩy vào trước", BLUE, BLUE_BG),
            ("a = 30", "[ebp + 8]", "người gọi đẩy vào sau", BLUE, BLUE_BG),
            ("địa chỉ quay về", "[ebp + 4]", "do lệnh call đẩy vào", PURPLE, PURPLE_BG),
            ("ebp cũ của người gọi", "[ebp]", "do push ebp đẩy vào  ◄ ebp, esp", ORANGE, ORANGE_BG)]
    for i, (value, offset, note, color, fill) in enumerate(rows):
        y = 72 + i * 58
        c.box(24, y, 250, 48, fill=fill, outline=color)
        c.text(149, y + 24, value, 15, color, "bold", "mm")
        c.text(292, y + 24, offset, 16, TEXT, "mono", "lm")
        c.text(420, y + 24, note, 13, MUTED, anchor="lm")
    c.text(24, 72 + 4 * 58 + 6, "địa chỉ thấp", 13, MUTED)
    c.text(24, 350, "Kết quả trả về nằm trong eax. Vì vậy tham số đầu tiên ở ebp + 8, không phải ebp + 4.", 14)
    c.save("asm-call-frame.png")


if __name__ == "__main__":
    compile_pipeline()
    registers()
    memory_brackets()
    loop_flow()
    stack_push_pop()
    call_frame()
