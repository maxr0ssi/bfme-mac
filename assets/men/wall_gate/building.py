"""Men wall gate (MenWallGateSmall, and Arnor's; model GBWallGateN): EA's two gate towers kept whole -
the ashlar shafts on their battered bases, the belfries with their four round-arched openings,
the slate domes - and made a Gondor gatehouse (men/dome.py and men/wall_segment/wall.py,
the walls' shared kit):

- each tower: the citadel's machicolated gallery round the shaft top (corbels, a black band of
  silver stars, merlons), voussoir arches with keystones and sills round EA's belfry openings, a
  flush parapet of merlons round the dome's foot, four corbelled bartizans with slate spirelets
  on the belfry's corners, steel ribs on the dome, a lantern cupola, a gilt orb and a spike;
  arrow slits in stone surrounds on the shafts;
- over the gate a bridge between the towers carrying the walls' crown (the machicolated slab
  with its stars, breastwork, merlons in the walls' rhythm) and a winged-helm crest on a pedestal
  in the middle, the guard's crown over the way in;
- two house-colour banners hung from the bridge over the gate, one on each face.

EA's gate (GBFDOTOWA, mesh coordinates; the model turns it 90 degrees: mesh x is the wall's run,
mesh y across it): towers centred at (+-49.57, +-0.21), shafts of chamfered-square section (half
9.45, chamfer 0.28 of it) from a base (0..4.6) to 49.79, a cornice in to 53.33, belfries (half
9.95) from 54.23 to 69.38 with openings 6 wide (sill 57.32, crown 66.48) in the middle of each
face, the domes' rings (half, z) 7.58 71.62, 5.57 76.04, 3.0 79.33, the spikes to 83.0; outer
buttresses to x +-64.03, y +-14.94 (the footprint). The gate leaves (BOX06-09, 40 high) hang
between the towers and swing in |y| <= 5 (model x), |x| <= 40, z 0..40: the bridge's underside
is at 41, the banners hang at |y| 7.3..7.7.
"""
from sagekit.building import Building

from ..style import MenStyle

TOWERS = ((49.57, 0.21), (-49.57, -0.21))    # the shafts' centres
BELFRIES = ((49.38, 0.1), (-49.38, -0.1))     # the belfries' and domes' (EA's are a little off the shafts')
SHAFT, BELFRY = 9.45, 9.93
GALLERY = (45.8, 2.0)             # corbel foot, slab out of the shaft
OPENING = (57.32, 66.48, 3.0)     # EA's belfry openings: sill, crown, half width
PARAPET = (68.9, 71.2)            # a flush parapet round the dome's foot
BARTIZAN = (12.7, 64.2, 1.9, 7.0, 6.0)   # centre radius on the diagonals, corbel foot, r, h, spire
DOME = [(70.0, 9.2), (71.62, 7.58), (76.04, 5.57), (79.33, 3.0)]
LANTERN = (78.9, 2.35, 83.8)
FINIAL = (89.4, 97.0)             # model 97.0: +16.9 % (limit 20 %)
BRIDGE = (40.35, 41.0)            # half run (into the towers' inner faces at 40.17), underside
BANNER = (45.4, 6.8, 16.5, 1.5)   # z_top (under the slab), width, length, out of the cornice
SLITS = (26.0, 33.8)


class WallGate(Building):
    style = MenStyle()
    source = "GBWallGateN"
    target = "GBFDOTOWA"
    sheet = "GBFortress1.tga"
    sheet_normal = "GBFortress1_NRM.tga"
    own_textures = {"GBFortress1.tga": "GBFortressC.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallGate"
    views = {                                                   # model space: the towers along y
        "rts": ((0.0, 0.0, 41.5), 342, 50, -38, 50),
        "close": ((0.0, 0.0, 50.0), 210, 24, -30, 45),
        "tower": ((0.0, 49.6, 70.0), 95, 20, -30, 45),
        "ingame": ((0.0, 0.0, 41.5), 777, 53, -62, 50),
    }

    def design(self, kit):
        out = []
        for (cx, cy), b in zip(TOWERS, BELFRIES):
            out += self._tower(kit, cx, cy, b)
        return out + self._bridge(kit)

    @staticmethod
    def _tower(kit, cx, cy, belfry):
        from mathutils import Vector as V

        from .. import dome as D
        from ..wall_segment.wall import FACE, slit
        sec = D.Section(cx, cy, chamfer=0.28)
        top = D.Section(*belfry, chamfer=0.28)
        inner = 6 if cx > 0 else 2                   # the face toward the gate (the bridge meets it)
        zc, out_ = GALLERY
        res = D.gallery(kit, sec, SHAFT, zc, out=out_, skip=(inner,))
        s0, s1, w = OPENING
        res += D.window_frames(kit, top, BELFRY, s0, s1, w, faces=(0, 2, 4, 6), d=(0.0, 0.8), panel=False, rim=0.7)
        res += D.parapet(kit, top, BELFRY, *PARAPET, d_in=-2.0, d_out=0.0, merlon=dict(w=1.9, gap=1.5, h=2.4, cap=0.5),
                         skip=(1, 3, 5, 7), trim=0.4)
        R, z0, r, h, spire = BARTIZAN
        res += D.bartizans(kit, top, R, z0, r=r, h=h, spire=spire)
        res += D.crown(kit, top, (DOME[0][1] + 0.1, DOME[0][0] + 0.5), DOME, lantern=LANTERN, finial=FINIAL)
        for a, t, n, L in sec.faces(SHAFT):         # arrow slits on the faces along the wall (the outer
            if L < 8 or abs(n.y) < 0.9:             # one has EA's buttress, the inner one the bridge)
                continue
            res += slit(V((a.x, a.y, 0)) - n * FACE, t, n, L / 2, *SLITS)
        return res

    @staticmethod
    def _bridge(kit):
        from mathutils import Vector as V

        from sagekit.blender.geometry import box

        from ..wall_segment.wall import CORNICE, FACE, crown
        half, z0 = BRIDGE
        out = [box(-half, half, -FACE, FACE, z0, 42.2, "stoneA", cap0=("stoneB", True), cap1=("top", False)),
               box(-half, half, -CORNICE, CORNICE, 42.0, 49.5, "stoneA", cap0=("stoneB", True), cap1=("top", True))]
        a, t = V((0, 0, 0)), V((1, 0, 0))
        for s in (1, -1):
            n = V((0, s, 0))
            out += crown(kit, a, t, n, -half, half, skip=[(-3.2, 3.2)])
            z_top, width, length, d = BANNER
            out += kit.banner(a + n * CORNICE, t, n, 0.0, z_top, width, length, d=d)
        out += kit.winged_crest(a, t, V((0, 1, 0)), 0.0, 52.1, -2.2, 2.2, s=1.3)
        return out

    def decals(self):
        from ..paint import men_layers
        from ..wall_segment.wall import STAR_BAND
        Star = men_layers()[2]
        zc = GALLERY[0]
        from ..wall_segment.paintwall import wall_layers
        return [Star(zrange=STAR_BAND, pitch=3.0, r=0.8), Star(zrange=(zc + 3.7, zc + 6.0), pitch=3.1, r=0.85),
                wall_layers()()]

    def emphasis(self, c, n):
        if c.z > 40:
            return 1.35                       # bridge, galleries, belfries and domes
        return 1.0

