"""Elven floodgate doors (ElvenFloodgateExpansion, Draw module ModuleTag_DrawDoors, model
EBFFGate_DRCA): the five stone leaves that close the floodgate's niches and drop to let the flood out
(EBFFGate_DROA opens them; the same leaves, derived).

EA's body (EBFFGATE2, 280 triangles, on a bone turned a quarter about z): five pointed leaves round
the drum, each a thin slab (wings to 30.41, a pointed top to 34.47) carrying a raised lancet boss
up the middle: a shallow V whose ridge stands 0.34 proud of its shoulders, the shoulders upright to
24.19, the ridge to 30.72, then pointing back to the tip at 36.62. LEAVES lists each boss by its
shoulders and ridge (mesh coordinates, z 0).

The redesign dresses every boss as a door-post in the citadel's metals: a mithril bead up the
ridge, one gilt clasp across it between silver edges, and a gilt leaf on its pointed top (the first
pass's three knotwork clasps were clutter, and brought teal where the palette keeps it to EA's
glass). Nothing stands out more than 0.45 from EA's surface or above its tip, so the leaves still
close into the niches and drop as EA's do. No cloth: the doors move, a house-colour model would
not."""
from sagekit.building import Building

from ..style import ElvenStyle

# each leaf's boss at the ground: (left shoulder, ridge, right shoulder)
_LEFT = [((-18.23, -2.47), (-18.07, -4.06), (-17.26, -5.44)),
         ((-16.01, 11.52), (-15.37, 12.98), (-14.18, 14.04))]
LEAVES = _LEFT + [tuple((-x, y) for x, y in reversed(leaf)) for leaf in _LEFT] + \
    [((1.56, 20.47), (0.0, 20.82), (-1.56, 20.47))]
MIDDLE = (0.0, 6.0)                 # inside the ring of leaves: "outward" is away from it
SHOULDER, RIDGE_TOP = 24.19, 30.72
BANDS = ((10.9, 12.5),)             # the clasp: gilt between silver edges
BEAD = (0.22, 0.6, 23.4)            # half width, from, to
EMBLEM = (24.4, 6.3, 2.8)           # foot, length, width: a gilt leaf on the boss's pointed top


class FloodgateDoors(Building):
    style = ElvenStyle()
    source = "EBFFGate_DRCA"
    target = "EBFFGATE2"
    sheet = "EBFortress.tga"
    sheet_normal = "EBFortress_NRM.tga"
    own_textures = {"EBFortress.tga": "EBFortresG.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_DrawDoors",)
    HOUSE_DRAW = "ModuleTag_Draw_HCFloodgateDoors"
    house_tags = ()                 # no cloth on moving leaves
    # the bosses' ridges are the footprint's edge: the bead, clasps and leaf stand up to 0.6 past it
    # (the closed leaves stay behind the drum's pier fronts, 1.4 further out)
    footprint_margin = 0.65
    # EA builds these leaves at ground level; the closed healthy model hangs 21.240873 higher.
    lifecycle = {"EBFFGate_DRA": {"match_offset": (0, 0, -21.240873)}}
    views = {
        "rts": ((6.2, 0.0, 39.5), 131, 50, -38, 50),     # model space: the leaves' bone stands them 21.24 up
        "close": ((6.2, 0.0, 39.5), 77, 24, -30, 45),
        "ingame": ((6.2, 0.0, 39.5), 297, 53, -62, 50),
    }

    def design(self, kit):
        out = []
        for leaf in LEAVES:
            out += self._boss(kit, *leaf)
        return out

    @staticmethod
    def _outward(a, b):
        """(t, n) along a -> b and its horizontal normal away from the ring's middle."""
        from mathutils import Vector as V
        t = (b - a).normalized()
        n = V((t.y, -t.x, 0))
        mid = (a + b) / 2
        if n.dot(mid - V((MIDDLE[0], MIDDLE[1], 0))) < 0:
            n = -n
        return t, n

    def _boss(self, kit, left, ridge, right):
        from mathutils import Vector as V
        from sagekit.blender.geometry import prism_uz
        L, P, R = (V((p[0], p[1], 0)) for p in (left, ridge, right))
        t, n = self._outward(L, R)
        out = []
        # the bands, one prism on each facet of the V: the ends at the shoulders are faces, the ends
        # meeting at the ridge are buried under the bead
        for a, b, ends in ((L, P, (None, "trim")), (P, R, ("trim", None))):
            tf, nf = self._outward(a, b)
            ln = (b - a).length
            for z0, z1 in BANDS:
                out.append(prism_uz(a, tf, nf, [(0.0, z0), (ln, z0), (ln, z1), (0.0, z1)], -0.05, 0.2,
                                    ["gilt", ends[0], "gilt", ends[1]], "gilt", None))
                for zb in (z0, z1):                        # silver edges standing a little prouder
                    out.append(prism_uz(a, tf, nf, [(0.0, zb - 0.16), (ln, zb - 0.16), (ln, zb + 0.16), (0.0, zb + 0.16)],
                                        -0.05, 0.3, ["trim", ends[0], "trim", ends[1]], "trim", None))
        h, z0, z1 = BEAD                                   # the ridge's mithril bead, over the clasp
        out.append(prism_uz(P, t, n, [(-h, z0), (h, z0), (h, z1), (-h, z1)], -0.12, 0.38, ["trim"] * 4, "trim", None))
        foot, length, width = EMBLEM
        out.append(kit.leaf_blade(P, t, n, 0.0, foot, length, width, thick=0.18, d=0.22))
        return out

    def emphasis(self, c, n):
        return 1.3 if c.z > 20 else 1.0       # the leaves' pointed tops: what the RTS camera sees
