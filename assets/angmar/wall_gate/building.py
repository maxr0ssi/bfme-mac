"""Angmar wall gate (AngmarWallGateSmall; model KBAngwGN_OP): EA's two battered pylons kept whole -
each with its great horn curving in over the gateway, EA's small spike on its outer end and the
emblem low on its end face - and the door slab between them untouched. The gate becomes the
Witch-king's:

- a gatehouse lintel: a heavy stone beam laid across the gateway from pylon to pylon just over
  the door's top (z 76.4..86), its rimed top rising to a low point in the middle, the walls'
  merlons along its flat runs, icicles under them;
- a barbed iron portcullis in each mouth of the gateway, raised into the lintel: eleven thick bars,
  rimed crossbars, steel teeth with barbs hanging to z ~59 (units pass under them), a beam set into
  both pylons (a gatehouse's two portcullises: either face may be the field side);
- a pointed keystone set into the lintel's middle (0.4 proud of its faces, its point at z 93.4),
  the Witch-king's sigil inset on both its faces: an iron kite plate with a steel rim, the
  faceless helm in black iron with its eye-slit glowing cold, the crown's seven steel tines;
- a sorcerer's cold brazier on each pylon's top between the horn and EA's spike ("coldflame");
- the walls' frozen dress: a corbel with icicles under the pylon tops on both faces, ice drifts on
  the plinth ledge up each pylon's faces. No merlons: the pylons have no walk, and their small
  tops (14 x 16, EA's horn and spike on them) carry the brazier alone.

No new peak: EA's horns are the gate's (the frozen tines stand on the wall tower). No banners.

EA's facts (TOWERS mesh coordinates = model, measured 2026-10-01, ray casts and the door's
animations): the pylons |y| 41..68.4 on a plinth to z 10.4 (|x| 12.9, the ends |y| 68.4), battered
from |x| 11.7 / |y| 66.2 to 7.4 / 57.4 at their tops (z 79..82.6, a ridge to 86.3 along x 0); the
horns rise from |y| 41..48 on the tops and curve in to their points at (0.2, +-29.9, 129.2); EA's
spike on each outer end at |y| 57, z 96. The door (BONE_DOOR 01, its bone at z 37.9) is a slab
x -5.5..5.1, |y| < 40.1, z 0..75.8 that sinks into the ground to open (KBAngwGN_OPAN, 100 frames:
z -77.9..-2.1 open) and rises to close (KBAngwGN_CLSAN). Kept clear: the gateway |y| < 40.1 below
z 76.2 in the door's slot |x| < 5.5 (the lintel's underside at 76.4, over the closed door's top;
the portcullises hang in the planes |x| 6.6, outside the slot), the end faces |y| 68.4
where the wall segments meet. No Ice Walls mesh on this model; the Ice Walls sheet gets our own
copy (KBFortressE_Ice). Lifecycle models in its Draw module: KBAngwGN_A, KBAngwGN_D1, KBAngwGN_D2,
KBAngwGN_D3CLS, KBAngwGN_D3OPN. House colour: none.
"""
from sagekit.building import Building

from ..style import AngmarStyle

PYLON = (41.4, 57.4)                 # the pylon tops' inner and outer ends (|y|)
BRAZIER = (52.4, 82.6, 3.4, 12.0)    # |y|, z, r, h
LINTEL = (44.0, 7.4, 76.4, 86.0)     # |y| (its ends in the pylons), |x|, underside (over the door's 75.8), top
GRILLE = (6.6, 40.2, 64.5, 80.0)     # |x| of the two portcullises, half width, z0 (teeth to ~59), z1 (in the lintel)
KEYSTONE = (7.8, 0.5)                # its faces (0.4 proud of the lintel's), the sigil's scale
PEAK = (5.0, 14.0)                   # the lintel's top rises 5 to a low point over the keystone, over |y| < 14


def _fire_points():
    y, z, r, h = BRAZIER
    return [(0.0, s * y, round(z + h * 0.62, 1), "coldflame") for s in (1, -1)]


