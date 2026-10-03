#!/usr/bin/env python3
"""Build the cah pack's Shieldmaiden into build/assets/cah/men_sm/ with the kit
(assets/cah/kit/models.py): EA's sources (hash-checked), both sheets and masks (the Men's tiles,
assets/cah/men_cg/paint.py, under her own names), our three models (_U, _C, mounted _M), the INI
fragment, every check. Nothing in the game changes.

    python3 -m assets.cah.men_sm.build [--skip-paint]
"""
import sys

from ..kit.models import build_class
from ..men_cg.paint import paint
from . import design

if __name__ == "__main__":
    build_class(design, lambda work: paint(work, "skcah_hwsm"), skip_paint="--skip-paint" in sys.argv[1:])
