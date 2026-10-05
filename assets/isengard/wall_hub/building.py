"""Isengard wall hub (IsengardCastleWallHub; model IBWallRmprtN): EA's hexagonal wall tower where
segments meet, kept whole - the shaft with its two bands, the leaning parapet, the knife fins round
its foot - and given the citadel's blade cluster on its roof (shapes_walls.hub, shared with
isengard/fortress_wall_hub):

- a needle stack on the axis (lozenge section, iron edge fins, a spiked ember collar, a blade
  crown round an ember throat) to model 84 (+34.6 %), between two matching lozenge blades (along
  x, sharp edges to the x corners, three layered fins a face, silver edges, ember slits, leaning out a
  little as Orthanc's horns) to model 82: the three one pointed mass nearly corner to corner;
- the walls' lozenge needles (the segments' crest needles) on the parapet's six corners to
  model 72.5;
- iron spikes leaning out of each parapet face; silver on the six corner arrises; a pair of
  pointed ember slits on every face.

No fire and no banners: hubs repeat along every wall (the stack's throat glows, no fire point).
Segments run into any face (the middle 16.6 of it, to model z 59.24): nothing new stands out of a
face there but the slits (0.2 proud); everything else is on the roof and the parapet's corners.
The mesh hangs on a bone at z 25.47 (model z = mesh z + 25.47); the design is in mesh coordinates.
"""
import os

from sagekit.building import Building

from ..style import IsengardStyle

# The crown (shapes_walls.hub): "A", Orthanc's horned top (Max's pick of the hubs_v1 options, 2026-09-30;
# "pair" is the old blade pair, "B" and "C" the other options); ISENGARD_HUB_CROWN overrides it for a preview.
HUB_CROWN = "A"
BONE_Z = 25.47                      # the mesh hangs on a bone this high: fire points are in model space
HUB_FIRE = {"pair": [], "A": [(0.0, 0.0, 39.8, "brazier")], "B": [(0.0, 0.0, 37.1, "grate")],
            "C": [(0.0, 0.0, 45.0, "hearth")]}         # mesh coordinates, from the design's fire log
# The fire reduction (Max, 2026-10-05, docs/ART.md "Fire budget": a building whose fire is not its identity,
# at most 6 live particles): none on any crown; hubs repeat along every wall (and the citadel's, which take
# these). 0 live (was 6.0).
HUB_FIRE = {crown: [] for crown in HUB_FIRE}


def crown():
    return os.environ.get("ISENGARD_HUB_CROWN", HUB_CROWN)


def fire_points():
    return [(x, y, round(z + BONE_Z, 1), k) for x, y, z, k in HUB_FIRE[crown()]]


class WallHub(Building):
    style = IsengardStyle()
    source = "IBWallRmprtN"
    target = "IBFBALTOW01"
    sheet = "IBFortress.tga"
    sheet_normal = "IBFortress_NRM.tga"
    own_textures = {"IBFortress.tga": "IBFortresD.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallHub"
    house_tags = ()                 # no banners: hubs repeat along every wall
    fire_points = fire_points()
    max_z_growth = 0.35             # the blade crown to model 84 (+35 %), as the citadel's (Max's OK for walls' hubs)
    views = {
        "rts": ((0.0, -0.0, 40.0), 225, 50, -38, 50),
        "close": ((0.0, -0.0, 56.0), 150, 24, -30, 45),
        "ingame": ((0.0, -0.0, 31.2), 456, 53, -62, 50),
    }

    def design(self, kit):
        from ..shapes_walls import hub
        from ..shapes_industry import logged
        return logged(kit, lambda k: hub(k, crown()))

    def emphasis(self, c, n):
        if c.z > 30:
            return 1.35                       # the crown: what the RTS camera sees
        return 1.0
