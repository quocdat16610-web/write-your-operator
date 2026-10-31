@echo off
rem One-click launcher: creates .venv on first run, installs dependencies into it, starts the app.
setlocal
cd /d "%~dp0"
set "VENV_PY=.venv\Scripts\python.exe"

if not exist "%VENV_PY%" (
    echo [MyOS Academy] Tao moi truong ao .venv lan dau...
    py -3 -m venv .venv 2>nul || python -m venv .venv
)
if not exist "%VENV_PY%" (
    echo Khong tao duoc .venv. Hay cai Python tu python.org roi chay lai.
    pause
    exit /b 1
)

echo [MyOS Academy] Kiem tra thu vien...
"%VENV_PY%" -m pip install --disable-pip-version-check -q -r requirements.txt

rem Newer PySide6 builds fail to load on some machines ("DLL load failed"); fall back to 6.6.3.1.
"%VENV_PY%" -c "import PySide6.QtWidgets" 2>nul
if errorlevel 1 (
    echo [MyOS Academy] PySide6 moi khong chay tren may nay, chuyen sang ban 6.6.3.1...
    "%VENV_PY%" -m pip install --disable-pip-version-check -q --force-reinstall "PySide6-Essentials==6.6.3.1" "shiboken6==6.6.3.1"
)

"%VENV_PY%" main.py
if errorlevel 1 pause
