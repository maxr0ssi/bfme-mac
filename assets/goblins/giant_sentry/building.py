"""The Goblin giant sentry (WildGiantSentryExpansion): EA's crowned column kept whole - the plated
column flaring at its foot, the crater at its top the mountain giant stands in, the ring of great
spikes round the crater's rim, the brace down to the ground at the back - and made the giant's
perch in blood, iron and bone: a crown of six great crimson horns curling out of the rim and a
horned-skull totem on its back, skulls driven onto four of the rim's spikes and hung on chains
under the rim, four ribs rising from a skirt of black rock to grip the column (pad.py, the
expansions' pad), heaps of round boulders in rope nets at its foot (the giant's ammunition), a
great gnawed thigh bone leaning on it, a skull on the brace's post and one ragged house-colour
banner under the rim.

EA's facts (WBFGSENTRY mesh coordinates, measured; work/measure.json): WBFGSentry, 368 triangles on
WBFortress.tga (own copy WBFortresE.tga); x -53.80..42.01, y -39.18..42.20, z 0..53.50. The column:
about (-2, 2), its corners at z 20 at (-21.9, +-2.5), (-19.2, -15.2), (-4.1, -20.1), (11.9, -15.1),
(20.9, 0), (11.7, 15.8), (-4.1, 24.1), (-18.3, 15.2), flaring to x 28.3 at the ground; the crater
floor (P1, the giant's stand, bone P1 at (-10.5, 0, 30)) x -17..13, y -14..15.5 at z 29.5, the
rim's spikes out to r ~40 at z 40..53.5: nothing new stands over the crater. The brace: a post
x -53.8..-22, |y| < 3.3 to z 44.2. Lifecycle: WBFGSentry_A (construction), _D2, _D3. House colour:
none of EA's; our own (HOUSE_DRAW).
"""
from sagekit.building import Building

from ..style import GoblinStyle

C = (-2.0, 2.0)                               # the column's axis
HEAPS = [((25.5, -16.0), 5, 1), ((8.0, -28.5), 4, 2), ((19.5, 22.5), 4, 3)]      # (centre, boulders, seed)
# the rim's great spikes that carry a skull: (root, tip), measured
TROPHIES = [((-3.0, -29.5, 45.0), (-8.7, -39.2, 48.5)), ((29.0, -2.8, 41.4), (42.0, -1.3, 43.2)),
            ((14.5, 23.8, 41.0), (20.9, 29.6, 46.8)), ((-26.5, 23.0, 46.5), (-36.7, 30.8, 50.5))]
POST = (-50.5, 0.0, 43.6)
# the crown: great horns rooted on the rim's outer lip (r 19.5 about C, z 44.5), between EA's spikes
HORNS = [(-150, 19.0), (-115, 21.0), (-40, 21.0), (25, 20.0), (72, 21.0), (118, 19.0)]     # (degrees, length)
TOTEM = (-21.3, 0.8, 43.6, 12.0, 3.8)          # the skull totem on the back rim: x, y, z, height, skull
# the banner on the column's front face (its z 35 edge (-4.1, -23.2)..(13.5, -17.6)): u, top, width, length
BANNER = (8.8, 34.5, 7.5, 18.0)


def boulders(kit, c, count, seed, r=2.7):
    """A heap of round boulders (the giant's ammunition) with rope thongs bound round the top one."""
    import math

    from ..arrow_den.pad import jitter
    V, Z = kit.V, kit.Z
    out = []
    spots = [(0.0, 0.0, 0.0)] + [(math.cos(a), math.sin(a), 0.0) for a in
                                 (2 * math.pi * i / (count - 2) + seed for i in range(count - 2))]
    for i, (ux, uy, _) in enumerate(spots[:count - 1]):
        rr = r * (0.75 + 0.45 * jitter(seed, i))
        p = V((c[0] + ux * r * 1.5, c[1] + uy * r * 1.5, 0.0))
        out.append(kit.tube([p, p + Z * rr * 0.5, p + Z * rr * 1.25, p + Z * rr * 1.8],
                            [rr * 0.62, rr, rr * 0.86, rr * 0.3], "rock", k=7, cap0="rock", cap1="rock",
                            phase=jitter(seed, i + 9)))
    top = V((c[0], c[1], r * 2.1))
    out.append(kit.tube([top - Z * r * 0.6, top, top + Z * r * 0.75, top + Z * r * 1.2],
                        [r * 0.8, r * 1.05, r * 0.8, r * 0.3], "rock", k=7, cap0="rock", cap1="rock", phase=seed))
    for ax in ((1, 0.3, 0), (-0.3, 1, 0)):
        out += kit.lashing(top + Z * r * 0.1, V(ax), r * 0.62, turns=1, w=0.6)
    return out


