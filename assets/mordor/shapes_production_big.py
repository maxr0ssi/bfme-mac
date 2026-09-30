"""The Mordor production buildings' big pieces (Blender side), pass 2: the one bold new mass each
building gets, readable at the RTS camera. Module functions of the kit, like shapes_production.py.

Fire never sits on a perched bowl (the citadel's pass 5 lesson: a mass on a support reads stuck
on). It comes out of grounded structure: a stack of black basalt rising from the ground, its mouth
opening into a claw of spikes rising from INSIDE it round the fire, as the citadel's crowns.

    claw_stack(c, r, z1, H, kind)     a jagged, battered basalt stack from the ground (z0) to its
                                      flared mouth at z1: iron bands at two setbacks, ember slits and
                                      a lava seam on the face toward `face`, the claw inside its mouth
                                      (spikes H tall), the fire `kind` in the throat, `smoke` above
    siege_tower(c, t, w, h, built)    a half-built orc siege tower: four raking timber posts, floor
                                      bands, braces, iron plates up the front (t) to `built`, a
                                      raised drawbridge with barbed teeth, the top storey bare frame
    smoke_rack(p, q, h, rows)         a great gantry of charred timber from p to q: two A-frames and
                                      tie beams, `rows` bars of meat hooks with heavy dark carcasses
    log_ramp(c, t, length, r, rows)   felled trunks stacked in a stepped pile rising along t, pinned
                                      by stakes, a chain across it
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft, prism_uz

from .shapes_production import _jit, _v, claw

CAMERA = (0.79, -0.62)                      # toward the RTS camera (azimuth -38 degrees)


def _ring(c, r, z, k, seed, off):
    return [V((c[0] + off.x + r * _jit(seed, i, 0.14) * math.cos(2 * math.pi * i / k + 0.2),
               c[1] + off.y + r * _jit(seed, i, 0.14) * math.sin(2 * math.pi * i / k + 0.2), z)) for i in range(k)]


def claw_stack(kit, c, r, z1, H, z0=0.0, n=7, s=1.6, kind="chimney", smoke="plume", k=7, seed=0.0,
               lean=(0.0, 0.0), face=CAMERA, slits=(0.5, 0.78)):
    """A basalt stack at c (x, y) from z0 to its mouth at z1, r across at its foot; see the module."""
    h = z1 - z0
    lean = V((lean[0], lean[1], 0))
    prof = [(0.0, 1.0), (0.1, 0.92), (0.36, 0.8), (0.37, 0.86), (0.39, 0.8), (0.7, 0.68), (0.71, 0.74),
            (0.73, 0.68), (0.9, 0.62), (1.0, 0.86)]
    rings = [_ring(c, r * q, z0 + h * f - (0.5 if f == 0 else 0), k, seed, lean * f) for f, q in prof]
    top = V((c[0], c[1], z1)) + lean
    rings += [_ring(top, r * 0.6, z1 + 0.3, k, seed, V((0, 0, 0))), _ring(top, r * 0.52, z1 - 2.0, k, seed, V((0, 0, 0)))]
    tags = ["stoneA", "stoneA", "iron", "iron", "stoneA", "iron", "iron", "stoneA", "stoneB", "trim", "iron"]
    out = [loft(rings, tags, cap0=("stoneA", False), cap1=("ember", True))]
    fd = V((face[0], face[1], 0)).normalized()               # the side facing the camera: slits and a seam
    ring0 = rings[0]
    j = max(range(k), key=lambda i: ((ring0[i] + ring0[(i + 1) % k]) / 2 - V((c[0], c[1], ring0[i].z))).normalized().dot(fd))
    pts = []
    for f in (0.06, 0.2, 0.33, 0.45, 0.6):
        rr = rings[min(range(len(prof)), key=lambda i: abs(prof[i][0] - f))]
        a, b = rr[j], rr[(j + 1) % k]
        g = 0.35 + 0.3 * math.sin(f * 17.0 + seed)
        p = a.lerp(b, g)
        pts.append(V((p.x, p.y, z0 + h * f)))
    nrm = ((ring0[j] + ring0[(j + 1) % k]) / 2 - V((c[0], c[1], ring0[j].z)))
    nrm = V((nrm.x, nrm.y, 0)).normalized()
    out += kit.face_crack(pts, nrm, w=r * 0.16, depth=0.35)
    for ri, rj in ((4, 5), (7, 8))[:len(slits)]:                # pointed ember slits on the side faces
        f0, f1 = prof[ri][0], prof[rj][0]
        bat = (prof[ri][1] - prof[rj][1]) * r / ((f1 - f0) * h)
        for jj in ((j + 2) % k, (j - 2) % k):
            a, b = rings[ri][jj], rings[ri][(jj + 1) % k]
            m = (a + b) / 2
            t = V((b.x - a.x, b.y - a.y, 0)).normalized()
            nn = V((t.y, -t.x, 0))
            if nn.dot(V((m.x - c[0], m.y - c[1], 0))) < 0:
                nn = -nn
            zc = z0 + h * f0 + 0.6
            out += kit.witch_slit(V((m.x, m.y, 0)) - Z * 0, t, nn, 0.0, zc, r * 0.26, h * (f1 - f0) * 0.7, d0=-1.0,
                                  d1=0.35, bat=bat, sill=False, tag="ember")
    out += claw(kit, (top.x, top.y), r * 0.64, z1 - 1.6, H, n=n, s=s, r1=r * 0.3, phase=seed * 40.0 + 90.0 / n)
    kit.fire(top + Z * 0.2, kind)
    if smoke:
        kit.fire(top + Z * (H * 0.7), smoke)
    return out


def siege_tower(kit, c, t, w=7.0, h=58.0, built=0.62, seed=0.0):
    """A half-built orc siege tower at c facing t; see the module. w: half its width at the foot."""
    c, t = _v(c), _v(t).normalized()
    n = V((-t.y, t.x, 0))
    top_w = w * 0.72
    P = lambda u, v, z: c + t * (u * (w - (w - top_w) * z / h)) + n * (v * (w - (w - top_w) * z / h)) + Z * z  # noqa: E731
    out = []
    for u, v in ((1, 1), (1, -1), (-1, 1), (-1, -1)):          # the raking corner posts
        out.append(kit.beam(P(u, v, 0.3), P(u, v, h), 0.75, "wood"))
    floors = [h * f for f in (0.08, 0.3, 0.52, 0.74, 0.96)]
    for z in floors:                                           # floor bands round all four sides
        for (u0, v0), (u1, v1) in (((1, 1), (1, -1)), ((-1, 1), (-1, -1)), ((1, 1), (-1, 1)), ((1, -1), (-1, -1))):
            out.append(kit.beam(P(u0, v0, z), P(u1, v1, z), 0.45, "wood"))
    for i in range(len(floors) - 1):                           # braces on the sides
        z0, z1 = floors[i], floors[i + 1]
        for v in (1, -1):
            out.append(kit.beam(P(1, v, z0), P(-1, v, z1), 0.3, "wood"))
        out.append(kit.beam(P(-1, 1, z0), P(-1, -1, z1), 0.3, "wood"))
    zb = h * built
    for i in range(4):                                         # iron plates up the front, to `built`
        z0, z1 = zb * i / 4 + 0.4, zb * (i + 1) / 4
        wz = w - (w - top_w) * z1 / h
        a = c + t * (w - (w - top_w) * (z0 + z1) / 2 / h + 0.45)
        out += kit.plate(a, n, t, -wz + 0.3, wz - 0.3, z0, z1 - 0.2, d=0.0, th=0.5, pitch=2.4, rivet=0.25)
    for s in (-1, 1):                                          # plates on the sides, lower half
        for i in range(2):
            z0, z1 = zb * i / 3 + 0.4, zb * (i + 1) / 3
            a = c + n * (s * (w - (w - top_w) * (z0 + z1) / 2 / h + 0.45))
            out += kit.plate(a, t, n * s, -w * 0.8, w * 0.8, z0, z1 - 0.2, d=0.0, th=0.45, pitch=2.8, rivet=0.25)
    zd = floors[3]                                             # the drawbridge, raised against the front
    wd = w - (w - top_w) * zd / h
    a = c + t * (wd + 1.2)
    out.append(prism_uz(a, n, t, [(-wd * 0.75, zd), (wd * 0.75, zd), (wd * 0.75, zd + 11.0), (-wd * 0.75, zd + 11.0)],
                        -0.3, 0.5, ["wood"] * 4, "wood", "wood"))
    for i in range(5):
        u = -wd * 0.6 + wd * 1.2 * i / 4
        out.append(kit.beam(a + n * u + Z * (zd + 10.8) + t * 0.3, a + n * u + Z * (zd + 13.5) + t * 1.0, 0.3,
                            "steel", 0.0))
    for s in (-1, 1):
        out += kit.chain(P(0.9, s * 0.8, floors[4]), a + n * (s * wd * 0.7) + Z * (zd + 10.5), link=1.3, w=0.45, th=0.18)
    for u, v in ((1, 1), (1, -1), (-1, 1), (-1, -1)):          # steel spikes out of the post heads
        p = P(u, v, h)
        out.append(kit.beam(p, p + (t * u + n * v) * 1.2 + Z * 4.2, 0.4, "steel", 0.0))
    return out


def smoke_rack(kit, p, q, h=26.0, rows=2, hooks=5, seed=0.0):
    """A great gantry of charred timber from p to q (feet on the ground); see the module."""
    p, q = _v(p), _v(q)
    t = (q - p).normalized()
    n = V((-t.y, t.x, 0))
    L = (q - p).length
    out = []
    for e in (p, q):                                           # A-frames, raking legs, iron-shod heads
        for s in (-1, 1):
            out.append(kit.beam(e + n * (s * h * 0.26) + Z * 0.3, e + Z * h, 0.8, "wood"))
        out.append(kit.beam(e + n * (-h * 0.16) + Z * h * 0.4, e + n * (h * 0.16) + Z * h * 0.4, 0.5, "wood"))
        out.append(kit.beam(e + Z * (h - 0.6), e + Z * (h + 3.5) - t * 0.6, 0.45, "steel", 0.0))
    bars = [(0.0, h - 0.5)] + [(s * h * 0.12, h * 0.62) for s in ((-1, 1) if rows > 1 else ())]
    for off, z in bars:
        out.append(kit.beam(p + n * off + Z * z, q + n * off + Z * z, 0.65, "wood"))
    for bi, (off, z) in enumerate(bars):
        for i in range(hooks):
            f = (i + 0.5) / hooks
            top = p.lerp(q, f) + n * off + Z * (z - 0.6)
            drop = 1.2 + 1.4 * ((i * 7 + bi * 3) % 3) / 2
            out += kit.chain(top, top - Z * drop, link=1.2, w=0.45, th=0.18)
            b = top - Z * (drop + 0.6)
            out += kit.hook(b + Z * 0.6, 1.6, chain=0.0)
            if (i + bi) % 3 != 2:                                  # a carcass, split, the ribs showing
                ln = 6.5 + 1.5 * math.sin(i * 1.7 + seed)
                out.append(kit.tube([b, b - Z * ln * 0.45 + n * 0.4, b - Z * ln], [1.2, 1.7, 0.8], "soot", k=6,
                                    cap0="soot", cap1="soot", phase=0.3 * i))
                out.append(kit.tube([b - Z * 1.2 - t * 0.6, b - Z * ln * 0.7 - t * 0.9], [0.8, 0.6], "trim", k=4,
                                    cap0="trim", cap1="trim"))
    del L
    return out


def log_ramp(kit, c, t, length=18.0, r=1.9, rows=5, seed=0.0):
    """Felled trunks `length` long (lying square to t) in a pile of `rows` courses at c, and three
    long skids leaning from the ground along t up onto its top (the ramp the logs roll down to the
    saw); iron stakes pin the pile's ends, a chain lashes it."""
    c, t = _v(c), _v(t).normalized()
    ax = V((-t.y, t.x, 0))                                     # the logs' axis
    out = []
    for j in range(rows):
        cnt = rows - j
        for i in range(cnt):
            u = (i - (cnt - 1) / 2) * r * 2.02
            m = c + t * u + Z * (r + j * r * 1.72) + ax * (0.4 * math.sin(i * 2.1 + j + seed))
            out.append(kit.tube([m - ax * (length / 2), m + ax * (length / 2)], [r, r * 0.9], "wood", k=6, cap0="wood",
                                cap1="wood", phase=0.3 * i))
    top = c + Z * (rows * r * 1.72 + 0.2)
    for e in (-1, 0, 1):                                       # the skids
        f = c - t * (rows * r * 1.02 + rows * r * 2.2) + ax * (e * length * 0.3) + Z * 0.8
        out.append(kit.beam(f, top - t * (r * 0.5) + ax * (e * length * 0.3), 0.6, "wood"))
    for s in (-1, 1):
        for e in (-1, 1):
            f = c + ax * (s * (length / 2 - 1.2)) + t * (e * (rows * r + 0.8))
            out += kit.stake(f + Z * 0.6, V((e * t.x * 0.15, e * t.y * 0.15, 1.0)), rows * r * 1.9, r=0.5, barbs=1,
                             seed=seed + s + e)
    out += kit.chain(c - t * (rows * r) + Z * r * 1.2, top + Z * 0.8, link=1.4, w=0.5, th=0.2)
    out += kit.chain(top + Z * 0.8, c + t * (rows * r) + Z * r * 1.2, link=1.4, w=0.5, th=0.2)
    return out
