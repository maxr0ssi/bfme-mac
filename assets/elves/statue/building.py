"""The Elven statue (ElvenStatue, elvenstatue.ini): EA's warrior in stone keeps his figure; the plain
octagonal die he stands on becomes an Elven plinth - a moulded slope with a silver coping, a knotwork
band on the lower die, a gilt bead at the step, tall lancet niches with gold leaf tracery on four
faces of the upper die and leaf banners (the player's colour) on the other four, a moulded cornice
under his feet, and four slender lantern columns with leaf capitals and crystal lanterns standing in
the corners of the footprint.

EA's model is two meshes on one bone: OBJECT12, the figure (9,828 triangles, ebstatue.tga), and
EBSTATUE01, the holder (112 triangles, ebstatueholder.tga + _nrm; its _d1 / _d2 sheets are the
damaged states). The holder is the building's own piece (no other faction or map draws
ebstatueholder), so it is the target: the figure stays EA's, byte for byte.

EBSTATUE01 (mesh = model coordinates) is a regular octagon round C (-0.25, -1.55) whose corners lie
at -4 + 45k degrees (so its bounding box, the footprint, touches four corners near the axes):
circumradius 11.7 from z -0.06 to 2.34, a slope in to 10.6 at 3.51, the lower die battered to 9.56 at
12.54, a step to 9.2 at 13.19, the upper die battered to 8.5 at 26.07 and a cap to 8.1 at 26.96. The
figure's feet go down to z 26.41 inside the cap (x -4.7..5.6, y -12.2..3.3): nothing new rises
above 26.05 inside the cap's circle. The footprint's four corner squares, outside the octagon, hold
the lantern columns. Height 27.02; the lanterns rise to 30.8 (+14 %; the figure stands to 90.4).
"""
import math

from sagekit.building import Building

from ..style import ElvenStyle

C = (-0.25, -1.55)                              # the octagon's centre
PHASE = -4.0                                    # its corners' angle (degrees) + 45 k
RINGS = [(-0.06, 11.7), (2.34, 11.7), (3.51, 10.6), (12.54, 9.56), (13.19, 9.2), (26.07, 8.5), (26.96, 8.1)]
LANTERN_R = 13.9                                # the corner columns, on the diagonals of the footprint
BANNER_FACES = (0, 6)                           # either side of the face the RTS camera looks at (7, -26.5 deg)


def column_xy(ang):
    return C[0] + LANTERN_R * math.cos(math.radians(ang)), C[1] + LANTERN_R * math.sin(math.radians(ang))


def radius(z):
    """EA's octagon circumradius at height z (linear between its rings)."""
    for (z0, r0), (z1, r1) in zip(RINGS, RINGS[1:]):
        if z0 <= z <= z1:
            return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return RINGS[-1][1]


def octagon(r, z):
    from mathutils import Vector as V
    return [V((C[0] + r * math.cos(math.radians(PHASE + 45 * k)), C[1] + r * math.sin(math.radians(PHASE + 45 * k)), z))
            for k in range(8)]


def path(r):
    """The octagon's outline at circumradius r, closed (a sweep path)."""
    pts = [(p.x, p.y) for p in octagon(r, 0.0)]
    return pts + [pts[0]]


def face(k, z):
    """Face k of the octagon at height z: (anchor, t, n); t x n = -z."""
    from mathutils import Vector as V
    th = math.radians(PHASE + 22.5 + 45 * k)
    n = V((math.cos(th), math.sin(th), 0))
    ap = radius(z) * math.cos(math.radians(22.5))
    return V((C[0] + n.x * ap, C[1] + n.y * ap, 0)), V((-n.y, n.x, 0)), n


