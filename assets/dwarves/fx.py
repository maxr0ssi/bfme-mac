"""The Dwarves' effects (sagekit/fx, docs/ART.md "Effects"): Erebor gold, from "Honey granite & gold"
(assets/dwarves/style.py), in the good powers they share and the fire and smoke of their damaged
buildings (Max, 2026-10-04: the good factions take their colours too).

    magic   the gold ramp: deep amber to honey gold to white (Dwarven Riches, Rallying Call, Rebuild)
    fire    the same gold ramp: a forge-gold fire, its core still white-hot, never grey or blue
    smoke   EA's grey plumes, their value kept, a warm gold cast
"""
from sagekit.fx.plan import FactionFX
from sagekit.fx.tint import ramp_from

from .style import PALETTE


class DwarvesFX(FactionFX):
    faction = "dwarves"
    tag = "Dwarves"
    books = ("DwarvesSpellBook",)
    ramps = dict(magic=ramp_from(PALETTE.ramps["gold"], name="Erebor gold"),
                 fire=ramp_from(PALETTE.ramps["gold"], name="Erebor gold"),
                 smoke=ramp_from([(0, (0, 0, 0)), (1, (1.0, .88, .62))], chroma=0.25, name="warm grey"))
    powers = ("SpellBookRallyingCall", "SpellBookHeal", "SpellBookRebuild", "SpellBookDwarvenRiches")
    structures = ("fire", "smoke")
