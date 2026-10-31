# MyOS Academy

Ứng dụng desktop Windows dạy bạn tự viết hệ điều hành bằng C++, với nội dung bài học do Claude soạn.

> Trạng thái: **Bước 2/7**: cây lộ trình 10 giai đoạn / 42 bài, trạng thái bài lưu SQLite.

## Cấu trúc thư mục

```
myos-academy/
├── main.py              # Điểm khởi động app
├── requirements.txt
├── core/                # Logic không phụ thuộc giao diện
│   ├── paths.py         # Đường dẫn %APPDATA%\MyOSAcademy
│   ├── settings.py      # AppSettings: model, giọng đọc, cỡ chữ, giao diện
│   ├── roadmap.py       # Lộ trình: giai đoạn, bài, tài liệu tham khảo, từ khóa video
│   ├── progress.py      # Trạng thái bài (chưa học/đang học/xong) và luật mở khóa
│   ├── credentials.py   # Lưu API key bằng keyring (Windows Credential Manager)
│   └── claude_client.py # Tạo client anthropic + dịch lỗi sang tiếng Việt
├── data/
│   └── database.py      # SQLite + migration theo PRAGMA user_version
└── ui/                  # Giao diện PySide6
    ├── main_window.py   # Cửa sổ chính
    ├── roadmap_tree.py  # Cây lộ trình bên trái (chuột phải: đổi trạng thái, mở khóa)
    ├── lesson_panel.py  # Trang chào, trang giai đoạn, trang bài
    ├── settings_dialog.py
    ├── theme.py         # Sáng/tối, cỡ chữ
    └── workers.py       # Chạy tác vụ mạng trong luồng nền
```

Dữ liệu người dùng nằm ở `%APPDATA%\MyOSAcademy\academy.db`. API key **không** nằm trong file này mà nằm trong Windows Credential Manager (mục `MyOSAcademy`).

## Chạy từ mã nguồn (Windows)

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

## Lấy API key

Vào console.anthropic.com → API Keys → Create Key, rồi dán key vào **Tệp → Cài đặt** trong app.

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
