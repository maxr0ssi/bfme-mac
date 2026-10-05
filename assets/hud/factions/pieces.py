"""Each faction palantir's 3D ornaments (stdlib; docs/HUD.md, "Ornaments in 3D").

sagekit/hud/pieces.py renders these in Blender (sagekit/blender/hudpieces.py) and the painter lays
the render, shadows included, over the frame. There are a handful of large pieces per faction at the
focal points: the joint between the rings (the double frame only), the top of the ring, the top
left and the bar's end caps. Coordinates are page px (x right, y down; z out of the page), on the
double page (512x256). The single page (256x256) keeps the minimap and the bar in the same place.

Room past the frame lies inside the page only (the quad EA's geometry draws): above the joint, off
the top left, under the bar's ends. The painter clips everything to frame.safe() (outside both
glasses, clear of the buttons and the resource numbers).

MATS:    the material library: base, metal, rough, ss (subsurface), trans, coat, emit/emit_s, grime
         (dirt in the hollows), wear (bright worn edges), frost, blood, var (tone variation).
PIECES:  per faction, (where, piece): where is "both" or "double"; a piece is a dict for the
         Blender script: tube (pts, r, profile round/hex/blade/leaf), star, box, disc, prism (poly),
         gem, skull, bone (a, b), hand.
LIGHT:   per faction the scene: sky (ambient colour), ambient, key, rim, rim_col.
"""

MATS = {
    "bone": dict(base=(0.62, 0.55, 0.42), rough=0.55, ss=0.2, grime=0.9, grime_col=(0.2, 0.12, 0.06), var=0.35,
                 noise_scale=0.3),
    "bone_blood": dict(base=(0.62, 0.55, 0.42), rough=0.5, ss=0.2, grime=0.85, grime_col=(0.25, 0.12, 0.06),
                       blood=0.6, var=0.3, noise_scale=0.25),
    "horn_red": dict(base=(0.40, 0.035, 0.03), rough=0.32, coat=0.6, grime=0.7, wear=0.35,
                     wear_col=(0.85, 0.75, 0.70), var=0.2),
    "horn_black": dict(base=(0.03, 0.03, 0.035), rough=0.3, coat=0.7, grime=0.4, frost=0.85),
    "iron": dict(base=(0.07, 0.065, 0.06), metal=1.0, rough=0.48, grime=0.5, wear=0.5, wear_col=(0.55, 0.53, 0.5)),
    "iron_black": dict(base=(0.05, 0.05, 0.055), metal=1.0, rough=0.35, wear=0.9, wear_col=(0.85, 0.87, 0.9)),
    "steel": dict(base=(0.42, 0.42, 0.44), metal=1.0, rough=0.13, grime=0.55, wear=0.6, wear_col=(0.95, 0.95, 0.97)),
    "gold": dict(base=(1.0, 0.70, 0.27), metal=1.0, rough=0.16, grime=0.45, grime_col=(0.35, 0.2, 0.05), wear=0.3,
                 wear_col=(1.0, 0.92, 0.7)),
    "silver": dict(base=(0.90, 0.92, 0.95), metal=1.0, rough=0.12, grime=0.4, grime_col=(0.3, 0.32, 0.36)),
    "stone_white": dict(base=(0.86, 0.85, 0.80), rough=0.6, grime=0.6, grime_col=(0.4, 0.38, 0.34), var=0.15),
    "enamel_blue": dict(base=(0.015, 0.05, 0.24), rough=0.3, coat=0.15),
    "plate_black": dict(base=(0.025, 0.025, 0.03), metal=0.6, rough=0.4, grime=0.3),
    "ice": dict(base=(0.66, 0.86, 1.0), rough=0.04, trans=0.35, coat=1.0, emit=(0.25, 0.55, 1.0), emit_s=0.35,
                ior=1.31),
    "sapphire": dict(base=(0.04, 0.18, 0.9), rough=0.03, coat=1.0, emit=(0.08, 0.25, 1.0), emit_s=0.6),
    "arken": dict(base=(0.92, 0.96, 1.0), rough=0.02, coat=1.0, emit=(0.7, 0.85, 1.0), emit_s=0.9),
    "white_glow": dict(base=(0.96, 0.97, 1.0), rough=0.35, emit=(0.55, 0.72, 1.0), emit_s=0.8),
    "white_hand": dict(base=(0.95, 0.95, 0.93), rough=0.4, ss=0.1, grime=0.5, emit=(1, 1, 1), emit_s=0.15),
    "ember": dict(base=(0.1, 0.02, 0.0), emit=(1.0, 0.35, 0.04), emit_s=4.0),
}


