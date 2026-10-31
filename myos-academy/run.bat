@echo off
rem One-click launcher: creates .venv on first run, installs dependencies into it, starts the app.
setlocal
cd /d "%~dp0"
set "VENV_PY=.venv\Scripts\python.exe"
set "CHECK_PY=import sys; sys.exit(sys.version_info[:3] < (3, 9, 2))"

rem Prefer a recent Python if the py launcher knows one.
set "NEW_PY="
for %%V in (3.13 3.12 3.11 3.10) do (
    if not defined NEW_PY (
        py -%%V -c "pass" >nul 2>&1 && set "NEW_PY=py -%%V"
    )
)

rem Python 3.9.0/3.9.1 have a typing bug that breaks edge-tts ("unhashable type: 'list'").
rem If a newer Python is installed, rebuild .venv with it.
if exist "%VENV_PY%" if defined NEW_PY (
    "%VENV_PY%" -c "%CHECK_PY%" || (
        echo [MyOS Academy] .venv dang dung Python 3.9.1 bi loi, tao lai bang %NEW_PY%...
        rmdir /s /q .venv
    )
)

if not exist "%VENV_PY%" (
    echo [MyOS Academy] Tao moi truong ao .venv...
    if defined NEW_PY (
        %NEW_PY% -m venv .venv
    ) else (
        py -3 -m venv .venv 2>nul || python -m venv .venv
    )
)
if not exist "%VENV_PY%" (
    echo Khong tao duoc .venv. Hay cai Python tu https://www.python.org/downloads/ roi chay lai.
    pause
    exit /b 1
)

"%VENV_PY%" -c "%CHECK_PY%" || (
    echo.
    echo [Canh bao] Python 3.9.1 tren may co loi lam giong doc edge-tts khong chay.
    echo Cai Python 3.12 tu https://www.python.org/downloads/ roi chay lai run.bat.
    echo.
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
