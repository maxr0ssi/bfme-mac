"""Mordor fortress barricade morgul sorcery (MordorFortressBarricadeExpansion): stub from `sagekit
new mordor`.

EA's MBBarrSorc (objects MordorFortressBarricadeExpansion; role hall_expansion): body
MBFLAVAMEFF, 124 triangles, painted from MinasMorgulFX2.tga, no normal map (DXT1).
In MBFLAVAMEFF mesh coordinates: x -42.23..44.61, y -17.20..17.22, z -2.39..131.65.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure mordor/fortress_barricade_morgul_sorcery` ->
work/measure.json.

Nearest Dwarven recipe: assets/dwarves/hall (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import MordorStyle


class FortressBarricadeMorgulSorcery(Building):
    style = MordorStyle()
    source = "MBBarrSorc"
    target = "MBFLAVAMEFF"
    sheet = "MinasMorgulFX2.tga"
    sheet_normal = None
    own_textures = {"MinasMorgulFX2.tga": "MinasMorgulFXH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_DrawMorgulSorcery",)
    HOUSE_DRAW = "ModuleTag_Draw_HCFortressBarricadeMorgulSorcery"
    views = {
        "rts": ((-27.6, -0.3, 64.6), 359, 50, -38, 50),
        "close": ((-27.6, -0.3, 64.6), 212, 24, -30, 45),
        "ingame": ((-27.6, -0.3, 64.6), 817, 53, -62, 50),
    }

    def design(self, kit):
        return []
