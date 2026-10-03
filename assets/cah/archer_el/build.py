#!/usr/bin/env python3
"""Build the cah pack's Elven Archer into build/assets/cah/archer_el/ with the kit
(assets/cah/kit/models.py): EA's sources (hash-checked), both sheets and masks, our two models, the
INI fragment, every check. Nothing in the game changes.

    python3 -m assets.cah.archer_el.build [--skip-paint]
"""
import sys

from ..kit.models import build_class
from . import design
from .paint import paint


def sheets(spec):
    return lambda work: paint(work, *(spec.SHEETS[k].lower()[:-4] for k in ("serious", "fun")))


if __name__ == "__main__":
    build_class(design, sheets(design), skip_paint="--skip-paint" in sys.argv[1:])
