"""Neutral ship wright (ShipWright, ShipwrightSecond, ShipWright_SP): stub from `sagekit new
neutral`.

EA's NBShipWrt_SKN (objects ShipWright, ShipwrightSecond, ShipWright_SP; role other): body
NEUTRAL, 1846 triangles, painted from NBShipWrt.tga + NBShipWrt_NRM.tga (DXT1).
In NEUTRAL mesh coordinates: x -96.18..140.17, y -38.59..66.61, z -31.92..80.36.
Other meshes (EA's, untouched): ROOF 64 (NBShipWrtFlag.TGA).
Lifecycle models in its Draw module: GBGenRubble, NBShipWrt_A, NBShipWrt_D1, NBShipWrt_D2,
NBShipWrt_D3, NBShipWrt_R.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
GBGenRubble (EA's generic rubble pile; six factions' camp keeps draw it) is a lifecycle skip.

EA's own capture hook: the INI shows GoodPart_A/B for the good factions and EvilPart_A/B for the
evil ones (SubObjectsUpgrade on the faction upgrades), but no model has those meshes: it shows
nothing. EA's modules stay as they are; our dress per faction (sagekit/capture.py) is the finer
version of the same idea, on the same upgrades, after them.

Ours (body): a ship in frame on the slipway, keel on blocks, ribs, stem and sternpost, the first
strakes planked; boarded panels on the crane tower and the shed's side for the dress banners.
Capture dress (dress.py): banners on the crane tower (+x) and the shed's long side (-y), the shed's
ridge crowned in the holder's manner.
EA's body measured: `python3 -m sagekit measure neutral/ship_wright` -> work/measure.json.

No Dwarven recipe plays this role.
"""
from sagekit.building import Building
from sagekit.capture import Capturable

from ..style import NeutralStyle

SPOTS = dict(banner=((59.4, 0, 0), (0, 1, 0), (1, 0, 0), 0.0, 72.0, 9.0, 18.0, 0.6),        # the crane tower's boards
             banner2=((0, -39.3, 0), (1, 0, 0), (0, -1, 0), -15.0, 31.0, 7.0, 14.0, 0.6),   # the shed's side, mid frame
             ridges=[((-60.0, 0.0), (40.0, 0.0), 56.6, 0.65)],
             porch=None, ceiling=102.0)


class ShipWright(Capturable, Building):
    style = NeutralStyle()
    footprint_margin = 6.5              # the dress banners hang off the shed's outermost faces (collision: the INI)
    source = "NBShipWrt_SKN"
    target = "NEUTRAL"
    sheet = "NBShipWrt.tga"
    sheet_normal = "NBShipWrt_NRM.tga"
    own_textures = {"NBShipWrt.tga": "NBShipWrH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    lifecycle = {"GBGenRubble": {"skip": "EA's generic rubble pile after the collapse (six factions' camp keeps draw "
                                         "it): none of our body is in it"}}
    views = {
        "rts": ((22.0, 14.0, 24.2), 640, 50, -62, 50),
        "close": ((40.0, -5.0, 30.0), 380, 26, -50, 45),
        "ingame": ((22.0, 14.0, 24.2), 1409, 53, -62, 50),
    }

    def body(self, kit):
        from ..shapes import hull
        out = hull(64.0, 104.0, 0.0, 4.6, 2.0)
        out.append(kit.box(58.8, 59.4, -8.0, 8.0, 50.0, 74.0, "planks|v", ("planks", True), ("beam", True)))
        out.append(kit.box(-21.0, -9.0, -39.3, -38.7, 14.0, 32.0, "planks|v", ("planks", True), ("beam", True)))
        return out

    def dress(self, kit):
        from ..dress import Spots, dress           # (Blender side: the factions' kits)
        return dress(Spots(**SPOTS))
