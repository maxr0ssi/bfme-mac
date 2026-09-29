"""The Goblin spider holes (WildSpiderHolesExpansion): EA's hunched carapace kept whole - the tall
plated crest at the back, the scaled shell, the brow over the dark spawn hollow at the front, the
low wavy ground ring - and made a great dead spider the Goblins breed their spiders in, in blood,
iron and bone: four pairs of jointed legs rise off the carapace to high knees and come down to
pointed feet on the ground ring (crimson chitin, bleached bone joints and bristles, an iron band
below each knee), cocoons hung from the front legs' shins on cords, skull piles and bones by the legs' feet
and a skirt of black rock along the ground ring (pad.py, the expansions' pad). No banner (the cap
for the spider holes is 0).

EA's facts (WBSHOLE mesh coordinates, measured; work/measure.json): WBSHole, 348 triangles on
WBFortress.tga (own copy WBFortresF.tga); x -48.47..16.23, |y| <= 25.16, z 0..46.84, mirror
symmetric in y. The body's walls stand at |y| 13..15 under an eave (|y| 17.6 at z 22-26); the
carapace rises to z 34-38 along the middle and to the crest's top (the flat back wall x -48.5,
|y| 13.3, z 46.8). The ground ring: |y| 23.8 at z 0 rising to a top at z 2.8-3.2 inside |y| 20.
The spawn hollow: the front, x > 0, |y| < 10, z 0..22 under the brow (x 12..16, z 20..24): spiders
come out there, so nothing new stands in x > -2, |y| < 11. Lifecycle: WBSHole_A (construction),
_D2, _D3. House colour: none of EA's; our own (HOUSE_DRAW), no cloth.
"""
from sagekit.building import Building

from ..style import GoblinStyle

# the legs, fanned like a spider's: (x of the root, x of the knee, x of the foot); root |y| 9 z 32,
# knee |y| 16.5 z 44, the tibia kinked out at |y| 22.4 z 21 down to the foot, |y| 23.6 z 0.6
LEGS = [(-38.0, -42.0, -46.5), (-28.0, -31.0, -35.0), (-17.0, -15.5, -12.5), (-6.5, -2.0, 5.5)]
ROOT, KNEE, KINK, FOOT = (9.0, 32.0), (16.5, 44.0), (22.4, 21.0), (23.6, 0.6)
PILES = [(-37.0, -21.0, 3, 2.1, 2), (-8.0, -21.0, 2, 2.0, 5), (-24.0, 20.5, 2, 2.0, 7)]


def leg(kit, x0, x1, x2, e):
    """One leg on side e (+-1): a crimson chitin femur from the carapace up to the knee, a bone
    knuckle, the tibia kinked out and down to a pointed bone foot, bristles along it, an iron band
    on the femur below the knee."""
    V = kit.V
    root, knee = V((x0, e * ROOT[0], ROOT[1])), V((x1, e * KNEE[0], KNEE[1]))
    foot = V((x2, e * FOOT[0], FOOT[1]))
    mid = root.lerp(knee, 0.5) + V((0, e * 0.4, 1.6))
    out = [kit.tube([root - (knee - root).normalized() * 2.0, root, mid, knee], [2.3, 2.2, 1.9, 1.6], "hide", k=6,
                    cap0="hide", cap1="hide")]
    out.append(kit.tube([knee - V((0, e * 1.0, 0.6)), knee + V((0, e * 0.3, 0.9)), knee + V((0, e * 0.9, 0.2))],
                        [1.8, 2.2, 1.6], "bone", k=6, cap0="bone", cap1="bone"))
    out += kit.spike(knee + V((0, -e * 0.2, 1.6)), V((0, -e * 0.25, 1)), 4.2, 0.6, tag="bone", k=4)
    kink = V(((x1 + x2) / 2, e * KINK[0], KINK[1]))
    ankle = kink.lerp(foot, 0.55)
    out.append(kit.tube([knee, knee.lerp(kink, 0.5) + V((0, e * 0.8, 0)), kink], [1.5, 1.4, 1.2], "hide", k=6,
                        cap0="hide", cap1="hide"))
    out.append(kit.tube([kink - (kink - knee).normalized() * 0.8, kink + V((0, 0, 0.6)), kink - V((0, 0, 1.2))],
                        [1.25, 1.5, 1.1], "bone", k=6, cap0="bone", cap1="bone"))
    out.append(kit.tube([kink, ankle], [1.05, 0.85], "hide", k=6, cap0="hide", cap1="hide"))
    for f in (0.3, 0.7):                                # bristles along the tibia's upper side
        p = knee.lerp(kink, f) + V((0, e * 0.6, 1.0))
        out += kit.spike(p, V((0, e * 0.5, 1.0)), 2.6, 0.32, tag="bone", k=3)
    m = root.lerp(knee, 0.78)
    d = (knee - root).normalized()
    out.append(kit.tube([m - d * 0.5, m + d * 0.5], [2.15, 2.1], "iron", k=6, cap0="iron", cap1="iron"))
    return out


