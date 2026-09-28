"""Men trebuchet tower (MenTrebuchetExpansion, build variation one; model GBFTRTOWA): EA's
twelve-sided drum kept whole - its ashlar, the painted corbel arcade, the carved pilaster on its
prow, the battered cornice and the half parapet - with the open platform left clear for the
trebuchet (P1, EA's, untouched), and dressed the citadel's way (drum.py, shared with
men/trebuchet_b): a moulded plinth, pilasters up the corners, arrow slits in round-headed
surrounds, White Tree shields beside the prow, the parapet's face banded black with silver stars,
square merlons on it and pinnacles at its ends and over the prow. No banners.

EA's facts: body GBFTRTOWA (108 triangles) on GBFortress1 (own copy GBFortressQ); lifecycle
GBFTRTOWA_A, _D2, _D3 (variation one: GBFTRTOWB is men/trebuchet_b's); no house model of EA's
(HOUSE_DRAW); no night meshes. Mesh coordinates (the model's origin at x 24.5, the bone).
"""
from sagekit.building import Building

from ..style import MenStyle


class Trebuchet(Building):
    style = MenStyle()
    source = "GBFTRTOWA"
    target = "GBFTRTOWA"
    sheet = "GBFortress1.tga"
    sheet_normal = "GBFortress1_NRM.tga"
    own_textures = {"GBFortress1.tga": "GBFortressQ.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCTrebuchet"
    house_tags = ()                     # no banners
    views = {
        "rts": ((-11.6, 0.0, 28.0), 193, 50, -38, 50),
        "close": ((-11.6, 0.0, 32.0), 150, 24, -30, 45),
        "ingame": ((-11.6, 0.0, 28.0), 439, 53, -62, 50),
    }

    def design(self, kit):
        from . import drum
        return drum.build(kit)

    def decals(self):
        from ..paint import men_layers
        from .drum import BAND
        return [men_layers()[2](zrange=BAND, pitch=3.2, r=0.9)]         # silver stars on the parapet's band

    def emphasis(self, c, n):
        if c.z > 44:
            return 1.35                       # the parapet: what the RTS camera sees
        return 1.0
