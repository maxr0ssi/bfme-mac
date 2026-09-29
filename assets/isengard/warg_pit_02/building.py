"""The Isengard warg pit's door (IsengardWargPit's ModuleTag_02): not a building but the gate of
the warg pit's run, a Draw module of its own. It stays EA's on purpose: design() adds nothing and
this recipe is not to be built.

EA's IBWARGPIT_DRC (158 triangles, painted from IBWargPit.tga, no normal map, cut-out alpha): the
shut leaf of lashed stakes, x 31.3..35.8, y -45.7..-28.4, z -0.4..27.3. Its Draw swaps it for
four more models: IBWARGPIT_DROA and IBWARGPIT_DRCA (the swing open and shut, animated),
IBWARGPIT_DRO (open: swung out to x 32.7..37.2, y -30.4..-13.1) and IBWargpit_DRA (building).
A redesign would have to ride all five, two of them animated; the leaf is small and palette A
reaches it anyway through `sagekit sheets` (IBWargPit.tga is Isengard's own sheet). The warg
pit's recipe frames it instead: a pair of blade pylons past both ends of the leaf, shut and swung
open, a chain slung between them over it and the White Hand on a shield (warg_pit/building.py).

The stub stays as the record of that decision (2026-09-29).
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
