"""Locations of files the app writes (database, logs, cached audio)."""
from __future__ import annotations

import os
from pathlib import Path

APP_DIR_NAME = "MyOSAcademy"


def app_data_dir() -> Path:
    """Return %APPDATA%\\MyOSAcademy on Windows, ~/.config/MyOSAcademy elsewhere."""
    base = os.environ.get("APPDATA")
    root = Path(base) if base else Path.home() / ".config"
    path = root / APP_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def database_path() -> Path:
    return app_data_dir() / "academy.db"
