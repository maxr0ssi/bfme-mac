"""Angmar mill (AngmarMill), pass 1 "the thrall mill": EA's ring wall, capstan and shed kept whole; the
wall becomes a stretch of Carn Dum's frozen wall (the walls group's merlons on its inner edge, a
corbel with icicles under the outer one, ice drifts up both feet); on the capstan the thralls push, a crown of
five small forged tines with frozen tips round the post's head, and a ring of iron barbs on the great
ring beam: both turn with the capstan (they ride EA's BONE_POST01, sagekit/skinbody.py); two cold
braziers on the back walk ("coldflame"). Kits: assets/angmar/shapes_walls.py (the wall's dress),
shapes_addons.py (the tines), shapes_crown.py (the braziers).

EA's KBMill (object AngmarMill, the build menu's "mill"; role farm): body BASE, 580 triangles, a
SKIN on three bones (sagekit/skinbody.py): BONE_MAIN01 (313 vertices: the ring wall and the shed's
walls; not animated), BONE_POST01 (519: the post, the millstone's teeth, the ring beam and its three
arms; KBMill_IDLE turns it) and BONEGEAR01 (106: the gear and shaft from the post to the shed; turned
too). Painted from KBMill.tga + KBMill_NRM.tga (DXT1). At rest in model space: x -48.37..51.45,
y -44.50..45.97, z 0.6..32.7.
Other meshes (EA's, untouched): ORC01..03 308 each (the thralls on BONE_POST01..03's skeletons);
V2 1309 (level 3: a watchtower over the shed, x 31.6..48.4, |y| < 8.7, to z 85; buttresses x 21.7..41.9,
y +-11.6..31.7 to z 31; a hopper over the post from z 35, r 4.3..15.3; chains to the wall); V1 510
(level 2: three great horns on raised wall blocks at (-42, 0), (15, -36), (14, 38), to z 49); PICK_BOX
10 (the shed's roof, x 27.5..51.5, to z 32.8; drawn); N_WINDOW 8; BASE_INVISIBLE_ 9 (a ground plane).
Lifecycle models in its Draw module: KBMill_A (pieces; its POST and RING draw KBMillNormal.tga),
KBMill_D1 (the healthy body rigid: derived), KBMill_D2, KBMill_D3 (skins).
House colour: KBHCMill.

EA's facts (measured 2026-10-04 at rest, sagekit/skinbody.py Rest): the ring wall's centre (-2.2, 0.5),
its faces vertical, inner r 36.0..36.7, outer r 42.0..42.8, top z 13.8 (raised blocks z 14.2 where V1's
horns stand), floor z 0.6, open on +X where the shed stands; the post's head r 6.0..6.5 at z 27..28.9
(the gear's top z 25.8 beside it); the ring beam r 13.5..17.4, z 6..15; the arms out to r 31.3 at
z 9.8..11.6; the shaft z 19.8..23.4 from x 6.5 to the shed; the thralls walk at r 20..31.
"""
from sagekit.building import Building

from ..style import AngmarStyle

CENTRE = (-2.2, 0.5)                  # the ring wall's centre (BONE_POST01's pivot: the capstan's axis)
WALL_TOP, FLOOR = 13.8, 0.6
# the wall's top corners (z 13.8) of its plain stretches, counter-clockwise, (inner, outer); the raised
# blocks under V1's horns carry nothing. V1 (level 2) wraps the wall in a thicker one (r 36.5..47, top
# z 14.5): the merlons stand on the inner edge, over the yard, so they read the same at every level;
# the corbel, icicles and drifts on the outer face are inside V1's shell from level 2
STRETCHES = [
    [((1.2, 36.4), (1.7, 42.4)), ((-3.7, 36.7), (-3.8, 42.9)), ((-17.6, 33.6), (-20.0, 39.2)),
     ((-29.2, 25.4), (-33.6, 29.6)), ((-36.9, 13.3), (-42.5, 15.5)), ((-37.7, 9.4), (-43.5, 10.6))],
    [((-37.4, -9.7), (-43.1, -11.3)), ((-36.3, -13.5), (-41.9, -16.0)), ((-28.2, -25.3), (-32.4, -29.7)),
     ((-16.3, -33.0), (-18.5, -38.8)), ((-2.2, -35.6), (-2.1, -41.8)), ((2.6, -34.7), (3.3, -41.0))],
    [((20.1, -27.1), (23.9, -32.1)), ((24.2, -23.7), (28.6, -28.1)), ((30.4, -13.6), (36.2, -15.8)),
     ((31.0, -9.8), (37.0, -10.4))],
    [((31.6, 10.5), (37.5, 10.9)), ((31.0, 14.5), (36.7, 16.8)), ((24.3, 24.5), (28.9, 28.7)),
     ((18.7, 29.3), (22.0, 34.5))],
]
SKIP = {(2, 2), (3, 0)}                             # (stretch, chord) left plain: under the shed's roof (PICK_BOX)
OUTER_SKIP = {(2, 0), (2, 1), (3, 1), (3, 2)}       # no corbel: V2's buttresses lean on the wall there (level 3)
DRIFTS = [(0, 1), (0, 3), (1, 1), (1, 3)]          # (stretch, chord): an ice drift up the outer foot
INNER_DRIFTS = [(0, 2), (0, 4), (1, 2), (1, 4)]    # and up the inner foot, beyond the arms' sweep (r 31.3)
BRAZIERS = [124.0, -124.0]                          # degrees round CENTRE, on the walk (r 40.0)

