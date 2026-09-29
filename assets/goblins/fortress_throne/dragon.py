"""The dragon on the Goblin throne (Blender side): EA's sculpt kept whole - the rearing wyrm on its
nest, the jagged crest down its neck and back, the swept wings, the forelegs gripping the bowl's
rim, the open jaws - and made the Goblins' chained war idol in blood, iron and bone.

EA's dragon (WBFGTHRONE mesh coordinates, measured from its sections; it faces +X, the gate): the
chest a hollow shell over the nest (z 74..108) open at the front (the drake's niche, x 4..14,
|y| < 8.5: the fire drake idles on B_DRAKE at (12.8, 0, 74.5): nothing new stands there); the neck
x -18..1.5, |y| < 7.3 at z 131; the head x -10..31, z 138..168, its eyes (FXEYE) at (20.3, +-7,
154.4), the mouth (FXMOUTH (16, 0, 146.4)) a wedge from the hinge (10, 150.5) opening to the upper
jaw's edge at (28, 143) and the lower jaw's at (25, 138); EA's horns from the crown to
(-8.3, +-11.9, 173.2); the crest's tips at y 0 (CREST); the wings behind (x -17..-35, |y| 12..25.2,
z 70..150), their tips at (-32, +-22.3, 149.8); the forearms from the shoulder (12, 14, 95) to the
wrist (23, 17, 86), the talons hanging over the rim to z 70.5, x <= 40.3. What is added:

    horns      two great crimson horns sweeping back from behind EA's, bleached white tips
    crown      a spiked iron crown round the horn roots, riveted, its tines tipped in bone
    jaws       bone fangs, upper and lower, blood on their points; two boar tusks out of the
               lower jaw; blood running off the lip
    collar     a riveted iron collar round the neck with spikes, a chain slung across the
               chest from it with a skull hanging at the throat, above the drake's niche
    crest      bleached spikes out of every tip of EA's crest, head to back
    wings      a bone spur rising from each wing tip, a skull driven onto the left one
    forelegs   iron shackles on the wrists chained to the nest, bone talons with blood on them
"""
from mathutils import Vector as V

from sagekit.blender.geometry import Z, sweep
# the crest's tips at y 0 (x, z) and the direction each spike leaves in (x, z)
CREST = [((-24.9, 84.2), (-1.0, 0.25), 7.5), ((-19.0, 94.5), (-1.0, 0.35), 5.5), ((-21.5, 108.0), (-1.0, 0.4), 6.5),
         ((-25.2, 118.0), (-1.0, 0.45), 9.0), ((-25.7, 133.2), (-1.0, 0.55), 9.5), ((-21.9, 143.3), (-0.85, 0.6), 8.5),
         ((-17.5, 154.6), (-0.7, 0.75), 7.5), ((-10.6, 161.2), (-0.6, 0.8), 5.5)]
# the neck's section at the collar (z 131) and the crown's path round the horn roots (z 165)
NECK = [(-18.0, -3.1), (-14.5, -5.75), (-6.1, -7.26), (-1.7, -4.4), (1.34, 0.0), (-1.7, 4.4), (-6.1, 7.26),
        (-14.5, 5.75), (-18.0, 3.1)]
COLLAR_Z = 131.0
CROWN = [(-3.2, 0.0), (0.2, -6.2), (5.0, -8.6), (10.2, -6.4), (13.6, 0.0), (10.2, 6.4), (5.0, 8.6), (0.2, 6.2)]
CROWN_Z = 165.2
# EA's talon tips (x, |y|, z) and the wrist (centre, axis, radius)
TALONS = [(29.2, 13.0, 70.6), (32.2, 18.3, 70.5), (36.8, 8.7, 71.3), (39.5, 13.1, 72.2)]
WRIST = ((22.0, 16.8, 87.0), (0.77, 0.2, -0.6), 3.7)
CHAIN_FOOT = (18.9, 12.9, 63.0)                   # the ring on the nest's flare each wrist is chained to
PENDANT = (11.0, 0.0, 115.5)                      # the skull at the throat, above the niche


