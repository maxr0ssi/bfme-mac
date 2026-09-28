"""The Gondor arrow tower's pieces (Blender side), shared by its two build variations: EA's
GBFARTOWA (men/arrow_tower) and GBFARTOWB (men/arrow_tower_b) are two proportions of one tower -
a chamfered-square shaft, a slimmer belfry of tall lancets and a steep chamfered dome - B's with
a taller shaft and joined on its -X side to a wall walk. A Spec holds one model's measurements
(its mesh coordinates); the functions lay the citadel's crown on it with the shared pieces of
men/garrison_tower/pad.py (gallery, plinth, banner) and men/wall_hub/dome.py (eave band, ribs):

    gallery    the machicolated gallery round the shaft top (a black band with silver stars,
               a parapet, square merlons), on the outward faces or all round
    bartizans  corbelled corner turrets with slit windows and slate spirelets on the front corners
               (all four where the footprint allows)
    belfry     pilasters up the belfry's chamfers
    crown      a steel eave band under the dome, pinnacles on the eave's chamfers, steel ribs, a
               lantern cupola, a gilt orb and a spike
    plinth     a moulded base course along the side faces
"""
import math
from types import SimpleNamespace as Spec

from mathutils import Vector as V

from sagekit.blender.geometry import prism_uz

A = Spec(shaft=(23.16, 0.21, 12.01, 3.4),                      # centre x, y, half, chamfer (to 49.5)
         gallery=(43.3, 46.9, 49.5, 51.0),                     # corbels, slab, walk (the shaft top), parapet
         belfry=(23.2, 0.16, 11.15, 3.15, 49.5, 72.47),        # centre, half, chamfer, foot, top
         dome=[(72.47, 12.0), (74.89, 10.0), (83.21, 7.1), (88.94, 3.9)],   # EA's point 93.62
         lantern=(89.6, 2.8, 94.2), finial=(99.5, 109.0),     # +16.4 %
         bartizan=(16.8, 42.4, 2.05, 8.6, 6.4), corners=(-45, 45), eave_pins=(70.0, 74.0, 4.2),
         closed=False)
B = Spec(shaft=(19.43, 0.26, 13.05, 3.7),                      # to 75.92
         gallery=(69.7, 73.3, 75.92, 77.4),
         belfry=(19.4, 0.14, 11.26, 3.15, 78.27, 100.33),
         dome=[(100.09, 11.7), (110.61, 7.72), (117.21, 4.22)],   # EA's point 122.93
         lantern=(117.8, 3.2, 123.5), finial=(129.5, 140.5),  # +14.3 %
         bartizan=(16.8, 68.9, 2.05, 9.8, 7.2), corners=(-45, 45, 135, -135), eave_pins=(97.8, 101.8, 4.6),
         closed=True)


def gallery(kit, s):
    from ..garrison_tower import pad
    from ..wall_hub import dome as D
    cx, cy, half, ch = s.shaft
    if not s.closed:                                            # the -X face lies on EA's footprint
        return pad.gallery(kit, 0.0, s.shaft, s.gallery, clear=0.0, back=0.5, skip=(1, 3))
    z_corbel, z_slab, z_walk, z_parapet = s.gallery
    sec = D.Section(cx, cy, chamfer=ch / half)
    return D.gallery(kit, sec, half, z_corbel, z_slab, z_walk, z_parapet, merlon=dict(w=2.3, gap=1.7, h=2.5),
                     skip=(1, 3, 5, 7))


def bartizans(kit, s):
    cx, cy, half, ch = s.shaft
    R, z0, r, h, spire = s.bartizan
    out = []
    for deg in s.corners:
        a = math.radians(deg)
        out += kit.bartizan(cx + R * math.cos(a), cy + R * math.sin(a), z0, r=r, h=h, spire=spire, facing=a)
    return out


def belfry(s):
    """Pilasters up the belfry's four chamfers, a moulded base on each."""
    bx, by, half, ch, z0, z1 = s.belfry
    c = half - ch / 2                                           # the chamfer's middle, along each axis
    out = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            n = V((sx, sy, 0)).normalized()
            t = V((-n.y, n.x, 0))
            a = V((bx + sx * c, by + sy * c, 0))
            out.append(prism_uz(a, t, n, [(-1.1, z0 + 2.6), (1.1, z0 + 2.6), (1.1, z1 - 1.3), (-1.1, z1 - 1.3)], -0.4, 0.5,
                                [None, "stoneB", "top", "stoneB"], "stoneA", None))
            out.append(prism_uz(a, t, n, [(-1.4, z0 + 1.2), (1.4, z0 + 1.2), (1.4, z0 + 2.6), (-1.4, z0 + 2.6)], -0.4, 0.8,
                                ["stoneB", "stoneB", "top", "stoneB"], "course", None))
    return out


def crown(kit, s):
    from ..wall_hub import dome as D
    bx, by, half, ch, z0, z1 = s.belfry
    cx, cy, h0, _ = s.shaft
    band = D.eave_band(D.Section(bx, by, chamfer=ch / half), half, z1 - 0.75, d=(-0.5, 0.35))   # under the eave's soffit
    sec = D.Section(cx, cy, chamfer=0.28)
    out = band + D.ribs(sec, s.dome)
    z_eave, h_eave = s.dome[0]
    c = h_eave * (1 - 0.28 / 2) + 0.3                         # the eave's chamfers, a little out
    za, zb, spire = s.eave_pins
    for sx in (-1, 1):                                          # pinnacles on the eave's chamfers
        for sy in (-1, 1):
            out += kit.pinnacle(cx + sx * c, cy + sy * c, za, zb, half=0.9, spire=spire)
    z, r, top = s.lantern
    out += kit.lantern(cx, cy, z, r=r, top=top)
    return out + kit.finial(cx, cy, top - 0.1, *s.finial)


def build(kit, s):
    from ..garrison_tower import pad
    return pad.plinth(0.0, s.shaft) + gallery(kit, s) + bartizans(kit, s) + belfry(s) + crown(kit, s)
