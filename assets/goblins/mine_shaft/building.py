"""The Goblin mine shaft (WildMineShaft; WBPit_SKN): EA's pit kept whole - the collar round the
hole (WBPITMETAL's rim), the rock slab on its -X side, the white rubble, the two torch poles,
on EA's stone mound (WBPITA) - and made a working Goblin mine:

    tower      a winch tower of lashed logs on the collar's +X+Y side (the silhouette): braced
               posts, a plank platform with a parapet of stakes, a troll skull on its corner, a
               boom out over the hole's edge with a big iron-rimmed wheel at its end, the chain down
               to an iron-banded bucket, a windlass at the tower's foot winding the rope
    walkway    a plank landing on two stringers from the collar out over the hole's edge to the
               bucket, on the +X+Y side
    shoring    plank revetments round the collar's inner lip, raking timber props on its outer
               slope, fire baskets on the tower and on EA's two torch poles
    spoil      a spoil heap and an ore heap, the ore cart between them
    trophies   two skulls on stakes at the front; one ragged house-colour banner on a post

EA's facts (WBPITMETAL = model coordinates; sagekit measure: work/measure.json): x
-38.83..59.67, y -44.18..49.41, z -0.84..17.96 (686 triangles on wbpit2). The collar is a ring
round the hole (centre about (21, -0.5)): its crest at z 13 on r ~21 (|y|) to ~24 (x), its
inner lip dropping to the hole at r 17..19.5. The units (EA's idle animations, wbpit_idla/idlb):
the goblin climbs from the pit's centre (20.2, -1.4, z -14.7) out toward (5.5, -11, 13) - the
hole's centre and that path stay clear, the bucket hangs 15 units off it; the archer
stands in x -12..-2, y -37..-16, z 6..22 - clear. EA's torch poles top out at z 18 at (-38.2, 5.9)
and (53.6, -18.5) under the night glows (N_GLOW01/02). Level 2 (V1) sets six timber frames round
the collar at about 5, 65, 124, 180, 245 and 305 degrees round the centre (r 24..30) and level 3
a rock and tower on the -X side (V2, V2A: x -43..3.5, y -10..36): the winch tower stands
between the 5 and 65 degree frames (x 46.5..53.5, y 18..25). max_z_growth 1.05 (Max,
2026-09-28): new tops stay under z 37.7.
"""
import math

from sagekit.building import Building

from ..style import GoblinStyle

CENTRE = (21.0, -0.5)
CREST = (22.5, 21.0, 13.0)                  # the collar's crest: radius along x, along y, height
LIP = (19.8, 17.6)                          # the inner lip (radii along x and y)
TOWER = (50.0, 21.5, 3.5, 22.0)             # the winch tower: centre (x, y), half-width, platform z
WHEEL = (32.0, 8.5, 25.0)                   # the wheel at the boom's end, over the hole's +X+Y edge
BUCKET = (32.0, 8.5, 12.5)                  # the bucket's rim centre
WALK = ((40.0, 14.5, 12.6), (34.5, 10.8, 12.6))  # the landing: from the collar out beside the bucket
WINDLASS = ((53.0, 11.0, 2.0), (0.6, -1))    # at the tower's foot
SHORING = [(100, 7.0), (140, 6.0), (290, 7.5), (330, 6.0)]   # (angle, width) of plank revetments
PROPS = [262, 288, 20]                      # angles of the raking props on the outer slope
CART = ((15.5, -40.0, 0.0), (1, 0.15))
HEAPS = [((4.0, -38.0, 0.0), 3.5, 3.4, 1), ((48.0, -33.0, 0.3), 6.5, 6.0, 2)]
TORCHES = [(-37.9, 5.9, 18.0), (53.6, -18.5, 18.0)]
BANNER = ((36.5, -37.0, 0.3), 29.5, (0.6, -1.0))
STAKES = [(21.5, -41.0, 0.3), (31.0, -40.5, 0.3)]
# The game's fire (sagekit/fire.py): the coal basket of the torch on the winch tower's -X-Y post
# (torch_bracket at z 12). The baskets on EA's two poles (TORCHES) take none: EA's flame cards
# N_GLOW01/02 burn there at night.
FIRE_POINTS = [(44.5, 16.0, 15.8, 'brazier')]


