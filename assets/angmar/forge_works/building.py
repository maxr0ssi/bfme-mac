"""Angmar forge works (AngmarForgeWorks), pass 1 "the crowned furnace": EA's hall, furnace drum and
troll yard kept whole; four forged tines of the Witch-king's crown with frozen tips rise from the
furnace drum's rim round EA's own fire; EA's six roof horns frozen from about 60 % of their height
(the walls group's `freeze`); icicles under both eaves of the long roof; the yard walls carry Carn
Dum's merlons and a corbel with icicles (the walls group's dress, as on the mill's ring); ice drifts
at the hall's feet; the troll's bellows lever gets iron bands and a frosted iron head, which ride EA's
BONEPUMP and rise and fall with it (sagekit/skinbody.py). Kits: assets/angmar/shapes_addons.py (the
tines), shapes_walls.py (merlons, corbels, drifts, freeze), shapes_ice.py (icicles).

EA's KBForge (object AngmarForgeWorks; role forge): body BASE, 1,991 triangles, a SKIN: MAINBONE
(2,715 vertices: the whole works, not animated), BONEPUMP (the bellows' lever and boards; KBForge_IDLE
pumps it: the lever's head rises and falls 18), 98 leather vertices blended between the two, a few on
the troll's feet and hands at weight 0. Painted from KBForge.tga + KBForge_NRM.tga (DXT1). At rest:
x -49.9..48.7, y -55.3..55.1, z 0..73.3.
Other meshes (EA's, untouched): HILLTROLL 842 (the troll at the lever, (-21, -30)); V1 86 (level 2: two
great horns either side of the drum, x -54..-36.5 and -11..6.3, y 19.6..28.5, to z 74.8); V2 442 (level 3:
a timber watchtower on the roof, x 24.4..41.4, y 24.5..42, z 39.5..110); N_WINDOW 40 (the long walls'
windows); N_GLOW 16 and FIRECARDS01/_2 (the furnace's glow and flame cards); INVISIBLEPICKBO 2.
The door is a Draw of its own (KBForgeDoor). EA's fire burns in the drum (Smoke01: AngForgeWorksFire,
AngForgeSmoke, the glows).
Lifecycle models: KBForge_A (pieces), KBForge_D1 (a remodelled body, 1,997 triangles), KBForge_D2,
KBForge_D3 (skins).
House colour: none of EA's (the style's template, KBHCBtlTwr, copied).

EA's facts (measured 2026-10-04 at rest): the hall along y, its long walls' faces x -8.1 and 43.6 (the
pilasters to 46.6), its gables y +-50.7, the eaves z 34.9 at x -14 and 48.7, the ridge x 17.4 at z 54;
the horns: the ridge ends' (17.4, -49, 53.6..73.3) and (17.4, 49.5, 53.9..67.7), the gable corners'
(44.8 / -10.1, +-48.6, 36.5..55.2); the furnace drum centred (-24, 26), its rim r 17.4..21.7 at z 55;
the yard walls (top z 12.9): the west x -49.9..-44.5 from y -49.7 to 49.7, the south y -49.7..-44.3
from x -44.5 to -8.2; the lever from (-30, -8, 15) to its head (-35.7, -34.2, 30.2).
"""
from sagekit.building import Building

from ..style import AngmarStyle

DRUM = (-24.0, 26.0)
TINES = dict(z0=54.6, r=19.4, H=19.0, W=4.6, degs=(60.0, 120.0, -60.0, -120.0))   # clear of V1's horns (E, W)
# EA's horns, frozen: [(centre up the horn from the frost line to the point)], the casing's radii
HORNS = [
    ([(17.4, -49.0, 63.0), (17.4, -48.6, 66.0), (17.5, -48.0, 68.4), (17.5, -46.9, 70.8), (17.5, -45.6, 73.0)],
     [2.6, 2.3, 1.7, 1.1, 0.5]),
    ([(17.4, 49.4, 59.8), (17.4, 49.1, 62.2), (17.3, 48.9, 64.3), (17.3, 47.9, 66.2), (17.3, 47.1, 67.5)],
     [2.6, 2.3, 1.7, 1.1, 0.5]),
]
for sx in (44.6, -9.9):
    for sy in (1, -1):
        HORNS.append(([(sx, sy * 48.8, 46.0), (sx - 0.4 * (sx > 0) + 0.4 * (sx < 0), sy * 48.6, 48.6),
                       (sx - 0.6 * (sx > 0) + 0.6 * (sx < 0), sy * 48.2, 50.8),
                       (sx - 1.4 * (sx > 0) + 1.4 * (sx < 0), sy * 47.4, 53.4),
                       (sx - 2.2 * (sx > 0) + 2.2 * (sx < 0), sy * 46.6, 55.0)], [2.3, 2.2, 1.7, 1.0, 0.45]))
EAVES = [((48.3, 0.0), (0, 1, 0), (1, 0, 0), -52.0, 52.0), ((-13.6, 0.0), (0, 1, 0), (-1, 0, 0), -52.0, -2.0)]
EAVE_Z = 34.6
YARD_TOP, YARD_FLOOR = 12.9, 0.6
# the yard walls' outer faces: (anchor, along, out, u0, u1, flush); the west wall leaves V1's horn (y 18..30)
# clear and is EA's footprint edge (x -49.9): its merlons stand flush, no corbel
YARD = [((-49.9, 0.0), (0, 1, 0), (-1, 0, 0), -44.0, 17.5, True), ((-49.9, 0.0), (0, 1, 0), (-1, 0, 0), 30.5, 49.7, True),
        ((0.0, -49.7), (1, 0, 0), (0, -1, 0), -44.5, -8.6, False)]