class GiantSentry(Building):
    style = GoblinStyle()
    source = "WBFGSentry"
    target = "WBFGSENTRY"
    sheet = "WBFortress.tga"
    sheet_normal = "WBFortress_NRM.tga"
    own_textures = {"WBFortress.tga": "WBFortresE.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    facet_islands = 8                       # the Goblin kit's unwrap overlaps a little: seams at EA's islands and 8-degree turns
    HOUSE_DRAW = "ModuleTag_Draw_HCGiantSentry"
    views = {
        "rts": ((-5.9, 1.5, 26.8), 301, 50, -38, 50),
        "close": ((-5.9, 1.5, 26.0), 215, 22, -38, 45),
        "ingame": ((-5.9, 1.5, 26.8), 683, 53, -62, 50),
    }

    def design(self, kit):
        import math

        from ..arrow_den import pad
        V, Z = kit.V, kit.Z
        box = (-53.8, 42.0, -39.18, 42.2)
        foot = pad.ring(C, 23.5, 10, 0.1)
        foot = [p for p in foot if p[0] > -20.0]            # not under the brace
        out = pad.skirt(kit, foot, C, r=2.8, h=2.6, pitch=3.4, out=1.0, seed=17, box=box, closed=False)
        out += pad.skirt(kit, [(-52.0, 4.6), (-44.0, 4.6), (-44.0, -4.6), (-52.0, -4.6)], (-48.0, 0.0), r=2.2, h=2.2,
                         pitch=3.0, out=0.5, seed=19, box=box, closed=False)
        angles = [35, 145, -145, -35]
        for i, a in enumerate(angles):
            a = math.radians(a)
            rad = V((math.cos(a), math.sin(a), 0))
            f = V((C[0], C[1], 0)) + rad * 29.0
            top = V((C[0], C[1], 25.0)) + rad * 18.8
            ctrl = [f, f + rad * 3.5 + Z * 10.0, top + rad * 6.0 + Z * 2.0, top]
            out += pad.rib(kit, ctrl, 2.0, tip=True)
            out += pad.rock(kit, (f.x, f.y), 3.4, 3.2, seed=31 + i)
        for root, tip in TROPHIES:                          # skulls driven onto the rim's spikes
            root, tip = V(root), V(tip)
            d = (tip - root).normalized()
            p = root.lerp(tip, 0.5)
            out += kit.skull(p + Z * 0.4, V((d.x, d.y, 0)), 3.3, detail=1)
            out.append(kit.tube([p - d * 2.2 - Z * 1.0, p - d * 2.2 - Z * 2.8], [0.55, 0.45], "gore", k=4, cap0="gore",
                                cap1="gore"))
        # skulls hung on chains under the rim, between the ribs
        for a in (0, 90, -90, 180 - 35, -180 + 35):
            a = math.radians(a)
            rad = V((math.cos(a), math.sin(a), 0))
            hang = V((C[0], C[1], 37.2)) + rad * (21.8 if abs(math.cos(a)) < 0.5 else 23.5)
            out += kit.chain(hang, hang - Z * 3.0)
            out += kit.skull(hang - Z * 4.4 + rad * 0.4, rad, 2.4, detail=0)
        # the crown: great crimson horns curling out of the rim, iron-collared, and a skull totem
        for a, length in HORNS:
            rad = V((math.cos(math.radians(a)), math.sin(math.radians(a)), 0))
            base = V((C[0], C[1], 44.5)) + rad * 19.5
            out += kit.horn(base, rad * 0.3 + Z, rad * 0.75 + Z * 0.7, length, 2.2, n=6, k=6, tip_from=0.55)
            out.append(kit.tube([base + Z * 0.6, base + Z * 2.4], [2.6, 2.4], "iron", k=6, cap0="iron", cap1="iron"))
        x, y, z, height, size = TOTEM
        out += kit.totem(V((x, y, z)), height, size, facing=(1, -0.3, 0), skulls=2)
        for (x, y), count, seed in HEAPS:
            out += boulders(kit, (x, y), count, seed)
        # a gnawed thigh bone leaning on the column's front
        out += kit.bone(V((31.0, 6.0, 2.2)), V((20.5, 5.0, 24.0)), 1.45, k=6, knob=1.9)
        x, y, z = POST
        out += kit.skull_on_spike(V((x, y, z - 1.0)), 6.0, 3.0, facing=(1, -0.6, 0))
        bx, top, w, length = BANNER
        a, t = V((-4.1, -23.2, 0)), V((17.6, 5.6, 0)).normalized()
        out += kit.banner(a, t, t.cross(Z), bx, top, w, length, d=1.8, mark="claw")
        return out

    def decals(self):
        from ..paint import goblin_layers
        anchors = [(POST[0], POST[1], POST[2] + 4.0, 1.8, 6.0), (31.0, 6.0, 1.5, 2.4, 2.0)]
        for root, tip in TROPHIES:
            x, y, z = ((a + b) / 2 for a, b in zip(root, tip))
            anchors.append((x, y, z - 1.0, 2.2, 7.0))
        return [goblin_layers()["Gore"](anchors)]

    def emphasis(self, c, n):
        return 1.3 if c.z > 30 else 1.0
