"""The Men's effects (sagekit/fx, docs/ART.md "Effects"): "Gondor: white stone, steel and sable" from
assets/men/style.py in the good powers Gondor and Arnor share (EA's are teal and pale blue).

    magic   the Gondor gold ramp: a muted warm gold to white (Rallying Call, Heal, Rebuild)

The Army of the Dead keeps EA's ghost green; the buildings burn in EA's own fire.
"""
from sagekit.fx.plan import FactionFX
from sagekit.fx.tint import ramp_from

from .style import PALETTE


class MenFX(FactionFX):
    faction = "men"
    tag = "Men"
    books = ("MenSpellBook", "ArnorSpellBook")
    ramps = dict(magic=ramp_from(PALETTE.ramps["gold"], name="Gondor gold"))
    powers = ("SpellBookRallyingCall", "SpellBookHeal", "SpellBookRebuild")
