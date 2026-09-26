"""Dwarven wall hub (DwarvenWallHubSmall, model DBWallRmprtN): EA's squat hexagonal bastion where
wall segments meet, given the fortress's tower crown - a bronze-banded coping and the solid chevron
parapet round its rim (the wall segments' own, at the same heights, so the parapet line runs on
through the hub), stepped corner blocks with gilded points at its six corners, a stepped crown with
a gold rune belt and a triangle frieze on its central roof block, and an Erebor-blue banner on each
of its four slanted faces.

Segments run into the hub from any side, so every face keeps its plane: nothing stands out of the
hexagon's two faces that lie on the footprint (y = +-22.5) or past its corners; the banners hang
on the four slanted faces, whose middles lie well inside the footprint. All measurements in
DBWALLRMPRTN mesh coordinates, taken from the original model.

EA's hub: a hexagonal prism (corners below) with walls to z 51.65, a 0.9 chamfer up to a ring at
z 53.06 (the segments' walkway height), a slope up to a platform at z 56.6 (about 7 in from the
faces) and a central hexagonal block (radius ~9.4 about (0, 0.45)) with sloped sides to z 63.2."""
from sagekit.building import Building

from ..style import DwarvenStyle

HEX = [(25.492, 0.0), (12.39, 22.5), (-12.39, 22.5), (-25.492, 0.0), (-12.39, -22.5), (12.39, -22.5)]
WALL_TOP = 51.653
INSET = 1.5                      # coping path: the hexagon's faces moved in by this; d = 1.5 is the face
# coping round the rim (d out of the path): a bronze band on the wall's top edge, the coping face
# flush with the wall, a bronze chamfer, the top at z 57 (the segments'), the inner face down to
# the ring; the bottom edge runs buried through the wall head
COPING = [(1.1, 51.3), (INSET, WALL_TOP), (INSET, 52.6), (INSET, 56.6), (1.1, 57.0), (-2.0, 57.0), (-2.0, 52.9)]
COPING_TAGS = ["trim", "trim", "stoneA", "trim", "top", "stoneA", None]
# corner blocks: rhombi on the corner's two faces (s: inset along both faces, w: side), tiers
# (s, w, z0, z1, tag), then a gilded point. The first tier stands 0.25 behind the coping face (a
# block flush with it would share its plane) and starts buried in the ring, so no gap opens under
# its inner end over the sloping roof
CORNER_TIERS = [(0.25, 6.0, 52.9, 61.0, "stoneB"), (0.8, 4.9, 61.0, 63.6, "stoneA"), (1.35, 3.8, 63.6, 65.4, "stoneA")]
CORNER_POINT = 68.0
# the crown on the central block: (radius, z) rings about CENTRE, tags per ring interval
CENTRE = (0.0, 0.45)
CROWN = [(8.9, 63.1), (8.5, 66.4), (9.0, 66.4), (9.0, 67.2), (7.4, 67.2), (7.0, 70.2), (5.4, 70.2), (5.1, 72.2),
         (3.6, 72.2)]
CROWN_TAGS = ["rune", "trim", "trim", "top", "tri", "top", "stoneA", "top"]
CROWN_POINT = 75.4               # height limit: 0.06 + 63.16 x 1.2 = 75.85
# banners on the slanted faces (HEX sides 0, 2, 3, 5), hung under the painted rune band (z ~43..51,
# the segments' band height) so the band runs on unbroken: z_top, width, length
BANNER = (42.4, 7.0, 22.0)
SLANTED = (0, 2, 3, 5)


def inset_hex(e):
    """HEX with every face moved in by e (corners re-intersected)."""
    from mathutils import Vector as V
    P = [V(p) for p in HEX]
    lines = []
    for i in range(6):
        a, b = P[i], P[(i + 1) % 6]
        t = (b - a).normalized()
        n = V((t.y, -t.x))
        if n.dot((a + b) / 2) < 0:
            n = -n
        lines.append((a - n * e, t))

    def meet(l1, l2):
        (p, d), (q, f) = l1, l2
        s = ((q.x - p.x) * f.y - (q.y - p.y) * f.x) / (d.x * f.y - d.y * f.x)
        return p + d * s
    return [meet(lines[i - 1], lines[i]) for i in range(6)]


