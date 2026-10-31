"""Turn a lesson's Markdown into paragraphs to read aloud: no code, no tables, symbols spelled out."""
from __future__ import annotations

import re
from dataclasses import dataclass

LECTURE_SECTIONS = ("Mục tiêu", "Lý thuyết", "Lỗi hay gặp")
SUMMARY_SECTION = "Bản nghe"

FENCE_RE = re.compile(r"^```.*?^```[ \t]*$", re.M | re.S)
SECTION_RE = re.compile(r"^## +(.+?)[ \t]*$", re.M)
LIST_ITEM_RE = re.compile(r"^(?:[-*]|\d+\.)\s+")


@dataclass(frozen=True)
class Segment:
    spoken: str  # what the voice says
    anchor: str  # plain text as it appears on screen, used to highlight the paragraph


def _sections(source: str) -> dict[str, str]:
    parts = SECTION_RE.split(source)
    # parts = [before, title1, body1, title2, body2, ...]
    return {parts[i].strip(): parts[i + 1] for i in range(1, len(parts) - 1, 2)}


def plain_text(markdown_text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", markdown_text)  # [label](url) -> label
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"^#{1,6}\s+", "", text)
    text = LIST_ITEM_RE.sub("", text)
    return " ".join(text.split())


def spoken_text(plain: str) -> str:
    text = re.sub(r"\b0x([0-9A-Fa-f]+)\b", lambda m: "không x " + " ".join(m.group(1).upper()), plain)
    text = text.replace("×", " nhân ").replace(" = ", " bằng ").replace("→", " rồi ")
    text = re.sub(r"[►◄▼│┌└├─]+", " ", text)
    return " ".join(text.split())


def _paragraphs(body: str) -> list[Segment]:
    segments: list[Segment] = []
    body = FENCE_RE.sub("", body)
    for block in re.split(r"\n\s*\n", body):
        lines = [line for line in block.strip().splitlines() if line.strip()]
        if not lines or lines[0].lstrip().startswith("|"):
            continue  # tables are read with the eyes
        if LIST_ITEM_RE.match(lines[0]):
            chunks = []
            for line in lines:
                if LIST_ITEM_RE.match(line) or not chunks:
                    chunks.append(line)
                else:
                    chunks[-1] += " " + line
        else:
            chunks = [" ".join(lines)]
        for chunk in chunks:
            if chunk.startswith(("Gợi ý:", "- youtube:", "![")):
                continue
            plain = plain_text(chunk)
            if plain:
                segments.append(Segment(spoken_text(plain), plain))
    return segments


def lecture_segments(source: str) -> list[Segment]:
    """The 'teacher' reading: goal, theory and common mistakes, each introduced by its heading."""
    sections = _sections(source)
    segments: list[Segment] = []
    for title in LECTURE_SECTIONS:
        if title in sections:
            segments.append(Segment(f"Phần {title.lower()}.", title))
            segments.extend(_paragraphs(sections[title]))
    return segments


def summary_segments(source: str) -> list[Segment]:
    return _paragraphs(_sections(source).get(SUMMARY_SECTION, ""))
