"""Project paths + font preparation. Everything is relative to the package root."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLANTS_DIR = ROOT / "plants"
PLANTS_SRC = PLANTS_DIR / "out"                  # master plant SVGs
BUILD = ROOT / "build"
PLANTS_PRINT = BUILD / "plants_print"            # print-prepped copies used on the cards
FONTS = ROOT / "fonts"
STATIC_FONTS = BUILD / "fonts"

DM_SERIF = FONTS / "DMSerifDisplay-Regular.ttf"
FRAUNCES_VAR = FONTS / "Fraunces[SOFT,WONK,opsz,wght].ttf"
FRAUNCES_ITALIC_VAR = FONTS / "Fraunces-Italic[SOFT,WONK,opsz,wght].ttf"
FRAUNCES_MEDIUM = STATIC_FONTS / "Fraunces-Medium-static.ttf"
FRAUNCES_ITALIC = STATIC_FONTS / "Fraunces-Italic-static.ttf"


def ensure_static_fonts():
    """Instance the variable Fraunces fonts used for the plant-name labels (done once, into build/fonts)."""
    if FRAUNCES_MEDIUM.exists() and FRAUNCES_ITALIC.exists():
        return
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    STATIC_FONTS.mkdir(parents=True, exist_ok=True)
    for src, dst, wght in ((FRAUNCES_VAR, FRAUNCES_MEDIUM, 560), (FRAUNCES_ITALIC_VAR, FRAUNCES_ITALIC, 400)):
        inst = instancer.instantiateVariableFont(TTFont(str(src)), {"wght": wght, "opsz": 9, "SOFT": 0, "WONK": 0})
        inst.save(str(dst))
