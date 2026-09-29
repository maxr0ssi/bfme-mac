"""The Goblin kit's bone and gore (a mixin of GoblinShapes, assets/goblins/shapes.py): bleached
white trophies that give the dark faction its contrast, and the dried blood that goes with them.

Skulls and skeletons are built in a local frame: `facing` is the horizontal direction the face
looks, sizes are in world units. Their eye sockets, noses and mouths are "socket" (black); bone
is "bone" (bleached white), blood "gore" (dark crimson), cords "rope".

    bone(p, q, r)                      a long bone with knobbed ends
    skull(c, facing, s, detail)        a skull about s tall centred on c: domed cranium, scowling
                                       brow, real black sockets and nose, cheekbones, teeth, a jaw
                                       (detail 0/1/2 by size; tusks=True for a goblin's)
    horned_skull(c, facing, s)         a beast's skull with two curling horns (a troll's, a warg's)
    skull_on_spike(base, height, s)    an iron spike with a skull driven down onto it
    skull_pile(c, r, count, s)         a heap of skulls and a few long bones
    spine(p, q, r)                     a string of vertebrae
    ribcage(c, facing, s)              a spine and three pairs of curved ribs
    skeleton(c, facing, h, pose)       a whole skeleton, pelvis at c: "hang" (arms and legs
                                       dangling) or "slump" (sitting, legs forward)
    impaled(base, height, h, facing)   a sharpened stake with a skeleton lashed to it
    totem(base, height, s, facing)     a pole crowned by a horned skull, a bone crossbar with
                                       skulls hung from it on cords, rope lashings
    carcass(top, length, r)            a hide sack hung on a hook, its cut end bloody
    drip(a, t, n, u, z, length, w, d)  a run of blood down a wall face
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft, prism_uz


# The skull, in units of its size s (u across, d forward, z up from the jaw's hinge line): a domed
# cranium set back behind a face of separate bones, so the eye sockets and the nose are real holes
# (black plates deep behind the brow, the cheekbones and the nasal bridge), exaggerated to read small.
# Cranium rings (z, half-width, half-depth, forward offset): the face's back at about d 0.3
CRANIUM = [(0.04, 0.30, 0.30, -0.02), (0.60, 0.50, 0.50, -0.20), (0.86, 0.45, 0.48, -0.14),
           (1.03, 0.16, 0.2, -0.14)]
CRANIUM_SMALL = [CRANIUM[0], CRANIUM[1], (0.97, 0.3, 0.34, -0.14)]
CRANIUM_RING = [(-0.75, 1.0), (0.75, 1.0), (1.0, 0.2), (0.7, -0.8), (-0.7, -0.8), (-1.0, 0.2)]    # (u, d): a broad face
# face bones: (u, z) polygon, d0, d1, tag; mirrored pieces are listed once for u > 0
BROW = ([(0.04, 0.55), (0.46, 0.63), (0.44, 0.76), (0.04, 0.69)], 0.2, 0.6)          # a scowl: low over the nose
SOCKET_BACK = ([(-0.42, 0.34), (0.42, 0.34), (0.42, 0.62), (-0.42, 0.62)], 0.2, 0.31)
BRIDGE = ([(-0.06, 0.4), (0.06, 0.4), (0.06, 0.62), (-0.06, 0.62)], 0.26, 0.5)
TEMPLE = ([(0.37, 0.36), (0.5, 0.33), (0.5, 0.62), (0.38, 0.62)], 0.2, 0.47)
CHEEK = ([(0.07, 0.3), (0.5, 0.26), (0.52, 0.38), (0.08, 0.41)], 0.22, 0.54)
MUZZLE = ([(-0.31, 0.1), (0.31, 0.1), (0.34, 0.3), (-0.34, 0.3)], 0.2, 0.46)
NASAL = ([(-0.1, 0.41), (0.1, 0.41), (0.0, 0.16)], 0.2, 0.5)
MOUTH = ([(-0.28, -0.03), (0.28, -0.03), (0.28, 0.11), (-0.28, 0.11)], 0.18, 0.36)
CHIN = ([(-0.22, -0.17), (0.22, -0.17), (0.26, -0.04), (-0.26, -0.04)], 0.22, 0.47)
TEETH_UP = [-0.2, -0.07, 0.07, 0.2]


class Frame:
    """A local frame: P(u, d, z) = origin + side*u + fwd*d + up*z."""

    def __init__(self, origin, facing, up=Z):
        self.o, self.up = V(origin), V(up).normalized()
        f = V(facing) - self.up * V(facing).dot(self.up)
        self.fwd = f.normalized() if f.length > 1e-6 else V((1, 0, 0))
        self.side = self.up.cross(self.fwd).normalized()

    def P(self, u, d, z):
        return self.o + self.side * u + self.fwd * d + self.up * z

    def slab(self, poly, d0, d1, tag, back=None):
        """A convex (u, z) polygon extruded along fwd from d0 to d1: front and sides `tag`."""
        r0 = [self.P(u, d0, z) for u, z in poly]
        r1 = [self.P(u, d1, z) for u, z in poly]
        return loft([r0, r1], [tag], cap0=(back or tag, back is not None), cap1=(tag, True))


class BoneKit:
    # ------------------------------------------------------------------ bones
    def bone(self, p, q, r, k=5, knob=1.7, tag="bone"):
        """A long bone from p to q: a shaft of radius r swelling to knobbed ends."""
        p, q = V(p), V(q)
        d = q - p
        pts = [p, p + d * 0.1, p + d * 0.22, q - d * 0.22, q - d * 0.1, q]
        radii = [r * knob * 0.7, r * knob, r, r, r * knob, r * knob * 0.7]
        return [self.tube(pts, radii, tag, k=k, cap0=tag, cap1=tag)]

    def skull(self, c, facing, s, detail=2, up=Z, tusks=False):
        """A skull about s tall centred on c, looking along `facing`: a domed cranium, a heavy brow,
        deep black eye sockets and nasal cavity framed by the nasal bridge, the temples and the
        cheekbones, a row of upper teeth over a dark mouth and a jaw. detail 2 (big, s > 3): a
        separate lower jaw hinged to the cranium and the temples; 1: the muzzle, nose, mouth and two
        teeth over a chin block; 0 (small, s < 2.5): a plainer cranium, the brow, the sockets, the
        cheekbones and a chin. tusks: two tusks up from the jaw (a goblin's or an orc's). About
        100 / 150 / 210 triangles."""
        up = V(up).normalized()
        F = Frame(V(c) - up * 0.45 * s, facing, up)
        levels = CRANIUM if detail else CRANIUM_SMALL
        rings = [[F.P(x * w * s, fw * s + y * dd * s, z * s) for x, y in CRANIUM_RING] for z, w, dd, fw in levels]
        out = [loft(rings, ["bone"] * (len(rings) - 1), cap0=("bone", True), cap1=("bone", True))]

        def piece(spec, tag="bone", mirror=False, closed=False):
            poly, d0, d1 = spec
            polys = [poly] + ([[(-u, z) for u, z in reversed(poly)]] if mirror else [])
            return [F.slab([(u * s, z * s) for u, z in pg], d0 * s, d1 * s, tag, back=tag if closed else None)
                    for pg in polys]
        out += piece(BROW, mirror=True, closed=True) + piece(SOCKET_BACK, "socket", closed=True) + piece(BRIDGE)
        out += piece(CHEEK, mirror=True, closed=True) + piece(CHIN, closed=True)
        if detail >= 1:
            out += piece(MUZZLE, closed=True) + piece(NASAL, "socket") + piece(MOUTH, "socket", closed=True)
        if detail >= 2:
            out += piece(TEMPLE, mirror=True, closed=True)
        if detail >= 1:
            for u in TEETH_UP[1:3] if detail == 1 else TEETH_UP:
                out.append(F.slab([((u - 0.055) * s, 0.11 * s), ((u + 0.055) * s, 0.11 * s), (u * s, 0.0)],
                                  0.34 * s, 0.46 * s, "bone"))
        if detail >= 2:
            for e in (-1, 1):
                out.append(self.tube([F.P(e * 0.23 * s, 0.3 * s, -0.1 * s), F.P(e * 0.37 * s, -0.04 * s, 0.26 * s)],
                                     [0.07 * s, 0.06 * s], "bone", k=4, cap0="bone", cap1="bone", phase=math.pi / 4))
        if tusks:
            for e in (-1, 1):
                out += self.horn(F.P(e * 0.2 * s, 0.4 * s, -0.08 * s), F.up * 1.0 + F.fwd * 0.3 + F.side * e * 0.2,
                                 F.up * 1.0 - F.fwd * 0.1, 0.55 * s, 0.07 * s, n=3, k=4, root="bone")
        return out

    def horned_skull(self, c, facing, s, horn=1.6, detail=2):
        """A beast's skull (a troll's, a warg's) with two horns curling out and up from its brow,
        horn * s long."""
        F = Frame(V(c) - Z * 0.45 * s, facing)
        out = self.skull(c, facing, s, detail)
        for e in (-1, 1):
            base = F.P(e * 0.46 * s, -0.12 * s, 0.74 * s)
            out += self.horn(base, F.side * e + Z * 0.25, Z * 0.9 + F.fwd * 0.5 + F.side * e * 0.3, horn * s,
                             0.2 * s, n=3, k=5, tip_from=0.35)
        return out

    def skull_on_spike(self, base, height, s, facing=(1, 0, 0), r=None, tag="iron", blood=True):
        """An iron spike `height` tall with a skull driven down onto it (its tip out of the crown),
        and dried blood down the shaft below it."""
        base = V(base)
        r = r or 0.16 * s
        out = self.spike(base, Z, height + 0.95 * s, r, tag=tag, k=4)
        c = base + Z * height
        out += self.skull(c, facing, s, detail=1)
        if blood:
            out.append(self.tube([c - Z * 0.5 * s, c - Z * 1.4 * s], [r * 1.12, r * 0.95], "gore", k=4,
                                 cap0=None, cap1="gore", phase=math.pi / 4))
        return out

    def skull_pile(self, c, r, count, s, seed=3, bones=1, face=None):
        """A heap of `count` skulls about r across the base, facing out (or mostly toward `face`,
        where the camera is), and `bones` long bones."""
        c = V(c)
        out = []
        low = max(2, int(round(count * 0.6)))
        high = max(0, count - low - 1)
        rows = [(low, r * (0.62 if low > 2 else 0.4), 0.68 * s), (high, r * 0.28, 1.4 * s)]
        for i, (m, rad, z) in enumerate(rows):
            for j in range(m):
                a = 2 * math.pi * (j + 0.5 * i) / max(m, 1) + seed
                radial = V((math.cos(a), math.sin(a), 0))
                turn = 0.35 * math.sin(seed * 3.1 + j * 1.7)
                look = radial * math.cos(turn) + Z.cross(radial) * math.sin(turn)
                if face is not None:
                    look = look * 0.45 + V(face).normalized()
                out += self.skull(c + radial * rad + Z * z, look, s, detail=0)
        if count > low + high:
            top = V(face) if face is not None else V((math.cos(seed), math.sin(seed), 0))
            out += self.skull(c + Z * (1.72 * s), top, s * 1.1, detail=1)
        for j in range(bones):
            a = seed * 2.3 + j * 2.4
            d = V((math.cos(a), math.sin(a), 0.18))
            p = c + V((math.cos(a + 1.3), math.sin(a + 1.3), 0)) * r * 0.55 + Z * 0.62 * s
            out += self.bone(p - d * 1.3 * s, p + d * 1.3 * s, 0.13 * s)
        return out

    # ------------------------------------------------------------------ skeletons
    def spine(self, p, q, r, n=None, tag="bone"):
        """Vertebrae from p to q, each a short block with a gap."""
        p, q = V(p), V(q)
        n = n or max(2, int((q - p).length / (r * 2.2)))
        out = []
        for i in range(n):
            a, b = p.lerp(q, (i + 0.1) / n), p.lerp(q, (i + 0.8) / n)
            out.append(self.tube([a, b], [r, r * 0.9], tag, k=4, cap0=tag, cap1=tag, phase=math.pi / 4))
        return out

    def ribcage(self, c, facing, s, pairs=3, spine=True):
        """A ribcage s tall centred on c: the spine behind and `pairs` pairs of curved ribs."""
        F = Frame(c, facing)
        out = []
        if spine:
            out += self.spine(F.P(0, -0.2 * s, -0.55 * s), F.P(0, -0.2 * s, 0.55 * s), 0.07 * s, n=5)
        for i in range(pairs):
            z = 0.35 * s - i * 0.28 * s
            w = 0.38 * s * (1.0 - 0.12 * abs(i - 1))
            for e in (-1, 1):
                pts = [F.P(e * 0.03 * s, -0.2 * s, z), F.P(e * w, -0.08 * s, z - 0.05 * s),
                       F.P(e * w * 0.9, 0.16 * s, z - 0.13 * s), F.P(e * 0.12 * s, 0.3 * s, z - 0.2 * s)]
                out.append(self.tube(pts, [0.05 * s, 0.055 * s, 0.05 * s, 0.035 * s], "bone", k=3, cap0="bone", cap1="bone"))
        return out

    def skeleton(self, c, facing, h, pose="hang"):
        """A skeleton h tall standing, its pelvis at c: "hang" (arms and legs dangling, hung by the
        neck or lashed to a stake) or "slump" (sat against a wall, legs out along facing)."""
        F = Frame(c, facing)

        def P(u, d, z):
            return F.P(u * h, d * h, z * h)
        out = self.ribcage(P(0, 0.0, 0.22), facing, 0.22 * h, pairs=2, spine=False)
        out += self.spine(P(0, -0.04, 0.02), P(0, -0.04, 0.34), 0.03 * h, n=3)
        out += self.skull(P(0, 0.02, 0.43), F.fwd, 0.15 * h, detail=0)
        out.append(self.tube([P(-0.09, -0.02, 0.0), P(0.09, -0.02, 0.0)], [0.035 * h, 0.035 * h], "bone", k=4,
                             cap0="bone", cap1="bone"))
        r = 0.022 * h
        if pose == "hang":
            limbs = [((0.12, 0, 0.31), (0.16, 0.02, 0.12), (0.15, 0.05, -0.05)),
                     ((0.07, 0, 0.0), (0.08, 0.03, -0.24), (0.08, 0.0, -0.48))]
        else:
            limbs = [((0.12, 0, 0.31), (0.18, 0.08, 0.14), (0.14, 0.22, 0.03)),
                     ((0.07, 0, 0.0), (0.1, 0.24, 0.1), (0.1, 0.44, -0.06))]
        for e in (-1, 1):
            for a, b, t in limbs:
                pa, pb, pt = P(e * a[0], a[1], a[2]), P(e * b[0], b[1], b[2]), P(e * t[0], t[1], t[2])
                out.append(self.tube([pa, pb], [r, r], "bone", k=3, cap0="bone", cap1="bone"))
                out.append(self.tube([pb, pt], [r, r * 0.8], "bone", k=3, cap0="bone", cap1="bone"))
        return out

    def impaled(self, base, height, h, facing=(1, 0, 0), r=None):
        """A sharpened timber stake `height` tall with a skeleton h tall lashed to its front, its
        skull at the top, blood down the stake."""
        base, F = V(base), Frame(base, facing)
        r = r or 0.045 * h
        out = self.stake(base, base + Z * height, r)
        pelvis = base + Z * (height - 0.62 * h) + F.fwd * (r + 0.05 * h)
        out += self.skeleton(pelvis, facing, h, "hang")
        for z in (0.2, 0.36):
            out += self.lashing(base + Z * (height - 0.62 * h + z * h), Z, r + 0.06 * h, turns=1, w=0.05 * h)
        out.append(self.tube([base + Z * (height - 0.72 * h), base + Z * (height - 1.15 * h)], [r * 1.1, r * 1.02],
                             "gore", k=5, cap0="gore", cap1="gore"))
        return out

    def totem(self, base, height, s, facing=(1, 0, 0), r=None, skulls=2, ribs=True):
        """A timber pole `height` tall crowned by a horned skull s tall, with a bone crossbar below
        it hung with `skulls` small skulls on cords, rope lashings, and (ribs) a ribcage and spine
        lashed to the pole's front under the crossbar."""
        base, F = V(base), Frame(base, facing)
        r = r or 0.16 * s
        top = base + Z * height
        out = self.pole(base, top, r)
        out += self.horned_skull(top + Z * 0.45 * s + F.fwd * 0.1 * s, facing, s, horn=1.3)
        zb = top - Z * 0.55 * s
        a, b = zb - F.side * 1.2 * s + F.fwd * (r + 0.1 * s), zb + F.side * 1.2 * s + F.fwd * (r + 0.1 * s)
        out += self.bone(a, b, 0.1 * s, k=4)
        out += self.lashing(zb, Z, r, turns=1, w=0.16 * s)
        out += self.lashing(base + Z * height * 0.45, Z, r, turns=1, w=0.16 * s)
        for i in range(skulls):
            e = -1 if i % 2 == 0 else 1
            hang = a.lerp(b, 0.12 if e < 0 else 0.88)
            low = hang - Z * 0.85 * s
            out.append(self.tube([hang, low], [0.05 * s, 0.05 * s], "rope", k=3, cap0="rope", cap1="rope"))
            out += self.skull(low - Z * 0.3 * s, facing, 0.55 * s, detail=0)
        if ribs:
            rc = zb - Z * 1.25 * s + F.fwd * (r + 0.3 * s)
            out += self.ribcage(rc, facing, 1.5 * s, spine=False)          # the pole is its spine
            out += self.lashing(rc + Z * 0.45 * s - F.fwd * (0.3 * s), Z, r, turns=1, w=0.14 * s)
        return out

    def carcass(self, top, length, r, facing=(1, 0, 0)):
        """A flayed hide sack `length` long hung from an iron hook at top; its cut end is bloody."""
        top, F = V(top), Frame(top, facing)
        out = [self.tube([top + Z * 0.6 * r, top + F.fwd * 0.5 * r + Z * 0.2 * r, top + F.fwd * 0.3 * r - Z * 0.4 * r,
                          top - Z * 0.5 * r], [0.12 * r, 0.12 * r, 0.12 * r, 0.1 * r], "iron", k=4, cap0="iron", cap1="iron")]
        pts = [top - Z * (0.3 + f * length) for f in (0.0, 0.2, 0.45, 0.7, 0.88, 1.0)]
        radii = [0.25 * r, 0.8 * r, r, 0.95 * r, 0.7 * r, 0.3 * r]
        out.append(self.tube(pts, radii, ["hide", "hide", "hide", "gore", "gore"], k=5, cap0="hide", cap1="gore",
                             squash=0.65))
        return out

    @staticmethod
    def drip(a, t, n, u, z, length, w, d, th=0.14):
        """A run of dried blood lying on a wall face (a, t, n) from z down `length`, w wide at the
        top, ending in a bead."""
        zb = z - length
        run = [(u - w / 2, z), (u + w / 2, z), (u + w * 0.22, zb + w * 0.5), (u - w * 0.22, zb + w * 0.5)]
        bead = [(u + w * 0.35 * math.cos(2 * math.pi * i / 6), zb + w * 0.3 + w * 0.35 * math.sin(2 * math.pi * i / 6))
                for i in range(6)]
        return [prism_uz(a, t, n, run, d - 0.05, d + th, ["gore"] * 4, "gore", None),
                prism_uz(a, t, n, bead, d - 0.05, d + th * 1.3, ["gore"] * 6, "gore", None)]
