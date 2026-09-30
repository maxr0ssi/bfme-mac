"""Mordor fortress magma cauldrons (MordorFortressCitadel): EA's cauldron tower, pan and spouts kept whole;
the magma's road shown: a furnace glowing at the tower's foot with lava cracks running up from it,
lava brimming in every spout and running down the outer walls (magma.py).

EA's MBFMCauld (objects MordorFortressCitadel; role fortress_upgrade): body MBFMCAULD, 780
triangles, painted from MBFortress.tga + MBFortress_NRM.tga (DXT5, cut-out alpha: our texture is
DXT5).
In MBFMCAULD mesh coordinates: x -52.74..52.74, y -52.74..52.74, z 0.00..98.92.
Lifecycle models in its Draw module: MBFMCauld_A, MBFMCauld_D2, MBFMCauld_D3.
House colour: MBHCFortress.
EA's body measured: `python3 -m sagekit measure mordor/fortress_magma_cauldrons` ->
work/measure.json.

EA's facts (measured 2026-09-30, work/measure.json, EA's vertices and bones): the cauldron tower on
the citadel's -X inner face (x -41.08..-26.47, |y| < 6.24, z 0..66, its courtyard face at x
-26.47), its two horns (inner faces |y| 7.76, z 56..89.5, tips (-36, +-6, 98.7)) and a floor at z
70 (x -48..-24.7, y -33.5..7.8); the pan on the -X walk (x -50.1..-31.3, y -35.3..-3.6, z 51..74);
eight spouts on the outer faces, each a pointed mouth 6.9 wide (frame z 25.3..37.3, its recess
z 26.5..31.6 sunk to 2.1 behind the front at 52.7), EA's bones MAGMABONE01..08 at z 27.42:
(+-49.4..49.7, +-23.8) and (+-23.8..24.0, +-49.5). The cauldron itself is a skinned model of its
own (MBFMCauld_SKN: CAULDRON at x -42.3..-29.8, y -22.8..15.9, z 69.6..91.3 at rest, on
B_CAULDRON (-36.1, -22.5, 76.8); and the orc who tips it), drawn by ModuleTag_DrawMagmaCauldronsGuy
and animated (MBFMCauld_SKL.MBFMCauld_ATKA): nothing of ours stands above the tower's foot on the
courtyard face or over the pan. When the cauldrons fire, EA's MordorFortSpray, MordorFortSpray02,
MenFortressSteam and MordorFortProxy start at the eight MAGMABONEs.
"""
from sagekit.building import Building

from ..style import MordorStyle


# Real fire: (x, y, z, kind) in MBFMCAULD mesh coordinates, from the design (the kit's fire log)
FIRE_POINTS = [(-25.5, 0.0, 2.5, 'furnace'), (51.6, -23.8, 27.6, 'embers'), (23.8, -51.6, 27.6, 'embers'),
               (-23.9, -51.6, 27.6, 'embers')]


class FortressMagmaCauldrons(Building):
    style = MordorStyle()
    fire_points = FIRE_POINTS
    source = "MBFMCauld"
    target = "MBFMCAULD"
    sheet = "MBFortress.tga"
    sheet_normal = "MBFortress_NRM.tga"
    own_textures = {"MBFortress.tga": "MBFortresC.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_DrawMagmaCauldrons",)
    views = {
        "rts": ((0.0, 0.0, 49.5), 394, 50, -38, 50),
        "close": ((0.0, 0.0, 49.5), 233, 24, -30, 45),
        "ingame": ((0.0, 0.0, 49.5), 895, 53, -62, 50),
        "tower": ((-30.0, 0.0, 30.0), 120, 22, -20, 45),
        "spout": ((24.0, -52.0, 22.0), 55, 12, -75, 45),
    }

    def design(self, kit):
        from assets.isengard.shapes_industry import logged

        from . import magma
        return logged(kit, lambda k: k.retag(magma.build(k)))
