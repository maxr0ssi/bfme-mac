"""The Dwarves' effects (sagekit/fx, docs/ART.md "Effects"): "Honey granite & gold" from
assets/dwarves/style.py in the good powers they share (EA's are teal and pale blue).

    magic   the gold ramp: deep amber to honey gold to white (Dwarven Riches, Rallying Call, Heal,
            Rebuild)

Their buildings burn in EA's own fire (a natural fire on a good faction's stone).
"""
from sagekit.fx.plan import FactionFX
from sagekit.fx.tint import ramp_from

from .style import PALETTE


class DwarvesFX(FactionFX):
    faction = "dwarves"
    tag = "Dwarves"
    books = ("DwarvesSpellBook",)
    ramps = dict(magic=ramp_from(PALETTE.ramps["gold"], name="gold"))
    powers = ("SpellBookRallyingCall", "SpellBookHeal", "SpellBookRebuild", "SpellBookDwarvenRiches")