DRIFTS = [((43.6, 0.0), (0, 1, 0), (1, 0, 0), -31.0), ((43.6, 0.0), (0, 1, 0), (1, 0, 0), 33.0),
          ((0.0, -49.7), (1, 0, 0), (0, -1, 0), -36.0)]
LEVER = ((-30.0, -8.0, 15.0), (-35.7, -34.2, 30.2))     # the bellows' lever, its foot to its head (BONEPUMP)

FIRE_POINTS = []


class ForgeWorks(Building):
    style = AngmarStyle()
    source = "KBForge"
    target = "BASE"
    sheet = "KBForge.tga"
    sheet_normal = "KBForge_NRM.tga"
    own_textures = {"KBForge.tga": "KBForgH.tga"}    # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((-0.6, 0.0, 30.0), 350, 50, -38, 50),
        "close": ((-0.6, 0.0, 30.0), 210, 24, -30, 45),
        "ingame": ((-0.6, 0.0, 30.0), 800, 53, -62, 50),
        "yard": ((-28.0, -10.0, 20.0), 150, 30, -150, 45),       # the troll's yard and the drum (-X)
    }
    anim_views = ("rts", "yard")       # the RTS camera, and the troll's lever close (renders/anim/)
    fire_points = FIRE_POINTS
    bake_hidden = ("V1", "V2", "N_WINDOW", "N_GLOW", "FIRECARDS01", "FIRECARDS_2", "INVISIBLEPICKBO")

    def design(self, kit):
        static = kit.retag(self._works(kit))
        pumping = kit.retag(self._lever(kit))
        return static + self.ride(pumping, "BONEPUMP")

    @staticmethod
    def _works(kit):
        from mathutils import Vector as V

        from sagekit.blender.geometry import prism_uz

        from .. import shapes_army as A
        from ..shapes_addons import tine_crown
        from ..shapes_walls import corbel, foot_ice, freeze, merlon_us, merlons
        A.floor(0.0)
        t = TINES
        out = tine_crown(kit, DRUM, t["z0"], [(d, t["r"]) for d in t["degs"]], t["H"], t["W"], seed=2.0)
        for i, (path, radii) in enumerate(HORNS):        # the frost line at the path's second point: a slim casing
            path, radii = path[1:], [r * 0.85 for r in radii[1:]]
            out += freeze(kit, path, radii, seed=1.7 + 1.3 * i, crystals=3)
        for i, (a, tt, n, u0, u1) in enumerate(EAVES):
            out += kit.icicles(V((a[0], a[1], 0)), V(tt), V(n), u0, u1, EAVE_Z, 4.5, int((u1 - u0) / 2.4),
                               d=0.0, crust=0.9, seed=11.0 + i)
        phase = 0
        for i, (a, tt, n, u0, u1, flush) in enumerate(YARD):
            a, tt, n = V((a[0], a[1], 0)), V(tt), V(n)
            us = merlon_us(u0, u1)
            out += merlons(kit, a, tt, n, us, YARD_TOP, w=3.2, h=6.0, d0=-2.0, d1=-0.05 if flush else 0.4, phase=phase)
            phase = (phase + len(us)) % 2
            if flush:
                continue
            out += corbel(kit, a, tt, n, u0, u1, YARD_TOP - 1.9, out=1.2, length=4.5, seed=5.0 + i)
            zc = YARD_TOP - 1.9                     # the corbel's open top under a rime crust
            out.append(prism_uz(a, tt, n, [(u0, zc - 0.1), (u1, zc - 0.1), (u1, zc + 0.45), (u0, zc + 0.45)],
                                -0.3, 1.3, [None, "rime", "rime", "rime"], "rime", None))
        for i, (a, tt, n, u) in enumerate(DRIFTS):
            out += foot_ice(kit, V((a[0], a[1], 0)), V(tt), V(n), u, w=6.0, h=10.0, reach=1.75, floor=0.6,
                            seed=4.0 * i)
        return out

    @staticmethod
    def _lever(kit):
        """Iron bands round the lever and an iron head on it, frosted: they pump with EA's BONEPUMP."""
        import math

        from mathutils import Vector as V
        a, b = V(LEVER[0]), V(LEVER[1])
        d = (b - a).normalized()
        out = []
        for f in (0.3, 0.52):
            c = a.lerp(b, f)
            out.append(kit.tube([c - d * 0.6, c + d * 0.6], [1.25, 1.25], "iron", k=8, cap0="iron", cap1="iron"))
        c = a.lerp(b, 0.74)                     # below the troll's grip at the head
        out.append(kit.tube([c - d * 1.6, c + d * 1.6], [1.6, 1.6], "iron", k=6, cap0="iron", cap1="iron",
                            phase=math.pi / 6))
        side = d.cross(V((0, 0, 1))).normalized()
        for s in (1, -1):                       # two spurs off the head, rimed
            p = c + side * s * 1.3
            out.append(kit.tube([p, p + (side * s + V((0, 0, 0.6))).normalized() * 2.6], [0.5, 0.0], "steel", k=4,
                                cap0="steel", cap1=None))
        return out
