"""Men stable (GondorStable): EA's body kept whole - the square central block with its octagonal
cupola and the stable door on the yard, the two slate-roofed wings running out at 45 degrees
with their stall arcades and open-porched gable ends - and dressed like the citadel.

EA's GBStable_SKN, body GBSTABLE (2186 triangles), painted from GBStable.tga (own copy
GBStablH.tga; the Elven stable draws GBStable too). GBSTABLE hangs on a bone turned 90 degrees:
`world_space`, every number here is in model (world) axes. The model is symmetric about
y = -0.56 (MID): the south-east wing is the north-east one mirrored. What EA's body is, measured:

    centre  a square block, centre (-28.35, -0.55), half 12.25, corners chamfered 3.4; its front
            (x -16.2, the yard side) with the stable door (x -16.6, |y| < 7, under an arch to
            z 35), a string course at 36-37.5, the upper wall to the cornice at 49-50 and a roof
            deck at 51; the cupola: a drum (vertices at 22.5 + k 45 degrees, radius 8.9) from
            51.2 to 53.0, the dome 55.9 (7.72), 58.0 (4.47), its point at 58.8
    wings   north-east: the stall arcade's anchor line x - y = -35.4 (the piers' faces 1.1 out of
            it; the stall arches' crowns at u 8.2 and 20.2 along (0.71, 0.71) from (-17.7, 17.7),
            open to z 28.5); a flat soffit at 31.6, the eave's edge 3.3 out at 35.4, the roof
            rising 0.85 per unit back to the ridge (-17.65, 33.34) -> (-8.0, 43.0) at 46.7-46.9;
            the gable end's pediment at axial 13.9 from (-16.7, 34.28) along (0.71, 0.71), the
            porch arch's band at 15.3 (the arch half 7.25, springing 22.5, crown 26.6), the raking
            coping's apex at 49.9. The SE arcade stands 0.7 further back than the NE one's mirror
    level 3 V2 sets a belfry on the central block (its base x -39.7..-17.0 from 51.5, the shaft
            half 8.2); V2's flag poles leave the gables at z 44.7 on their centre lines and
            climb outwards (the flags hang from z 28, s = 0): the gables keep their centre lines
            clear. EA's house banner (GBHCStable) stands on a pole on the north-east gable's apex

What stands on it here:

    crown   the citadel's machicolated gallery round the central block (corbels from 44.6, a
            sable slab of silver stars, a parapet and square merlons), bartizans with slate
            spirelets corbelled out of the two yard-side chamfers, pinnacles on the back two
    cupola  steel eave band and ribs, a lantern, gilt orb and spike (inside V2 at level 3)
    front   one house-colour banner over the stable door (the cap is 2 with EA's house banner)
    wings   steel ridge rolls with cresting and gilt knobs; slate dormers with arched windows over
            the NE stall arches; keystones on the stall arches, capitals and consoles on the piers, a sable band of gilt
            stars along the eaves' fascia
    gables  pinnacles on EA's raking cornice's eave corners (and on the south-east apex),
            a voussoir archivolt round each porch arch (its keystone under the flag's foot)
"""
from sagekit.building import Building

from ..style import MenStyle

MID = -0.56                                     # the model's mirror plane y = MID
C, HALF, CH = (-28.35, -0.55), 12.25, 3.4       # the central block
Z_CORBEL, Z_SLAB, Z_WALK, Z_PARAPET = 44.6, 48.0, 50.0, 50.9
OUT = 1.8                                       # the gallery's front, out of the upper wall
CUP = (-28.35, -0.3)
DRUM = 8.9
DOME = [(54.0, 7.9), (55.91, 7.72), (58.0, 4.47), (58.75, 0.9)]
RIDGE = ((-17.65, 33.34, 46.72), (-8.1, 42.9, 46.9))
ARCADE = ((-17.7, 17.7), 1.1)                   # the NE arcade's anchor on x - y = -35.4, the piers' faces out of it
SE_FACE = 0.4                                  # the SE arcade's piers, in the NE frame (mirrored)
ARCHES = (8.2, 20.2)
GABLE = ((-16.7, 34.28), 13.9, 15.3)             # axis origin, the pediment's and the porch face's axial positions
TILES = [(0, 0, 920, 672), (1432, 1272, 2048, 1912)]    # GBStable's slate (4x upscale pixels, rows top-down)
NOT_BAKED = ("X_GUHORSE", "HRSHEADS", "WINDOW_N01", "V1", "V2", "V2FLAG")