class WallGate(Building):
    style = AngmarStyle()
    source = "KBAngwGN_OP"
    target = "TOWERS"
    sheet = "KBFortressB.tga"
    sheet_normal = "KBFortressB_NRM.tga"
    own_textures = {"KBFortressB.tga": "KBFortressE.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    facet_islands = 8                       # the unwrap overlapped (0.05%): seams at EA's islands and 8-degree turns
    HOUSE_DRAW = "ModuleTag_Draw_HCWallGate"
    house_tags = ()
    # The fire reduction (Max, 2026-10-05, docs/ART.md "Fire budget": a building whose fire is not its identity,
    # at most 6 live particles): the pylons' braziers a small cold flame each. 6.0 live (was 14.4).
    fire_points = [(0.0, 52.4, 90.0, 'coldtorch'), (0.0, -52.4, 90.0, 'coldtorch')]
    # EA's gate rises through the ground; it stands whole on it at frame 466
    lifecycle = {"KBAngwGN_A": {"match": 466}}
    views = {
        "rts": ((0.0, 0.0, 64.6), 418, 50, -38, 50),
        "close": ((0.0, 0.0, 64.6), 247, 24, -30, 45),
        "pylon": ((0.0, -50.0, 86.0), 90, 38, -38, 45),          # a pylon's top: the brazier, the horn, EA's spike
        "ingame": ((0.0, 0.0, 64.6), 951, 53, -62, 50),
    }

    def design(self, kit):
        from mathutils import Vector as V

        from sagekit.blender.geometry import loft

        from ..shapes_walls import corbel, foot_ice, grille, keystone, merlon_us, merlons
        ly, lx, z0, z1 = LINTEL
        ridge = lambda y: z1 + PEAK[0] * max(0.0, 1.0 - abs(y) / PEAK[1])          # noqa: E731
        sec = lambda y: [V((-lx, y, z0)), V((lx, y, z0)), V((lx, y, ridge(y) - 1.2)),       # noqa: E731
                         V((lx - 1.2, y, ridge(y))), V((-lx + 1.2, y, ridge(y))), V((-lx, y, ridge(y) - 1.2))]
        ys = [-ly, -33.0, -22.0, -PEAK[1], -7.0, 0.0, 7.0, PEAK[1], 22.0, 33.0, ly]
        tags = [["stoneA", "stoneA", "stoneA", "rime", "stoneA", "stoneA"]] * (len(ys) - 1)       # the top rimed
        out = [loft([sec(y) for y in ys], tags, cap0=("stoneA", True),
                    cap1=("stoneA", True))]                 # end caps kept: EA's pylon tops are open
        for sx in (1, -1):                                  # battlement and icicles on the flat runs, the portcullises
            a, t, n = V((sx * lx, 0, 0)), V((0, 1, 0)), V((sx, 0, 0))
            us = merlon_us(-ly + 3.0, -PEAK[1] - 1.0, pitch=7.0) + merlon_us(PEAK[1] + 1.0, ly - 3.0, pitch=7.0)
            out += merlons(kit, a, t, n, us, z1, d0=-2.4, d1=0.2, phase=(sx + 1) // 2)
            for u0, u1 in ((-ly + 5.0, -PEAK[1]), (PEAK[1], ly - 5.0)):
                out += kit.icicles(a, t, n, u0, u1, z1 - 1.0, 5.0, 8, d=0.3, crust=0.8, w=1.2, seed=sx + u0)
            gx, gw, gz0, gz1 = GRILLE
            out += grille(kit, V((sx * gx, 0, 0)), V((0, 1, 0)), V((sx, 0, 0)), -gw, gw, gz0, gz1, bars=11,
                          rails=(0.42,), r=0.9, teeth=5.4, ext=3.0)
        half, ks = KEYSTONE
        out += keystone(kit, (0.0, 0.0, z0), (0, 1, 0), half, ks)
        for sy in (1, -1):
            y, z, r, h = BRAZIER
            out += kit.cold_brazier((0.0, sy * y, z), r=r, h=h, seed=sy + 2.0)
            for sx in (1, -1):
                t, n = V((0, 1, 0)), V((sx, 0, 0))
                c0, c1 = sorted((sy * 43.0, sy * PYLON[1]))
                out += corbel(kit, V((sx * 7.35, 0, 0)), t, n, c0, c1, 77.4, out=1.3, length=5.5, seed=sx + 3 * sy)
                out += foot_ice(kit, V((sx * 11.65, 0, 0)), t, n, sy * 53.0, w=12.0, h=13.0, reach=2.05, floor=10.4,
                                k=6, seed=sx * 2 + sy)
        return kit.retag(out)
