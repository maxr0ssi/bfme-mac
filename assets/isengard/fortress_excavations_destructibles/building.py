"""Isengard fortress excavations destructibles (IsengardFortressCitadel): EA's chute and ladders kept
whole; glowing ore down the chute out of an iron skip, a lantern, a fire basket (spoil.py).

EA's IBFExcavB (objects IsengardFortressCitadel; role fortress_upgrade): body IBFEXCAVB, 374
triangles, painted from IBFortress.tga + IBFortress_NRM.tga (DXT5, cut-out alpha: our texture is
DXT5).
In IBFEXCAVB mesh coordinates: x -35.04..15.15, y -56.80..29.66, z 10.00..66.36.
Lifecycle models in its Draw module: IBFExcavB_A, IBFExcavB_D3.
House colour: IBHCFortress.
EA's body measured: `python3 -m sagekit measure isengard/fortress_excavations_destructibles` ->
work/measure.json.

Nearest Dwarven recipe: assets/dwarves/fortress_barrels (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import IsengardStyle


# Real fire (the game's particle systems on bones, docs/ART.md "Fire"): (x, y, z, kind) in the target's
# coordinates, collected from the design (kit.flames / kit.fire record them when the kit has a
# `fire_log` list); run again after moving a fire.
FIRE_POINTS = [
    (-7.2, -30.8, 36.0, 'embers'), (-8.1, 28.2, 56.9, 'brazier')
]


class FortressExcavationsDestructibles(Building):
    style = IsengardStyle()
    fire_points = FIRE_POINTS
    source = "IBFExcavB"
    target = "IBFEXCAVB"
    sheet = "IBFortress.tga"
    sheet_normal = "IBFortress_NRM.tga"
    own_textures = {"IBFortress.tga": "IBFortresK.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_DrawExcavationsDestructibles",)
    views = {
        "rts": ((-9.9, -13.6, 38.2), 252, 50, -38, 50),
        "close": ((-15.0, -15.0, 32.0), 110, 35, -30, 45),
        "ingame": ((-9.9, -13.6, 38.2), 574, 53, -62, 50),
    }

    def design(self, kit):
        from . import spoil
        return spoil.build(kit)
