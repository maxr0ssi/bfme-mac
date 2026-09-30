"""Mordor gate watchers morgul sorcery (MordorGateWatchersExpansion): stub from `sagekit new
mordor`.

EA's MBWatSorc (objects MordorGateWatchersExpansion; role hall_expansion): body MBFLAVAMEFF, 124
triangles, painted from MinasMorgulFX2.tga, no normal map (DXT1).
In MBFLAVAMEFF mesh coordinates: x -34.71..36.66, y -22.45..22.11, z -2.39..131.65.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure mordor/gate_watchers_morgul_sorcery` ->
work/measure.json.

Nearest Dwarven recipe: assets/dwarves/hall (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import MordorStyle


class GateWatchersMorgulSorcery(Building):
    style = MordorStyle()
    source = "MBWatSorc"
    target = "MBFLAVAMEFF"
    sheet = "MinasMorgulFX2.tga"
    sheet_normal = None
    own_textures = {"MinasMorgulFX2.tga": "MinasMorgulFXB.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_DrawMorgulSorcery",)
    HOUSE_DRAW = "ModuleTag_Draw_HCGateWatchersMorgulSorcery"
    views = {
        "rts": ((-35.5, -1.1, 64.6), 348, 50, -38, 50),
        "close": ((-35.5, -1.1, 64.6), 206, 24, -30, 45),
        "ingame": ((-35.5, -1.1, 64.6), 791, 53, -62, 50),
    }

    def design(self, kit):
        return []
