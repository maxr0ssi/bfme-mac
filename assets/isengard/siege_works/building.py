"""Isengard siege works (IsengardSiegeWorks): stub from `sagekit new isengard`.

EA's IBSeigeWork (objects IsengardSiegeWorks; role siege): body IBSEIGEFRAME, 932 triangles,
painted from IBSeigeWork.tga + IBSeigeWork_NRM.tga (DXT5, cut-out alpha: our texture is DXT5).
In IBSEIGEFRAME mesh coordinates: x -78.99..37.70, y -50.65..51.03, z -2.95..60.23.
Target ambiguous: V2 (362 triangles) could be the body too (the rule takes a normal-mapped mesh
standing on the ground, then the largest); set `target` to the mesh the design redesigns.
Other meshes (EA's, untouched): V2 362 (IBSeigeWork.tga, IBSeigeWork_NRM.tga); IBSEIGEWALLS 228
(IBSeigeWall.tga, IBSeigeWall_NRM.tga); V2A 102 (IBSeigeWall.tga, IBSeigeWall_NRM.tga); N_WINDOW
80 (WBCave.tga, WBCave_NRM.tga); N_FIRE 16 (EXFireTorchSeq.tga).
Lifecycle models in its Draw module: IBSeigeW_A, IBSeigeW_D1, IBSeigeW_D2, IBSeigeW_D3.
House colour: IBHCSeigeWork.
EA's body measured: `python3 -m sagekit measure isengard/siege_works` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/siege_works (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import IsengardStyle


class SiegeWorks(Building):
    style = IsengardStyle()
    source = "IBSeigeWork"
    target = "IBSEIGEFRAME"
    sheet = "IBSeigeWork.tga"
    sheet_normal = "IBSeigeWork_NRM.tga"
    own_textures = {"IBSeigeWork.tga": "IBSeigeWorH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((-0.4, -0.2, 29.3), 368, 50, -38, 50),
        "close": ((-0.4, -0.2, 29.3), 217, 24, -30, 45),
        "ingame": ((-0.4, -0.2, 29.3), 836, 53, -62, 50),
    }

    def design(self, kit):
        return []
