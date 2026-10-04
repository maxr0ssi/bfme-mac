"""The Men's effects (sagekit/fx, docs/ART.md "Effects"): Gondor white-gold, from "Gondor: white stone,
steel and sable" (assets/men/style.py), in the good powers Gondor and Arnor share and the fire and
smoke of their damaged buildings (Max, 2026-10-04: the good factions take their colours too).

    magic   the Gondor gold ramp, topped with white: muted warm gold to white (Rallying Call, Heal, Rebuild)
    fire    the same white-gold ramp: a golden fire, white-hot at the core, never grey or blue
    smoke   EA's grey plumes, their value kept, a faint warm-white cast

The Army of the Dead keeps EA's ghost green.
"""
from sagekit.fx.plan import FactionFX
from sagekit.fx.tint import ramp_from

from .style import PALETTE

WHITE_GOLD = list(PALETTE.ramps["gold"]) + [(1.05, (1.0, .98, .92))]


class MenFX(FactionFX):
    faction = "men"
    tag = "Men"
    books = ("MenSpellBook", "ArnorSpellBook")
    ramps = dict(magic=ramp_from(WHITE_GOLD, name="Gondor white-gold"),
                 fire=ramp_from(WHITE_GOLD, name="Gondor white-gold"),
                 smoke=ramp_from([(0, (0, 0, 0)), (1, (1.0, .95, .85))], chroma=0.2, name="warm white-grey"))
    powers = ("SpellBookRallyingCall", "SpellBookHeal", "SpellBookRebuild")
    structures = ("fire", "smoke")
