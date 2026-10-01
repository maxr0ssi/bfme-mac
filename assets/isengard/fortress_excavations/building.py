"""Isengard fortress excavations (IsengardFortressCitadel): the pits of Isengard. EA's terraced pit kept
whole; fire and smoke out of the shafts, the south one under an iron kerb and a glowing grate (pass 4,
2026-09-30: its needle flue went), terrace spikes, an ore cart (pits.py).

EA's IBFExcav (objects IsengardFortressCitadel; role fortress_upgrade): body IBFEXCAV, 875
triangles, painted from IBFortress.tga + IBFortress_NRM.tga (DXT5, cut-out alpha: our texture is
DXT5).
In IBFEXCAV mesh coordinates: x -54.18..54.18, y -54.18..57.03, z -0.00..91.81.
Other meshes (EA's, untouched): IBFEXCAVAT2 314 (IBFortress.tga, IBFortress_NRM.tga); IBFEXCAVAT5
160 (IBFortress.tga, IBFortress_NRM.tga); IBFEXCAVAT3 142 (IBFortress.tga, IBFortress_NRM.tga);
IBFEXCAVAT4 28 (IBFortress.tga, IBFortress_NRM.tga).
Lifecycle models in its Draw module: IBFExcav_A, IBFExcav_D3.
House colour: IBHCFortress.
EA's body measured: `python3 -m sagekit measure isengard/fortress_excavations` ->
work/measure.json.

Nearest Dwarven recipe: assets/dwarves/fortress_barrels (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import IsengardStyle


# Real fire (the game's particle systems on bones, docs/ART.md "Fire"): (x, y, z, kind) in the target's
# coordinates, collected from the design (kit.flames / kit.fire record them when the kit has a
# `fire_log` list); run again after moving a fire.
FIRE_POINTS = [
    (-18.5, 27.5, 21.0, 'chimney'), (16.8, 27.5, 21.0, 'chimney'), (-0.2, -31.8, 22.0, 'chimney')
]


class FortressExcavations(Building):
    style = IsengardStyle()
    fire_points = FIRE_POINTS
    source = "IBFExcav"
    target = "IBFEXCAV"
    sheet = "IBFortress.tga"
    sheet_normal = "IBFortress_NRM.tga"
    own_textures = {"IBFortress.tga": "IBFortresJ.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_DrawExcavations",)
    views = {
        "rts": ((0.0, 1.4, 45.9), 397, 50, -38, 50),
        "close": ((0.0, 1.4, 25.0), 180, 40, -30, 45),
        "ingame": ((0.0, 1.4, 45.9), 902, 53, -62, 50),
    }

    def design(self, kit):
        from . import pits
        return pits.build(kit)
