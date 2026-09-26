"""Elves green pasture fence (ElvenGreenPasture): the paddock of EA's stable - a fence of pale
carved branch rails between posts, closed on the far side by a round-headed stone gate - made
Elven:

- the gate's round head becomes pointed: a hood of dressed moonstone fills the spandrels between
  EA's round extrados and a pointed outline, under a silver moulding with an enamel soffit;
- a crystal lantern hangs on a gilt rod from the gate's crown;
- each of the four corner posts gets a gilt collar and leaf finial.

A second body of EBStable_SKN: chained on elves/green_pasture (`base`), built after it. The fence is
drawn at every upgrade level (`always_shown`), so it may carry cloth and night lights like a body:
the crown lantern glows at night (a pane on its crystal and a small glow card round it). No cloth
is designed here.

Its bone is tilted 90 degrees: world_space, every number in model (world) axes, measured on EA's
model:
  gate      its face x 37.88..38.37 (the fence's edge: footprint_margin lets the moulding stand
            0.45 proud), centred y -0.2: jambs |y| 13.5..18.1 up to the springing z 18.8; the
            extrados (|y|, z) (18.1, 18.8) (16.5, 25.0) (12.8, 30.5) (6.2, 34.1) (0, 35.3), the
            intrados' crown z 30.1
  posts     corners (-29.3, -59.4) (-29.3, 58.4) (17.0, -59.5) (17.0, 58.5), tops z 10.6
Footprint x -32.8..38.37, y -63.44..62.44; height 35.45 (+20 % allowed: top 42.4)."""
from sagekit.building import Building

from ..style import ElvenStyle

GATE_X, GATE_U, GATE_D0 = 38.37, -0.2, -0.49
EXTRADOS = [(18.1, 18.8), (16.5, 25.0), (12.8, 30.5), (6.2, 34.1), (0.0, 35.3)]
HOOD_HALF, HOOD_SPRING, HOOD_APEX = 18.1, 18.8, 40.4
CROWN_Z = 30.1
POSTS = [(-29.3, -59.4), (-29.3, 58.4), (17.0, -59.5), (17.0, 58.5)]
POST_TOP = 10.6
LAMP_H, LAMP_R = 3.2, 0.6
LAMP_Z = CROWN_Z - 1.3 - LAMP_H           # the crown lantern's crystal stands on this (hangs from the crown)


def extrados_z(u):
    """EA's extrados height at |u| from the gate's axis (its facets, linearly)."""
    u = min(abs(u), EXTRADOS[0][0])
    for (u0, z0), (u1, z1) in zip(EXTRADOS, EXTRADOS[1:]):
        if u1 <= u <= u0:
            return z0 + (z1 - z0) * (u0 - u) / (u0 - u1)
    return EXTRADOS[-1][1]


class GreenPastureFence(Building):
    style = ElvenStyle()
    source = "EBStable_SKN"
    target = "FENCE"
    base = "elves/green_pasture"
    always_shown = True                 # the paddock is there at every level: lights and cloth allowed
    sheet = "EBStable_Alpha.tga"
    sheet_normal = None
    own_textures = {"EBStable_Alpha.tga": "EBStable_AlphH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    world_space = True                  # its bone is tilted 90 degrees
    footprint_margin = 0.6              # the gate's face is the fence's edge: its moulding stands proud
    tri_budget = 15000
    bake_hidden = ("P_ARWEN_C", "N_WINDOW", "N_GLOW")
    views = {
        "rts": ((2.8, -0.5, 17.6), 328, 50, -38, 50),
        "close": ((2.8, -0.5, 17.6), 194, 24, -30, 45),
        "ingame": ((2.8, -0.5, 17.6), 744, 53, -62, 50),
        "gate": ((38.0, -0.2, 22.0), 90, 12, 0, 45),
    }

    def design(self, kit):
        s = []
        s += self._hood(kit)                    # 1. the gate's pointed hood
        s += self._lantern(kit)                 # 2. the crown lantern
        s += self._posts(kit)                   # 3. post finials
        return s

    @staticmethod
    def _frame():
        from mathutils import Vector as V
        return V((GATE_X, 0, 0)), V((0, 1, 0)), V((1, 0, 0))

    # ------------------------------------------------------------------ 1. hood
    def _hood(self, kit):
        """Vertical strips from EA's extrados up to the pointed outline (in the arch's own
        thickness, the back showing to the paddock), and the barge-board moulding over them."""
        from sagekit.blender.geometry import prism_uz
        from ..barracks.motifs import barge_board
        a, t, n = self._frame()
        pointed = kit.arch_outline(HOOD_HALF, HOOD_SPRING, HOOD_APEX, 0.0, 10)

        def pointed_z(u):
            for (u0, z0), (u1, z1) in zip(pointed, pointed[1:]):
                if u1 <= u <= u0:
                    return z0 + (z1 - z0) * (u0 - u) / (u0 - u1)
            return HOOD_APEX
        steps = sorted({round(p[0], 4) for p in pointed} | {p[0] for p in EXTRADOS}, reverse=True)
        out = []
        for s in (1, -1):
            for u0, u1 in zip(steps, steps[1:]):
                z00, z01, z10, z11 = extrados_z(u0), pointed_z(u0), extrados_z(u1), pointed_z(u1)
                q = [(GATE_U + s * u0, z00), (GATE_U + s * u1, z10), (GATE_U + s * u1, z11), (GATE_U + s * u0, z01)]
                out.append(prism_uz(a, t, n, q, GATE_D0, 0.0, [None] * 4, "stoneA", "stoneB"))
        out += barge_board(kit, a, t, n, GATE_U, pointed, w=0.75, d0=GATE_D0 - 0.2, d1=0.45)
        return out

    # ------------------------------------------------------------------ 2. lantern
    @staticmethod
    def _lantern(kit):
        from ..shapes import turned
        x, y = GATE_X + GATE_D0 / 2, GATE_U
        out = [turned(x, y, [(0.09, CROWN_Z - 1.3), (0.09, CROWN_Z + 0.4)], ["gilt"], 6, cap0=("gilt", True),
                      cap1=("gilt", False))]
        out += kit.crystal_lantern(x, y, LAMP_Z, h=LAMP_H, r=LAMP_R, finial=False)
        return out

    @staticmethod
    def night_lights(kit):
        """The crown lantern: a pane on its crystal's camera side and a glow card round it, small
        enough (10 across) to stay in the gateway between the jambs."""
        from ..barracks.motifs import crystal_light, lantern_glow
        x, y = GATE_X + GATE_D0 / 2, GATE_U
        return [crystal_light(x, y, LAMP_Z, LAMP_H, LAMP_R, "crown lantern"),
                lantern_glow(x, y, LAMP_Z, LAMP_H, "crown lantern", size=10.0)]

    # ------------------------------------------------------------------ 3. posts
    @staticmethod
    def _posts(kit):
        from ..shapes import turned
        out = []
        for x, y in POSTS:
            out.append(turned(x, y, [(0.55, POST_TOP - 0.4), (0.7, POST_TOP + 0.1), (0.4, POST_TOP + 0.5)],
                              ["gilt", "gilt"], 8, cap0=("gilt", True), cap1=("gilt", True)))
            out += kit.leaf_finial(x, y, POST_TOP + 0.4, 2.6, 0.9)
        return out

    def emphasis(self, c, n):
        return 1.5 if c.x > 36 and c.z > 15 else 1.0      # the gate's hood
