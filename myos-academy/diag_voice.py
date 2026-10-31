"""Check each step of read-aloud separately. Run: .venv\\Scripts\\python.exe diag_voice.py"""
from __future__ import annotations

import sys
import time
import traceback
from pathlib import Path

TEXT = "Xin chào, đây là bài kiểm tra giọng đọc của MyOS Academy."


def step(title: str) -> None:
    print(f"\n=== {title} ===", flush=True)


def play_with_mci(path: Path) -> None:
    from ui.audio_player import ALIAS, _mci

    _mci(f'open "{path}" type mpegvideo alias {ALIAS}')
    try:
        print("length (ms):", _mci(f"status {ALIAS} length"))
        _mci(f"play {ALIAS}")
        for _ in range(100):  # up to 20 seconds
            mode = _mci(f"status {ALIAS} mode")
            print("  mode:", mode, flush=True)
            if mode == "stopped":
                break
            time.sleep(0.2)
    finally:
        _mci(f"close {ALIAS}")


def main() -> None:
    print("Python:", sys.version.split()[0], sys.executable)

    step("1. edge-tts tao file mp3 (can Internet)")
    out = Path("diag_voice.mp3").resolve()
    try:
        from core.tts import synthesize_edge
        synthesize_edge(TEXT, "vi-VN-HoaiMyNeural", 1.0, out)
        print("OK, file:", out, "-", out.stat().st_size, "bytes")
    except Exception:
        traceback.print_exc()
        out = None

    step("2. Phat file mp3 bang MCI cua Windows")
    if out is None:
        print("Bo qua vi buoc 1 loi.")
    elif sys.platform != "win32":
        print("Bo qua: chi chay tren Windows.")
    else:
        try:
            play_with_mci(out)
            print("OK: ban co nghe thay cau 'Xin chao...' khong?")
        except Exception:
            traceback.print_exc()

    step("3. pyttsx3 doc truc tiep (offline)")
    try:
        import pyttsx3
        engine = pyttsx3.Engine()
        voices = engine.getProperty("voices")
        for voice in voices:
            print("  giong:", voice.name, "|", voice.id)
        engine.say("Hello, this is the Windows voice test.")
        engine.runAndWait()
        print("OK: ban co nghe thay cau tieng Anh khong?")
    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    main()
    try:
        input("\nNhan Enter de dong...")
    except EOFError:
        pass