def band(kit, path, z, h, th=0.8, inner=1.6, rivets=1, tag="iron", center=(0, 0), closed=False):
    """A riveted iron band h tall along a closed convex (x, y) path at height z, standing th proud
    of it and sunk `inner` into what it wraps (the hoop of the kit on any outline); closed: its
    inner face too (a ring standing free of what it goes round, like the crown)."""
    pts = [tuple(p) for p in path] + [tuple(path[0])]
    prof = [(-inner, z - h / 2), (th, z - h / 2), (th, z + h / 2), (-inner, z + h / 2)]
    solids, segs = sweep(pts, prof, [tag, tag, tag, tag if closed else None], center=center)
    out = list(solids)
    if rivets:
        for a2, b2, t2, n2 in segs[::rivets]:
            m = (a2 + b2) / 2
            out += kit.rivets(V((m.x, m.y, 0)), V((t2.x, t2.y, 0)), V((n2.x, n2.y, 0)), [(0.0, z)], th, 0.32)
    return out


def outline_normals(path, center):
    """(point, outward horizontal unit normal) at every corner of a closed outline."""
    out = []
    c = V((center[0], center[1], 0))
    for p in path:
        q = V((p[0], p[1], 0))
        out.append((q, (q - c).normalized()))
    return out


def head(kit):
    out = []
    for e in (-1, 1):
        # the great horns, from behind EA's, sweeping back and curling up
        out += kit.horn(V((-4.0, e * 4.2, 156.0)), V((-0.6, e * 0.8, -0.05)), V((-0.1, e * 0.3, 1.0)), 27.0, 2.8,
                        n=7, k=7, root="hide", tip="bone", tip_from=0.45)
        # a frill of bone spikes behind the jaw
        for p, d, length in (((3.0, e * 6.4, 148.5), (-0.85, e * 0.5, 0.1), 6.0),
                             ((1.5, e * 6.8, 154.0), (-0.8, e * 0.5, 0.35), 7.0)):
            out += kit.horn(V(p), V(d), V((-0.9, e * 0.3, 0.5)), length, 0.9, n=3, k=5, root="bone", tip="bone")
        # fangs: upper ones down from the upper jaw, lower ones up; blood on the points
        for x, length in ((15.0, 3.0), (19.5, 3.6), (24.0, 3.2)):
            zu = 150.5 - 0.417 * (x - 10.0)
            out += kit.spike(V((x, e * 3.3, zu + 0.6)), V((0.12, 0, -1)), length + 0.6, 0.55, tag="bone", k=4, tip="gore")
        for x, length in ((17.5, 2.6), (22.0, 2.8)):
            zl = 150.5 - 0.83 * (x - 10.0)
            out += kit.spike(V((x, e * 3.0, zl - 0.6)), V((0.1, 0, 1)), length + 0.6, 0.5, tag="bone", k=4, tip="gore")
        # the boar tusks out of the lower jaw
        out += kit.horn(V((21.0, e * 4.0, 141.0)), V((0.45, e * 0.75, 0.3)), V((0.1, e * 0.2, 1.0)), 9.0, 1.0,
                        n=4, k=6, root="bone", tip="bone")
        # blood running off the lower lip
        p = V((24.5, e * 1.6, 138.6))
        out.append(kit.tube([p + Z * 0.6, p, p - Z * 1.6, p - Z * 2.6, p - Z * 3.0], [0.45, 0.4, 0.28, 0.4, 0.0], "gore",
                            k=5, cap0="gore", cap1=None))
    # the iron crown round the horn roots, its tines tipped in bone
    out += band(kit, CROWN, CROWN_Z, 3.2, th=0.85, inner=1.0, rivets=2, center=(5.0, 0.0), closed=True)
    for i, (q, n) in enumerate(outline_normals(CROWN, (5.0, 0.0))):
        length = 7.5 if i == 4 else (5.0 if i % 2 else 6.0)
        base = q + n * 0.4 + Z * (CROWN_Z + 1.0)
        d = n * 0.28 + Z
        out += kit.spike(base, d, length, 0.75, tag="iron", k=4, tip="bone")
    return out


