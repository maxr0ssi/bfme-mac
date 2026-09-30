"""Mordor fortress morgul sorcery (MordorFortressCitadel): stub from `sagekit new mordor`.

EA's MBFSorcery (objects MordorFortressCitadel; role fortress_upgrade): body MBFLAVAMEFF, 124
triangles, painted from MinasMorgulFX2.tga, no normal map (DXT1).
In MBFLAVAMEFF mesh coordinates: x -65.62..69.32, y -63.81..63.86, z -2.39..131.65.
House colour: MBHCFortress.
EA's body measured: `python3 -m sagekit measure mordor/fortress_morgul_sorcery` ->
work/measure.json.

Nearest Dwarven recipe: assets/dwarves/fortress_monument (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import MordorStyle


class FortressMorgulSorcery(Building):
    style = MordorStyle()
    source = "MBFSorcery"
    target = "MBFLAVAMEFF"
    sheet = "MinasMorgulFX2.tga"
    sheet_normal = None
    own_textures = {"MinasMorgulFX2.tga": "MinasMorgulFXX.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_DrawMorgulSorcery",)
    views = {
        "rts": ((1.8, 0.0, 64.6), 504, 50, -38, 50),
        "close": ((1.8, 0.0, 64.6), 298, 24, -30, 45),
        "ingame": ((1.8, 0.0, 64.6), 1145, 53, -62, 50),
    }

    def design(self, kit):
        return []
