"""Isengard warg pit 02 (IsengardWargPit): stub from `sagekit new isengard`.

EA's IBWARGPIT_DRC (objects IsengardWargPit; role stable): body IBWARGPIT_DRC, 158 triangles,
painted from IBWargPit.tga, no normal map (DXT5, cut-out alpha: our texture is DXT5).
In IBWARGPIT_DRC mesh coordinates: x 31.26..35.81, y -45.66..-28.37, z -0.42..27.33.
Lifecycle models in its Draw module: IBWARGPIT_DRCA, IBWARGPIT_DRO, IBWARGPIT_DROA,
IBWargpit_DRA.
House colour: IBHCWargPit.
EA's body measured: `python3 -m sagekit measure isengard/warg_pit_02` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/barracks (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import IsengardStyle


class WargPit02(Building):
    style = IsengardStyle()
    source = "IBWARGPIT_DRC"
    target = "IBWARGPIT_DRC"
    sheet = "IBWargPit.tga"
    sheet_normal = None
    own_textures = {"IBWargPit.tga": "IBWargPiX.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_02",)
    views = {
        "rts": ((33.5, -37.0, 13.5), 73, 50, -38, 50),
        "close": ((33.5, -37.0, 13.5), 43, 24, -30, 45),
        "ingame": ((33.5, -37.0, 13.5), 165, 53, -62, 50),
    }

    def design(self, kit):
        return []
