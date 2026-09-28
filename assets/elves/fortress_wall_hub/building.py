"""Elven fortress wall hub (ElvenCastleWallHubExpansion, model EBEFWHub): the round tower the
fortress raises at a corner of its own when the wall-hub expansion is bought.

EA's EBEFWHub draws the castle wall hub's body a second time: EBWALLRMPRTN01 (374 triangles) is the
free-standing hub's EBWALLRMPRTN (elves/wall_hub) vertex for vertex, beside a wall run of its own
out of the west side into the fortress (EBWALLRMPRTN, 148, EA's and untouched) and EA's dome
(SPHERE01, on a bone at 47.09: r 20.65, z 51.06..67.6), which stays. So the recipe is the wall
hub's design whole, imported from elves/wall_hub (EA's body kept whole; the walls' band and
mithril coping round the rim; EA's lattice dome crowned in gold - gilt ribs, a collar, a leaf
coronet and finial; five crystal lanterns on silver posts on the rim; no banners): a fortress
corner and the free-standing hubs read as one wall. The wall run meets the hub within 14 degrees of
the -x axis: no lantern stands at 180.

The construction state shows EBWallRmprtN_A, the free-standing hub's own model: elves/wall_hub
ships it carrying its body (the same design), so this recipe neither derives nor rebuilds it."""
from sagekit.building import Building

from ..style import ElvenStyle
from ..wall_hub.building import WallHub

WALL_HUB_MODEL = "EBWallRmprtN_A"


class FortressWallHub(WallHub):
    style = ElvenStyle()
    source = "EBEFWHub"
    target = "EBWALLRMPRTN01"
    sheet = "EBFortress.tga"
    sheet_normal = "EBFortress_NRM.tga"
    own_textures = {"EBFortress.tga": "EBFortresX.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCFortressWallHub"
    lifecycle = {WALL_HUB_MODEL: {"skip": "elves/wall_hub's own model: it ships it with the same design"},
                 "EBEFWHub_D3": {"match": "rest"}}
    views = {
        "rts": ((-8.0, 0.0, 30.0), 230, 48, -24, 50),
        "close": ((-4.0, 0.0, 36.0), 140, 20, -18, 45),
        "ingame": ((-8.0, 0.0, 26.0), 480, 53, -62, 50),
    }

    is_body = Building.is_body      # this is the expansion's own object (WallHub leaves it out)

    def drawn_models(self, install):
        return [m for m in super().drawn_models(install) if m.lower() != WALL_HUB_MODEL.lower()]
