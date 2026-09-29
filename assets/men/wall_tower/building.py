"""Men wall tower (MenWallTowerSmall, and Arnor's; model GBWallTwrN): EA's wall tower kept whole -
the ashlar shaft with its corner buttresses and the carved emblem on its field faces, the belfry
with its painted arched windows, the slate dome - and crowned as the citadel's towers are
(men/dome.py, the shared tower top):

- the citadel's machicolated gallery round the shaft top: two-step corbels, a slab whose front is
  a black band of silver stars, a parapet and square merlons with capstones;
- four corbelled bartizans on the diagonals over EA's corner buttresses, slit windows, steel-
  banded cornices, slate spirelets and steel spikes;
- a flush parapet of merlons round the belfry's top, in front of the dome's eave;
- a steel eave band, steel ribs up the dome, a lantern cupola, a steel mast, a gilt orb and a
  spike;
- one house-colour banner hung from the gallery on the +x face, clear of EA's emblem.

EA's GBFARTOWA (mesh coordinates = model coordinates): a chamfered-square shaft (half 12.01,
chamfer 0.28 of it, centred at (0.02, 0.21)) from its base (0..4.6) to 49.5, corner buttresses on
the diagonals to 46.4 (the footprint: x -16.87..17.08, y -16.94..16.91), the emblem on the +-x
faces at z 26.6..39.9 (|y| <= 5), the belfry (the same section) to 72.47, a sloped eave in to the
dome (half 10.0 at 74.89, 7.1 at 83.21, 3.98 at 88.94) and its point at 93.62. The wall runs
along y through it (BOX01, EA's wall stub under the tower, stays EA's).
"""
from sagekit.building import Building

from ..style import MenStyle

C = (0.02, 0.21)
SHAFT = 12.01
GALLERY = (44.3, 2.0)              # corbel foot, slab out of the shaft (front at 14.0)
BARTIZAN = (16.2, 44.6, 2.0, 8.2, 6.4)   # centre radius on the diagonals, corbel foot, r, h, spire
PARAPET = (72.0, 74.6)             # round the belfry's top
DOME = [(74.89, 10.0), (83.21, 7.1), (88.94, 3.98)]
LANTERN = (88.7, 4.2, 95.0)        # wraps EA's dome point (its collar covers the dome at 88.7..89.8)
FINIAL = (101.4, 110.5)            # +18.0 % (limit 20 %)
BANNER = (50.2, 6.0, 10.0, 0.6)    # z_top, width, length (ends at 40.2, over EA's emblem), out of the slab


class WallTower(Building):
    style = MenStyle()
    source = "GBWallTwrN"
    target = "GBFARTOWA"
    sheet = "GBFortress1.tga"
    sheet_normal = "GBFortress1_NRM.tga"
    own_textures = {"GBFortress1.tga": "GBFortressX.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallTower"
    views = {
        "rts": ((0.1, 0.0, 50.0), 250, 50, -38, 50),
        "close": ((0.1, 0.0, 62.0), 150, 24, -30, 45),
        "crown": ((0.1, 0.0, 80.0), 80, 20, -38, 45),
        "ingame": ((0.1, 0.0, 46.8), 526, 53, -62, 50),
    }

    def design(self, kit):
        from mathutils import Vector as V

        from .. import dome as D
        sec = D.Section(*C, chamfer=0.28)
        zc, out_ = GALLERY
        res = D.gallery(kit, sec, SHAFT, zc, out=out_)
        R, z0, r, h, spire = BARTIZAN
        res += D.bartizans(kit, sec, R, z0, r=r, h=h, spire=spire)
        res += D.parapet(kit, sec, SHAFT, *PARAPET, d_in=-2.2, d_out=0.0, merlon=dict(w=2.0, gap=1.6, h=2.4, cap=0.5),
                         skip=(1, 3, 5, 7), trim=0.5)
        top = D.Section(C[0], 0.1, chamfer=0.28)
        res += D.crown(kit, top, (DOME[0][1] + 0.1, DOME[0][0] + 0.3), DOME, lantern=LANTERN, finial=FINIAL)
        z_top, width, length, d = BANNER
        a, t, n = V((C[0] + SHAFT + out_, C[1], 0)), V((0, 1, 0)), V((1, 0, 0))
        res += kit.banner(a, t, n, 0.0, z_top, width, length, d=d)
        return res

    def decals(self):
        from ..paint import men_layers
        zc = GALLERY[0]
        from ..wall_segment.paintwall import wall_layers
        return [men_layers()[2](zrange=(zc + 3.7, zc + 6.0), pitch=3.1, r=0.85), wall_layers()()]

    def emphasis(self, c, n):
        if c.z > 44:
            return 1.35                       # gallery, belfry and dome: what the RTS camera sees
        return 1.0