class Statue(Building):
    style = ElvenStyle()
    source = "EBStatue"
    target = "EBSTATUE01"                        # the holder; OBJECT12 (the figure) stays EA's
    sheet = "ebstatueholder.tga"                 # lower case, as the model names it
    sheet_normal = "ebstatueholder_nrm.tga"
    own_textures = {"ebstatueholder.tga": "ebstatueholdeH.tga"}   # free in EA's files and every recipe
    tri_budget = 6000
    views = {
        "rts": ((-0.3, -1.6, 40.0), 190, 50, -38, 50),
        "close": ((-0.3, -1.6, 17.0), 78, 20, -32, 45),
        "ingame": ((-0.3, -1.6, 40.0), 360, 53, -62, 50),
    }

    def design(self, kit):
        s = []
        s += self._mouldings(kit)                # 1. slope coping, knotwork band, gilt bead, cornice
        for k in range(8):                      # 2. gold-traceried niches round the upper die, two banners
            s += self._banner(kit, k) if k in BANNER_FACES else self._niche(kit, k)
        for k in range(4):                      # 3. lantern columns in the footprint's corners
            s += self._lantern_column(kit, 45 + 90 * k)
        return s

    # ------------------------------------------------------------------ 1. mouldings
    @staticmethod
    def _mouldings(kit):
        from sagekit.blender.geometry import loft, sweep
        out = []
        # silver coping on the slope's top edge (EA's slope 2.34..3.51 stays; the coping sits above it)
        out.append(loft([octagon(radius(3.6) - 0.6, 3.55), octagon(radius(3.6) + 0.35, 3.55),
                         octagon(radius(3.6) + 0.6, 3.95), octagon(radius(3.6) + 0.45, 4.45), octagon(radius(4.6) - 0.6, 4.6)],
                        [None, "trim", "coping", "top"], cap0=("stoneB", False), cap1=("top", False)))
        # knotwork band between gilt beads on the lower die, just under its step
        out += kit.filigree_band(path(radius(11.2)), 10.5, 11.9, d=0.3, center=C)
        # a gilt bead on the step between the dies
        out += sweep(path(radius(12.9)), [(-0.3, 12.55), (0.12, 12.6), (0.25, 12.85), (0.12, 13.1), (-0.3, 13.15)],
                     [None, "gilt", "gilt", "gilt", None], center=C)[0]
        # the cornice under the figure's feet: corbel, enamel frieze, silver coping; its top (26.05)
        # stays under the feet (26.41) and outside the cap it rings
        z0, z1 = 23.9, 26.05
        r0 = radius(z0)
        out.append(loft([octagon(r0 - 0.6, z0), octagon(r0 + 0.1, z0), octagon(r0 + 0.55, z0 + 0.5),
                         octagon(r0 + 0.55, z0 + 1.2), octagon(r0 + 0.95, z0 + 1.5), octagon(r0 + 0.95, z1 - 0.2),
                         octagon(r0 + 0.7, z1), octagon(radius(z1) - 0.2, z1)],
                        [None, "trim", "enamel", "trim", "coping", "trim", "top"], cap0=("stoneB", False),
                        cap1=("top", False)))
        return out

    # ------------------------------------------------------------------ 2. niches and banners
    @staticmethod
    def _niche(kit, k):
        """A tall lancet niche on face k of the upper die: a spray of three gilt leaves (the gold
        tracery) on a deep slate ground, inside a silver arch frame with a slate reveal and a gilt
        leaf at its tip, over a silver sill. Anchored at the arch's top, where the battered face is
        furthest back (the face stands 0.38 further out at the niche's foot: the leaves at d 0.55
        stay proud of it all the way down)."""
        from sagekit.blender.geometry import prism_uz
        z0, spring, apex = 14.1, 19.9, 22.6
        a, t, n = face(k, apex)
        half = 1.7
        panel = kit.arch_outline(half + 0.45, spring, apex + 0.45, 0.0, 6)
        poly = [(-panel[0][0], z0), (panel[0][0], z0)] + [(x, z) for x, z in panel[:-1]] + \
               [(-x, z) for x, z in reversed(panel)]
        out = [prism_uz(a, t, n, poly, -0.6, 0.12, [None] * len(poly), "enamel", None)]
        out.append(kit.leaf_blade(a, t, n, 0.0, z0 + 0.3, 7.6, 1.7, thick=0.2, d=0.55))
        for side in (1, -1):
            out.append(kit.leaf_blade(a, t, n, 0.0, z0 + 0.6, 4.4, 1.0, lean=0.3 * side, thick=0.2, d=0.5))
        out += kit.arch(a, t, n, 0.0, half, z0, spring, apex, w=0.62, d0=-0.6, d1=0.4, ogee=0.2, k=6)
        # a sill under the niche
        out.append(prism_uz(a, t, n, [(-half - 0.9, z0 - 0.55), (half + 0.9, z0 - 0.55), (half + 0.9, z0), (-half - 0.9, z0)],
                            -0.6, 0.95, [None, "trim", "top", "trim"], "trim", None))
        return out

    @staticmethod
    def _banner(kit, k):
        """A leaf banner in the player's colour on face k, from a gilt rod under the cornice."""
        a, t, n = face(k, 19.0)
        return kit.leaf_banner(a, t, n, 0.0, 23.3, 3.3, 9.2, d=0.35, free=True)

    # ------------------------------------------------------------------ 3. lantern columns
    @staticmethod
    def _lantern_column(kit, ang):
        """A slender column in a corner of the footprint: a moulded pedestal as high as EA's base
        slab, a shaft with a leaf capital and a crystal lantern (the statue's light) on top."""
        from sagekit.blender.geometry import loft
        from ..shapes import ring
        cx, cy = column_xy(ang)
        out = [loft([ring(cx, cy, 1.45, -0.06, 8, phase=math.pi / 8), ring(cx, cy, 1.45, 2.2, 8, phase=math.pi / 8),
                     ring(cx, cy, 1.55, 2.45, 8, phase=math.pi / 8), ring(cx, cy, 1.25, 2.9, 8, phase=math.pi / 8)],
                    ["stoneA", "trim", "coping"], cap0=("stoneB", False), cap1=("top", True))]
        out += kit.column(cx, cy, 2.9, 23.2, r=0.72, k=10, leaves=6)
        out += kit.crystal_lantern(cx, cy, 23.2, h=6.4, r=0.95)
        return out

    def emphasis(self, c, n):
        return 1.3 if c.z > 13.0 else 1.0
