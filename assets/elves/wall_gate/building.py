"""Elven wall gate (ElvenCastleWallGate, model EBWallGateN_SKN): EA's two square gate towers with
their warrior statues and the four lattice door leaves between them, kept whole, joined by a
slender bridge in the walls' crown. The bridge carries the segments' filigree band, mithril coping
and leaf-cresting over the doors, at the walls' heights, so the line runs from the segments round
the towers and across the gate; over its middle stands a free pointed arch (gilt leaf finial) with
a crystal lantern hung in it. Each tower head gets the band and the silver coping round its flared
cap under the statue (no merlons: EA's knotwork pyramid and the statue are the head), a crystal
lantern on a silver post on each corner. Two banners in the player's colour, one down the outer
face of each tower on the same side: the wall run's only cloth.

Skinned model: the leaves (EBGATEDOOR00..03 on their own bones, x +-0.5, |y| <= 40.07, z <= 48.5)
fold open to the -x side, ending along x -20..0 at |y| 39.5..40.5 against the towers' inner faces
(EBWallGateN_SKL.EBWallGateN_OPN). Everything new stays above z 48.9 over the doors and their travel,
or on the towers' outer (x) faces and heads: the passage (|y| < 40.16) stays clear.

EA's gate (EBWALLGATEN, mesh coordinates = model space): towers x +-9.3 (9.1 at the top), |y|
40.16..58.68 (centres +-49.43) to z 47.4; a flared cap to x +-10.25, |y| 39.18..59.68 at 52.37; a
pyramid to +-7.48 at 56.54 and a plinth top +-6.28 at 60.16 under EA's statues (LUSTATUE, to 102.4).
The wall segments meet the towers' outer faces (|y| 58.68) at |x| <= 4.9: nothing is added there.
"""
from sagekit.building import Building

from ..style import ElvenStyle

TOWER_Y = 49.43                   # tower centre line
HEAD = 9.7                        # the tower crown's face line: a square of this half size (beads
                                  # 0.48 out: EA's footprint is y -59.65..59.68)
HEAD_IN = -2.35                   # its coping reaches in to 7.4, into EA's pyramid
SHAFT_X = 9.12                    # the shaft's x face at the banner's top (9.29 at the foot)
BRIDGE_Y = TOWER_Y - HEAD + 0.5   # the bridge's crown runs 0.5 into the towers' crown rings (its
                                  # open ends buried in their cores)
# the arch on the bridge's middle: half width, spring, apex (limit 60.16 x 1.2 = 72.19)
ARCH = (6.0, 60.0, 67.0)
LAMP = (59.8, 5.0)                # the lantern hung in it: foot z, height
TOWER_BANNER = (45.6, 7.5, 28.0)  # z_top (under the flare), width, length
BANNER_SIDE = 1                   # the banners hang on the towers' +x faces (the camera's side)
CORNER_LAMP = (8.9, 5.6, 3.4)     # lanterns on the tower heads' corners: offset, crystal, post


class WallGate(Building):
    style = ElvenStyle()
    source = "EBWallGateN_SKN"
    target = "EBWALLGATEN"
    sheet = "EBFortress.tga"
    sheet_normal = "EBFortress_NRM.tga"
    own_textures = {"EBFortress.tga": "EBFortresD.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallGate"
    views = {
        "rts": ((0, 0, 40), 300, 48, -24, 50),
        "close": ((0, 0, 50), 175, 20, -18, 45),
        "ingame": ((0, 0, 30), 676, 53, -62, 50),
    }

    def design(self, kit):
        return self._bridge(kit) + self._arch(kit) + self._heads(kit) + self._banners(kit)

    @staticmethod
    def _bridge(kit):
        """The walls' crown across the gap, its core's underside the bridge's soffit (0.4 over the
        leaves' points)."""
        from ..wall_segment.wall import FACE_X, crown
        out = []
        for s in (1, -1):
            path = [(s * FACE_X, -BRIDGE_Y), (s * FACE_X, BRIDGE_Y)]
            out += crown(kit, path, (0, 0), -FACE_X, inner=None, caps=False,
                         core_tags=["stoneB", "stoneB", None, None])
        return out

    @staticmethod
    def _arch(kit):
        """A free pointed arch over the bridge's middle, a crystal lantern hung in it."""
        from mathutils import Vector as V

        from assets.elves.shapes import turned

        from ..wall_segment.wall import ARCH_OGEE, COPING
        half, spring, apex = ARCH
        out = kit.arch(V((0, 0, 0)), V((0, 1, 0)), V((1, 0, 0)), 0.0, half, COPING[1] - 0.1, spring, apex, w=1.3,
                       d0=-0.8, d1=0.8, ogee=ARCH_OGEE, free=True)
        z, h = LAMP
        out.append(turned(0, 0, [(0.09, z + 0.9 * h), (0.09, apex + 0.3)], ["gilt"], 6, cap0=("gilt", True),
                          cap1=("gilt", False)))
        out += kit.crystal_lantern(0, 0, z, h, 0.9, finial=False)
        return out

    @staticmethod
    def _heads(kit):
        """The band and silver coping round each tower head, a lantern on each corner."""
        from ..wall_segment.wall import COPING, crown, lantern_post
        out = []
        for sy in (1, -1):
            cy = sy * TOWER_Y
            sq = [(HEAD, cy - HEAD), (HEAD, cy + HEAD), (-HEAD, cy + HEAD), (-HEAD, cy - HEAD), (HEAD, cy - HEAD)]
            # closed on the inside too: EA's pyramid has no top under the statue, so a face left
            # open inside it would show its back to the sky through the tower
            out += crown(kit, sq, (0, cy), HEAD_IN, inner="stoneB", parapet=False,
                         core_tags=[None, "stoneB", None, "stoneB"])
            o, h, post = CORNER_LAMP
            for px in (1, -1):
                for py in (1, -1):
                    out += lantern_post(kit, px * o, cy + py * o, COPING[1], h=h, r=0.75, post=post)
        return out

    @staticmethod
    def _banners(kit):
        """A long leaf banner down each tower's face on one side of the wall (two in all)."""
        from mathutils import Vector as V
        z_top, width, length = TOWER_BANNER
        sx = BANNER_SIDE
        a, t, n = V((sx * SHAFT_X, 0, 0)), V((0, sx, 0)), V((sx, 0, 0))
        out = []
        for sy in (1, -1):
            out += kit.leaf_banner(a, t, n, sx * sy * TOWER_Y, z_top, width, length, d=0.05)
        return out

    def emphasis(self, c, n):
        if c.z > 48:
            return 1.4                        # crowns, bridge, arch: what the RTS camera sees
        return 1.0