def T(pts, r, mat, profile="round", aspect=1.0):
    return dict(kind="tube", pts=pts, r=r, mat=mat, profile=profile, aspect=aspect)


def bezel(at, r, gem_mat, rim_mat="gold"):
    x, y = at
    return [("both", dict(kind="disc", at=[x, y], r=r + 1.3, h=1.4, bevel=0.6, mat=rim_mat)),
            ("both", dict(kind="gem", at=[x, y, 1.3], r=r, mat=gem_mat))]


def icicles(x0, step, y, lengths, r):
    return [("both", T([[x0 + i * step, y, 2.5], [x0 + i * step + 0.4, y + 0.6 * L, 3.0], [x0 + i * step + 0.6, y + L, 2.5]],
                       [r * (0.8 + 0.25 * (L / 20)), r * 0.7, 0.02], "ice", "hex")) for i, L in enumerate(lengths)]


def crystals(x, y, spec):
    """Hexagonal crystals radiating from (x, y): (angle deg, length, radius)."""
    import math
    out = []
    for a, L, r in spec:
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        out.append(T([[x, y, 2.0], [x + c * L * 0.78, y + s * L * 0.78, 3.5 + r], [x + c * L, y + s * L, 3.0 + r]],
                     [r, r, 0.02], "ice", "hex"))
    return out


# the focal points (page px): the joint, the top of the ring, the root off the top left, the bar's ends
JOINT, TOP, TL, BL, BR = (242, 50), (128, 12), (44, 42), (25, 218), (229, 218)

