"""Angmar fortress house of healing (AngmarFortressCitadel): stub from `sagekit new angmar`.

EA's KBFHoLa (objects AngmarFortressCitadel; role fortress_upgrade): body KBFHOLA, 754 triangles,
painted from KBFortressX.tga + KBFortressX_NRM.tga (DXT1).
In KBFHOLA mesh coordinates: x 34.17..71.90, y -42.80..43.71, z 40.38..138.73.
Other meshes (EA's, untouched): N_WINDOW 18 (GBNightWIndows.tga).
Lifecycle models in its Draw module: KBFHoLa_A, KBFHoLa_D1, KBFHoLa_D2.
House colour: KBHCFortress.
EA's body measured: `python3 -m sagekit measure angmar/fortress_house_of_healing` ->
work/measure.json.

Nearest Dwarven recipe: assets/dwarves/fortress_monument (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import AngmarStyle


class FortressHouseOfHealing(Building):
    style = AngmarStyle()
    source = "KBFHoLa"
    target = "KBFHOLA"
    sheet = "KBFortressX.tga"
    sheet_normal = "KBFortressX_NRM.tga"
    own_textures = {"KBFortressX.tga": "KBFortressN.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_HouseOfHealingDraw",)
    views = {
        "rts": ((53.0, 0.5, 89.6), 300, 50, -38, 50),
        "close": ((53.0, 0.5, 89.6), 177, 24, -30, 45),
        "ingame": ((53.0, 0.5, 89.6), 682, 53, -62, 50),
    }

    def design(self, kit):
        return []
