"""The Mordor citadel's four towers below their crowns (Blender side): witch-light in the flutes and
great chains slung from crown to crown.

EA's towers (MBFORTRESS mesh coordinates, measured 2026-09-30): axes at (+-41.75, +-42.5); a star
shaft of eight knife ribs at 0, 45, .. degrees (r 14 at z 77 to r 9 at z 115) with deep V flutes
between them, their floors at 22.5 + 45k degrees from r 7.6 (z 74.8) to r 6.0 (z 104.8). The
crowns above are ours (crown.py).

    slits       a tall pointed lancet (z 80..95) on the floor of each flute the RTS camera sees,
                leaning with it: unlit windows (the palette's dim ember), but on every tower the one
                pair facing the camera keeps the Morgul witch-light, the same accent on all four (Max,
                pass 7: far less green; "why only green on one?" when the back tower alone had it)
    chains      heavy chains from the back crown to the left and right crowns and from the left
                crown to the front one (z 128, sagging 14..16; the -X one stays above the magma
                cauldrons, z 112). The cages that hung off the towers and this chain were cut in
                pass 4: too small to read at RTS
"""
import math

from mathutils import Vector as V

from .crown import TOWERS

FLUTE = ((7.6, 74.8), (6.0, 104.8))           # a flute's floor: (r, z) at its foot and head
CAMERA = V((0.788, -0.616, 0))                # toward the RTS camera (azimuth -38 degrees)
ANCHOR = 128.0                                # the chains hang from the crowns' sheaths


def flute_r(z):
    (r0, z0), (r1, z1) = FLUTE
    return r0 + (r1 - r0) * (z - z0) / (z1 - z0)


def slits(kit):
    out = []
    lean = -(FLUTE[1][0] - FLUTE[0][0]) / (FLUTE[1][1] - FLUTE[0][1])       # the floor leans in 0.053 per unit
    for cx, cy in TOWERS.values():
        for k in range(8):
            a = math.radians(22.5 + 45 * k)
            n = V((math.cos(a), math.sin(a), 0))
            if n.dot(CAMERA) < -0.3:
                continue
            t = V((-n.y, n.x, 0))
            base = V((cx, cy, 0)) + n * flute_r(80.0)
            tag = "witch" if n.dot(CAMERA) > 0.8 else "slit"      # every tower's pair facing the camera
            out += kit.witch_slit(base, t, n, 0.0, 80.0, 2.6, 15.0, d0=-1.0, d1=1.6, bat=lean, sill=False, tag=tag)
    return out


def chains(kit):
    (bx, by), (lx, ly), (fx, fy), (rx, ry) = (TOWERS[k] for k in ("back", "left", "front", "right"))
    heavy = dict(link=5.2, w=1.8, th=0.65)
    out = []
    solids, _ = kit.hung_chain(V((bx + 13.2, by, ANCHOR)), V((rx - 13.2, ry, ANCHOR)), 16.0, **heavy)
    out += solids
    solids, _ = kit.hung_chain(V((bx, by - 13.2, ANCHOR)), V((lx, ly + 13.2, ANCHOR)), 14.0, **heavy)
    out += solids
    solids, _ = kit.hung_chain(V((lx + 13.2, ly, ANCHOR)), V((fx - 13.2, fy, ANCHOR)), 16.0, **heavy)
    out += solids
    return out


def build(kit):
    return slits(kit) + chains(kit)
