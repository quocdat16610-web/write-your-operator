"""The fixed curriculum: 10 stages, 42 lessons, plus per-stage references and video searches.

Text wrapped in `backticks` is rendered as inline code by the UI.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import quote_plus


@dataclass(frozen=True)
class Lesson:
    id: str  # "0.1"
    title: str
    stage: int


@dataclass(frozen=True)
class Stage:
    number: int
    title: str
    result: str  # what you can see in QEMU at the end of the stage
    theory: str
    big_exercise: str
    duration: str
    lessons: tuple[Lesson, ...] = field(default=())


@dataclass(frozen=True)
class Reference:
    name: str
    url: str | None
    stages: range
    note: str


@dataclass(frozen=True)
class VideoSearch:
    query: str
    stages: tuple[int, ...]
    note: str

    @property
    def url(self) -> str:
        return youtube_search_url(self.query)


def youtube_search_url(query: str) -> str:
    return "https://www.youtube.com/results?search_query=" + quote_plus(query)


def _stage(number: int, title: str, result: str, theory: str, big_exercise: str,
           duration: str, lessons: list[tuple[str, str]]) -> Stage:
    return Stage(number, title, result, theory, big_exercise, duration,
                 tuple(Lesson(lesson_id, name, number) for lesson_id, name in lessons))


STAGES: tuple[Stage, ...] = (
    _stage(0, "Nền tảng",
           "`make run` build và chạy kernel; dừng được kernel bằng GDB",
           "BIOS/UEFI, bootloader, chế độ real/protected, thanh ghi x86, stack, calling convention",
           "Viết hàm assembly cộng hai số và gọi từ C++", "1–2 tuần",
           [("0.1", "Máy tính khởi động thế nào"),
            ("0.2.1", "Assembly 1: Thanh ghi và lệnh mov"),
            ("0.2.2", "Assembly 2: Phép tính, bộ nhớ, system call"),
            ("0.2.3", "Assembly 3: So sánh, nhảy và vòng lặp"),
            ("0.2.4", "Assembly 4: Stack, call và ret"),
            ("0.2.5", "Assembly 5: C++ gọi assembly (cdecl)"),
            ("0.3", "Makefile cho dự án"),
            ("0.4", "Cross-compiler i686-elf-g++ và debug bằng GDB + QEMU")]),
    _stage(1, "Kernel x86 đầu tiên",
           '`kprintf("x = %d", x)` in được ra màn hình và cổng serial',
           "VGA text mode, I/O port, ABI C++, global constructors",
           "Màn hình khởi động có logo ASCII và thông tin hệ thống", "1–2 tuần",
           [("1.1", "Lớp Terminal: in chữ, xuống dòng, cuộn, màu"),
            ("1.2", "printf tự viết (số, hex, chuỗi)"),
            ("1.3", "Runtime C++: constructor toàn cục, __cxa_pure_virtual, kernel panic"),
            ("1.4", "Serial port để log ra terminal")]),
    _stage(2, "CPU và ngắt",
           "Gõ phím là chữ hiện lên; đồng hồ đếm giây; chia cho 0 hiện màn hình lỗi",
           "Segmentation, GDT, IDT, exception vs IRQ, PIC, PIT, scancode",
           "Trình gõ chữ có Backspace, Shift, Caps Lock", "2–3 tuần",
           [("2.1", "GDT"),
            ("2.2", "IDT và xử lý exception"),
            ("2.3", "PIC và ngắt phần cứng"),
            ("2.4", "Timer PIT"),
            ("2.5", "Bàn phím PS/2")]),
    _stage(3, "Bộ nhớ",
           "`new`/`delete` và `Vector<T>` chạy trong kernel",
           "Physical vs virtual memory, page table, TLB, heap allocator",
           "Lệnh `meminfo` in tổng RAM, đã dùng, còn trống", "3–4 tuần",
           [("3.1", "Đọc memory map từ multiboot"),
            ("3.2", "Physical memory manager (bitmap)"),
            ("3.3", "Phân trang (paging)"),
            ("3.4", "Heap: tự viết kmalloc/kfree, operator new/delete"),
            ("3.5", "Thư viện kernel nhỏ: String, Vector tự viết bằng template")]),
    _stage(4, "Đa nhiệm",
           "Hai tác vụ chạy xen kẽ; chương trình ring 3 gọi syscall `write`",
           "Process, context switch, scheduler, privilege ring, TSS",
           "Thêm độ ưu tiên và lệnh `sleep(ms)`", "3–4 tuần",
           [("4.1", "Process/thread và context switch"),
            ("4.2", "Scheduler round-robin"),
            ("4.3", "User mode (ring 3)"),
            ("4.4", "System call")]),
    _stage(5, "Ổ đĩa và file",
           "`cat /hello.txt` đọc file từ ổ đĩa ảo; chạy được file ELF",
           "Block device, VFS, cấu trúc FAT32, định dạng ELF",
           "Lệnh `ls` liệt kê thư mục và kích thước file", "3–4 tuần",
           [("5.1", "Driver đĩa ATA"),
            ("5.2", "VFS"),
            ("5.3", "Hệ thống file FAT32 (chỉ đọc trước)"),
            ("5.4", "Chạy chương trình ELF từ đĩa")]),
    _stage(6, "Shell và đồ họa",
           "Shell có `help`, `clear`, `echo`, `ls`; màn hình đồ họa vẽ được cửa sổ",
           "Phân tích lệnh, framebuffer, pixel format, bitmap font",
           "Cửa sổ kéo thả bằng chuột", "3–4 tuần",
           [("6.1", "Shell dòng lệnh"),
            ("6.2", "Framebuffer đồ họa (VBE/GRUB)"),
            ("6.3", "Vẽ font, cửa sổ đơn giản, chuột")]),
    _stage(7, "Chuyển sang 64-bit",
           "Kernel x86_64 khởi động bằng Limine/UEFI; mã chia `arch/x86` và `arch/arm64`",
           "Long mode, paging 4 cấp, UEFI, thiết kế lớp trừu tượng phần cứng (HAL)",
           "Port toàn bộ các giai đoạn 1–6 sang 64-bit", "2–3 tuần",
           [("7.1", "Long mode x86_64"),
            ("7.2", "Khởi động bằng UEFI hoặc Limine"),
            ("7.3", "Tách mã theo kiến trúc (arch/x86, arch/arm64) để chuẩn bị port")]),
    _stage(8, "ARM64 (kiến trúc điện thoại)",
           "Cùng kernel C++ chạy trên `qemu-system-aarch64 -machine virt`, có shell qua UART",
           "AArch64 assembly, exception level EL0–EL3, GIC, MMU ARM, Device Tree",
           "Chạy shell trên ARM với cùng mã nguồn chung", "4–6 tuần",
           [("8.1", "Assembly AArch64 cơ bản"),
            ("8.2", "Kernel chạy trên QEMU -machine virt, in chữ qua UART PL011"),
            ("8.3", "Exception levels và vector table"),
            ("8.4", "Timer và GIC"),
            ("8.5", "MMU ARM64"),
            ("8.6", "Device Tree"),
            ("8.7", "Port scheduler và shell sang ARM64")]),
    _stage(9, "Phần cứng thật",
           "Kernel khởi động từ USB trên PC thật và trên Raspberry Pi",
           "Boot từ USB, firmware Raspberry Pi, quy trình khởi động Android",
           "In chữ ra UART của Raspberry Pi qua cáp USB-serial", "Tuỳ phần cứng",
           [("9.1", "Chạy trên máy tính thật qua USB"),
            ("9.2", "Chạy trên Raspberry Pi"),
            ("9.3", "Tìm hiểu khởi động trên điện thoại Android thật (bootloader, fastboot) và giới hạn thực tế")]),
)

REFERENCES: tuple[Reference, ...] = (
    Reference("OSDev Wiki", "https://wiki.osdev.org", range(0, 10),
              "Tra cứu chính: Bare Bones, GDT, IDT, Paging, C++"),
    Reference("OSTEP", "https://pages.cs.wisc.edu/~remzi/OSTEP/", range(3, 6),
              "Sách lý thuyết OS miễn phí, dễ đọc"),
    Reference("xv6", "https://github.com/mit-pdos/xv6-public", range(2, 6),
              "OS nhỏ của MIT, đọc code để so sánh"),
    Reference("SerenityOS", "https://github.com/SerenityOS/serenity", range(4, 8),
              "OS lớn viết bằng C++, xem cách tổ chức code thực tế"),
    Reference("Limine", "https://github.com/limine-bootloader/limine", range(7, 8),
              "Bootloader cho kernel 64-bit"),
    Reference("raspberry-pi-os", "https://github.com/s-matyukevich/raspberry-pi-os", range(8, 10),
              "Hướng dẫn kernel ARM64 cho Raspberry Pi"),
    Reference("postmarketOS", "https://postmarketos.org", range(9, 10),
              "Danh sách điện thoại có thể chạy hệ điều hành tự do"),
    Reference("Intel SDM, ARM Architecture Reference Manual", None, range(2, 9),
              "Tài liệu gốc của hãng chip, tra khi cần chi tiết thanh ghi"),
)

VIDEO_SEARCHES: tuple[VideoSearch, ...] = (
    VideoSearch('nanobyte "Building an OS"', (0, 1, 2, 5),
                "Đi từ bootloader, giải thích chậm, dùng C và assembly"),
    VideoSearch('Daedalus Community "Making an OS (x86)"', (0, 1, 2),
                "Video ngắn, mỗi video một khái niệm"),
    VideoSearch('CodePulse "64-bit operating system kernel"', (7,), "Lên 64-bit với long mode"),
    VideoSearch("Andreas Kling SerenityOS", (4, 5, 6, 7),
                "Lập trình OS thật bằng C++, xem cách tổ chức code"),
    VideoSearch("AArch64 bare metal", (8, 9), "Từ khóa tìm cho phần ARM"),
    VideoSearch("Raspberry Pi bare metal", (8, 9), "Từ khóa tìm cho phần ARM"),
)

PHONE_REALITY_NOTE = (
    "Bạn sẽ viết được kernel chạy trên kiến trúc ARM64 của điện thoại, nhưng chạy trên một chiếc "
    "điện thoại thật là việc của cả nhóm người nhiều năm: phải mở khóa bootloader, driver màn hình, "
    "cảm ứng và modem thường đóng mã nguồn, mỗi mẫu máy mỗi khác. Mục tiêu thực tế là khởi động kernel "
    "qua `fastboot` và in chữ ra framebuffer mà bootloader để lại. Nên dùng máy cũ mà postmarketOS đã "
    "hỗ trợ và chấp nhận rủi ro hỏng máy."
)

ALL_LESSONS: tuple[Lesson, ...] = tuple(lesson for stage in STAGES for lesson in stage.lessons)
_LESSON_INDEX = {lesson.id: index for index, lesson in enumerate(ALL_LESSONS)}


def lesson_by_id(lesson_id: str) -> Lesson:
    return ALL_LESSONS[_LESSON_INDEX[lesson_id]]


def previous_lesson(lesson_id: str) -> Lesson | None:
    index = _LESSON_INDEX[lesson_id]
    return ALL_LESSONS[index - 1] if index > 0 else None


def stage_by_number(number: int) -> Stage:
    return STAGES[number]


def references_for(stage: int) -> list[Reference]:
    return [ref for ref in REFERENCES if stage in ref.stages]


def videos_for(stage: int) -> list[VideoSearch]:
    return [video for video in VIDEO_SEARCHES if stage in video.stages]
