"""Turn a lesson's Markdown into HTML that QTextBrowser can show.

Code blocks are highlighted with Pygments (inline styles, since Qt's CSS support is limited) and get a
Copy link. Links use custom schemes that LessonPanel handles: copy:<n>, hint:<n>, and normal http(s).
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass, field

import markdown
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_by_name
from pygments.util import ClassNotFound

from core.roadmap import youtube_search_url

FENCE_RE = re.compile(r"^```([\w+-]*)[ \t]*(?:title=(\S+))?[ \t]*\n(.*?)^```[ \t]*$", re.M | re.S)
HINT_RE = re.compile(r"^Gợi ý:[ \t]*(.+)$", re.M)
YOUTUBE_RE = re.compile(r"^- youtube:[ \t]*(.+?)[ \t]*(?:\|[ \t]*(.+))?$", re.M)
IMAGE_WIDTH = 720
LEXER_ALIASES = {"asm": "nasm", "linker": "text", "ld": "text", "sh": "bash", "shell": "bash"}


def rich(text: str) -> str:
    """Escape text for HTML and turn `backticks` into <code>."""
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", html.escape(text))


@dataclass
class CodeBlock:
    language: str
    title: str | None
    code: str


@dataclass
class RenderedLesson:
    html: str
    code_blocks: list[CodeBlock] = field(default_factory=list)


def _lexer(language: str):
    name = LEXER_ALIASES.get(language, language) or "text"
    try:
        return get_lexer_by_name(name)
    except ClassNotFound:
        return TextLexer()


def _code_html(index: int, block: CodeBlock, dark: bool) -> str:
    style = "monokai" if dark else "friendly"
    formatter = HtmlFormatter(noclasses=True, style=style, nowrap=True)
    body = highlight(block.code, _lexer(block.language), formatter)
    background = formatter.style.background_color or ("#272822" if dark else "#f0f0f0")
    # Tokens without a colour inherit this, not the window palette (light text on light code is unreadable).
    foreground = "#f8f8f2" if dark else "#1e1e1e"
    label = html.escape(block.title or block.language or "")
    copy = "" if block.language in ("", "text") else f"<a href='copy:{index}'>📋 Copy</a>"
    header = ""
    if label or copy:
        header = (f"<tr><td bgcolor='{'#3a3b3f' if dark else '#dcdcdc'}'>"
                  f"<b><font color='{'#f0f0f0' if dark else '#1e1e1e'}'>{label}</font></b>"
                  f"&nbsp;&nbsp;&nbsp;{copy}</td></tr>")
    return (f"<table width='100%' cellspacing='0' cellpadding='8' border='0'>{header}"
            f"<tr><td bgcolor='{background}'><pre style='margin:0; color:{foreground}'>{body}</pre></td></tr></table>")


def render_lesson(source: str, revealed_hints: set[int], dark: bool) -> RenderedLesson:
    blocks: list[CodeBlock] = []
    hints: list[str] = []

    def take_code(match: re.Match) -> str:
        blocks.append(CodeBlock(match.group(1).lower(), match.group(2), match.group(3).rstrip("\n")))
        return f"\n\nCODEBLOCK{len(blocks) - 1}\n\n"

    def take_hint(match: re.Match) -> str:
        hints.append(match.group(1))
        return f"\n\nHINTBLOCK{len(hints) - 1}\n\n"

    def youtube_link(match: re.Match) -> str:
        query, note = match.group(1), match.group(2)
        link = f"[🔎 {query}]({youtube_search_url(query)})"
        return f"- {link}" + (f": {note}" if note else "")

    source = re.sub(r"\A# .*\n", "", source)  # the panel header already shows the title
    text = FENCE_RE.sub(take_code, source)  # first, so hint/youtube syntax inside code is left alone
    text = HINT_RE.sub(take_hint, text)
    text = YOUTUBE_RE.sub(youtube_link, text)

    body = markdown.markdown(text, extensions=["tables", "sane_lists"])
    body = body.replace("<table>", "<table border='1' cellspacing='0' cellpadding='6' width='100%'>")
    body = body.replace("<img ", f"<img width='{IMAGE_WIDTH}' ")  # PNGs are drawn at 2x for sharpness
    for index, block in enumerate(blocks):
        body = body.replace(f"<p>CODEBLOCK{index}</p>", _code_html(index, block, dark))
    for index, hint in enumerate(hints):
        inner = markdown.markdown(hint).removeprefix("<p>").removesuffix("</p>")
        shown = (f"<p>💡 <b>Gợi ý:</b> {inner}</p>" if index in revealed_hints
                 else f"<p><a href='hint:{index}'>💡 Xin gợi ý</a></p>")
        body = body.replace(f"<p>HINTBLOCK{index}</p>", shown)
    return RenderedLesson(body, blocks)
