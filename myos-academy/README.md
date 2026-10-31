# MyOS Academy

Ứng dụng desktop Windows dạy bạn tự viết hệ điều hành bằng C++. Bài học được soạn sẵn và đóng gói trong app: không cần mạng, không cần API key.

> Trạng thái: **Bước 4**: bài học soạn sẵn + nghe đọc (giảng cả bài hoặc bản tóm tắt). Đã có **Bài 0.1** và **Bài 0.2.1 đến 0.2.5** (Assembly, có hình và hoạt hình); các bài sau được thêm dần.

## Cấu trúc thư mục

```
myos-academy/
├── main.py              # Điểm khởi động app
├── run.bat              # Bấm đúp để tạo .venv, cài thư viện và chạy app
├── requirements.txt
├── content/
│   ├── lessons/         # Bài học soạn sẵn: 0.1.md, 0.2.1.md, ...
│   ├── images/          # Hình minh họa (PNG), vẽ bằng tools/make_diagrams.py
│   └── animations/      # Kịch bản hoạt hình từng bước (JSON)
├── tools/make_diagrams.py # Vẽ lại hình minh họa (cần Pillow, chỉ dùng khi soạn bài)
├── core/                # Logic không phụ thuộc giao diện
│   ├── paths.py         # Đường dẫn %APPDATA%\MyOSAcademy
│   ├── settings.py      # AppSettings: giọng đọc, cỡ chữ, giao diện
│   ├── roadmap.py       # Lộ trình: giai đoạn, bài, tài liệu tham khảo, từ khóa video
│   ├── progress.py      # Trạng thái bài (chưa học/đang học/xong) và luật mở khóa
│   ├── lesson_content.py # Đọc file bài học trong content/lessons
│   ├── x86sim.py        # Bộ mô phỏng CPU x86 mini cho hoạt hình
│   ├── speech_text.py   # Tách bài thành các đoạn để đọc (bỏ code, bảng; đọc ký hiệu thành chữ)
│   └── tts.py           # Tạo giọng đọc bằng edge-tts hoặc pyttsx3, lưu cache âm thanh
├── data/
│   └── database.py      # SQLite + migration theo PRAGMA user_version
└── ui/                  # Giao diện PySide6
    ├── main_window.py   # Cửa sổ chính
    ├── roadmap_tree.py  # Cây lộ trình bên trái (chuột phải: đổi trạng thái, mở khóa)
    ├── lesson_panel.py  # Trang chào, trang giai đoạn, trang bài
    ├── lesson_renderer.py # Markdown → HTML: tô màu code, nút Copy, gợi ý ẩn, nút YouTube
    ├── animation_dialog.py # Cửa sổ hoạt hình: code, thanh ghi, stack, thuyết minh
    ├── read_aloud.py    # Điều khiển đọc to: tạo âm thanh ở luồng nền, đọc trước đoạn kế tiếp
    ├── audio_player.py  # Phát mp3/wav bằng MCI có sẵn trong Windows
    ├── settings_dialog.py
    ├── theme.py         # Sáng/tối, cỡ chữ
    └── workers.py       # Chạy tác vụ nặng trong luồng nền
```

Tiến độ học và cài đặt nằm ở `%APPDATA%\MyOSAcademy\academy.db`.

## Chạy từ mã nguồn (Windows)

**Cách dễ nhất:** bấm đúp vào `run.bat`. Lần đầu nó tự tạo môi trường ảo `.venv`, cài thư viện vào **đúng** Python đó
rồi mở app. Các lần sau bấm đúp là chạy.

**Cách thủ công:**

Cần Python 3.11 trở lên (tải tại python.org, nhớ tích "Add python.exe to PATH").

Mở PowerShell trong thư mục `myos-academy`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Nếu PowerShell báo không cho chạy script, chạy một lần lệnh
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` rồi thử lại.

## Định dạng một bài học

Mỗi bài là một file Markdown `content/lessons/<mã bài>.md` với các mục `## Mục tiêu`, `## Lý thuyết`,
`## Code`, `## Giải thích từng dòng` (bảng hai cột), `## Kết quả mong đợi`, `## Lỗi hay gặp`, `## Bài tập`,
`## Câu hỏi kiểm tra`, `## Bản nghe`, `## Video tham khảo`. Các quy ước riêng:

- Dòng bắt đầu bằng `Gợi ý:` bị ẩn, chỉ hiện khi bấm "Xin gợi ý".
- Dòng `- youtube: từ khóa | ghi chú` thành nút mở trang tìm kiếm YouTube.
- Khối code ghi tên file bằng ```` ```nasm title=boot.asm ````.

## Hoạt hình bài giảng

Bài nào có nút **🎬 Xem hoạt hình** sẽ mở một cửa sổ chạy chương trình assembly **từng lệnh một**, giống một video
có thuyết minh: dòng code vừa chạy sáng lên, thanh ghi và ô stack vừa đổi sáng màu vàng, có nút Phát / Dừng / Lùi /
Tới và thanh tua. Giá trị trên màn hình do `core/x86sim.py` tính ra khi chạy thật kịch bản, không gõ tay.

Kịch bản nằm ở `content/animations/<mã bài>.json` (định dạng mô tả ở đầu `ui/animation_dialog.py`).

## Nghe đọc

Trong mỗi bài có hai nút:

- **🎓 Nghe giảng**: đọc to mục tiêu, lý thuyết và lỗi hay gặp, bỏ qua code, bảng và sơ đồ.
- **🎧 Nghe tóm tắt**: đọc phần Bản nghe.

Đoạn đang đọc được tô sáng và trang tự cuộn theo. Chọn bộ đọc trong **Cài đặt**:

- **edge-tts** (mặc định): giọng tiếng Việt tự nhiên (Hoài My, Nam Minh), cần Internet. Đoạn đã nghe được lưu ở
  `%APPDATA%\MyOSAcademy\audio`, nghe lại không cần mạng.
- **pyttsx3**: offline, dùng giọng có sẵn của Windows. Muốn có giọng tiếng Việt, cài gói giọng nói tiếng Việt trong
  Settings → Time & language → Speech; nếu không, nó đọc bằng giọng tiếng Anh.

## Build file .exe

Có ở Bước 7.

## Lỗi hay gặp khi chạy

**`ImportError: DLL load failed while importing Shiboken: The specified procedure could not be found`**

Nguyên nhân thường gặp nhất là bộ thư viện Microsoft Visual C++ Runtime trên máy đã cũ. PySide6 cần bản mới.

1. Cài bản mới nhất của **Microsoft Visual C++ Redistributable (x64)**: https://aka.ms/vs/17/release/vc_redist.x64.exe, rồi khởi động lại PowerShell.
2. Cài lại PySide6 cho sạch:
   ```powershell
   pip uninstall -y PySide6 PySide6-Essentials PySide6-Addons shiboken6
   pip install --no-cache-dir -r requirements.txt
   ```
3. Kiểm tra Python là bản **64-bit**, từ **3.11 đến 3.13**:
   `python -c "import sys, platform; print(sys.version, platform.architecture()[0])"`
