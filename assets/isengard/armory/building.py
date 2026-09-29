"""Isengard armory (IsengardArmory): stub from `sagekit new isengard`.

EA's IBArmory_SKN (objects IsengardArmory; role siege): body IBARMORY, 468 triangles, painted
from IBArmory.tga + IBArmory_NRM.tga (DXT5, cut-out alpha: our texture is DXT5).
In IBARMORY mesh coordinates (identity bone): x -27.48..39.96, y -39.10..50.11, z -1.58..45.31.
Checked by hand (2026-09-28): the scaffolder picked IBARMORYWHEEL1 (525), the great treadwheel on
a bone tilted 8 degrees (x -32.7..50.7, y -41.9..-18.1, z -32.7..50.5), because the wheel's rim
dips to z -32.7 and made the house look raised. The house is IBARMORY; the wheel stays EA's.
Other meshes (EA's, untouched): IBARMORYWHEEL1 525 (IBArmory.tga, IBArmory_NRM.tga); V2 524
(IBArmory.tga, IBArmory_NRM.tga); MUGBLNSLV1 258 (MUOrcLabor.tga); V1A 232 (IBArmory.tga,
IBArmory_NRM.tga); N_WINDOW 80 (WBCave.tga, WBCave_NRM.tga); IBARMORYWHEEL2 64 (IBArmory.tga,
IBArmory_NRM.tga); OBJECT01 24 (IUUrukahi.tga); N_FIRE 16 (EXFireTorchSeq.tga).
Lifecycle models in its Draw module: IBArmory_A, IBArmory_D1, IBArmory_D2, IBArmory_D3.
House colour: IBHCArmory.
EA's body measured: `python3 -m sagekit measure isengard/armory` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/siege_works (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import IsengardStyle


class Armory(Building):
    style = IsengardStyle()
    source = "IBArmory_SKN"
    target = "IBARMORY"
    sheet = "IBArmory.tga"
    sheet_normal = "IBArmory_NRM.tga"
    own_textures = {"IBArmory.tga": "IBArmorH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((6.2, 5.5, 21.9), 267, 50, -38, 50),
        "close": ((6.2, 5.5, 21.9), 158, 24, -30, 45),
        "ingame": ((6.2, 5.5, 21.9), 606, 53, -62, 50),
    }

    def design(self, kit):
        return []
