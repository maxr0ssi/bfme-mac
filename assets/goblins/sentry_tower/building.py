"""The Goblin sentry tower (WildSentryTower): EA's watchtower kept whole - the rough black stone
shaft, the four horn-plate buttresses at its foot, the porch over the door and its ramp, the great
riveted hood with its spiked eaves and forked tip - and made a small cousin of the citadel's spires
in blood, iron and bone: a riveted iron band round the hood, four great horns sweeping out of it
and four small tusks under them, an iron spike from its tip with a skull driven onto it, a skull on
a spike out of the shaft and a painted hide nailed to it, a gibbet cage hung from an iron arm under
the hood, a skirt of black rock and skull piles round the foot, and one ragged house-colour banner
over the porch.

EA's facts (DBTOWER mesh coordinates, measured; work/measure.json): WBTower, 1289 triangles on
WBTower.tga (own copy WBToweH.tga; new faces are mapped onto the faction's WBFortress atlas);
x -42.03..30.01, y -27.60..28.27, z -0.25..123.77. The mesh hangs on a bone turned 180 degrees:
the model's +x is the mesh's -x, so the game's camera looks at the mesh's -x and +y sides. The
shaft: about (2.5, -2), x -10..17, y -16..12 from z 28 to 60; the hood flares from there to its
eaves (r ~25 at z 72..84), narrows to r 16 at z 96 about (3, 0.8) and to the forked tip at z 121..124
about (2, -1.6). The door and ramp: x < -12, |y| < 10, the porch over them to z 24: nothing new
there. The lookout: N_WINDOW (EXLightStreaks) casts its streaks out from under the eaves, r up to
37 at z 69..88: nothing new beyond the hood in that band. Lifecycle: WBTower_A (construction), _D1,
_D2, _D3. House colour: WBHCTower.
"""
from sagekit.building import Building

from ..style import GoblinStyle

HOOD = (3.0, 0.8)                             # the hood's axis above the eaves
TIP = (2.0, -1.6, 121.0)
SPIKE_TOP, SKULL_Z, SKULL_S = 144.5, 132.5, 5.2
SHAFT = (2.5, -2.0)
# the hood's outline at z 99.2 (measured; the band's top edge: the hood narrows upward)
HOOD_99 = [(-12.1, -15.2), (19.4, -8.9), (13.1, 4.2), (12.0, 6.0), (2.2, 16.6), (-5.8, 8.2), (-10.5, 0.0)]
BANNER = ((-8.3, 3.8), (-9.9, -4.6), 57.0, 7.0, 19.0)    # the shaft's -x face (a, b), top, width, length