class WallHub(Building):
    style = DwarvenStyle()
    source = "DBWallRmprtN"
    target = "DBWALLRMPRTN"
    sheet = None                                                # the faction atlas DBFortress1
    own_textures = {"DBFortress1.tga": "DBFortressR.tga"}       # taken: B C E F G H J K M P Q S V W
    # our own house-colour model's Draw module: a tag of its own (the framework's shared default
    # would collide where one object shows two of our models, see wall_segment)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallHub"
    views = {
        "rts": ((0, 0, 32), 270, 48, -24, 50),
        "close": ((0, 0, 36), 175, 20, -18, 45),
        "ingame": ((0, 0, 28), 560, 53, -62, 50),
    }

    def design(self, kit):
        return self.parapet(kit) + self.corner_blocks() + self._crown() + self.banners(kit)

    @staticmethod
    def parapet(kit):
        """1. the coping round the rim with the chevron parapet on all six sides."""
        from sagekit.blender.geometry import sweep
        path = inset_hex(INSET)
        solids, segs = sweep([(p.x, p.y) for p in path + path[:1]], COPING, COPING_TAGS)
        for a, b, t, n in segs:
            solids += kit.chevron_parapet(a, t, n, (b - a).length, d0=-1.7, d1=INSET)
        return solids

    @staticmethod
    def corner_blocks():
        """2. a stepped block with a gilded point on each of the six corners."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import loft
        solids, H = [], [V(p) for p in HEX]
        for i in range(6):
            c, e1, e2 = H[i], (H[i + 1 - 6] - H[i]).normalized(), (H[i - 1] - H[i]).normalized()

            def rh(s, w, z):
                q = [c + e1 * s + e2 * s, c + e1 * (s + w) + e2 * s, c + e1 * (s + w) + e2 * (s + w), c + e1 * s + e2 * (s + w)]
                return [V((p.x, p.y, z)) for p in q]
            for s, w, z0, z1, tag in CORNER_TIERS:
                solids.append(loft([rh(s, w, z0), rh(s, w, z1)], [tag], cap0=("top", False), cap1=("top", True)))
            s, w = CORNER_TIERS[-1][0], CORNER_TIERS[-1][1]
            top = rh(s, w, CORNER_TIERS[-1][3])
            apex = c + (e1 + e2) * (s + w / 2)
            solids.append(loft([top, [V((apex.x, apex.y, CORNER_POINT))] * 4], ["trim"], cap0=("top", False),
                               cap1=("top", False)))
        return solids

    @staticmethod
    def banners(kit, shift=None):
        """4. a banner on each slanted face; shift: {face: move along it, from its middle}."""
        from mathutils import Vector as V
        solids, H = [], [V(p) for p in HEX]
        z_top, width, length = BANNER
        for i in SLANTED:
            a, b = H[i], H[(i + 1) % 6]
            t = (b - a).normalized()
            n = V((t.y, -t.x, 0))
            if n.dot(V((a.x + b.x, a.y + b.y, 0))) < 0:
                n = -n
            u = (b - a).length / 2 + (shift or {}).get(i, 0.0)
            solids += kit.banner(V((a.x, a.y, 0)), V((t.x, t.y, 0)), n, u, z_top, width, length, d=0.05)
        return solids

    @staticmethod
    def _crown():
        import math

        from mathutils import Vector as V
        from sagekit.blender.geometry import loft
        cx, cy = CENTRE

        def R(r, z):
            return [V((cx + r * math.cos(math.radians(60 * k)), cy + r * math.sin(math.radians(60 * k)), z)) for k in range(6)]
        rings = [R(r, z) for r, z in CROWN]
        out = [loft(rings, CROWN_TAGS, cap0=("top", False), cap1=("top", False))]
        out.append(loft([rings[-1], [V((cx, cy, CROWN_POINT))] * 6], ["trim"], cap0=("top", False), cap1=("top", False)))
        return out

    def emphasis(self, c, n):
        if c.z > 52:
            return 1.4                        # crown and parapet: what the RTS camera sees
        return 1.0
