#!/usr/bin/env python3
"""Build the cah pack's Captain of Gondor into build/assets/cah/men_cg/ with the kit
(assets/cah/kit/models.py): EA's sources (hash-checked), both sheets and masks, our three models
(_U, _C, mounted _M), the INI fragment, every check. Nothing in the game changes.

    python3 -m assets.cah.men_cg.build [--skip-paint]
"""
import sys

from ..kit.models import build_class
from . import design
from .paint import paint

if __name__ == "__main__":
    build_class(design, lambda work: paint(work, "skcah_hwcg"), skip_paint="--skip-paint" in sys.argv[1:])
