"""The lava moat (Blender side): EA's ring of rock and its lava kept whole; the moat made cruel.

    rafts       dark crusts of cooling slag drifting on EA's lava (its plane OBJECT01 at z 2.29 over
                the channel's floor at z 1): two or three to every 10 degrees of the channel
    teeth       jagged basalt teeth along the outer bank's crest, leaning out, lava glowing in the
                crack at each one's foot
    stakes      crooked impaling stakes (two barbs, a steel point) leaning out from the outer bank
    fire        thin smoke rising off the lava and embers (EA's systems, orange)

EA's moat measured by raycast (2026-09-30): at every 5 degrees the outer edge r_out (90.5..108.4:
the ring follows the square citadel), the inner bank sloping from z 9..12 at the wall's foot to the
channel's floor (z 1.0) about r_out - 21, the outer bank's crest (z 3..10) about r_out - 11.5,
sloping out to the ground at r_out. The ramp crosses it at +X (no bank within 10 degrees of it).

Kept clear: the citadel's lava channels at its wall feet, the ramp and its stakes (no raft within 22
degrees of +X, no tooth or stake within 20), and the expansions' pads (EA's base file: at -90, 180, 90, +-45 and +-135 degrees,
114.5 out on the sides and 129 on the diagonals; their bodies reach back to 48.7 from the centre,
up to 22.7 to each side): the teeth and stakes stand only between them (the rafts, flat on the
lava, run under them).
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import prism_uz

# angle: (outer edge r_out, the crest's z at r_out - 11.5), EA's moat by raycast
RING = {-180: (94.4, 6.8), -175: (95.3, 10.2), -170: (97.1, 6.4), -165: (98.0, 3.6), -160: (97.8, 6.1),
        -155: (98.9, 4.2), -150: (102.3, 3.5), -145: (106.9, 7.1), -140: (107.4, 5.1), -135: (108.0, 7.6),
        -130: (106.6, 7.8), -125: (105.6, 4.4), -120: (103.4, 3.5), -115: (100.6, 4.8), -110: (97.5, 5.3),
        -105: (93.1, 4.1), -100: (90.5, 5.8), -95: (91.5, 3.6), -90: (93.0, 3.4), -85: (91.7, 3.8), -80: (90.9, 5.1),
        -75: (92.4, 4.1), -70: (94.4, 6.5), -65: (97.4, 6.9), -60: (101.7, 3.7), -55: (105.3, 3.8), -50: (105.3, 6.4),
        -45: (106.0, 3.8), -40: (105.7, 6.0), -35: (105.4, 5.9), -30: (100.4, 3.8), -25: (96.6, 3.4), -20: (93.9, 2.8),
        -15: (92.0, 2.3), 15: (93.7, 3.8), 20: (98.0, 7.6), 25: (102.0, 3.8), 30: (103.6, 3.5), 35: (106.0, 7.1),
        40: (104.9, 4.3), 45: (104.1, 1.5), 50: (105.7, 4.9), 55: (108.4, 4.4), 60: (105.4, 3.8), 65: (101.2, 4.9),
        70: (98.3, 8.0), 75: (96.8, 6.3), 80: (95.8, 4.4), 85: (92.8, 3.5), 90: (90.9, 3.4), 95: (92.5, 4.6),
        100: (94.8, 4.4), 105: (95.3, 5.0), 110: (95.9, 7.9), 115: (98.6, 5.8), 120: (103.7, 3.5), 125: (108.4, 3.6),
        130: (107.2, 6.8), 135: (107.1, 4.5), 140: (106.0, 4.7), 145: (106.1, 7.5), 150: (101.8, 3.6), 155: (98.8, 4.5),
        160: (94.8, 7.8), 165: (91.6, 4.6), 170: (90.6, 3.2), 175: (92.0, 3.7)}
PADS = (-135, -90, -45, 45, 90, 135, 180)
LAVA = 2.29                                     # EA's lava plane (OBJECT01)


def free(a, margin=16.0):
    """Clear of the ramp (+X, 20 degrees) and of every pad's corridor (`margin` degrees)."""
    if abs(a) < 20:
        return False
    return all(abs((a - p + 180) % 360 - 180) > margin for p in PADS)


