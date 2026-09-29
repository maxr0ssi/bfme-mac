"""Isengard mine launcher (IsengardMineLauncherExpansion): EA's launcher kept whole; merlons and fins
on the front, Hands and slits on the tower, ramp jaws, orcfire mines, a brazier and a firebox
(launcher.py).

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


# Real fire (the game's particle systems on bones, docs/ART.md "Fire"): (x, y, z, kind) in the target's
# coordinates, collected from the design (kit.flames / kit.fire record them when the kit has a
# `fire_log` list); run again after moving a fire.
FIRE_POINTS = [
    (-9.4, 21.6, 39.1, 'brazier'), (-9.3, 6.0, 37.0, 'furnace')
]


class MineLauncher(Building):
    style = IsengardStyle()
    fire_points = FIRE_POINTS
    source = "IBFMLaunch"
    target = "IBFMLAUNCH"
    sheet = "IBFortress.tga"
    sheet_normal = "IBFortress_NRM.tga"
    own_textures = {"IBFortress.tga": "IBFortresP.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCMineLauncher"
    views = {
        "rts": ((-0.7, 0.0, 37.3), 276, 50, -38, 50),
        "close": ((-8.0, 0.0, 40.0), 150, 30, -30, 45),
        "ingame": ((-0.7, 0.0, 37.3), 627, 53, -62, 50),
    }

    def design(self, kit):
        from . import launcher
        return launcher.build(kit)
