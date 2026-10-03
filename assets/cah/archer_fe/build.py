#!/usr/bin/env python3
"""Build the cah pack's Female Elven Archer into build/assets/cah/archer_fe/ with the kit
(assets/cah/kit/models.py): EA's sources (hash-checked), both sheets and masks, our two models, the
INI fragment, every check. Nothing in the game changes.

    python3 -m assets.cah.archer_fe.build [--skip-paint]
"""
import sys

from ..archer_el.build import sheets
from ..kit.models import build_class
from . import design

if __name__ == "__main__":
    build_class(design, sheets(design), skip_paint="--skip-paint" in sys.argv[1:])
