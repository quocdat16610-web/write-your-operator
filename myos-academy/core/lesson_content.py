"""Lessons written ahead of time, shipped with the app as Markdown files in content/lessons/<id>.md.

Each file uses fixed level-2 headings (## Mục tiêu, ## Lý thuyết, ## Code, ...). Extra conventions:
- a line starting with "Gợi ý:" is a hidden hint, shown only when the learner asks for it;
- a list item "- youtube: <search words> | <what to watch for>" becomes a YouTube search link;
- images use normal Markdown, with paths relative to content/: ![caption](images/name.png).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def content_root() -> Path:
    # PyInstaller unpacks bundled data under sys._MEIPASS; from source it sits next to core/.
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base / "content"


def content_dir() -> Path:
    return content_root() / "lessons"


def load_lesson(lesson_id: str) -> str | None:
    path = content_dir() / f"{lesson_id}.md"
    return path.read_text(encoding="utf-8") if path.exists() else None


def load_animations(lesson_id: str) -> list[dict]:
    """Step-by-step animations for a lesson: content/animations/<id>.json (see ui/animation_dialog.py)."""
    path = content_root() / "animations" / f"{lesson_id}.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))["animations"]


def available_lessons() -> set[str]:
    return {path.stem for path in content_dir().glob("*.md")}