class SentryTower(Building):
    style = GoblinStyle()
    source = "WBTower"
    target = "DBTOWER"
    sheet = "WBTower.tga"
    sheet_normal = "WBTower_NRM.tga"
    own_textures = {"WBTower.tga": "WBToweH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    facet_islands = 8                       # the Goblin kit's unwrap overlaps a little: seams at EA's islands and 8-degree turns
    views = {
        "rts": ((6.0, -0.3, 66.0), 339, 50, -38, 50),
        "close": ((0.0, 0.0, 66.0), 330, 18, -38, 45),
        "ingame": ((6.0, -0.3, 61.8), 770, 53, -62, 50),
    }

    def design(self, kit):
        return self._hood(kit) + self._shaft(kit) + self._foot(kit)

    @staticmethod
    def _hood(kit):
        import math

        from ..arrow_den import pad
        V, Z = kit.V, kit.Z
        out = pad.band(kit, HOOD_99, 98.3, 1.8, th=1.2, inner=3.0, rivets=1, center=HOOD, closed=True)
        out += kit.horn_crown(V((HOOD[0], HOOD[1], 0)), 102.0, 10.5, 4, 25.0, 2.7, rise=0.85, lean=0.4,
                              phase=math.radians(35), k=6, n=5)
        for i in range(4):                      # small tusks between the horns, above the lookout
            a = math.radians(80 + 90 * i)
            rad = V((math.cos(a), math.sin(a), 0))
            base = V((HOOD[0], HOOD[1], 93.0)) + rad * 15.5
            out += kit.tusk(base, rad + Z * 0.5, rad * 0.3 + Z, 7.5, 0.9, n=4, k=5)
        tip = V(TIP)
        top = V((TIP[0] - 1.0, TIP[1] + 0.6, SPIKE_TOP))
        path = [tip - Z * 6.0, tip, tip.lerp(top, 0.45), top]
        out.append(kit.tube(path, [1.9, 1.7, 1.25, 0.0], "iron", k=6, cap0="iron", cap1=None))
        c = tip.lerp(top, (SKULL_Z - TIP[2]) / (SPIKE_TOP - TIP[2]))
        out += kit.skull(c, V((-0.8, 0.6, 0)), SKULL_S, detail=2)
        for z in (126.0,):
            p = tip.lerp(top, (z - TIP[2]) / (SPIKE_TOP - TIP[2]))
            out.append(kit.tube([p - Z * 0.6, p + Z * 0.6], [1.9, 1.8], "iron", k=6, cap0="iron", cap1="iron"))
        return out

    @staticmethod
    def _shaft(kit):
        V, Z = kit.V, kit.Z
        out = []
        # a skull on a spike out of the shaft, toward the camera's side
        d = V((-0.55, 0.75, 0.3)).normalized()
        base = V((-4.0, 11.6, 42.0))
        out += kit.spike(base, d, 8.0, 0.5, k=4, tip="gore")
        out += kit.skull(base + d * 4.8 + Z * 0.4, V((d.x, d.y, 0)), 3.8, detail=1)
        # a crimson hide nailed to the shaft's +y side under the ledge, war paint on it
        a, b = V((6.7, 11.5, 0)), V((-3.8, 12.2, 0))
        t = (b - a).normalized()
        out += kit.hide_panel(a, t, t.cross(Z), 5.3, 42.0, 6.2, 12.0, d=0.8, mark="hand")
        # the gibbet: an iron arm out of the shaft's +y side under the hood, a cage on a chain
        root, tip = V((8.0, 10.6, 57.5)), V((8.0, 24.3, 58.5))
        out.append(kit.tube([root, root + V((0, 4.0, 1.4)), tip], [0.6, 0.55, 0.45], "iron", k=4, cap0="iron",
                            cap1="iron"))
        out.append(kit.tube([root + V((0, 0.5, -6.0)), root.lerp(tip, 0.45)], [0.4, 0.35], "iron", k=4, cap0="iron",
                            cap1="iron"))
        out += kit.cage(tip - Z * 3.6, 9.0, 2.8, facing=(-0.8, 0.6, 0), chain=3.2)
        (ax, ay), (bx, by), top, w, length = BANNER
        a, b = V((ax, ay, 0)), V((bx, by, 0))
        t = (b - a).normalized()
        out += kit.banner(a, t, t.cross(Z), (b - a).length / 2, top, w, length, d=1.6, mark="eye")
        return out

    @staticmethod
    def _foot(kit):
        from ..arrow_den import pad
        V = kit.V
        box = (-42.03, 30.01, -27.6, 28.27)
        ring = pad.ring(SHAFT, 21.5, 12, 0.2)
        ring = [p for p in ring if not (p[0] < -8 and abs(p[1]) < 13)]      # not in front of the door
        out = pad.skirt(kit, ring, SHAFT, r=2.6, h=2.4, pitch=3.6, out=1.0, seed=23, box=box, closed=False)
        out += kit.skull_pile(V((-17.0, 17.5, 0.0)), 3.2, 4, 2.4, seed=3, face=(-0.8, 0.6, 0))
        out += kit.skull_pile(V((-15.0, -18.5, 0.0)), 3.0, 3, 2.3, seed=5, face=(-0.9, 0.3, 0))
        return out

    def decals(self):
        from ..paint import goblin_layers
        tip = TIP
        anchors = [(tip[0], tip[1], SKULL_Z - 1.5, 2.2, 9.0), (-6.2, 14.4, 43.0, 1.8, 7.0),
                   (-17.0, 17.5, 0.8, 2.6, 2.0), (-15.0, -18.5, 0.8, 2.6, 2.0)]
        return [goblin_layers()["Gore"](anchors)]

    def emphasis(self, c, n):
        return 1.3 if c.z > 90 else 1.0
