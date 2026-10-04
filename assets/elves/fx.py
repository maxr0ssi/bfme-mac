"""The Elves' effects (sagekit/fx, docs/ART.md "Effects"): "Ivory, mithril and mallorn gold" from
assets/elves/style.py in the good powers they share (EA's are teal and pale blue).

    magic   the mithril ramp: blue-grey to bright silver-white (Rallying Call, Heal)

The Elven Wood keeps EA's golden rays, leaves and butterflies (a forest, not a glow).

Their buildings burn in EA's own fire.
"""
from sagekit.fx.plan import FactionFX
from sagekit.fx.tint import ramp_from

from .style import PALETTE


class ElvesFX(FactionFX):
    faction = "elves"
    tag = "Elves"
    books = ("ElvesSpellBook",)
    ramps = dict(magic=ramp_from(PALETTE.ramps["trim"], name="mithril"))
    powers = ("SpellBookRallyingCall", "SpellBookHeal")