def ne_frame(anchor, d=0.0):
    """(a, t, n) on the NE wing's yard side: n = (0.71, -0.71), t = (0.71, 0.71), a d out along n."""
    from mathutils import Vector as V
    r = 0.70711
    n, t = V((r, -r, 0)), V((r, r, 0))
    return V((anchor[0], anchor[1], 0)) + n * d, t, n


def gable_frame(axial):
    """(a, t, n) on the NE wing's gable end at `axial` along the wing: n = (0.71, 0.71), u across."""
    from mathutils import Vector as V
    r = 0.70711
    (ox, oy), _, _ = GABLE
    n = V((r, r, 0))
    return V((ox, oy, 0)) + n * axial, V((-r, r, 0)), n


class Stable(Building):
    style = MenStyle()
    source = "GBStable_SKN"
    target = "GBSTABLE"
    sheet = "GBStable.tga"
    sheet_normal = "GBStable_NRM.tga"
    own_textures = {"GBStable.tga": "GBStablH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    world_space = True
    bake_hidden = NOT_BAKED
    views = {
        "rts": ((-8.0, -0.5, 28.5), 368, 50, -38, 50),
        "close": ((-15.0, -0.5, 30.0), 200, 26, -32, 45),
        "gable": ((-4.0, -46.0, 30.0), 110, 16, -45, 45),
        "stalls": ((-4.0, 30.0, 30.0), 110, 20, -40, 45),
        "ingame": ((2.8, -0.7, 28.5), 837, 53, -62, 50),
    }

    def design(self, kit):
        from .pieces import mirrored
        wing = self._arcade(kit, ARCADE[1], 3.6) + self._roof(kit) + self._gable(kit, apex=False)
        se = mirrored(self._arcade(kit, SE_FACE, 3.1) + self._roof(kit, dormers=False) + self._gable(kit, apex=True), MID)
        return self._crown(kit) + self._cupola(kit) + self._front(kit) + wing + se

    # ------------------------------------------------------------------ the central block
    @staticmethod
    def _crown(kit):
        """The citadel's gallery round the central block: a sable slab on two-step corbels, a
        parapet and merlons on the four faces; bartizans on the yard-side chamfers, pinnacles on
        the back ones."""
        import math

        from mathutils import Vector as V

        from sagekit.blender.geometry import sweep

        from ..motifs import corbel_table, octagon
        cx, cy = C
        path = octagon(cx, cy, HALF, CH)
        slab = [(-2.0, Z_SLAB), (OUT, Z_SLAB), (OUT, Z_WALK), (-2.0, Z_WALK)]
        out, segs = sweep(path, slab, ["stoneB", "enamel", "top", None], center=C)
        par = [(OUT - 1.15, Z_WALK - 0.1), (OUT - 0.1, Z_WALK - 0.1), (OUT - 0.1, Z_PARAPET), (OUT - 1.15, Z_PARAPET)]
        out += sweep(path, par, [None, "stoneA", "top", "stoneA"], center=C)[0]
        for a, b, t, n in segs:
            L = (b - a).length
            a3, t3, n3 = V((a.x, a.y, 0)), t.to_3d(), n.to_3d()
            if L < 6:                            # a chamfer
                m = (a3 + V((b.x, b.y, 0))) / 2
                if m.x > cx:                      # the yard side: a corbelled bartizan
                    c = m + n3 * (OUT + 1.2)
                    out += kit.bartizan(c.x, c.y, Z_CORBEL - 1.2, r=1.9, h=5.6, spire=6.4,
                                        facing=math.atan2(n3.y, n3.x))
                else:
                    c = m + n3 * 1.2
                    out += kit.pinnacle(c.x, c.y, Z_WALK, Z_PARAPET + 3.2, half=1.15, spire=4.2)
                continue
            out += corbel_table(kit, a3, t3, n3, 0.3, L - 0.3, Z_CORBEL, pitch=3.0, d1=0.8, d2=OUT, h=1.7)
            out += kit.merlons(a3, t3, n3, 0.35, L - 0.35, Z_PARAPET, OUT - 1.15, OUT - 0.1, w=2.1, gap=1.5, h=2.5)
        return out

    @staticmethod
    def _cupola(kit):
        import math

        from ..motifs import knob
        from ..shapes import rail, turned
        cx, cy = CUP
        out = [turned(cx, cy, [(DRUM + 0.25, 52.7), (DRUM + 0.25, 53.5)], ["trim"], k=8, phase=math.pi / 8,
                      cap0=("trim", True), cap1=("trim", True))]
        for k in range(8):
            th = math.pi / 8 + k * math.pi / 4
            pts = [(cx + (r + 0.16) * math.cos(th), cy + (r + 0.16) * math.sin(th), z + 0.06) for z, r in DOME]
            out.append(rail(pts, 0.26, "trim", 0.16))
        out += kit.lantern(cx, cy, 57.7, r=2.4, top=61.2)
        out += knob(cx, cy, 61.1, 67.5, r=0.8)
        return out

    @staticmethod
    def _front(kit):
        """The banner hangs clear of the string course (2.1 out) over the door's arch, under the
        gallery's corbels."""
        from mathutils import Vector as V
        a, t, n = V((-16.2, 0, 0)), V((0, 1, 0)), V((1, 0, 0))
        return kit.banner(a, t, n, C[1], Z_CORBEL - 1.0, 5.2, 12.0, d=2.4)

    # ------------------------------------------------------------------ one wing (the NE; the SE mirrors it)
    @staticmethod
    def _arcade(kit, face, eave):
        """Keystones on the stall arches' crowns (nothing in the openings: the horses' heads come
        out of them), a moulded capital and a console under the soffit on each pier (EA's own
        buttresses below). `face`: the piers' faces out of the anchor line (SE_FACE on the SE wing,
        whose arcade stands 0.7 further back than the NE one's mirror image). A sable band of gilt
        stars on the eave's fascia (its front at `eave`, 32.6-35.4)."""
        from ..motifs import slab, star_frieze
        from .pieces import keystone
        a, t, n = ne_frame(ARCADE[0], face)
        out = []
        for u in ARCHES:
            out += keystone(a, t, n, u, 28.2, 31.0, half0=0.65, half1=1.0, d0=-0.3, d1=1.7)
        for u in (14.2, 26.6):
            out.append(slab(a, t, n, u - 1.0, u + 1.0, 26.0, 26.8, -0.3, 0.9, front="course"))
            out.append(slab(a, t, n, u - 0.55, u + 0.55, 26.8, 31.45, -0.3, 1.55, ("stoneB", "stoneB", "stoneB", "stoneB"), "stoneB"))
        a0, t, n = ne_frame(ARCADE[0])
        out += star_frieze(kit, a0, t, n, 0.2, 28.4, 32.8, h=2.3, d0=eave - 1.1, d1=eave, count=9)
        return out

    @staticmethod
    def _roof(kit, dormers=True):
        """The ridge roll and two dormers on the yard slope (the roof: z = 37.4 - 0.85 d, d along n
        from the anchor line; the front of a dormer at d -1.2, its back buried at d -9.5). The SE
        wing's yard slope faces away from the light and crowds the central block: no dormers."""
        from ..motifs import ridge
        from .pieces import dormer
        p, q = RIDGE
        out = ridge(p, q, r=0.3, cresting=2.0, spike=1.6)
        a, t, n = ne_frame(ARCADE[0])
        for u in (ARCHES if dormers else ()):
            out += dormer(kit, a, t, n, u, -1.2, 37.6, 41.4, 2.3, 2.2, -9.5)
        return out

    @staticmethod
    def _gable(kit, apex):
        """Raking coping and pinnacles on the gable (no apex pinnacle on the NE gable: EA's house
        banner stands there); a voussoir archivolt round the porch arch, its keystone under z 28."""
        from .pieces import gable_dress
        _, ped, porch = GABLE
        a, t, n = gable_frame(ped)
        out = gable_dress(kit, a, t, n, 12.3, 35.9, 49.9, 1.4, 2.6, apex=apex, coping=False, pin=(1.5, 3.2, 0.85))
        a, t, n = gable_frame(porch)
        out += kit.voussoirs(a, t, n, (7.35, 4.2, 22.4), (8.8, 5.4, 22.4), -0.3, 0.6, count=9, key=(0.7, 27.9, 0.3))
        return out

    @property
    def sheet_atlas(self):
        from ..prodkit import with_tiles
        return with_tiles(super().sheet_atlas, TILES)      # EA's slate roofs stay slate (the citadel's charcoal)

    def variants(self, install):
        from ..levels import with_damaged      # EA's damaged stable (D1-D3) draws GBStable_D
        return with_damaged(self, super().variants(install), "GBStable_D.tga")

    def decals(self):
        from ..paint import men_layers
        from .pieces import KeepFire                   # the hay and the gate's gilt vines keep EA's colours
        return [men_layers()[2](zrange=(Z_SLAB, Z_WALK), pitch=3.0, r=0.7),    # silver stars on the gallery's band
                KeepFire(((-60.0, -60.0, -5.0), (60.0, 60.0, 30.0)), hue=(20.0, 62.0), sat=(0.33, 0.48), val=(0.28, 0.42))]

    def emphasis(self, c, n):
        if c.z > 43:
            return 1.35                       # the crown, cupola, ridges and dormers
        return 1.0