PIECES = {
    "goblins": [
        ("double", dict(kind="bone", a=[230, 54, 5], b=[262, 15, 8], mat="bone_blood", size=1)),
        ("both", T([[45, 44, 3], [32, 29, 6], [22, 15, 7], [17, 4, 6]], [4.2, 3.4, 2.0, 0.02], "bone")),
        ("both", dict(kind="skull", at=[128, 11.5, 4], size=15, mat="bone")),
        ("both", T([[121, 9, 5], [111, 4, 7], [101, 4.5, 6], [94, 9, 5]], [2.6, 2.1, 1.3, 0.02], "horn_red")),
        ("both", T([[135, 9, 5], [145, 4, 7], [155, 4.5, 6], [162, 9, 5]], [2.6, 2.1, 1.3, 0.02], "horn_red")),
        ("both", dict(kind="skull", at=[13, 127, 4], size=17, rot=-90, mat="bone_blood")),
        ("both", dict(kind="skull", at=[BL[0], BL[1], 4], size=12, mat="bone_blood")),
        ("both", dict(kind="skull", at=[BR[0], BR[1], 4], size=12, mat="bone_blood")),
    ],
    "mordor": [
        ("double", dict(kind="box", at=[242, 52], size=[22, 7], h=3.0, bevel=0.9, mat="plate_black")),
        ("double", T([[242, 50, 4], [241, 32, 7], [244, 13, 7], [249, 3, 6]], [5.2, 3.9, 2.0, 0.02], "iron_black", "blade", 0.22)),
        ("double", T([[233, 50, 4], [224, 35, 6], [216, 22, 5]], [4.0, 2.8, 0.02], "iron_black", "blade", 0.22)),
        ("double", T([[251, 51, 4], [261, 37, 6], [270, 27, 5]], [4.0, 2.8, 0.02], "iron_black", "blade", 0.22)),
        ("double", dict(kind="gem", at=[242, 49.5, 3.5], r=1.6, mat="ember", smooth=True)),
        ("both", T([[45, 43, 4], [31, 27, 6], [21, 12, 6], [17, 3, 5]], [4.6, 3.3, 1.6, 0.02], "iron_black", "blade", 0.22)),
        ("both", dict(kind="box", at=[128, 16], size=[26, 5], h=2.5, bevel=0.8, mat="plate_black")),
        ("both", T([[128, 16, 3.5], [128, 9, 5], [128, 2, 4]], [3.4, 2.3, 0.02], "iron_black", "blade", 0.25)),
        ("both", T([[118, 17, 3], [116, 11, 4], [113, 5, 3.5]], [2.6, 1.7, 0.02], "iron_black", "blade", 0.25)),
        ("both", T([[138, 17, 3], [140, 11, 4], [143, 5, 3.5]], [2.6, 1.7, 0.02], "iron_black", "blade", 0.25)),
        ("both", T([[22, 222, 3], [11, 229, 4], [3, 235, 3]], [3.6, 2.2, 0.02], "iron_black", "blade", 0.25)),
        ("both", T([[231, 223, 3], [239, 236, 4], [244, 248, 3]], [3.6, 2.2, 0.02], "iron_black", "blade", 0.25)),
    ],
    "angmar": [
        *[("double", p) for p in crystals(242, 50, [(-90, 36, 4.4), (-114, 27, 3.6), (-66, 28, 3.7),
                                                   (-136, 17, 2.6), (-44, 18, 2.7)])],
        ("both", T([[45, 43, 3], [31, 31, 6], [22, 15, 7], [26, 3, 6]], [4.8, 3.6, 2.0, 0.02], "horn_black")),
        *[("both", p) for p in crystals(128, 16, [(-90, 14, 3.0), (-125, 11, 2.4), (-55, 11, 2.4)])],
        *icicles(13, 6, 226, [11, 19, 14, 22, 9], 2.3),
        *icicles(219, 6, 226, [10, 21, 15, 18, 8], 2.3),
    ],
    "elves": [
        ("double", T([[242, 52, 3], [242, 31, 6], [242, 5, 7]], [3.4, 2.5, 0.02], "silver", "hex")),
        ("double", dict(kind="gem", at=[242, 40, 6.5], r=3.0, mat="gold", smooth=True)),
        ("double", T([[240, 42, 6], [231, 35, 6], [224, 25, 5]], [0.4, 3.0, 0.02], "gold", "leaf", 0.35)),
        ("double", T([[244, 42, 6], [253, 35, 6], [260, 25, 5]], [0.4, 3.0, 0.02], "gold", "leaf", 0.35)),
        ("both", T([[45, 43, 3], [35, 31, 5], [24, 19, 5], [17, 8, 4]], [0.6, 4.2, 3.0, 0.02], "gold", "leaf", 0.35)),
        ("both", T([[123, 12, 3], [113, 9, 4], [104, 11, 3]], [0.5, 2.7, 0.02], "gold", "leaf", 0.35)),
        ("both", T([[133, 12, 3], [143, 9, 4], [152, 11, 3]], [0.5, 2.7, 0.02], "gold", "leaf", 0.35)),
        *bezel(TOP, 3.8, "arken"),
        *bezel(BL, 2.8, "arken", "silver"),
        *bezel(BR, 2.8, "arken", "silver"),
    ],
    "dwarves": [
        ("double", dict(kind="prism", poly=[(229, 56), (255, 56), (255, 49), (251, 49), (251, 42), (247, 42),
                                            (247, 35), (237, 35), (237, 42), (233, 42), (233, 49), (229, 49)],
                        h=3.5, bevel=0.7, mat="gold")),
        *[("double", p) for _, p in bezel((242, 30), 4.4, "arken")],
        ("both", T([[45, 43, 3], [34, 30, 5], [26, 19, 5]], [3.6, 2.4, 0.02], "gold", "blade", 0.4)),
        *[("both", p) for _, p in bezel((24, 16), 2.6, "sapphire")],
        *bezel(TOP, 4.0, "sapphire"),
        *bezel(BL, 3.2, "sapphire"),
        *bezel(BR, 3.2, "sapphire"),
    ],
    "men": [
        ("double", T([[242, 57, 3], [242, 38, 6], [242, 24, 7]], [6.0, 4.4, 0.02], "stone_white", "hex")),
        ("double", dict(kind="box", at=[242, 46], size=[12, 2.6], h=6.5, bevel=0.6, mat="silver")),
        ("double", dict(kind="star", at=[242, 20], r=5.8, n=6, inner=0.42, h=2.2, z=5, bevel=0.5, mat="silver")),
        ("both", T([[45, 43, 3], [33, 29, 5], [23, 17, 5]], [2.8, 3.6, 0.02], "silver", "blade", 0.3)),
        ("both", dict(kind="box", at=[128, 12], size=[33, 17.5], h=1.6, bevel=0.6, mat="silver")),
        ("both", dict(kind="box", at=[128, 12], size=[29, 14], h=1.2, z=1.6, bevel=0.4, mat="enamel_blue")),
        ("both", T([[128, 18.5, 3], [128, 6, 3.3]], [0.8, 0.6], "white_glow")),
        *[("both", T([[128, y0, 3], [128 + s * dx, y0 - dy, 3.2]], [0.5, 0.3], "white_glow"))
          for y0, dx, dy in ((14, 6, 5), (11.5, 5, 4.5), (9, 3.5, 3.5)) for s in (1, -1)],
        ("both", dict(kind="star", at=[118, 9], r=2.2, n=6, h=1.0, z=2.8, bevel=0.3, mat="silver")),
        ("both", dict(kind="star", at=[138, 9], r=2.2, n=6, h=1.0, z=2.8, bevel=0.3, mat="silver")),
        ("both", dict(kind="star", at=list(BL), r=4.0, n=6, h=1.8, bevel=0.5, mat="silver")),
        ("both", dict(kind="star", at=list(BR), r=4.0, n=6, h=1.8, bevel=0.5, mat="silver")),
    ],
    "isengard": [
        ("double", T([[242, 51, 4], [242, 30, 7], [242, 6, 6]], [3.8, 2.4, 0.02], "iron_black", "blade", 0.6)),
        ("double", T([[233, 51, 4], [226, 35, 6], [230, 16, 6]], [3.6, 2.4, 0.02], "iron_black", "blade", 0.6)),
        ("double", T([[251, 51, 4], [258, 35, 6], [254, 16, 6]], [3.6, 2.4, 0.02], "iron_black", "blade", 0.6)),
        ("both", T([[45, 43, 3], [31, 27, 5], [20, 10, 5]], [3.2, 2.0, 0.02], "iron_black", "blade", 0.6)),
        ("both", dict(kind="box", at=[128, 12], size=[27, 18], h=1.6, bevel=0.6, mat="iron_black")),
        ("both", dict(kind="box", at=[128, 12], size=[23, 14.5], h=1.2, z=1.6, bevel=0.4, mat="plate_black")),
        ("both", dict(kind="hand", at=[128, 13, 3.3], size=16, mat="white_hand", res=0.04)),
        ("both", T([[22, 220, 3], [6, 226, 4]], [3.2, 0.02], "steel", "blade", 0.4)),
        ("both", T([[232, 222, 3], [243, 239, 4]], [3.2, 0.02], "steel", "blade", 0.4)),
    ],
}

LIGHT = {
    "goblins": dict(sky=(1.0, 0.9, 0.85), ambient=0.35, key=3.0, rim=0.9, rim_col=(1.0, 0.6, 0.5)),
    "mordor": dict(sky=(0.9, 0.85, 0.8), ambient=0.3, key=3.0, rim=1.2, rim_col=(1.0, 0.5, 0.2)),
    "angmar": dict(sky=(0.8, 0.9, 1.0), ambient=0.4, key=3.0, rim=1.0, rim_col=(0.5, 0.75, 1.0)),
    "elves": dict(sky=(1.0, 0.98, 0.94), ambient=0.4, key=3.4, rim=0.8, rim_col=(0.8, 0.9, 1.0)),
    "dwarves": dict(sky=(1.0, 0.95, 0.85), ambient=0.38, key=3.4, rim=0.8, rim_col=(0.6, 0.7, 1.0)),
    "men": dict(sky=(0.95, 0.97, 1.0), ambient=0.4, key=3.2, rim=0.8, rim_col=(0.8, 0.85, 1.0)),
    "isengard": dict(sky=(0.95, 0.96, 1.0), ambient=0.35, key=3.2, rim=1.0, rim_col=(1.0, 0.55, 0.25)),
}
