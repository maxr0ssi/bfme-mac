"""The Goblin spider pit (WildSpiderPit; WBSpidPit_SKN): EA's black rock spire kept whole - the
spire and its hump, the boulders round its foot, the crimson carved hole of the pit (SPI PIT)
and the glowing web cards strung from the spire to the ground (WEBS, EA's cut-outs) - and made
the lair of a brood-mother, clutched by the legs of a great dead spider:

    legs       five jointed legs, crimson chitin with bleached claws, rising from the spire and
               bending down over the rock to the ground (the new silhouette; the webs hang
               between them)
    spire      a skull on an iron spike on the spire's tip
    larder     a timber gibbet on the -Y side with two flayed carcasses hung for the brood
    trophies   skull piles and gnawed bones round the rock's foot
    banner     one ragged house-colour banner on a post on the -Y boulder

EA's facts (ROCK = model coordinates; sagekit measure: work/measure.json): ROCK x -39.98..25.39,
y -44.46..44.16, z -1.84..73.61 (330 triangles on WBBStone); the spire peaks at z 73.6 at
(-6.5, -16), the hump at z 49 at (-6, 14); the pit's hole (SPI PIT, x -8..43, |y| < 24, z 0..39)
opens to +X where the spiders come out: nothing new at x > 8 inside |y| < 22, and nothing past
ROCK's x 25.4. The webs (WEBS, cut-outs on EA's sheets) and the level-3 cocoons (skinned) stay
EA's. Height limit +20 %: z 88.7.
"""
import math

from sagekit.building import Building

from ..style import GoblinStyle

SPIRE = (-6.5, -16.0, 70.2)                  # the spire's tip (x, y, z of its surface)
# the legs: (angle round the spire (deg), root z at r 4, knee (r, z), foot (r, z on the rock or ground))
LEGS = [(115, 53.0, (15.0, 63.0), (30.0, 16.0)), (150, 45.0, (16.0, 60.0), (30.0, 10.5)),
        (200, 45.0, (16.5, 64.0), (30.0, 0.0)), (250, 45.0, (16.0, 59.0), (29.0, 0.0)),
        (300, 52.0, (15.0, 62.0), (29.0, 0.0))]
GIBBET = (19.5, -33.0, 0.3)
BANNER = ((-14.0, -34.0, 7.0), 25.0, (0.3, -1.0))
PILES = [(21.0, -24.0, 2.6, 3, 1), (-26.0, -30.0, 0.0, 3, 2), (20.0, 26.0, 0.6, 3, 3)]
BONES = [((14.0, -28.0), (17.0, -22.0)), ((-30.0, -20.0), (-33.0, -14.5)), ((17.0, 30.0), (22.0, 32.0))]


class SpiderPit(Building):
    style = GoblinStyle()
    source = "WBSpidPit_SKN"
    target = "ROCK"
    sheet = "WBBStone.tga"
    sheet_normal = "WBBStone_NRM.tga"
    own_textures = {"WBBStone.tga": "WBBStonH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    facet_islands = 8                       # the unwrap overlapped (5%): seams at EA's islands and 8-degree turns
    bake_hidden = ("WEBS", "N_WINDOW", "N_FIRE")          # the web cards would bake their shadow onto the rock
    views = {
        "rts": ((-7.3, -0.2, 35.9), 294, 50, -38, 50),
        "close": ((-7.3, -0.2, 35.9), 174, 24, -30, 45),
        "ingame": ((-7.3, -0.2, 35.9), 667, 53, -62, 50),
    }

    def design(self, kit):
        from mathutils import Vector as V

        from ..cave import motifs as M
        out = []
        cx, cy, top = SPIRE
        for ang, root_z, (kr, kz), (fr, fz) in LEGS:
            rad = V((math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0))
            c = V((cx, cy, 0))

            def P(r, z):
                return c + rad * r + V((0, 0, z))
            ar, az = kr + (fr - kr) * 0.78, kz + (fz - kz) * 0.45        # the ankle: the shin reaches out, then drops
            pts = [P(4.0, root_z), P(10.0, root_z + (kz - root_z) * 0.8), P(kr, kz), P((kr + ar) / 2 + 0.6, (kz + az) / 2),
                   P(ar, az), P((ar + fr) / 2, (az + fz) / 2), P(fr, fz - 0.6)]
            out.append(kit.tube(pts, [1.9, 1.7, 1.45, 1.25, 1.05, 0.7, 0.0], ["hide", "hide", "hide", "hide", "bone", "bone"],
                                k=6, cap0="hide", cap1=None))
            for p, r in ((pts[2], 1.95), (pts[4], 1.5)):             # the joints: bleached knuckles
                d = (pts[pts.index(p) + 1] - pts[pts.index(p) - 1]).normalized()
                out.append(kit.tube([p - d * 0.9, p, p + d * 0.9], [r * 0.9, r, r * 0.9], "bone", k=6, cap0="bone",
                                    cap1="bone"))
            for f in (0.35, 0.7):                                    # bristles on the upper leg
                p = pts[1].lerp(pts[2], f)
                out += kit.spike(p, rad * 0.4 + V((0, 0, 1)), 2.6, 0.3, k=3)
        out += kit.skull_on_spike(V((cx, cy, top - 0.5)), 7.0, 3.8, facing=(1, -0.5, 0))
        # the larder: a post and an arm, two carcasses on chains
        g = V(GIBBET)
        out += M.post(kit, g, 21.0, 0.8, point=True)
        arm0, arm1 = g + V((0.6, 0.0, 18.5)), g + V((-9.0, -3.0, 20.5))
        out += kit.pole(arm0 + V((1.2, 0.4, 0)), arm1, 0.55)
        out += kit.lashing(g + V((0, 0, 18.7)), V((0, 0, 1)), 0.8, turns=2, w=0.35)
        for f, length in ((0.45, 7.0), (0.9, 8.5)):
            hook = arm0.lerp(arm1, f) - V((0, 0, 0.5))
            out += kit.chain(hook, hook - V((0, 0, 2.5)))
            out += kit.carcass(hook - V((0, 0, 2.5)), length, 1.6, facing=(0.3, -1, 0))
        out += M.prop(kit, g + V((0.0, 4.5, 0.0)), g + V((0.0, 0.8, 12.0)), 0.5)
        foot, h, facing = BANNER
        out += M.pole_banner(kit, V(foot), h, facing, 6.2, 14.0, mark="eye", top="skull", side=1)
        for px, py, pz, count, seed in PILES:
            out += kit.skull_pile(V((px, py, pz - 0.3)), 3.0, count, 2.0, seed=seed, face=(1, -0.4, 0))
        for (x0, y0), (x1, y1) in BONES:
            out += kit.bone(V((x0, y0, 0.3)), V((x1, y1, 0.6)), 0.3)
        return out

    def decals(self):
        from ..paint import goblin_layers
        cx, cy, top = SPIRE
        g = GIBBET
        anchors = [(cx, cy, top + 6.0, 2.0, 7.0), (g[0] - 4.0, g[1] - 1.3, g[2] + 9.0, 2.2, 6.0),
                   (g[0] - 8.0, g[1] - 2.7, g[2] + 8.0, 2.2, 6.0)]
        anchors += [(px, py, pz + 0.8, 2.6, 2.0) for px, py, pz, _, _ in PILES]
        return [goblin_layers()["Gore"](anchors)]

    def emphasis(self, c, n):
        if c.z > 40:
            return 1.3                        # the legs' knees and the spire's crown
        return 1.0
