"""Mordor fortress lava moat (MordorFortressLavaMoat): EA's ring of rock and lava kept whole, made cruel:
crusts of slag drifting on the lava, jagged basalt teeth and impaling stakes on the outer bank between
the expansions' pads, smoke and embers (moat.py).

EA's MBFLavaMoat (objects MordorFortressLavaMoat; role fortress_addon): body MBFLAVAMOAT, 630
triangles, painted from MBFortress.tga + MBFortress_NRM.tga (DXT5, cut-out alpha: our texture is
DXT5).
In MBFLAVAMOAT mesh coordinates: x -96.57..93.61, y -93.48..95.19, z 0.00..16.93.
Other meshes (EA's, untouched): MBFLAVAMEFF 96 (MinasMorgulFX2.tga, MinasMorgulFX3.tga);
MBFLAVAMALPH 64 (MBFortress.tga); OBJECT01 60 (S3_Lava.tga).
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure mordor/fortress_lava_moat` -> work/measure.json.

EA's facts (measured 2026-09-30, work/measure.json and a raycast, moat.py RING): an object of its own
(MordorFortressLavaMoat, spawned by the citadel's upgrade at its centre, so these are the citadel's
coordinates); a ring of rock from the wall's foot out to r 90.5..108.4 (it follows the square), its
channel's floor at z 1 about r_out - 21, EA's lava plane OBJECT01 (S3_Lava.tga) at z 2.29 from r
55.7 to 99.7, the outer bank's crest (z 3..10) about r_out - 11.5; the ramp crosses at +X. EA's
MBFLAVAMEFF (a sorcery flare to z 131.7, MinasMorgulFX) and MBFLAVAMALPH (an alpha ground decal) are
kept in game and left out of renders (bake_hidden).
"""
from sagekit.building import Building

from ..style import MordorStyle


# Real fire: (x, y, z, kind) in MBFLAVAMOAT mesh coordinates, from the design (the kit's fire log)
FIRE_POINTS = [(-29.8, -73.8, 2.6, 'smoke'), (-71.6, 30.4, 2.6, 'smoke'), (31.3, 73.8, 2.6, 'embers'),
               (28.7, -67.6, 2.6, 'embers'), (-70.7, -30.0, 2.6, 'embers')]


class FortressLavaMoat(Building):
    style = MordorStyle()
    fire_points = FIRE_POINTS
    source = "MBFLavaMoat"
    target = "MBFLAVAMOAT"
    sheet = "MBFortress.tga"
    sheet_normal = "MBFortress_NRM.tga"
    own_textures = {"MBFortress.tga": "MBFortresE.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCFortressLavaMoat"
    # EA's sorcery flare (MBFLAVAMEFF, MinasMorgulFX, to z 131.7) and its alpha ground decal (MBFLAVAMALPH):
    # kept in game, left out of bakes and renders
    bake_hidden = ("MBFLAVAMEFF", "MBFLAVAMALPH")
    views = {
        "rts": ((-1.5, 0.9, 8.5), 591, 50, -38, 50),
        "close": ((-1.5, 0.9, 8.5), 349, 24, -30, 45),
        "ingame": ((-1.5, 0.9, 8.5), 1342, 53, -62, 50),
    }

    def design(self, kit):
        from assets.isengard.shapes_industry import logged

        from . import moat
        return logged(kit, lambda k: k.retag(moat.build(k)))
