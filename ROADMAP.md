# Lộ trình tự viết hệ điều hành bằng C++ (x86 → ARM64)

Dự án: `~/myos` · Môi trường: Windows + WSL2 (Ubuntu) + QEMU · Ngôn ngữ: C++ (freestanding) + NASM / GNU as

## Cách dùng file này

- Mỗi bài học trong lộ trình có **một video riêng**: bấm vào link 🔎 để mở trang **tìm kiếm YouTube** đúng chủ đề bài đó.
- Mình **không tự làm được video**, và cũng **không bịa link video cụ thể** (link có thể sai hoặc video đã bị xoá). Link 🔎 là link tìm kiếm thật của YouTube, nên lúc nào bấm cũng có kết quả.
- Cột **Kênh gợi ý** chỉ ghi những kênh mình chắc chắn có tồn tại. Gõ tên kênh cùng từ khoá vào YouTube để lọc kết quả cho chuẩn. Ô có dấu `—` nghĩa là không có kênh nào mình đủ chắc chắn, bạn chọn video từ kết quả tìm kiếm.
- Mẹo chọn video: ưu tiên video **dưới 3 năm tuổi**, có **demo chạy trên QEMU**, và tác giả **công khai mã nguồn** (GitHub). Gặp video dùng Rust hoặc C thì vẫn xem được, vì khái niệm giống hệt nhau.
- Đánh dấu `[x]` vào ô vuông khi học xong một bài.

### Các kênh YouTube tham khảo chung

| Kênh | Mạnh về |
|---|---|
| Computerphile | Giải thích khái niệm máy tính dễ hiểu |
| Ben Eater | Phần cứng, CPU, bus, ngắt ở mức mạch điện |
| Core Dumped | Hoạt hình minh hoạ khái niệm hệ điều hành (process, scheduler, bộ nhớ) |
| Low Level | Assembly, C, bảo mật, ARM |
| Jacob Sorber | C, Makefile, GDB, lập trình hệ thống |
| Daedalus Community | Loạt video tự viết OS x86 |
| nanobyte | Loạt video "Building an OS" (bootloader, FAT, x86) |
| Queso Fuego | Loạt livestream dài tự viết OS hobby |
| CodePulse | Kernel 64-bit x86_64 từ đầu |
| Andreas Kling | SerenityOS: OS thật viết bằng C++ |
| Onur Mutlu Lectures | Bài giảng đại học về kiến trúc máy tính (nâng cao) |
| Low Byte Productions | Lập trình bare-metal / nhúng, ARM |

Tài liệu đọc kèm (không phải video): OSDev Wiki (wiki.osdev.org), Intel SDM, ARM Architecture Reference Manual, "Operating Systems: Three Easy Pieces" (OSTEP, miễn phí).

---

## Giai đoạn 0: Nền tảng

