"""Isengard mine launcher (IsengardMineLauncherExpansion): stub from `sagekit new isengard`.

EA's IBFMLaunch (objects IsengardMineLauncherExpansion; role catapult_tower): body IBFMLAUNCH,
1094 triangles, painted from IBFortress.tga + IBFortress_NRM.tga (DXT5, cut-out alpha: our
texture is DXT5).
In IBFMLAUNCH mesh coordinates: x -38.43..36.99, y -33.41..33.41, z -0.06..74.72.
Other meshes (EA's, untouched): BOMB1 367 (IUDemoTeamW.tga); BOMB2 367 (IUDemoTeamW.tga); BOMB3
367 (IUDemoTeamW.tga); IBFMLAUNCHB 22 (IBFortress.tga).
Lifecycle models in its Draw module: IBFMLaunch_A, IBFMLaunch_D2, IBFMLaunch_D3.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure isengard/mine_launcher` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/catapult_tower (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import IsengardStyle


class MineLauncher(Building):
    style = IsengardStyle()
    source = "IBFMLaunch"
    target = "IBFMLAUNCH"
    sheet = "IBFortress.tga"
    sheet_normal = "IBFortress_NRM.tga"
    own_textures = {"IBFortress.tga": "IBFortresP.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCMineLauncher"
    views = {
        "rts": ((-0.7, 0.0, 37.3), 276, 50, -38, 50),
        "close": ((-0.7, 0.0, 37.3), 163, 24, -30, 45),
        "ingame": ((-0.7, 0.0, 37.3), 627, 53, -62, 50),
    }

    def design(self, kit):
        return []