def at(a, r, z=0.0):
    t = math.radians(a)
    return V((r * math.cos(t), r * math.sin(t), z))


def raft(c, r, seed):
    """A flat, irregular crust of slag floating on the lava (five-sided, its top a little domed)."""
    k = 5
    pts = [(r * (0.75 + 0.3 * math.sin(seed * 3.7 + i * 2.1)), 2 * math.pi * i / k + seed) for i in range(k)]
    ring = lambda s, z: [c + V((rr * s * math.cos(t), rr * s * math.sin(t), z)) for rr, t in pts]  # noqa: E731
    from sagekit.blender.geometry import loft
    return loft([ring(1.0, LAVA - 0.5), ring(1.0, LAVA + 0.25), ring(0.6, LAVA + 0.55)], [["soot"] * k] * 2,
                cap0=("soot", False), cap1=("soot", True))


def rafts(kit):
    """Crusts spread across the channel's width (r_out - 26 .. r_out - 16), one to three to every 5
    degrees, 1.2 to 3.2 across; a glowing bubble of lava here and there between them."""
    out = []
    for a in sorted(RING):
        if abs(a) < 25:                             # the ramp's stakes stand at 17.7 and 19.2 degrees
            continue
        rmid = RING[a][0] - 21.0
        for j in range(1 + int(abs(math.sin(a * 0.91)) * 2.2)):
            s = a * 0.37 + j * 1.9
            aa = a + 4.6 * (0.5 + 0.5 * math.sin(s * 3.1)) - 2.3
            rr = rmid + 4.6 * math.sin(s * 1.7 + j)
            out.append(raft(at(aa, rr, 0), 1.2 + 2.0 * math.sin(s * 2.3) ** 2, s))
        if a % 15 == 0:
            out.append(kit.facet_lump(at(a + 2.5, rmid - 1.5 * math.sin(a), LAVA + 0.1), 0.9, "flame"))
    return out


def tooth(kit, a, lean_out=0.35, h=5.0, w=2.2, seed=0.0):
    """A jagged basalt tooth on the outer bank's crest at angle a, leaning out."""
    rout, cz = RING[a]
    r = rout - 11.5
    n = at(a, 1.0).normalized()
    t = V((-n.y, n.x, 0))
    base = at(a, r)
    poly = [(-w / 2, cz - 1.5), (w / 2, cz - 1.5), (w * 0.3, cz + h * 0.7), (0.05 * w, cz + h), (-w * 0.4, cz + h * 0.55)]
    out = [prism_uz(base, t, n, poly, -w * 0.45, w * 0.45, ["rock"] * 5, "rock", "rock", bat=-lean_out)]
    out.append(prism_uz(base + n * (w * 0.5), t, n, [(-w * 0.35, cz - 1.2), (w * 0.35, cz - 1.2), (0.0, cz + 0.4)],
                        -0.2, 0.25, ["ember"] * 3, "ember", "soot"))
    return out


def build(kit):
    out = rafts(kit)
    for a in sorted(RING):
        if free(a, 16.0):
            out += tooth(kit, a, h=5.5 + 2.0 * ((a // 5) % 3 == 0), w=2.6, seed=a)
    for a in range(-180, 180, 5):
        if not free(a + 2.5, 17.0) or (a // 5) % 2:
            continue
        rout, cz = RING[a]
        c = at(a + 2.5, rout - 9.0, cz - 1.0)
        d = (at(a + 2.5, 1.0).normalized() * 0.38 + V((0, 0, 1))).normalized()
        out += kit.stake(c, d, min(13.5, 19.8 - cz), r=0.7, barbs=2, seed=a * 0.1)
    for a, kind in ((-112, "smoke"), (157, "smoke"), (67, "embers"), (-67, "embers"), (-157, "embers")):
        kit.fire(at(a, RING[a - a % 5 if a % 5 else a][0] - 21.0, LAVA + 0.3), kind)
    return out
