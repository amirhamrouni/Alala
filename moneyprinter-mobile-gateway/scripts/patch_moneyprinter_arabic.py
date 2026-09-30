#!/usr/bin/env python3
"""Patch a Colab MoneyPrinterTurbo checkout for Arabic subtitles.

Idempotent runtime patch:
- copies a system font with Arabic glyphs into resource/fonts
- installs arabic-reshaper + python-bidi in MoneyPrinterTurbo's venv
- auto-selects the Arabic-capable font for Arabic video_language
- reshapes and reorders Arabic subtitle lines immediately before TextClip rendering
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


FONT_NAME = "DejaVuSans.ttf"
FONT_CANDIDATES = (
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/truetype/freefont/FreeSans.ttf"),
)
PATCH_MARK = "# ALALA_ARABIC_RTL_PATCH"


def find_font() -> Path:
    for path in FONT_CANDIDATES:
        if path.is_file():
            return path
    raise RuntimeError("No Arabic-capable system font was found")


def install_dependencies(repo: Path) -> None:
    python_bin = repo / ".venv" / "bin" / "python"
    if not python_bin.is_file():
        raise RuntimeError(f"MoneyPrinter venv Python not found: {python_bin}")
    subprocess.run(
        [
            "uv",
            "pip",
            "install",
            "--python",
            str(python_bin),
            "arabic-reshaper>=3.0.0",
            "python-bidi>=0.6.0",
        ],
        cwd=repo,
        check=True,
    )


def patch_video_py(repo: Path) -> bool:
    target = repo / "app" / "services" / "video.py"
    text = target.read_text(encoding="utf-8")
    if PATCH_MARK in text:
        return False

    helper_anchor = "from PIL import Image, ImageDraw, ImageFont\n"
    helper = '''from PIL import Image, ImageDraw, ImageFont

# ALALA_ARABIC_RTL_PATCH
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except Exception:
    arabic_reshaper = None
    get_display = None


def _alala_contains_arabic(text: str) -> bool:
    return any(
        "\\u0600" <= ch <= "\\u06ff"
        or "\\u0750" <= ch <= "\\u077f"
        or "\\u08a0" <= ch <= "\\u08ff"
        or "\\ufb50" <= ch <= "\\ufdff"
        or "\\ufe70" <= ch <= "\\ufeff"
        for ch in str(text or "")
    )


def _alala_rtl_display(text: str) -> str:
    if not _alala_contains_arabic(text):
        return text
    if arabic_reshaper is None or get_display is None:
        return text

    shaped_lines = []
    for line in str(text).split("\\n"):
        if _alala_contains_arabic(line):
            reshaped = arabic_reshaper.reshape(line)
            shaped_lines.append(get_display(reshaped, base_dir="R"))
        else:
            shaped_lines.append(line)
    return "\\n".join(shaped_lines)
'''
    if helper_anchor not in text:
        raise RuntimeError("Could not find Pillow import anchor in video.py")
    text = text.replace(helper_anchor, helper, 1)

    font_anchor = '''    if params.subtitle_enabled:
        if not params.font_name:
            params.font_name = "STHeitiMedium.ttc"
'''
    font_replacement = '''    if params.subtitle_enabled:
        language = str(getattr(params, "video_language", "") or "").strip().lower()
        if language in {"ar", "arabic", "ar-ar", "ar-sa", "ar-eg", "ar-tn"}:
            arabic_font = os.path.join(utils.font_dir(), "DejaVuSans.ttf")
            if os.path.isfile(arabic_font):
                params.font_name = "DejaVuSans.ttf"
        if not params.font_name:
            params.font_name = "STHeitiMedium.ttc"
'''
    if font_anchor not in text:
        raise RuntimeError("Could not find subtitle font selection anchor in video.py")
    text = text.replace(font_anchor, font_replacement, 1)

    wrap_anchor = '''        wrapped_txt, txt_height = wrap_text(
            phrase,
            max_width=text_max_width,
            font=font_path,
            fontsize=params.font_size,
        )
        interline = int(params.font_size * 0.25)
'''
    wrap_replacement = '''        wrapped_txt, txt_height = wrap_text(
            phrase,
            max_width=text_max_width,
            font=font_path,
            fontsize=params.font_size,
        )
        wrapped_txt = _alala_rtl_display(wrapped_txt)
        interline = int(params.font_size * 0.25)
'''
    if wrap_anchor not in text:
        raise RuntimeError("Could not find subtitle wrapping anchor in video.py")
    text = text.replace(wrap_anchor, wrap_replacement, 1)

    target.write_text(text, encoding="utf-8")
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default="/content/MoneyPrinterTurbo")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not (repo / "app" / "services" / "video.py").is_file():
        raise RuntimeError(f"Not a MoneyPrinterTurbo checkout: {repo}")

    font_source = find_font()
    font_dest = repo / "resource" / "fonts" / FONT_NAME
    font_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(font_source, font_dest)

    install_dependencies(repo)
    changed = patch_video_py(repo)

    print(f"Arabic font: {font_dest}")
    print("Arabic RTL patch:", "applied" if changed else "already applied")


if __name__ == "__main__":
    main()
