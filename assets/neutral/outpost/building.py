"""Neutral outpost (Outpost, OutpostSecond): stub from `sagekit new neutral`.

EA's NBOutpost_SKN (objects Outpost, OutpostSecond; role other): body BOX01, 620 triangles,
painted from NBOutpost.tga + NBOutpost_NRM.tga (DXT1).
In BOX01 mesh coordinates: x -68.70..52.76, y -87.78..70.87, z 0.00..112.54.
Other meshes (EA's, untouched): RUSAM01 379 (GUVendor.tga); TOWNWOMAN 316 (GUTownWmn_D.tga);
CHICKEN 112 (CUChicken02.tga); BASKET 94 (GBMrkplaceP.tga).
Lifecycle models in its Draw module: GBGenRubble, NBOutpost_A, NBOutpost_D1, NBOutpost_D2,
NBOutpost_D3, NBOutpost_R.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
GBGenRubble (EA's generic rubble pile; six factions' camp keeps draw it) is a lifecycle skip.

Ours (body): a market in the yard, two stalls under faded madder canopies with their counters, and
barrels. Capture dress (dress.py): banners on the front house's east gable and the watchtower, the
front and back houses' ridges crowned in the holder's manner, the Goblins' fence before the back house.
EA's body measured: `python3 -m sagekit measure neutral/outpost` -> work/measure.json.

No Dwarven recipe plays this role.
"""
from sagekit.building import Building
from sagekit.capture import Capturable

from ..style import NeutralStyle

SPOTS = dict(banner=((52.2, 0, 0), (0, 1, 0), (1, 0, 0), -58.0, 72.0, 8.0, 18.0, 1.0),      # the front house's east gable
             banner2=((0, -47.9, 0), (1, 0, 0), (0, -1, 0), -54.0, 58.0, 9.0, 18.0, 0.6),   # the watchtower's -y face, under its gallery
             ridges=[((-5.9, -58.0), (52.2, -58.0), 85.7, 1.72), ((-32.0, 8.1), (-32.0, 55.4), 59.3, 1.2)],
             porch=((-14.0, 21.0), (6.0, 21.0)))


class Outpost(Capturable, Building):
    style = NeutralStyle()
    footprint_margin = 3.0              # the east gable's banner hangs off the model's outermost face (collision: the INI)
    source = "NBOutpost_SKN"
    target = "BOX01"
    sheet = "NBOutpost.tga"
    sheet_normal = "NBOutpost_NRM.tga"
    own_textures = {"NBOutpost.tga": "NBOutposH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    lifecycle = {"GBGenRubble": {"skip": "EA's generic rubble pile after the collapse (six factions' camp keeps draw "
                                         "it): none of our body is in it"}}
    views = {
        "rts": ((-8.0, -8.5, 56.3), 530, 50, -62, 50),
        "close": ((-8.0, -20.0, 50.0), 330, 24, -55, 45),
        "ingame": ((-8.0, -8.5, 56.3), 1144, 53, -62, 50),
    }

    def body(self, kit):
        out = kit.stall((18.0, -12.0), (1, 0, 0), 12.0, 7.0, 9.0)
        out += kit.stall((40.0, 2.0), (0, 1, 0), 11.0, 7.0, 8.5)
        for x, y in ((6.0, -20.0), (9.2, -21.0), (7.5, -17.6), (30.0, -22.0)):
            out += kit.barrel(x, y)
        return out

    def dress(self, kit):
        from ..dress import Spots, dress           # (Blender side: the factions' kits)
        return dress(Spots(**SPOTS))