def lip_point(angle, rx, ry, z):
    from mathutils import Vector as V
    a = math.radians(angle)
    return V((CENTRE[0] + rx * math.cos(a), CENTRE[1] + ry * math.sin(a), z))


class MineShaft(Building):
    style = GoblinStyle()
    source = "WBPit_SKN"
    target = "WBPITMETAL"
    fire_points = FIRE_POINTS
    sheet = "wbpit2.tga"
    sheet_normal = "wbpit2_nrm.tga"
    own_textures = {"wbpit2.tga": "wbpitH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    max_z_growth = 1.05                     # a flat rim: the winch tower (see the docstring)
    facet_islands = 8                       # the unwrap overlapped (0.08%): seams at EA's islands and 8-degree turns
    bake_hidden = ("V1", "V2", "V2A", "N_GLOW", "N_GLOW01", "N_GLOW02")
    views = {
        "rts": ((10.4, 2.6, 8.6), 302, 50, -38, 50),
        "close": ((10.4, 2.6, 8.6), 178, 24, -30, 45),
        "rim": ((21.0, -0.5, 12.0), 120, 30, -50, 45),
        "ingame": ((10.4, 2.6, 8.6), 686, 53, -62, 50),
    }

    def design(self, kit):
        from mathutils import Vector as V

        from sagekit.blender.geometry import closed

        from ..cave import motifs as M
        out = []
        cx, cy = CENTRE
        rx, ry, zc = CREST
        out += self._tower(kit, M)
        # the landing: two stringers and planks across, a post under its outer end
        p, q = V(WALK[0]), V(WALK[1])
        d = (q - p).normalized()
        s = V((-d.y, d.x, 0))
        for e in (-1, 1):
            out += kit.pole(p - d * 3.5 + s * e * 1.8 - V((0, 0, 0.3)), q + s * e * 1.8 - V((0, 0, 0.3)), 0.45)
        n = int((q - p).length / 1.3) + 3
        for i in range(n):
            m = (p - d * 3.0).lerp(q, i / (n - 1)) + V((0, 0, 0.35))
            out.append(kit.tube([m - s * 2.4, m + s * 2.4], [0.3, 0.3], "timber", k=4, cap0="timber", cap1="timber",
                                phase=math.pi / 4, squash=2.0))
        # shoring: plank revetments on the inner lip, props on the outer slope
        for ang, w in SHORING:
            a = math.radians(ang)
            c0 = lip_point(ang, LIP[0] - 0.8, LIP[1] - 0.6, 0.0)
            nrm = V((-math.cos(a) / LIP[0], -math.sin(a) / LIP[1], 0)).normalized()     # facing into the hole
            t = V((-nrm.y, nrm.x, 0))
            out += M.plank_wall(kit, c0, t, nrm, -w / 2, w / 2, 3.0, zc + 1.2, d=-0.6, w=1.4, th=0.5)
        for ang in PROPS:
            foot = lip_point(ang, rx + 6.5, ry + 6.5, 0.4)
            head = lip_point(ang, rx + 0.5, ry + 0.5, zc - 0.5)
            out += M.prop(kit, foot, head, 0.55)
        for i in range(24):                                     # rivets on the crest
            a = 2 * math.pi * i / 24
            pr = V((cx + (rx + 0.3) * math.cos(a), cy + (ry + 0.3) * math.sin(a), 0))
            nr = V((math.cos(a) / rx, math.sin(a) / ry, 0)).normalized()
            out += closed(kit.rivets(pr, V((-nr.y, nr.x, 0)), nr, [(0.0, zc - 0.9)], 0.0, r=0.55))
        # spoil and ore, the cart between
        for c, r, h, seed in HEAPS:
            out += M.heap(kit, V(c), r, h, lumps=5, seed=seed)
        c, facing = CART
        out += M.cart(kit, V(c), facing)
        for x, y, z in TORCHES:
            base = V((x, y, z - 1.2))
            out.append(kit.tube([base - V((0, 0, 1.0)), base + V((0, 0, 0.6))], [0.55, 0.5], "iron", k=5, cap0="iron",
                                cap1="iron"))
            out += M.torch(kit, base, V((0, 0, 1)), 1.4, r=0.3)
        foot, h, facing = BANNER
        out += M.pole_banner(kit, V(foot), h, facing, 6.5, 15.0, mark="hand", top="spike", side=1)
        for i, (sx, sy, sz) in enumerate(STAKES):
            out += M.stakes(kit, [(sx, sy, sz), (sx + 0.1, sy, sz)], 6.5 + i, r=0.6, lean=(0.05, -0.1, 0), pitch=2.0,
                            skulls=(0,), skull=2.1, seed=3)
        return out

    @staticmethod
    def _tower(kit, M):
        """The winch tower on the collar's +X+Y side (between level 2's frames), its boom over the
        hole's edge: four lashed posts, girts and a braced X on the two faces the camera sees, a
        plank platform with a parapet of sharpened stakes, a troll skull on its front corner; the
        boom out to the wheel, the chain down to the bucket, the windlass at the tower's foot and
        its rope up to the wheel."""
        from mathutils import Vector as V
        cx, cy, h, zp = TOWER
        out, deck = M.watchtower(kit, (cx, cy, 0.5), h, zp)
        corners = [V((cx + ex * h, cy + ey * h, 0)) for ex, ey in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        out += kit.horned_skull(deck[0] + V((0.6, 0.6, 6.4)), (0.3, -1, 0), 3.6, horn=1.3, detail=1)
        # the boom out over the hole's edge, a strut under it, the wheel at its end
        wc = V(WHEEL)
        root = V((cx - h * 0.5, cy - h * 0.5, zp + 3.5))
        out += kit.pole(root - (wc - root).normalized() * 3.0, wc + (wc - root).normalized() * 1.5, 0.95, k=6)
        out += kit.pole(V((cx - h, cy - h, 9.0)), root.lerp(wc, 0.55), 0.6)
        axle = (wc - root).cross(V((0, 0, 1))).normalized()
        out += M.wheel(kit, wc, axle, 4.0, spokes=6, rim=0.45, width=1.0)
        b = V(BUCKET)
        out += kit.chain(wc + V((0, 0, -0.2)) + (b - wc).cross(axle).normalized() * 0.0, b + V((0, 0, 1.5)), link=1.4, w=0.5)
        out += M.bucket(kit, b, r=1.7, h=2.4)
        c, along = WINDLASS
        out += M.windlass(kit, V(c), along, span=7.0, h=5.0, r=1.0)
        drum = V(c) + V((0, 0, 5.8))
        out.append(kit.tube([drum, wc + (root - wc).normalized() * 4.0], [0.22, 0.22], "rope", k=4, cap0="rope", cap1="rope"))
        out += M.torch_bracket(kit, corners[0] + V((-0.9, -0.9, 12.0)), (-1, -1), reach=1.6, length=3.0)
        return out

    def decals(self):
        from ..paint import goblin_layers
        cx, cy, h, zp = TOWER
        anchors = [(cx - h + 0.6, cy - h + 0.6, zp + 6.0, 2.2, 6.0)]
        anchors += [(sx, sy, sz + 6.0, 1.6, 4.0) for sx, sy, sz in STAKES]
        return [goblin_layers()["Gore"](anchors)]

    def emphasis(self, c, n):
        if c.z > 20:
            return 1.3                        # the tower's head: wheel, boom, skull
        return 1.0
