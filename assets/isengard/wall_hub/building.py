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
from sagekit.building import Building

from ..style import IsengardStyle


class WallHub(Building):
    style = IsengardStyle()
    source = "IBWallRmprtN"
    target = "IBFBALTOW01"
    sheet = "IBFortress.tga"
    sheet_normal = "IBFortress_NRM.tga"
    own_textures = {"IBFortress.tga": "IBFortresD.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallHub"
    house_tags = ()                 # no banners: hubs repeat along every wall
    max_z_growth = 0.35             # the blade crown to model 84 (+35 %), as the citadel's (Max's OK for walls' hubs)
    views = {
        "rts": ((0.0, -0.0, 40.0), 225, 50, -38, 50),
        "close": ((0.0, -0.0, 56.0), 150, 24, -30, 45),
        "ingame": ((0.0, -0.0, 31.2), 456, 53, -62, 50),
    }

    def design(self, kit):
        from ..shapes_walls import hub
        return hub(kit)

    def emphasis(self, c, n):
        if c.z > 30:
            return 1.35                       # the crown: what the RTS camera sees
        return 1.0
