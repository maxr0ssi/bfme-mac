"""Isengard fortress orcfire munitions (IsengardFortressCitadel): EA's five fire-pots kept whole, each
made a war-engine's pot - iron rim, silver lip, spikes, blades, ember band, orcfire jars - with real
fire at its mouth (pots.py).

EA's IBFOrcfire (objects IsengardFortressCitadel; role fortress_upgrade): body IBFORCFIRE, 920
triangles, painted from IBFortress.tga + IBFortress_NRM.tga (DXT5, cut-out alpha: our texture is
DXT5).
In IBFORCFIRE mesh coordinates: x -43.12..70.34, y -42.77..43.12, z 52.65..93.71.
Other meshes (EA's, untouched): MBFDPF 40 (EXFireTorchSeq.tga); MBFDPFG 20 (PG02.tga).
Lifecycle models in its Draw module: IBFOrcfire_A, IBFOrcfire_D1, IBFOrcfire_D2, IBFOrcfire_D3.
House colour: IBHCFortress.
EA's body measured: `python3 -m sagekit measure isengard/fortress_orcfire_munitions` ->
work/measure.json.

Nearest Dwarven recipe: assets/dwarves/fortress_barrels (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import IsengardStyle


# Real fire (the game's particle systems on bones, docs/ART.md "Fire"): (x, y, z, kind) in the target's
# coordinates, collected from the design (kit.flames / kit.fire record them when the kit has a
# `fire_log` list); run again after moving a fire.
FIRE_POINTS = [
    (37.5, 37.4, 90.2, 'brazier'), (37.5, -37.4, 90.2, 'brazier'), (-37.5, 37.4, 90.2, 'brazier'),
    (-37.5, -37.4, 90.2, 'brazier'), (61.0, 0.0, 66.9, 'brazier')
]


class FortressOrcfireMunitions(Building):
    style = IsengardStyle()
    fire_points = FIRE_POINTS
    source = "IBFOrcfire"
    target = "IBFORCFIRE"
    sheet = "IBFortress.tga"
    sheet_normal = "IBFortress_NRM.tga"
    own_textures = {"IBFortress.tga": "IBFortresG.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    bake_hidden = ("MBFDPF", "MBFDPFG")     # EA's fire cards: kept in game, left out of bakes and review renders
    parts = ("ModuleTag_DrawOrcfireMunitions",)
    views = {
        "rts": ((13.6, 0.2, 73.2), 326, 50, -38, 50),
        "close": ((37.5, -37.4, 86.0), 50, 38, 40, 45),
        "gate": ((61.0, 0.0, 60.0), 45, 30, -30, 45),
        "ingame": ((13.6, 0.2, 73.2), 741, 53, -62, 50),
    }

    def design(self, kit):
        from . import pots
        return pots.build(kit)
