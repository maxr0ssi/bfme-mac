"""Angmar's effects (sagekit/fx, docs/ART.md "Effects"): the shared spell book powers and the
buildings' fire and smoke in Carn Dum's cold colours, from assets/angmar/style.py.

    magic   the slits' ramp: navy to icy cyan to rime white (EA's evil glows are blood red)
    fire    the citadel's cold fire ramp: navy, ice-blue, white-hot (as SagekitColdFire)
    smoke   blue-black (as SagekitColdSmoke): EA's grey plumes, their value kept, a cold cast

The pilot (2026-10-04): the powers Angmar shares with the other evil books (War Chant, Summon Orcs
and Giants, Untamed Allegiance), and the fire and smoke on its damaged buildings. Angmar's own
powers (Snowbind, Frozen Land, Avalanche, Shade of the Wolf, Summon Wights, Blight) are EA's frost
and wight colours already, and stay EA's.
"""
from sagekit.fx.plan import FactionFX
from sagekit.fx.tint import ramp_from

from .style import NAVY, PALETTE


class AngmarFX(FactionFX):
    faction = "angmar"
    tag = "Angmar"
    books = ("AngmarSpellBook",)
    ramps = dict(magic=ramp_from(PALETTE.ramps["slit"], name="slit"),
                 fire=ramp_from(PALETTE.ramps["fire"], name="cold fire"),
                 smoke=ramp_from([(0, (0, 0, 0)), (1, NAVY)], chroma=0.3, name="blue-black"))
    powers = ("SpellBookWarChant", "SpellBookSummonOrcs", "SpellBookSummonGiants", "SpellBookUntamedAllegiance")
    structures = ("fire", "smoke")
