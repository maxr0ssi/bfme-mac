"""Isengard's effects (sagekit/fx, docs/ART.md "Effects"): palette A "Orthanc black and silver" from
assets/isengard/style.py, in the shared evil powers and the fire and smoke of its damaged buildings.

    magic   the forge-ember ramp (EA's War Chant is blood red, Devastation's flare green-yellow)
    fire    the forge-ember ramp (close to EA's orange)
    smoke   soot: EA's grey plumes, their value kept, Orthanc's cold blue-black cast

Isengard's Taint keeps EA's swamp green; the rest of its book is EA's.
"""
from sagekit.fx.plan import FactionFX
from sagekit.fx.tint import ramp_from

from .style import PALETTE


class IsengardFX(FactionFX):
    faction = "isengard"
    tag = "Isengard"
    books = ("IsengardSpellBook",)
    ramps = dict(magic=ramp_from(PALETTE.ramps["fire"], name="ember"),
                 fire=ramp_from(PALETTE.ramps["fire"], name="ember"),
                 smoke=ramp_from([(0, (0, 0, 0)), (1, (.86, .90, 1.0))], chroma=0.3, name="soot"))
    powers = ("SpellBookWarChant", "SpellBookIndustry", "SpellBookWildMenAllies", "SpellBookDevastation")
    # Industry's flare: near-black keys (13, 6, 2) that its glowing slave rides on; a glow all the same
    systems = {"IndustryFlare": "magic"}
    structures = ("fire", "smoke")
