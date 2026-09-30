"""Mordor fortress barricade (MordorFortressBarricadeExpansion): EA's wall and square tower kept whole, the tower
crowned as the citadel's towers are: a claw of spikes round a real fire in its open top, the Eye in
its windows, lava cracks up its faces, barbed teeth in the arch (tower.py).

EA's MBFBarric (objects MordorFortressBarricadeExpansion; role hall_expansion): body MBFBARRIC,
1199 triangles, painted from MBFortress.tga + MBFortress_NRM.tga (DXT5, cut-out alpha: our
texture is DXT5).
In MBFBARRIC mesh coordinates: x -65.75..9.99, y -13.19..13.19, z 0.00..120.82.
Other meshes (EA's, untouched): BIB 92 (MBFortress.tga); P1 2.
Lifecycle models in its Draw module: MBFBarric_A, MBFBarric_D2, MBFBarric_D3.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure mordor/fortress_barricade` -> work/measure.json.

EA's facts (measured 2026-09-30, work/measure.json and the model's vertices), in the expansion's own
frame (its pad on the citadel turns +X outward; EA's base file puts the pads 114.5 out on the sides and
129 out on the diagonals, so the wall's -X end meets the citadel's curtain or a corner tower):
a wall along x (faces y +-7.52, z 0..50, from x -65.75 to 8.9), its arch (x -62.75..-30.75, to z
40.5), the walk on it (EA's P1 at z 50, x -65.75..8.4, |y| < 7.5; the archers' bones ARROW_01..04 at
z 51); the square tower (x -28.79..-9.62, faces y +-9.59 to z 71, +-7.87 above with a pointed recess
8 wide at z 75.3..94.3 on each broad face, deeper windows on the narrow ones), its open top (floor z
111.1, merlons to z 120.8); EA's base plate BIB (x -41.1..4.6, |y| < 18.9, z 0..9.45) and P1 are
EA's meshes, untouched. Mirror-symmetric in y.
"""
from sagekit.building import Building

from ..style import MordorStyle


# Real fire: (x, y, z, kind) in the target's mesh coordinates, from the design (the kit's fire log)
FIRE_POINTS = [(-19.2, 0.0, 112.9, 'brazier')]


class FortressBarricade(Building):
    style = MordorStyle()
    fire_points = FIRE_POINTS
    source = "MBFBarric"
    target = "MBFBARRIC"
    sheet = "MBFortress.tga"
    sheet_normal = "MBFortress_NRM.tga"
    own_textures = {"MBFortress.tga": "MBFortresX.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCFortressBarricade"
    views = {
        "rts": ((-27.9, -0.0, 60.4), 319, 50, -38, 50),
        "close": ((-27.9, -0.0, 60.4), 189, 24, -30, 45),
        "ingame": ((-27.9, -0.0, 60.4), 725, 53, -62, 50),
        "crown": ((-19.25, 0.0, 115.0), 70, 30, -60, 45),
    }

    def design(self, kit):
        from assets.isengard.shapes_industry import logged

        from . import tower
        return logged(kit, lambda k: k.retag(tower.build(k)))
