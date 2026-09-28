"""Men wall hub upgradeable (MenWallHubSmallUpgradeable, and Arnor's; model GBWallUpgrdN): the plot a
wall upgrade (gate, postern, tower, trebuchet, hub) replaces. Its tower OBJECT03 is the same mesh
as the wall hub's (GBWallRmprtN), so it takes the same redesign: men/wall_hub's WallHub (the
flush parapet with the band of silver stars and merlons, six corner bartizans, the drum's
pilasters and window frames, the dome's steel ribs, lantern, orb and spike). See its docstring for
EA's measurements. No banners.

GBFORTRESS01/02, the wall stubs either side (23.6 x 40.4, 49.5 high), stay EA's: a chained recipe
(`base = "men/wall_hub_upgradeable"`) could carry the segments' crown through them later.
"""
from ..wall_hub.building import WallHub


class WallHubUpgradeable(WallHub):
    source = "GBWallUpgrdN"
    target = "OBJECT03"
    own_textures = {"GBFortress1.tga": "GBFortressG.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallHubUpgradeable"
    views = {
        "rts": ((0.0, 0.0, 49.1), 255, 50, -38, 50),
        "close": ((0.0, 0.0, 62.0), 125, 24, -30, 45),
        "ingame": ((0.0, 0.0, 49.1), 580, 53, -62, 50),
    }
