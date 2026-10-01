"""Angmar fortress spikes (AngmarFortressSpikes): stub from `sagekit new angmar`.

EA's KBFSpike (objects AngmarFortressSpikes; role fortress_addon): body KBFSPIKES, 1326
triangles, painted from KBFortressX.tga + KBFortressX_NRM.tga (DXT1).
In KBFSPIKES mesh coordinates: x -93.99..100.88, y -91.19..91.19, z 0.58..46.23.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure angmar/fortress_spikes` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/fortress_monument (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import AngmarStyle


class FortressSpikes(Building):
    style = AngmarStyle()
    source = "KBFSpike"
    target = "KBFSPIKES"
    sheet = "KBFortressX.tga"
    sheet_normal = "KBFortressX_NRM.tga"
    own_textures = {"KBFortressX.tga": "KBFortressQ.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCFortressSpikes"
    views = {
        "rts": ((3.4, -0.0, 23.4), 596, 50, -38, 50),
        "close": ((3.4, -0.0, 23.4), 352, 24, -30, 45),
        "ingame": ((3.4, -0.0, 23.4), 1354, 53, -62, 50),
    }

    def design(self, kit):
        return []