POST = (-2.2, 0.5)                    # the post turns about the capstan's axis
CROWN = dict(z0=28.3, r=4.0, H=9.0, W=1.7, n=5)    # the tines' feet in the post's head (top z 28.9)
BARBS = dict(r=17.2, z=14.6, n=12, L=3.4)           # on the ring beam's top edge, under the shaft (z 19.8)

FIRE_POINTS = [(-24.6, 33.7, 18.8, 'coldflame'), (-24.6, -32.7, 18.8, 'coldflame')]     # the braziers (design log)


class Mill(Building):
    style = AngmarStyle()
    source = "KBMill"
    target = "BASE"
    sheet = "KBMill.tga"
    sheet_normal = "KBMill_NRM.tga"
    own_textures = {"KBMill.tga": "KBMilH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    state_normals = ("KBMillNormal.tga",)            # KBMill_A's POST and RING: EA named that normal map off the pattern
    views = {
        "rts": ((1.5, 0.7, 16.0), 304, 50, -38, 50),
        "close": ((1.5, 0.7, 16.0), 180, 24, -30, 45),
        "ingame": ((1.5, 0.7, 16.0), 690, 53, -62, 50),
        "back": ((1.5, 0.7, 16.0), 200, 30, 140, 45),
    }
    anim_views = ("rts", "close")      # the RTS camera, and the capstan close (renders/anim/)
    # The fire reduction (Max, 2026-10-05, docs/ART.md "Fire budget": a building whose fire is not its identity,
    # at most 6 live particles): none. 0.0 live (was 14.4).
    fire_points = []
    lifecycle = {"KBMill_A": {"fill": True}}           # the build-up: cut along EA's pieces, the merlons kept slivers
    bake_hidden = ("V1", "V2", "N_WINDOW", "BASE_INVISIBLE_",    # level 1: the level-up meshes come later;
                   "PICK_BOX")          # a closed box round the shed's walls: it would black out their bake

    def design(self, kit):
        from assets.isengard.shapes_industry import logged      # prints the design's FIRE_POINTS
        return logged(kit, lambda k: self._pieces(k))

    def _pieces(self, kit):
        static = kit.retag(self._wall(kit))
        turning = kit.retag(self._capstan(kit))
        return static + self.ride(turning, "BONE_POST01")

    @staticmethod
    def _wall(kit):
        from mathutils import Vector as V

        from sagekit.blender.geometry import prism_uz

        from .. import shapes_army as A
        from ..shapes_walls import corbel, foot_ice, merlon_us, merlons
        A.floor(FLOOR)
        out = []
        phase = 0
        ctr = V((CENTRE[0], CENTRE[1], 0))
        for s, corners in enumerate(STRETCHES):
            for i, ((p, po), (q, qo)) in enumerate(zip(corners, corners[1:])):
                if (s, i) in SKIP:
                    continue
                for (x, y), (x1, y1), inner in ((p, q, True), (po, qo, False)):
                    a, t = V((x, y, 0)), V((x1 - x, y1 - y, 0))
                    L = t.length
                    t.normalize()
                    n = V((t.y, -t.x, 0))
                    if (n.dot(a - ctr) < 0) != inner:
                        n = -n                      # inner: toward the yard; outer: away from it
                    if inner:
                        us = merlon_us(0.0, L)
                        out += merlons(kit, a, t, n, us, WALL_TOP, phase=phase)
                        phase = (phase + len(us)) % 2
                        if (s, i) in INNER_DRIFTS:
                            out += foot_ice(kit, a, t, n, L / 2, w=5.0, h=8.0, reach=1.6, floor=FLOOR, seed=5.0 * s + i)
                        continue
                    if (s, i) in OUTER_SKIP:
                        continue
                    out += corbel(kit, a, t, n, 0.0, L, WALL_TOP - 1.9, out=1.35, seed=7.0 * s + i,
                                  ends=(i == 0, i == len(corners) - 2))
                    zc = WALL_TOP - 1.9                 # the ledge's top under a rime crust (the corbel's top is open)
                    out.append(prism_uz(a, t, n, [(0.0, zc - 0.1), (L, zc - 0.1), (L, zc + 0.45), (0.0, zc + 0.45)],
                                        -0.3, 1.45, [None, "rime", "rime", "rime"], "rime", None))
                    if (s, i) in DRIFTS:
                        out += foot_ice(kit, a, t, n, L / 2, w=6.0, h=10.0, reach=1.75, floor=FLOOR, seed=3.0 * s + i)
        for deg in BRAZIERS:
            p = kit.polar(ctr, 40.0, deg, WALL_TOP)
            out += kit.cold_brazier((p.x, p.y, WALL_TOP), r=1.9, h=8.0, seed=deg / 100.0)
        return out

    @staticmethod
    def _capstan(kit):
        import math

        from mathutils import Vector as V

        from ..shapes_addons import tine_crown
        c = CROWN
        out = tine_crown(kit, POST, c["z0"], [(30.0 + i * 360.0 / c["n"], c["r"]) for i in range(c["n"])], c["H"], c["W"],
                         seed=4.0, rune=False, band=False, barbs=[(0.5, 1, 0.5)])
        b = BARBS                                           # iron barbs round the ring beam, raked back
        for i in range(b["n"]):
            a = math.radians(i * 360.0 / b["n"])
            e, side = V((math.cos(a), math.sin(a), 0)), V((-math.sin(a), math.cos(a), 0))
            p0 = V((POST[0], POST[1], 0)) + e * b["r"] + V((0, 0, b["z"] - 0.6))
            p1 = p0 + (e * 0.35 + side * 0.25 + V((0, 0, 1))).normalized() * b["L"]
            out.append(kit.tube([p0, p1], [0.55, 0.0], "iron", k=4, cap0="iron", cap1=None, phase=math.pi / 4))
        return out
