"""Dwarven sentry tower (DwarvenSentryTower): the slim tower keeps its shaft with the nested pointed
door frames, the stepped gabled buttresses and slit windows, and its cross-planned head with the
prow panels and archer windows. The head gains a Dwarven crown: a corbelled turret in each notch of
the cross capped by a stepped pyramid, a hex-frieze parapet with a stepped gable on each arm end,
and a stepped rune crown with a gilded point in the middle of the roof; under the head, a chevron
band of the triangle frieze along the V-shaped lower edge of each face and a keystone bracket under
each V point.

All numbers are DBFTOWER mesh coordinates measured on the original (symmetric in x and y): shaft
core +-11.01 / +-10.94 (square again at z 69.6), head faces at +-13.2 / +-13.14 whose lower edge is a
V (z 70.67 at the middle, 79.93 at the corners), cross-shaped roof at z 109.38 with arms +-8.27 wide reaching x +-14.67 / y +-14.55, corner
pillars x 8.27..13.2 / y 8.21..13.14 ending in pyramid caps at z 96.2..100.3. The archer bones
(ARROW_01..16) sit on the arm-end faces at z 100.7..101.7: nothing is placed in front of them.
"""
from sagekit.building import Building

from ..style import DwarvenStyle

ROOF = 109.38
ARM = (8.27, 14.67, 14.55)        # arm half-width, x-arm end, y-arm end
PILLAR = (8.27, 13.2, 8.21, 13.14)  # corner pillar in the +,+ quadrant: x0, x1, y0, y1 (below z 96.2)
TURRET = (8.1, 13.6, 8.1, 13.6)   # turret shaft in the +,+ quadrant: 1.0 back from the arm ends
HEAD_V = (70.67, 13.2, 13.14)     # head faces x = +-13.2 / y = +-13.14: their lower edge is a V from
                                  # z 70.67 at the middle up to 79.93 at the corners
SHAFT = (11.01, 10.94)            # shaft core half extents x / y under the head


class SentryTower(Building):
    style = DwarvenStyle()
    source = "DBTower"
    target = "DBFTOWER"
    sheet = "DBTower.tga"
    bake_hidden = ("DBTOWERG",)      # far-off ground patch (DBStoneA, not extracted): out of bakes and renders
    views = {                        # the automatic ones, but "close" framed on the head and crown
        "rts": ((0, 0, 55), 262, 50, -38, 50),
        "close": ((0, 0, 97), 105, 28, -32, 45),
        "ingame": ((0, 0, 55), 595, 53, -62, 50),
    }

    def design(self, kit):
        from mathutils import Vector as V
        solids = []
        _, ex, ey = ARM
        # 1. corner turrets in the notches of the cross, from the pillar tops up past the roof
        for sx in (-1, 1):
            for sy in (-1, 1):
                solids += turret(sx, sy)
        # 2. arm ends: hex-frieze parapet slab and a stepped gable, between the turrets
        x0 = TURRET[0]
        for a, t, n, d0 in ((V((ex, -x0, 0)), V((0, 1)), V((1, 0)), -2.2), (V((-ex, x0, 0)), V((0, -1)), V((-1, 0)), -2.2),
                            (V((x0, ey, 0)), V((-1, 0)), V((0, 1)), -2.1), (V((-x0, -ey, 0)), V((1, 0)), V((0, -1)), -2.1)):
            solids += crest(a, t, n, 2 * x0, 0.0, ROOF, d0, 0.9)
        # 3. a stepped rune crown in the middle of the roof
        solids += roof_crown()
        # 4. under the head: a chevron band of the triangle frieze following the V-shaped lower edge
        #    of each head face, and a keystone corbel under each V point
        vz, vx, vy = HEAD_V
        sx_, sy_ = SHAFT
        for a, t, n, L, slope, reach in (
                (V((vx, 0, 0)), V((0, 1)), V((1, 0)), vy + 0.45, (79.93 - vz) / vy, vx - sx_),
                (V((-vx, 0, 0)), V((0, -1)), V((-1, 0)), vy + 0.45, (79.93 - vz) / vy, vx - sx_),
                (V((0, vy, 0)), V((-1, 0)), V((0, 1)), vx + 0.45, (79.93 - vz) / vx, vy - sy_),
                (V((0, -vy, 0)), V((1, 0)), V((0, -1)), vx + 0.45, (79.93 - vz) / vx, vy - sy_)):
            solids += chevron_band(a, t, n, L, vz + 0.15, slope, 2.6, -0.3, 0.45)
            solids.append(keystone(V((a.x - n.x * reach, a.y - n.y * reach, 0)), t, n, reach + 0.45, 64.4, vz, slope))
        return solids

    def emphasis(self, c, n):
        if c.z > 95:
            return 1.5                        # the crown
        return 1.2 if c.z > 66 else 1.0


