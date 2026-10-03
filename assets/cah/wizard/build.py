#!/usr/bin/env python3
"""Build the cah pack's Wizards into build/assets/cah/wizard/ with the kit
(assets/cah/kit/models.py): EA's sources (hash-checked), both sheets and masks, our six models
(Wanderer, Avatar, Hermit; _U and _C), the INI fragment, every check. Nothing in the game changes.

    python3 -m assets.cah.wizard.build [--skip-paint]
"""
import sys

from ..kit.models import build_class
from . import design
from .paint import paint

if __name__ == "__main__":
    build_class(design, paint, skip_paint="--skip-paint" in sys.argv[1:])
