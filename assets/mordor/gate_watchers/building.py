"""Mordor gate watchers (MordorGateWatchersExpansion): stub from `sagekit new mordor`.

EA's GWatchers (objects MordorGateWatchersExpansion; role hall_expansion): body GWATCHERS, 1271
triangles, painted from MBFortress.tga + MBFortress_NRM.tga (DXT5, cut-out alpha: our texture is
DXT5).
In GWATCHERS mesh coordinates: x -65.75..-3.10, y -17.37..17.37, z -0.39..59.05.
Other meshes (EA's, untouched): BIB 92 (MBFortress.tga).
Lifecycle models in its Draw module: GWatchers_A, GWatchers_D2, GWatchers_D3.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure mordor/gate_watchers` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/hall (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import MordorStyle


class GateWatchers(Building):
    style = MordorStyle()
    source = "GWatchers"
    target = "GWATCHERS"
    sheet = "MBFortress.tga"
    sheet_normal = "MBFortress_NRM.tga"
    own_textures = {"MBFortress.tga": "MBFortresF.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCGateWatchers"
    views = {
        "rts": ((-34.4, -0.0, 29.3), 205, 50, -38, 50),
        "close": ((-34.4, -0.0, 29.3), 121, 24, -30, 45),
        "ingame": ((-34.4, -0.0, 29.3), 465, 53, -62, 50),
    }

    def design(self, kit):
        return []