def neck(kit):
    out = band(kit, NECK, COLLAR_Z, 4.2, th=1.0, inner=2.0, rivets=1, center=(-8.0, 0.0))
    for i, (q, n) in enumerate(outline_normals(NECK, (-8.0, 0.0))):
        if i in (1, 2, 6, 7):
            out += kit.spike(q + n * 0.6 + Z * COLLAR_Z, n + Z * 0.35, 5.5, 0.8, tag="iron", k=4)
    # a chain slung across the chest from the collar, a skull hanging at the throat
    pend = V(PENDANT)
    for e in (-1, 1):
        a = V((-2.6, e * 5.6, COLLAR_Z - 1.4))
        mid = V((5.0, e * 3.6, 121.0))
        out += kit.chain(a, mid, link=1.4, w=0.55, th=0.2)
        out += kit.chain(mid, pend + Z * 3.2, link=1.4, w=0.55, th=0.2)
    out.append(kit.tube([pend + Z * 3.6, pend + Z * 2.2], [0.7, 0.7], "iron", k=6, cap0="iron", cap1="iron"))
    out += kit.skull(pend, (1, 0, 0), 3.4, detail=2)
    return out


def crest(kit):
    out = []
    for (x, z), (dx, dz), length in CREST:
        d = V((dx, 0, dz)).normalized()
        out += kit.spike(V((x, 0, z)) - d * 1.4, d, length + 1.4, 1.25, tag="bone", k=5)
    return out


def wings(kit):
    out = []
    for e in (-1, 1):
        base = V((-31.4, e * 21.8, 147.0))
        out += kit.horn(base, V((0.05, -e * 0.12, 1.0)), V((0.6, -e * 0.1, 0.5)), 10.0, 1.5, n=4, k=6, root="bone", tip="bone")
        if e < 0:
            out += kit.skull(base + V((0.9, e * -0.6, 6.0)), (1, 0.3 * e, 0), 3.4, detail=2)
    return out


def forelegs(kit):
    out = []
    c, ax, r = WRIST
    for e in (-1, 1):
        cc, a = V((c[0], e * c[1], c[2])), V((ax[0], e * ax[1], ax[2])).normalized()
        # the shackle: a riveted iron cuff round the wrist and a staple under it
        out.append(kit.tube([cc - a * 1.4, cc + a * 1.4], [r, r], "iron", k=8, cap0="iron", cap1="iron"))
        out.append(kit.tube([cc - a * 0.5, cc + a * 0.5], [r + 0.45, r + 0.45], "iron", k=8, cap0="iron", cap1="iron"))
        low = cc + V((0.0, e * 0.6, -r - 0.3))
        foot = V((CHAIN_FOOT[0], e * CHAIN_FOOT[1], CHAIN_FOOT[2]))
        sag = low.lerp(foot, 0.5) + V((1.5, e * 1.2, -2.0))
        out += kit.chain(low, sag, link=1.5, w=0.6, th=0.22) + kit.chain(sag, foot, link=1.5, w=0.6, th=0.22)
        # bone talons out of EA's claws, blood on them
        for x, y, z in TALONS:
            out += kit.horn(V((x - 0.2, e * y, z + 1.3)), V((0.1, 0, -1)), V((-0.7, 0, -0.7)), 3.8, 0.62, n=3, k=5,
                            root="bone", tip="gore", tip_from=0.6)
    return out


def build(kit):
    return head(kit) + neck(kit) + crest(kit) + wings(kit) + forelegs(kit)


def gore_anchors():
    """(x, y, z, radius, run) of the dragon's bloody places, for the Gore paint layer."""
    out = [(24.0, 0.0, 139.5, 3.2, 6.0), (PENDANT[0], 0.0, PENDANT[2] - 1.5, 2.2, 7.0)]
    for e in (-1, 1):
        out += [(34.0, e * 13.0, 73.0, 3.5, 4.0), (-31.4, e * 21.8, 152.0, 1.6, 3.0) if e < 0 else (17.0, e * 3.0, 145.0, 2.0, 3.0)]
    return out
