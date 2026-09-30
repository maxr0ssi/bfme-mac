"""Mordor wall catapult (MordorWallCatapultExpansion): EA's spiked drum and its wall kept whole, the drum
split by lava: seams up its flute panels between the spiked fringe and the spiked crown (drum.py).

EA's MBFWCTow (objects MordorWallCatapultExpansion; role catapult_tower): body MBFWCTOW, 962
triangles, painted from MBFortress.tga + MBFortress_NRM.tga (DXT5, cut-out alpha: our texture is
DXT5).
In MBFWCTOW mesh coordinates: x -65.18..9.20, y -22.69..22.69, z -0.00..70.00.
Other meshes (EA's, untouched): P1 8.
Lifecycle models in its Draw module: MBFWCTow_A, MBFWCTow_D2, MBFWCTow_D3.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure mordor/wall_catapult` -> work/measure.json.

EA's facts (measured 2026-09-30, work/measure.json, a raycast of EA's mesh), in the expansion's own
frame (its pad turns +X outward, the wall's -X end against the citadel): the wall along x (x
-65.18..-33, |y| < 7.84, z 0..55, an arch under it); the drum on the axis (-14.8, 0): a fringe of
spike plates out to the footprint's +-22.69 (z 0..22), flat flute panels (r 19.0..19.8, z 24..40),
a spiked crown flaring from z 42 to its points at z 62, the tall front spike to z 68.4 (6.6, 0); the
top is the catapult's (EA's P1, z 48, x -65.18..3.15, |y| < 18.02). Mirror-symmetric in y.
"""
from sagekit.building import Building

from ..style import MordorStyle


# Real fire: (x, y, z, kind) in the target's mesh coordinates, from the design (the kit's fire log)
FIRE_POINTS = [(-1.2, -17.7, 58.3, 'brazier'), (-1.2, 17.7, 58.3, 'brazier'), (4.7, 5.2, 25.5, 'embers'),
               (4.7, -5.2, 25.5, 'embers')]


class WallCatapult(Building):
    style = MordorStyle()
    fire_points = FIRE_POINTS
    source = "MBFWCTow"
    target = "MBFWCTOW"
    sheet = "MBFortress.tga"
    sheet_normal = "MBFortress_NRM.tga"
    own_textures = {"MBFortress.tga": "MBFortresG.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallCatapult"
    views = {
        "rts": ((-28.0, -0.0, 35.0), 246, 50, -38, 50),
        "close": ((-28.0, -0.0, 35.0), 145, 24, -30, 45),
        "ingame": ((-28.0, -0.0, 35.0), 559, 53, -62, 50),
        "drum": ((-12.0, 0.0, 32.0), 90, 15, -20, 45),
    }

    def design(self, kit):
        from assets.isengard.shapes_industry import logged

        from . import drum
        return logged(kit, lambda k: k.retag(drum.build(k)))
