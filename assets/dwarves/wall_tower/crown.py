"""Crown pieces shared by the Dwarven walls, new and old (wall_*, oldwall_*): the fortress's
tower-crown vocabulary at any scale and height. Blender side only
(mathutils); every function returns closed, oriented solids."""
from mathutils import Vector as V

from sagekit.blender.geometry import box_rings, loft, prism_uz


def step_pyramid(cx, cy, z0, s):
    """shapes.step_pyramid at scale s standing on z0: three battered tiers, a gilded point."""
    out = []
    z = z0
    for h0, h1, dz, tg in ((3.9, 3.5, 6.0, "stoneB"), (2.9, 2.7, 2.4, "stoneA"), (1.9, 1.8, 1.7, "stoneA")):
        r0 = box_rings((cx - h0 * s, cx + h0 * s), (cy - h0 * s, cy + h0 * s), z, 0.3 * s)
        r1 = box_rings((cx - h1 * s, cx + h1 * s), (cy - h1 * s, cy + h1 * s), z + dz * s, 0.3 * s)
        out.append(loft([r0, r1], [tg], cap0=("top", False), cap1=("top", True)))
        z += dz * s
    r0 = box_rings((cx - 1.8 * s, cx + 1.8 * s), (cy - 1.8 * s, cy + 1.8 * s), z, 0.25 * s)
    out.append(loft([r0, [V((cx, cy, z + 2.1 * s))] * len(r0)], ["trim"], cap0=("top", False), cap1=("top", False)))
    return out


def ziggurat(cx, cy, z0, tiers, point):
    """A stepped roof block: tiers [(half0, half1, height, tag)] rising from z0, each tier's top a
    visible tread; `point` (half, height) a gilded pyramid on top. Returns (solids, top z)."""
    out = []
    z = z0
    for h0, h1, dz, tg in tiers:
        r0 = box_rings((cx - h0, cx + h0), (cy - h0, cy + h0), z, min(0.8, h0 * 0.1))
        r1 = box_rings((cx - h1, cx + h1), (cy - h1, cy + h1), z + dz, min(0.8, h1 * 0.1))
        out.append(loft([r0, r1], [tg], cap0=("top", False), cap1=("top", True)))
        z += dz
    h, dz = point
    r0 = box_rings((cx - h, cx + h), (cy - h, cy + h), z, min(0.4, h * 0.1))
    out.append(loft([r0, [V((cx, cy, z + dz))] * len(r0)], ["trim"], cap0=("top", False), cap1=("top", False)))
    return out, z + dz


def chevron(a, t, n, u, z0, w, d0, d1, s=1.0):
    """One stepped-triangle merlon (the fortress parapet's) centred at u on the line (a, t), out
    along n from d0 to d1, standing on z0, w wide: base slab, narrower step, bronze step, point."""
    h = w / 2
    zb, z1, z2, za = z0 + 2.8 * s, z0 + 4.1 * s, z0 + 5.4 * s, z0 + 7.0 * s
    g1, g2 = 1.35 * s, 2.7 * s
    return [
        prism_uz(a, t, n, [(u - h, z0), (u + h, z0), (u + h, zb), (u - h, zb)], d0, d1,
                 [None, "stoneB", "top", "stoneB"], "stoneB", "stoneA", bat=0.1),
        prism_uz(a, t, n, [(u - h + g1, zb), (u + h - g1, zb), (u + h - g1, z1), (u - h + g1, z1)], d0 + 0.3, d1 - 0.5,
                 [None, "stoneB", "top", "stoneB"], "stoneA", "stoneA"),
        prism_uz(a, t, n, [(u - h + g2, z1), (u + h - g2, z1), (u + h - g2, z2), (u - h + g2, z2)], d0 + 0.6, d1 - 0.8,
                 [None, "stoneB", "top", "stoneB"], "trim", "stoneA"),
        prism_uz(a, t, n, [(u - h + g2, z2), (u + h - g2, z2), (u, za)], d0 + 0.6, d1 - 0.8,
                 [None, "top", "top"], "stoneA", "stoneA"),
    ]


def band(a, t, n, u0, u1, z0, z1, d0, d1, tag, back=None):
    """A flat band on a face: a slab u0..u1, z0..z1, d0..d1 with bronze edges and `tag` on its front."""
    return prism_uz(a, t, n, [(u0, z0), (u1, z0), (u1, z1), (u0, z1)], d0, d1,
                    ["trim", "trim", "top", "trim"], tag, back)
