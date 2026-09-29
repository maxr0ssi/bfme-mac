"""Isengard wall hub (IsengardCastleWallHub; model IBWallRmprtN): EA's hexagonal wall tower where
segments meet, kept whole - the shaft with its two bands, the leaning parapet, the knife fins round
its foot - and crowned as Orthanc is (shapes_walls.hub, shared with isengard/fortress_wall_hub):

- six horns on the parapet's corners, leaning out and curling in to their points;
- a lozenge needle out of the roof with a silver collar and edges, to model z 75 (+19.9 %);
- three iron spikes leaning out of each parapet face between the horns;
- silver on the six corner arrises, a pair of pointed ember slits on every face.

No fire and no banners: hubs repeat along every wall. Segments run into any face (the middle 16.6
of it, to model z 59.24): nothing new stands out of a face there but the slits (0.2 proud) and
the spikes above the parapet (model 62.5). The mesh hangs on a bone at z 25.47 (model z = mesh z
+ 25.47); the design is in mesh coordinates.
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
    views = {
        "rts": ((0.0, -0.0, 31.2), 201, 50, -38, 50),
        "close": ((0.0, -0.0, 40.0), 119, 24, -30, 45),
        "ingame": ((0.0, -0.0, 31.2), 456, 53, -62, 50),
    }

    def design(self, kit):
        from ..shapes_walls import hub
        return hub(kit)

    def emphasis(self, c, n):
        if c.z > 30:
            return 1.35                       # the crown: what the RTS camera sees
        return 1.0
