"""Mordor's effects (sagekit/fx, docs/ART.md "Effects"): palette F2 "Fire, shadow and steel" from
assets/mordor/style.py, in the shared evil powers and the fire and smoke of its damaged buildings.

    magic   the lava ramp: ember to orange to white-hot (EA's War Chant is blood red)
    fire    the lava ramp (EA's flames, a deeper orange)
    smoke   ash: EA's grey plumes, their value kept, a warm cast

Taint keeps EA's own Morgul green (Max: green sparingly); the rest of Mordor's book is EA's.
"""
from sagekit.fx.plan import FactionFX
from sagekit.fx.tint import ramp_from

from .style import PALETTE


class MordorFX(FactionFX):
    faction = "mordor"
    tag = "Mordor"
    books = ("MordorSpellBook",)
    ramps = dict(magic=ramp_from(PALETTE.ramps["fire"], name="lava"),
                 fire=ramp_from(PALETTE.ramps["fire"], name="lava"),
                 smoke=ramp_from([(0, (0, 0, 0)), (1, (1.0, .82, .66))], chroma=0.3, name="ash"))
    powers = ("SpellBookWarChant", "SpellBookIndustry", "SpellBookUntamedAllegiance")
    # Industry's flare: near-black keys (13, 6, 2) that its glowing slave rides on; a glow all the same
    systems = {"IndustryFlare": "magic"}
    structures = ("fire", "smoke")