| ✓ | Bài | Học xong làm được gì | Video (tiếng Anh) | Từ khoá tiếng Việt | Kênh gợi ý |
|---|---|---|---|---|---|
| [ ] | **0.1** Máy tính khởi động thế nào | Hiểu BIOS → MBR → bootloader → kernel; tự viết một boot sector 512 byte | [🔎 how a computer boots BIOS MBR bootloader](https://www.youtube.com/results?search_query=how+a+computer+boots+BIOS+MBR+bootloader) | `quá trình khởi động máy tính BIOS UEFI` | Computerphile, Core Dumped |
| [ ] | **0.2** Assembly x86 đủ dùng | Đọc và viết được các lệnh mov, push, call, int, các thanh ghi | [🔎 x86 assembly NASM tutorial registers](https://www.youtube.com/results?search_query=x86+assembly+NASM+tutorial+registers) | `lập trình hợp ngữ x86 cơ bản` | Low Level |
| [ ] | **0.3** Makefile cho dự án | Build cả kernel chỉ bằng `make`, chạy bằng `make run` | [🔎 makefile tutorial C C++ beginners](https://www.youtube.com/results?search_query=makefile+tutorial+C+C%2B%2B+beginners) | `hướng dẫn viết Makefile C++` | Jacob Sorber |
| [ ] | **0.4** Cross-compiler i686-elf-g++ và GDB + QEMU | Có trình biên dịch chéo chuẩn OS, đặt breakpoint vào kernel | [🔎 osdev cross compiler i686-elf gcc build](https://www.youtube.com/results?search_query=osdev+cross+compiler+i686-elf+gcc+build) · [🔎 debug kernel qemu gdb](https://www.youtube.com/results?search_query=debug+kernel+qemu+gdb+remote) | `debug bằng gdb cơ bản` | Jacob Sorber (GDB) |

## Giai đoạn 1: Kernel x86 đầu tiên

| ✓ | Bài | Học xong làm được gì | Video (tiếng Anh) | Từ khoá tiếng Việt | Kênh gợi ý |
|---|---|---|---|---|---|
| [ ] | **1.1** Lớp Terminal | In chữ, xuống dòng, cuộn màn hình, đổi màu trên VGA text mode | [🔎 osdev VGA text mode 0xB8000 kernel](https://www.youtube.com/results?search_query=osdev+VGA+text+mode+0xB8000+kernel) | `VGA text mode lập trình hệ điều hành` | Daedalus Community |
| [ ] | **1.2** printf tự viết | `kprintf("%d %x %s")` in được số, hex, chuỗi | [🔎 implement printf from scratch C varargs](https://www.youtube.com/results?search_query=implement+printf+from+scratch+C+varargs) | `tự viết hàm printf trong C` | Jacob Sorber |
| [ ] | **1.3** Runtime C++ | Constructor toàn cục, `__cxa_pure_virtual`, kernel panic | [🔎 C++ kernel global constructors crti crtbegin](https://www.youtube.com/results?search_query=C%2B%2B+kernel+global+constructors+osdev) | `C++ không dùng thư viện chuẩn freestanding` | Andreas Kling |
| [ ] | **1.4** Serial port | Ghi log từ kernel ra terminal WSL qua COM1 | [🔎 osdev serial port COM1 logging qemu](https://www.youtube.com/results?search_query=osdev+serial+port+COM1+qemu) | `cổng nối tiếp serial UART là gì` | Ben Eater (UART/RS-232) |

## Giai đoạn 2: CPU và ngắt

| ✓ | Bài | Học xong làm được gì | Video (tiếng Anh) | Từ khoá tiếng Việt | Kênh gợi ý |
|---|---|---|---|---|---|
| [ ] | **2.1** GDT | Tự nạp bảng phân đoạn, hiểu ring 0 / ring 3 | [🔎 global descriptor table GDT osdev explained](https://www.youtube.com/results?search_query=global+descriptor+table+GDT+osdev+explained) | `bảng mô tả phân đoạn GDT x86` | Daedalus Community, nanobyte |
| [ ] | **2.2** IDT và exception | Bắt lỗi chia cho 0, page fault và in ra màn hình | [🔎 interrupt descriptor table IDT osdev](https://www.youtube.com/results?search_query=interrupt+descriptor+table+IDT+osdev) | `ngắt và ngoại lệ trong CPU` | Core Dumped |
| [ ] | **2.3** PIC và ngắt phần cứng | Remap PIC 8259, nhận IRQ | [🔎 8259 PIC interrupts explained osdev](https://www.youtube.com/results?search_query=8259+PIC+interrupts+explained+osdev) | `ngắt phần cứng IRQ là gì` | Ben Eater (interrupts) |
| [ ] | **2.4** Timer PIT | Đồng hồ tick 100 Hz, hàm `sleep()` | [🔎 programmable interval timer PIT 8253 osdev](https://www.youtube.com/results?search_query=programmable+interval+timer+PIT+8253+osdev) | `bộ định thời timer trong hệ điều hành` | — |
| [ ] | **2.5** Bàn phím PS/2 | Gõ phím thấy chữ hiện lên màn hình | [🔎 PS/2 keyboard driver scancode osdev](https://www.youtube.com/results?search_query=PS2+keyboard+driver+scancode+osdev) | `bàn phím PS/2 hoạt động thế nào` | Ben Eater (PS/2 keyboard) |

## Giai đoạn 3: Bộ nhớ

| ✓ | Bài | Học xong làm được gì | Video (tiếng Anh) | Từ khoá tiếng Việt | Kênh gợi ý |
|---|---|---|---|---|---|
| [ ] | **3.1** Memory map từ multiboot | Biết vùng RAM nào dùng được | [🔎 multiboot memory map osdev](https://www.youtube.com/results?search_query=multiboot+memory+map+osdev) | `bản đồ bộ nhớ memory map` | — |
| [ ] | **3.2** Physical memory manager | Cấp phát và trả lại từng trang 4 KB bằng bitmap | [🔎 physical memory manager bitmap osdev](https://www.youtube.com/results?search_query=physical+memory+manager+bitmap+osdev) | `quản lý bộ nhớ vật lý hệ điều hành` | Core Dumped |
| [ ] | **3.3** Phân trang | Bật paging, có địa chỉ ảo | [🔎 paging virtual memory explained x86](https://www.youtube.com/results?search_query=paging+virtual+memory+explained+x86) | `phân trang bộ nhớ ảo paging` | Core Dumped, Computerphile |
| [ ] | **3.4** Heap: kmalloc/kfree, new/delete | Dùng được `new` / `delete` trong kernel | [🔎 implement malloc free from scratch heap allocator](https://www.youtube.com/results?search_query=implement+malloc+free+from+scratch+heap+allocator) | `tự viết malloc cấp phát bộ nhớ động` | Jacob Sorber |
| [ ] | **3.5** String, Vector bằng template | Có thư viện kernel nhỏ kiểu `std::vector` | [🔎 implement vector class from scratch C++ template](https://www.youtube.com/results?search_query=implement+vector+class+from+scratch+C%2B%2B+template) | `tự viết lớp vector C++ template` | — |

## Giai đoạn 4: Đa nhiệm

| ✓ | Bài | Học xong làm được gì | Video (tiếng Anh) | Từ khoá tiếng Việt | Kênh gợi ý |
|---|---|---|---|---|---|
| [ ] | **4.1** Process/thread và context switch | Hai luồng chạy xen kẽ | [🔎 context switch explained operating system](https://www.youtube.com/results?search_query=context+switch+explained+operating+system) | `chuyển ngữ cảnh context switch tiến trình` | Core Dumped |
| [ ] | **4.2** Scheduler round-robin | Lập lịch tự động bằng ngắt timer | [🔎 round robin scheduling operating system](https://www.youtube.com/results?search_query=round+robin+scheduling+operating+system) | `lập lịch round robin hệ điều hành` | Core Dumped |
| [ ] | **4.3** User mode (ring 3) | Chạy chương trình ở chế độ người dùng, có TSS | [🔎 osdev user mode ring 3 TSS](https://www.youtube.com/results?search_query=osdev+user+mode+ring+3+TSS) | `chế độ người dùng và chế độ nhân` | — |
| [ ] | **4.4** System call | Chương trình gọi `int 0x80` để nhờ kernel in chữ | [🔎 system call explained int 0x80](https://www.youtube.com/results?search_query=system+call+explained+int+0x80) | `lời gọi hệ thống system call` | Core Dumped, Low Level |

## Giai đoạn 5: Ổ đĩa và file

| ✓ | Bài | Học xong làm được gì | Video (tiếng Anh) | Từ khoá tiếng Việt | Kênh gợi ý |
|---|---|---|---|---|---|
| [ ] | **5.1** Driver đĩa ATA | Đọc sector từ ổ đĩa ảo | [🔎 ATA PIO disk driver osdev](https://www.youtube.com/results?search_query=ATA+PIO+disk+driver+osdev) | `driver ổ cứng ATA` | — |
| [ ] | **5.2** VFS | Lớp trừu tượng `File` / `Inode` chung cho mọi hệ thống file | [🔎 virtual file system VFS explained](https://www.youtube.com/results?search_query=virtual+file+system+VFS+explained) | `hệ thống file ảo VFS` | — |
| [ ] | **5.3** FAT32 (chỉ đọc) | Liệt kê thư mục, đọc file từ đĩa | [🔎 FAT32 file system explained](https://www.youtube.com/results?search_query=FAT32+file+system+explained) | `cấu trúc hệ thống file FAT32` | nanobyte |
| [ ] | **5.4** Chạy ELF từ đĩa | Nạp và chạy chương trình riêng | [🔎 ELF file format explained loader](https://www.youtube.com/results?search_query=ELF+file+format+explained+loader) | `định dạng file ELF` | LiveOverflow |

## Giai đoạn 6: Shell và đồ hoạ

| ✓ | Bài | Học xong làm được gì | Video (tiếng Anh) | Từ khoá tiếng Việt | Kênh gợi ý |
|---|---|---|---|---|---|
| [ ] | **6.1** Shell dòng lệnh | Gõ lệnh `help`, `ls`, `cat`, `run` | [🔎 write a shell from scratch](https://www.youtube.com/results?search_query=write+a+shell+from+scratch) | `tự viết shell dòng lệnh` | — |
| [ ] | **6.2** Framebuffer (VBE/GRUB) | Vẽ pixel ở độ phân giải cao | [🔎 osdev framebuffer graphics GRUB VBE](https://www.youtube.com/results?search_query=osdev+framebuffer+graphics+GRUB+VBE) | `framebuffer đồ hoạ` | — |
| [ ] | **6.3** Font, cửa sổ, chuột | Giao diện cửa sổ đơn giản kéo thả được | [🔎 osdev window manager mouse PS/2 bitmap font](https://www.youtube.com/results?search_query=osdev+window+manager+mouse+bitmap+font) | `tự viết giao diện cửa sổ hệ điều hành` | Andreas Kling |

## Giai đoạn 7: Chuyển sang 64-bit

| ✓ | Bài | Học xong làm được gì | Video (tiếng Anh) | Từ khoá tiếng Việt | Kênh gợi ý |
|---|---|---|---|---|---|
| [ ] | **7.1** Long mode x86_64 | Kernel chạy 64-bit | [🔎 x86_64 long mode kernel from scratch](https://www.youtube.com/results?search_query=x86_64+long+mode+kernel+from+scratch) | `chế độ 64 bit long mode` | CodePulse |
| [ ] | **7.2** UEFI hoặc Limine | Khởi động kiểu máy tính hiện đại | [🔎 Limine bootloader kernel tutorial](https://www.youtube.com/results?search_query=Limine+bootloader+kernel+tutorial) · [🔎 UEFI boot explained](https://www.youtube.com/results?search_query=UEFI+boot+process+explained) | `khởi động UEFI là gì` | — |
| [ ] | **7.3** Tách mã theo kiến trúc | Cây thư mục `arch/x86`, `arch/arm64` | [🔎 kernel portability architecture abstraction layer](https://www.youtube.com/results?search_query=kernel+architecture+abstraction+layer+portable+os) | `thiết kế hệ điều hành đa kiến trúc` | — |

## Giai đoạn 8: ARM64 (kiến trúc điện thoại)

| ✓ | Bài | Học xong làm được gì | Video (tiếng Anh) | Từ khoá tiếng Việt | Kênh gợi ý |
|---|---|---|---|---|---|
| [ ] | **8.1** Assembly AArch64 | Đọc và viết lệnh ARM64 cơ bản | [🔎 ARM64 AArch64 assembly tutorial](https://www.youtube.com/results?search_query=ARM64+AArch64+assembly+tutorial) | `hợp ngữ ARM64` | Low Level |
| [ ] | **8.2** Kernel trên QEMU virt + UART PL011 | In chữ trên máy ảo ARM64 | [🔎 bare metal aarch64 qemu virt UART](https://www.youtube.com/results?search_query=bare+metal+aarch64+qemu+virt+UART) | `lập trình bare metal ARM` | Low Byte Productions |
| [ ] | **8.3** Exception levels, vector table | EL1/EL0, bắt exception | [🔎 ARM exception levels EL0 EL1 vector table](https://www.youtube.com/results?search_query=ARM+exception+levels+EL0+EL1+vector+table) | `exception level ARM` | — |
| [ ] | **8.4** Timer và GIC | Ngắt timer trên ARM | [🔎 ARM generic interrupt controller GIC timer](https://www.youtube.com/results?search_query=ARM+generic+interrupt+controller+GIC+timer) | `bộ điều khiển ngắt GIC ARM` | — |
| [ ] | **8.5** MMU ARM64 | Phân trang trên ARM | [🔎 ARM64 MMU page tables translation](https://www.youtube.com/results?search_query=ARM64+MMU+page+tables+translation) | `MMU ARM phân trang` | — |
| [ ] | **8.6** Device Tree | Đọc cấu hình phần cứng từ DTB | [🔎 device tree explained linux](https://www.youtube.com/results?search_query=device+tree+explained+linux) | `device tree là gì` | — |
| [ ] | **8.7** Port scheduler và shell | Shell của mình chạy trên ARM64 | [🔎 porting operating system to ARM64](https://www.youtube.com/results?search_query=porting+operating+system+kernel+to+ARM64) | `port hệ điều hành sang ARM` | — |

## Giai đoạn 9: Phần cứng thật

| ✓ | Bài | Học xong làm được gì | Video (tiếng Anh) | Từ khoá tiếng Việt | Kênh gợi ý |
|---|---|---|---|---|---|
| [ ] | **9.1** Máy tính thật qua USB | Boot OS của mình từ USB | [🔎 boot hobby os on real hardware USB](https://www.youtube.com/results?search_query=boot+hobby+os+on+real+hardware+USB) | `tạo USB boot hệ điều hành tự viết` | — |
| [ ] | **9.2** Raspberry Pi | Chạy kernel trên Raspberry Pi | [🔎 raspberry pi bare metal kernel aarch64](https://www.youtube.com/results?search_query=raspberry+pi+bare+metal+kernel+aarch64) | `lập trình bare metal Raspberry Pi` | Low Byte Productions |
| [ ] | **9.3** Khởi động trên điện thoại Android | Hiểu bootloader, fastboot và giới hạn thực tế | [🔎 android boot process bootloader fastboot explained](https://www.youtube.com/results?search_query=android+boot+process+bootloader+fastboot+explained) | `quá trình khởi động Android bootloader` | — |

> ⚠️ Nói trước về bài 9.3: chạy OS tự viết trên **điện thoại thật** là cực khó. Bootloader thường bị khoá, driver màn hình và cảm ứng không công khai, và làm sai có thể brick máy. Mục tiêu thực tế của bài là **hiểu** quy trình đó, còn kết quả chạy thật thì làm trên QEMU và Raspberry Pi.

---

## Cấu trúc mỗi bài học

Mục tiêu → Lý thuyết (ví dụ đời thường + sơ đồ ASCII) → Code đầy đủ + lệnh build/chạy → Giải thích từng dòng → Kết quả mong đợi → Lỗi hay gặp → Bài tập (Dễ / Vừa / Khó) → 3 câu hỏi kiểm tra → Bản nghe 150–250 từ → Video tham khảo.