# ---------------------------------------------------------------------- helpers (candidates for shapes.py)
def turret(sx, sy):
    """A corner turret in the (sx, sy) notch of the cross: a corbel from the corner pillar out to the
    turret shaft, the shaft (hexagon frieze at the top), a bronze cornice and the fortress's stepped
    pyramid at 0.8 scale."""
    from sagekit.blender.geometry import box_rings, loft

    def box(r, z, ch):
        x0, x1, y0, y1 = r
        return box_rings(sorted((sx * x0, sx * x1)), sorted((sy * y0, sy * y1)), z, ch)
    t = TURRET
    cx, cy = sx * (t[0] + t[1]) / 2, sy * (t[2] + t[3]) / 2
    h = (t[1] - t[0]) / 2
    out = [loft([box(PILLAR, 93.4, 0.3), box(t, 96.9, 0.4)], ["stoneB"], cap0=("top", False), cap1=("top", False)),
           loft([box(t, 96.9, 0.4), box(t, 106.6, 0.4), box(t, 108.9, 0.4)], ["stoneB", "hex"],
                cap0=("top", False), cap1=("top", False))]
    c0 = box_rings((cx - h, cx + h), (cy - h, cy + h), 108.9, 0.4)
    c1 = box_rings((cx - h - 0.55, cx + h + 0.55), (cy - h - 0.55, cy + h + 0.55), 109.7, 0.4)
    c2 = box_rings((cx - h - 0.55, cx + h + 0.55), (cy - h - 0.55, cy + h + 0.55), 110.3, 0.4)
    out.append(loft([c0, c1, c2], ["trim", "trim"], cap0=("top", False), cap1=("top", True)))
    out += step_pyramid(cx, cy, 110.3, 0.8)
    return out


def step_pyramid(cx, cy, z0, s):
    """shapes.step_pyramid at scale s, standing on z0."""
    from mathutils import Vector as V

    from sagekit.blender.geometry import box_rings, loft
    out = []
    z = z0
    for h0, h1, dz, tg in ((3.9, 3.5, 6.0, "stoneB"), (2.9, 2.7, 2.4, "stoneA"), (1.9, 1.8, 1.7, "stoneA")):
        r0 = box_rings((cx - h0 * s, cx + h0 * s), (cy - h0 * s, cy + h0 * s), z, 0.3)
        r1 = box_rings((cx - h1 * s, cx + h1 * s), (cy - h1 * s, cy + h1 * s), z + dz * s, 0.3)
        out.append(loft([r0, r1], [tg], cap0=("top", False), cap1=("top", True)))
        z += dz * s
    r0 = box_rings((cx - 1.8 * s, cx + 1.8 * s), (cy - 1.8 * s, cy + 1.8 * s), z, 0.25)
    out.append(loft([r0, [V((cx, cy, z + 2.1 * s))] * len(r0)], ["trim"], cap0=("top", False), cap1=("top", False)))
    return out


