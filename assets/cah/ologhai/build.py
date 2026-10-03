#!/usr/bin/env python3
"""Build the cah pack's Olog-hai (Troll, Snow Troll, Hill Troll) into build/assets/cah/ologhai/
with the kit (assets/cah/kit/models.py): EA's sources (hash-checked), both sheets and masks, our
six models, the INI fragment, every check. Nothing in the game changes.

    python3 -m assets.cah.ologhai.build [--skip-paint]
"""
import sys

from ..kit.models import build_class
from . import design

if __name__ == "__main__":
    build_class(design, design.paint, skip_paint="--skip-paint" in sys.argv[1:])
