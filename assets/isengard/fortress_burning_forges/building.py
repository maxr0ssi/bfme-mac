"""Isengard fortress burning forges (IsengardFortressCitadel): the forge's great wheel. EA's wheel is
kept whole - a twelve-sided iron disc (r 10..12.2, its faces at y -7.3 and -1.7, rim lips to -8.0
and -1.1), twelve ribs and rods to r 16.4, hooked lobes on its rim, the hub drum along +y - and made
a war-forge's fan: six silver-edged iron ribs on each face between EA's ribs, a riveted iron boss
on the -y face round EA's axle end (y -10.7), and six ember vents glowing between the ribs.

It turns: `IBFBForges_AN` spins IBFBFORGESA about its bone's y axis once every 180 frames
(LOOP_BACKWARDS), through the forge tower's slot (world |y| < 3.8, mesh y -8.3..-0.7, z 49..62): so
every new piece turns with it, stays inside r 16 of the hub, and below the hub (r > 4) stands at
most 0.8 off the faces, inside the slot. No fire points: the rig would stand still while the wheel turns (the forge tower,
fortress_burning_forges_destructibles, carries the fire).

EA's IBFBForges (objects IsengardFortressCitadel; role fortress_upgrade): body IBFBFORGESA, 957
triangles, painted from IBFortress.tga + IBFortress_NRM.tga (DXT5, cut-out alpha: our texture is
DXT5).
In IBFBFORGESA mesh coordinates: x -16.37..16.37, y -10.72..10.72, z -16.37..16.37.
Lifecycle models in its Draw module: IBFBForges_A.
House colour: IBHCFortress.
EA's body measured: `python3 -m sagekit measure isengard/fortress_burning_forges` ->
work/measure.json.

Nearest Dwarven recipe: assets/dwarves/fortress_statues (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import IsengardStyle


class FortressBurningForges(Building):
    style = IsengardStyle()
    source = "IBFBForges"
    target = "IBFBFORGESA"
    sheet = "IBFortress.tga"
    sheet_normal = "IBFortress_NRM.tga"
    own_textures = {"IBFortress.tga": "IBFortresL.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_DrawBurningForges",)
    views = {
        "rts": ((-42.1, 4.5, 66.2), 150, 50, -38, 50),
        "close": ((-42.1, 4.5, 66.2), 90, 12, -80, 45),
        "ingame": ((-42.1, 4.5, 66.2), 255, 53, -62, 50),
    }

    def design(self, kit):
        from . import wheel
        return wheel.build(kit)
