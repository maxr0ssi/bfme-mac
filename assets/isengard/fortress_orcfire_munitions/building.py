"""Isengard fortress orcfire munitions (IsengardFortressCitadel): stub from `sagekit new isengard`.

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


class FortressOrcfireMunitions(Building):
    style = IsengardStyle()
    source = "IBFOrcfire"
    target = "IBFORCFIRE"
    sheet = "IBFortress.tga"
    sheet_normal = "IBFortress_NRM.tga"
    own_textures = {"IBFortress.tga": "IBFortresG.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_DrawOrcfireMunitions",)
    views = {
        "rts": ((13.6, 0.2, 73.2), 326, 50, -38, 50),
        "close": ((13.6, 0.2, 73.2), 193, 24, -30, 45),
        "ingame": ((13.6, 0.2, 73.2), 741, 53, -62, 50),
    }

    def design(self, kit):
        return []
