"""Mordor fortress gorgoroth spire (MordorFortressCitadel): EA's tower of the Eye kept whole and set burning
as the citadel's crowns burn: a claw of jagged spikes round a real fire on each corner of the keep's
roof, lava seams up the shaft and the keep (spire.py).

EA's MBFEWEye (objects MordorFortressCitadel; role fortress_upgrade): body MBFEWEYE, 1060
triangles, painted from MBFortress.tga + MBFortress_NRM.tga (DXT5, cut-out alpha: our texture is
DXT5).
In MBFEWEYE mesh coordinates: x -19.15..19.15, y -23.32..23.32, z -0.00..174.75.
Lifecycle models in its Draw module: MBFEWEye_A, MBFEWEye_D2, MBFEWEye_D3.
House colour: MBHCFortress.
EA's body measured: `python3 -m sagekit measure mordor/fortress_gorgoroth_spire` ->
work/measure.json.

EA's facts (measured 2026-09-30, work/measure.json and the model's vertices): in the courtyard's middle,
mirror-symmetric in x and y. A square keep (faces +-13.03, z 0..75.2) on a foot to +-18.4 (z 0..61),
a skirt of pointed wedges round its top (+-13..19.4, z 69.9..77.6, the corners at (19.1, 13) and
(12.8, 19.4)); the keep's roof at z 75.2 round a square base (+-11, to z 78.8); a round shaft (r 8.8,
z 79..101), a spiked band (+-14.2 at z 107), the upper shaft (+-11..12.5, z 103..131); the crown
(+-11.9..17.6, z 131..143) and over it the Eye between two horns (tips (0, +-15.8, 173) and z 175,
the Eye at z 153..167). EA's bone EYEBONE at (0, 0, 160.8): GorSpireCharge, 02, 03 start there while
the spire powers up (UNPACKING). The citadel keeps |x| < 19.15, |y| < 23.3 clear for it.
"""
from sagekit.building import Building

from ..style import MordorStyle


# Real fire: (x, y, z, kind) in MBFEWEYE mesh coordinates, from the design (the kit's fire log)
FIRE_POINTS = [(-13.6, -13.6, 77.2, 'brazier'), (-13.6, 13.6, 77.2, 'brazier'), (13.6, -13.6, 77.2, 'brazier'),
               (13.6, 13.6, 77.2, 'brazier')]


class FortressGorgorothSpire(Building):
    style = MordorStyle()
    # The fire reduction (Max, 2026-10-05, docs/ART.md "Fire budget": a building whose fire is not its identity,
    # at most 6 live particles): none. 0.0 live (was 23.9).
    fire_points = []
    source = "MBFEWEye"
    target = "MBFEWEYE"
    sheet = "MBFortress.tga"
    sheet_normal = "MBFortress_NRM.tga"
    own_textures = {"MBFortress.tga": "MBFortresD.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_DrawGorgorothSpire",)
    views = {
        "rts": ((0.0, 0.0, 87.4), 407, 50, -38, 50),
        "close": ((0.0, 0.0, 87.4), 240, 24, -30, 45),
        "ingame": ((0.0, 0.0, 87.4), 924, 53, -62, 50),
        "foot": ((0.0, 0.0, 80.0), 95, 30, -38, 45),
        "crown": ((0.0, 0.0, 152.0), 90, 25, -38, 45),
    }

    def design(self, kit):
        from assets.isengard.shapes_industry import logged

        from . import spire
        return logged(kit, lambda k: k.retag(spire.build(k)))
