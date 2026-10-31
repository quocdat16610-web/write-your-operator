@echo off
rem Checks each read-aloud step (synthesis, MCI playback, pyttsx3) and prints what fails.
cd /d "%~dp0"
".venv\Scripts\python.exe" diag_voice.py