class SpiderHoles(Building):
    style = GoblinStyle()
    source = "WBSHole"
    target = "WBSHOLE"
    sheet = "WBFortress.tga"
    sheet_normal = "WBFortress_NRM.tga"
    own_textures = {"WBFortress.tga": "WBFortresF.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    facet_islands = 8                       # the Goblin kit's unwrap overlaps a little: seams at EA's islands and 8-degree turns
    HOUSE_DRAW = "ModuleTag_Draw_HCSpiderHoles"
    views = {
        "rts": ((-22.1, -0.0, 23.4), 208, 50, -38, 50),
        "close": ((-18.0, 0.0, 22.0), 160, 22, -38, 45),
        "ingame": ((-22.1, -0.0, 23.4), 472, 53, -62, 50),
    }

    def design(self, kit):
        from ..arrow_den import pad
        V, Z = kit.V, kit.Z
        box = (-48.47, 16.23, -25.16, 25.16)
        out = []
        for e in (-1, 1):
            for x0, x1, x2 in LEGS:
                out += leg(kit, x0, x1, x2, e)
            outline = [(-3.0, e * 17.5), (-24.0, e * 17.8), (-46.0, e * 16.0)]
            out += pad.skirt(kit, outline, (-22.0, 0.0), r=2.2, h=2.2, pitch=3.6, out=0.6, seed=9 + e, box=box,
                             closed=False, z=2.4)
        out += pad.skirt(kit, [(-46.5, -14.0), (-46.5, 14.0)], (-30.0, 0.0), r=1.6, h=2.0, pitch=3.5, out=0.3, seed=13,
                         box=box, closed=False, z=1.0)
        # cocoons hung from the front legs' shins
        for e in (-1, 1):
            x1 = LEGS[-1][1]
            x2 = LEGS[-1][2]
            top = V(((x1 + x2) / 2 + 0.2, e * (KINK[0] - 1.6), KINK[1] + 7.0))
            out.append(kit.tube([top + Z * 1.2, top - Z * 5.0], [0.18, 0.18], "rope", k=3, cap0="rope", cap1="rope"))
            out += kit.carcass(top - Z * 5.0, 6.5, 1.7, facing=(1, -0.5 * e, 0))
        for px, py, count, size, seed in PILES:
            out += kit.skull_pile(V((px, py, 1.6)), 2.8, count, size, seed=seed, face=(1, -0.6, 0))
        out += kit.bone(V((-20.0, -21.5, 2.2)), V((-13.5, -20.0, 2.6)), 0.3)
        return out

    def decals(self):
        from ..paint import goblin_layers
        anchors = [(px, py, 2.4, 2.4, 2.0) for px, py, *_ in PILES]
        x1, x2 = LEGS[-1][1:]
        anchors += [((x1 + x2) / 2, e * (KINK[0] - 1.6), KINK[1] - 5.0, 1.8, 3.0) for e in (-1, 1)]
        return [goblin_layers()["Gore"](anchors)]

    def emphasis(self, c, n):
        return 1.3 if c.z > 26 else 1.0
