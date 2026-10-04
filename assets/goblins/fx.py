"""The Goblins' effects (sagekit/fx, docs/ART.md "Effects"): palette E "Blood, iron and bone" from
assets/goblins/style.py, in the shared evil powers and the fire and smoke of their damaged buildings.

    magic   the crimson fire ramp (cool crimson, never orange)
    fire    the crimson fire ramp: their burning holds blaze blood red
    smoke   EA's grey plumes, their value kept, a red-black cast

Taint, Cave Bats, Spiderlings and the summons of beasts keep EA's colours.
"""
from sagekit.fx.plan import FactionFX
from sagekit.fx.tint import ramp_from

from .style import PALETTE


class GoblinsFX(FactionFX):
    faction = "goblins"
    tag = "Goblins"
    books = ("WildSpellBook",)
    ramps = dict(magic=ramp_from(PALETTE.ramps["fire"], name="crimson"),
                 fire=ramp_from(PALETTE.ramps["fire"], name="crimson"),
                 smoke=ramp_from([(0, (0, 0, 0)), (1, (1.0, .74, .74))], chroma=0.3, name="red-black"))
    powers = ("SpellBookWarChant", "SpellBookWildMenAllies", "SpellBookUntamedAllegiance")
    structures = ("fire", "smoke")
