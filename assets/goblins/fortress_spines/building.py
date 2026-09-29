"""The Goblin citadel's razor spines (WildFortressCitadel, FORTRESS_IMPROVEMENT_4): EA's ring kept
whole - the banded ring round the citadel's foot, its flat spikes fanning out along the ground,
the leaning uprights - and made a killing ground in blood, iron and bone: skulls driven onto six of
the tall uprights, bleached tusks in iron collars rising out of the ring between them, chevaux de
frise (logs with sharpened stakes crossed through them), and an impaled skeleton on a stake at each side and at
the back. No banner (the cap for the spines is 0: the citadel carries three).

EA's facts (WBFRSPIN mesh coordinates, measured; work/measure.json): WBFRSpin, 736 triangles on
WBFortress.tga (own copy WBFortresD.tga); x -76.52..77.32, y -73.50..73.63, z 0..13.83. The ring
(r 52..60, z 2..5, a fan to the centre under the citadel) is open at the gate (x > 50, |y| < 12);
38 uprights lean out from its top (bases r ~56, z 4.7) to tips at r 63..67, z 10.6..13.8 (the eight
tallest at +-16, +-73, +-107 and +-164 degrees); 29 flat spikes lie out to r 72..80 on the ground.
Shown with the citadel, whose pieces it must miss: the gate's ramp and doors (x > 44, |y| < 17),
its tusks, skull piles, impaled skeletons and banners (x > 45, |y| < 36), and the four spire
columns at (+-44.2, +-44.2) (r 3..5 below z 20). Nothing new goes there. `max_z_growth` 0.35: the
impaled skeletons stand to z 18.6, far under the citadel's walls (z 42).
Lifecycle: WBFRSpin_A (construction), _D2, _D3. House colour: WBHCFortress's (no cloth here).
"""
from sagekit.building import Building

from ..style import GoblinStyle

SKULLS = [73, 107, 164, -164, -107, -73]            # the tall uprights that carry a skull (degrees)
TUSKS = [56, 82, 98, 124, 142, 176, -176, -142, -124, -98, -82, -56]
IMPALED = [(90, 70.0), (-90, 70.0), (180, 71.0)]    # (angle, radius)
STAKES = [36, 66, 115, 153, -153, -115, -66, -36]                          # crossed-stake barricades


def pol(a, r, z=0.0):
    import math

    from mathutils import Vector as V
    a = math.radians(a)
    return V((r * math.cos(a), r * math.sin(a), z))


class FortressSpines(Building):
    style = GoblinStyle()
    source = "WBFRSpin"
    target = "WBFRSPIN"
    sheet = "WBFortress.tga"
    sheet_normal = "WBFortress_NRM.tga"
    own_textures = {"WBFortress.tga": "WBFortresD.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    facet_islands = 8                       # the Goblin kit's unwrap overlaps a little: seams at EA's islands and 8-degree turns
    parts = ("ModuleTag_DrawSpines",)
    max_z_growth = 0.35
    views = {
        "rts": ((0.4, 0.1, 6.9), 469, 50, -38, 50),
        "close": ((20.0, -30.0, 6.0), 150, 26, -38, 45),
        "ingame": ((0.4, 0.1, 6.9), 1067, 53, -62, 50),
    }

    def design(self, kit):
        V, Z = kit.V, kit.Z
        out = []
        # skulls driven onto the tall uprights (their bases 0.87 of the tip's radius, z 4.7)
        for a in SKULLS:
            tip = pol(a, 66.7 if abs(abs(a) - 164) < 1 else 65.0, 13.8)
            base = V((tip.x * 0.87, tip.y * 0.87, 4.7))
            p = base.lerp(tip, 0.62)
            out += kit.skull(p, V((tip.x, tip.y, 0)), 3.2, detail=1)
            out.append(kit.tube([p - Z * 1.0, p - Z * 2.6], [0.5, 0.4], "gore", k=4, cap0="gore", cap1="gore"))
        # bleached tusks rising out of the ring's top, leaning out
        for i, a in enumerate(TUSKS):
            base = pol(a, 58.5, 3.8)
            rad = pol(a, 1.0)
            out += kit.tusk(base, rad * 0.7 + Z, rad * 1.0 + Z * 0.35, 9.5 - (i % 2) * 1.5, 0.9, n=5, k=5)
        # chevaux de frise: a log along the ring with pairs of sharpened stakes crossed through it
        for i, a in enumerate(STAKES):
            p, q = pol(a - 4.0, 67.0, 3.0), pol(a + 4.0, 67.0, 3.0)
            out += kit.pole(p, q, 0.7)
            for j, f in enumerate((0.15, 0.5, 0.85)):
                m = p.lerp(q, f)
                rad = V((m.x, m.y, 0)).normalized()
                for e in (-1, 1):
                    foot = m - rad * e * 2.4 - Z * 2.5
                    top = m + rad * e * 3.2 + Z * 5.0
                    out += kit.stake(foot, top, 0.36, tip="gore" if (i + j + e) % 3 == 0 else None)
            out += kit.lashing(p.lerp(q, 0.5), q - p, 0.7, turns=1, w=0.5)
        for a, r in IMPALED:
            base = pol(a, r)
            out += kit.impaled(base, 16.2, 8.0, facing=pol(a, 1.0))
        return out

    def decals(self):
        from ..paint import goblin_layers
        anchors = []
        for a in SKULLS:
            tip = pol(a, 65.5, 13.8)
            p = pol(a, 65.5 * (0.87 + 0.13 * 0.62), 4.7 + 9.1 * 0.62)
            anchors.append((p.x, p.y, p.z - 1.2, 1.8, 6.0))
        for a, r in IMPALED:
            p = pol(a, r + 0.6, 9.0)
            anchors.append((p.x, p.y, p.z, 2.0, 8.0))
        return [goblin_layers()["Gore"](anchors)]
