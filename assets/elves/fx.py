"""The Elves' effects (sagekit/fx, docs/ART.md "Effects"): moonsilver, from "Ivory, mithril and mallorn
gold" (assets/elves/style.py), in the good powers they share and the fire and smoke of their damaged
buildings (Max, 2026-10-04: the good factions take their colours too).

    magic   the mithril ramp: blue-grey to bright silver-white (Rallying Call, Heal)
    fire    a warm core (pale ivory-gold at the flames' own brightness, white at the top) whose dim
            outer keys fade through pale silver-blue: still fire, never grey or blue
    smoke   EA's grey plumes, their value kept, a silver-blue cast

The Elven Wood keeps EA's golden rays, leaves and butterflies (a forest, not a glow).
"""
from sagekit.fx.plan import FactionFX
from sagekit.fx.tint import ramp_from

from .style import PALETTE

# lightness ~11 and ~23 (the fading keys, the flare's slaves): the trim ramp's silver-blue darks;
# ~34 up (the flames' own keys, ~36): warm ivory and mallorn gold to white
MOON_FIRE = [(0, PALETTE.ramps["trim"][0][1]), (.2, (.16, .18, .24)), (.35, (.36, .27, .19)),
             (.7, (.75, .60, .45)), (1, (1.0, .97, .92))]


class ElvesFX(FactionFX):
    faction = "elves"
    tag = "Elves"
    books = ("ElvesSpellBook",)
    ramps = dict(magic=ramp_from(PALETTE.ramps["trim"], name="moonsilver"),
                 fire=ramp_from(MOON_FIRE, name="moonsilver fire"),
                 smoke=ramp_from([(0, (0, 0, 0)), (1, (.80, .88, 1.0))], chroma=0.3, name="silver-blue grey"))
    powers = ("SpellBookRallyingCall", "SpellBookHeal")
    structures = ("fire", "smoke")