def crest(a, t, n, L, end, z0, d0, d1):
    """A parapet slab along a side (u 0..L from `a` along `t`, d0..d1 along `n`) carrying the hexagon
    frieze, with a stepped triangle gable over its visible middle; `end` = the length hidden in the
    corner blocks at each end."""
    from sagekit.blender.geometry import prism_uz
    out = []
    z1, z2, z3, z4 = z0 + 2.3, z0 + 4.0, z0 + 5.4, z0 + 9.0
    out.append(prism_uz(a, t, n, [(0, z0), (L, z0), (L, z1), (0, z1)], d0, d1,
                        ["stoneB", "stoneB", "top", "stoneB"], "hex", "stoneA"))
    u0, u1 = end + 2.0, L - end - 2.0
    out.append(prism_uz(a, t, n, [(u0, z1), (u1, z1), (u1, z2), (u0, z2)], d0 + 0.15, d1 - 0.35,
                        [None, "stoneB", "top", "stoneB"], "stoneA", "stoneA"))
    u0, u1 = u0 + 1.9, u1 - 1.9
    out.append(prism_uz(a, t, n, [(u0, z2), (u1, z2), (u1, z3), (u0, z3)], d0 + 0.3, d1 - 0.6,
                        [None, "trim", "top", "trim"], "trim", "stoneA"))
    out.append(prism_uz(a, t, n, [(u0, z3), (u1, z3), ((u0 + u1) / 2, z4)], d0 + 0.3, d1 - 0.6,
                        [None, "top", "top"], "stoneA", "stoneA"))
    return out


def roof_crown():
    """Battered tiers in the middle of the roof (rune belt, bronze cornice, triangle frieze, plain)
    and a gilded pyramid point: the tower's highest point."""
    from mathutils import Vector as V

    from sagekit.blender.geometry import box_rings, loft

    def ring(h, z, ch):
        return box_rings((-h, h), (-h, h), z, ch)
    z0 = ROOF
    out = [loft([ring(6.0, z0, 0.8), ring(5.7, z0 + 3.2, 0.8)], ["rune"], cap0=("top", False), cap1=("top", False)),
           loft([ring(6.1, z0 + 3.2, 0.8), ring(6.1, z0 + 3.8, 0.8), ring(5.6, z0 + 4.1, 0.7)],
                ["trim", "trim"], cap0=("trim", True), cap1=("top", True)),
           loft([ring(4.4, z0 + 4.1, 0.6), ring(4.1, z0 + 7.2, 0.6)], ["tri"], cap0=("top", False), cap1=("top", True)),
           loft([ring(2.9, z0 + 7.2, 0.45), ring(2.7, z0 + 9.6, 0.45)], ["stoneA"], cap0=("top", False), cap1=("top", True))]
    r = ring(2.1, z0 + 9.6, 0.35)
    out.append(loft([r, [V((0, 0, z0 + 14.6))] * len(r)], ["trim"], cap0=("top", False), cap1=("top", False)))
    return out


def chevron_band(a, t, n, L, zc, slope, h, d0, d1):
    """A band of height h following a V-shaped edge on a wall face (anchor a on the V's axis, along
    t, outward n): lowest at zc on the axis, rising by `slope` per unit out to +-L; the triangle
    frieze runs along each arm, bronze edges."""
    from sagekit.blender.geometry import prism_uz
    zL = zc + L * slope
    return [prism_uz(a, t, n, [(0, zc), (L, zL), (L, zL + h), (0, zc + h)], d0, d1,
                     ["trim", "stoneB", "trim", None], "tri|a", None),
            prism_uz(a, t, n, [(-L, zL), (0, zc), (0, zc + h), (-L, zL + h)], d0, d1,
                     ["trim", None, "trim", "stoneB"], "tri|a", None)]


def keystone(a, t, n, reach, z0, zv, slope, half=0.9, back=0.6):
    """An angular bracket on a wall face (anchor a, along t, outward n) under the point of a V-shaped
    overhang (point at zv on the axis, rising by `slope` per unit to the sides): from the face at z0
    out to `reach`, its top following the V."""
    from mathutils import Vector as V

    from sagekit.blender.geometry import loft

    def ring(u):
        zt = zv + slope * abs(u) + 0.25

        def P(d, z):
            return V((a.x + t.x * u + n.x * d, a.y + t.y * u + n.y * d, z))
        return [P(-back, z0), P(0.0, z0), P(reach, zt), P(-back, zt)]
    tags = [None, "stoneB", None, None]
    return loft([ring(-half), ring(0.0), ring(half)], [tags, tags], cap0=("stoneB", True), cap1=("stoneB", True))
