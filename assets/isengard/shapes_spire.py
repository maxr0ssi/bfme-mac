"""The Isengard kit's spires (a mixin of IsengardShapes, assets/isengard/shapes.py): slender
lozenge-plan blades in EA's manner - sharp edges front and back, faces broken by fins standing
proud, a flared and spurred foot, a hard taper to a needle - and the needle chimneys.

    lozenge(c, axis, L, W, z)          a lozenge ring: L along the axis, W across it
    blade_tower(c, axis, L, W, z0, z1) a blade tower: flared spurred foot, two set-back steps,
                                       layered fins on every face, silver edges front and back,
                                       ember slits, a collar, a needle tip; `lean` shifts its top
    needle_stack(c, axis, L, W, z0, z1) a needle chimney: lozenge section, fins up its sharp
                                       edges, a spiked collar, a crown of blades round a
                                       glowing throat
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft, prism_uz


# a blade tower's lozenge scale by height fraction: a flared foot, two set-back steps (ledges), a
# hard taper to a needle
PROFILE = [(0.0, None), (0.04, 1.0), (0.3, 0.93), (0.302, 0.84), (0.55, 0.74), (0.552, 0.66), (0.8, 0.42), (1.0, 0.03)]
BROAD = [(0.0, None), (0.04, 1.0), (0.3, 0.96), (0.302, 0.9), (0.55, 0.84), (0.552, 0.77), (0.82, 0.55), (1.0, 0.03)]


def scale(f, profile=PROFILE):
    """A blade tower's lozenge scale at height fraction f (above the foot)."""
    prof = profile[1:]
    if f <= prof[0][0]:
        return prof[0][1]
    for (f0, s0), (f1, s1) in zip(prof, prof[1:]):
        if f <= f1:
            return s0 + (s1 - s0) * (f - f0) / (f1 - f0)
    return prof[-1][1]


def _axes(axis):
    a = math.radians(axis)
    d = V((math.cos(a), math.sin(a), 0))
    return d, V((-d.y, d.x, 0))


class SpireKit:
    @staticmethod
    def lozenge(c, axis, L, W, z):
        d, p = _axes(axis)
        c = V((c[0], c[1], z))
        return [c + d * L, c + p * W, c - d * L, c - p * W]

    def _shaft(self, c, axis, L, W, z0, z1, lean, profile):
        """Lozenge rings along a profile [(z fraction, scale)], the centre shifted by lean * fraction."""
        c, lean = V((c[0], c[1], 0)), V((lean[0], lean[1], 0))
        rings = []
        for f, s in profile:
            z = z0 + (z1 - z0) * f
            rings.append(self.lozenge(c + lean * f, axis, L * s, W * s, z))
        return rings

    def _faces(self, rings, i):
        """(midpoint, outward normal, along) of face i (vertex i to i+1) of a lozenge ring."""
        a, b = rings[i], rings[(i + 1) % 4]
        m = (a + b) / 2
        t = (b - a).normalized()
        n = V((t.y, -t.x, 0))
        ctr = sum(rings, V((0, 0, 0))) / 4
        if n.dot(m - ctr) < 0:
            n = -n
        return m, n, t

    def blade_tower(self, c, axis, L, W, z0, z1, lean=(0, 0), flare=1.4, fins=1, spurs=True, slits=(0.3,),
                    collar=0.55, tag="stoneA", profile=PROFILE, fin_reach=1.0, slit_w=0.7):
        """A blade tower on c from z0 to a needle at z1 (see the module docstring): the profile
        PROFILE, set back in two steps; fins: fins per face (3: a tall deep one in the middle, a
        shorter shallower one each side - the faces in layers)."""
        prof = [(0.0, flare)] + profile[1:]
        rings = self._shaft(c, axis, L, W, z0, z1, lean, prof)
        out = [loft(rings, [tag] * (len(rings) - 1), cap0=(tag, False), cap1=(tag, True))]
        lean = V((lean[0], lean[1], 0))
        H = z1 - z0
        for k in (0, 2):                                 # silver on the sharp edges front and back, along each bend
            for r0, r1 in zip(rings[1:-2], rings[2:-1]):
                out.append(self.beam(r0[k], r1[k], 0.26, "trim"))
        zc = z0 + H * collar
        s = scale(collar, profile)
        ring = self.lozenge(V((c[0], c[1], 0)) + lean * collar, axis, L * s, W * s, 0)
        out.append(loft([[p + Z * (zc - 0.7) for p in self._grow(ring, -0.3)], [p + Z * (zc - 0.5) for p in self._grow(ring, 0.5)],
                         [p + Z * (zc + 0.5) for p in self._grow(ring, 0.5)], [p + Z * (zc + 0.7) for p in self._grow(ring, -0.3)]],
                        ["trim"] * 3, cap0=("trim", False), cap1=("trim", False)))
        spots = {0: (), 1: ((0.0, 1.0, 0.55),), 2: ((-0.2, 1.0, 0.5), (0.2, 1.0, 0.5)),
                 3: ((-0.3, 0.6, 0.3), (0.0, 1.0, 0.55), (0.3, 0.6, 0.3))}[int(fins)]
        for i in range(4):                               # fins standing proud of every face, in layers
            a, b = rings[1][i], rings[1][(i + 1) % 4]
            m, n, t = self._faces(rings[1], i)
            for u, depth, reach in spots:
                reach = min(0.85, reach * fin_reach)
                d0 = (1.2 + W * 0.35) * depth
                back = 0.8 + (1.0 - scale(reach, profile)) * W       # reaching into the face as it tapers
                out += self.blade(m + t * ((b - a).length * u), n, z0 + 0.5, z0 + H * reach, d0,
                                  max(0.3, d0 - H * reach * 0.128), w=0.55 + 0.25 * depth, tip=3.0 * depth, back=back)
        if spurs:                                        # the flared foot's spurs, EA's wall spikes
            for k in range(4):
                v = rings[0][k]
                d = (v - V((c[0], c[1], v.z))).normalized()
                out += self.blade(v - d * 0.8, d, z0 - 0.05, z0 + H * 0.08, 3.2, 1.0, w=0.7, tip=2.5, back=1.5)
        for f in slits:                                  # ember slits on every face
            zs = z0 + H * f
            s = scale(f, profile)
            ring = self.lozenge(V((c[0], c[1], 0)) + lean * f, axis, L * s, W * s, 0)
            for i in range(4):
                a, b = ring[i], ring[(i + 1) % 4]
                m = (a + b) / 2
                t = (b - a).normalized()
                n = V((t.y, -t.x, 0))
                if n.dot(m - sum(ring, V((0, 0, 0))) / 4) < 0:
                    n = -n
                for u in (-0.22, 0.22):
                    q = m + t * ((b - a).length * u)
                    h, sw = H * 0.1, slit_w / 2
                    out.append(prism_uz(q, t, n, [(-sw, zs), (sw, zs), (sw, zs + h * 0.8), (0, zs + h), (-sw, zs + h * 0.8)],
                                        -0.9, 0.2, ["ember"] * 5, "ember", None))
        return out

    @staticmethod
    def _grow(ring, g):
        ctr = sum(ring, V((0, 0, 0))) / 4
        return [p + (V((p.x - ctr.x, p.y - ctr.y, 0))).normalized() * g for p in ring]

    def needle_stack(self, c, axis, L, W, z0, z1, collar=0.55, glow=True):
        """A needle chimney: a lozenge shaft from a flared foot tapering to z1, fins up its two
        sharp edges, a spiked collar, and a crown of four blades round a glowing throat."""
        prof = [(0.0, 1.45), (0.05, 1.0), (0.35, 0.84), (0.352, 0.76), (0.92, 0.5)]
        rings = self._shaft(c, axis, L, W, z0, z1 - 2.0, (0, 0), prof)
        top = rings[-1]
        rim = self._grow([p + Z * 1.0 for p in top], 0.6)
        lip = [p + Z * 2.0 for p in rim]
        throat = [p + Z * 2.0 for p in self._grow(top, -0.18)]          # a wide glowing mouth
        deep = [p - Z * 2.2 for p in throat]
        tg = "ember" if glow else "iron"
        out = [loft(rings + [rim, lip, throat, deep], ["iron"] * len(rings) + ["trim", "iron", tg],
                    cap0=("iron", False), cap1=(tg, True))]
        H = z1 - z0
        for k in (0, 2):                                 # fins up the sharp edges (black: silver only on the rim)
            v = rings[1][k]
            d = (v - V((c[0], c[1], v.z))).normalized()
            out += self.blade(v - d * 0.3, d, z0 + 0.5, z0 + H * 0.8, 2.4, 0.6, w=0.45, tip=3.5, back=0.6, tag="iron",
                              edge="iron")
        zc = z0 + H * collar
        s = 0.76 + (0.5 - 0.76) * (collar - 0.352) / 0.568 if collar > 0.352 else 1.0 + (0.84 - 1.0) * (collar - 0.05) / 0.3
        ring = self.lozenge(c, axis, L * s, W * s, 0)
        out.append(loft([[p + Z * (zc - 0.7) for p in self._grow(ring, -0.2)], [p + Z * (zc - 0.5) for p in self._grow(ring, 0.45)],
                         [p + Z * (zc + 0.5) for p in self._grow(ring, 0.45)], [p + Z * (zc + 0.7) for p in self._grow(ring, -0.2)]],
                        ["iron", "ember", "iron"], cap0=("iron", False), cap1=("iron", False)))   # an ember-lit band
        for k in range(4):                               # the collar's spikes, and the crown's blades
            v = ring[k]
            d = V((v.x - c[0], v.y - c[1], 0)).normalized()
            p = V((v.x, v.y, zc)) + d * 0.3
            out.append(self.beam(p, p + (d + Z * 0.3).normalized() * (1.6 + L * 0.3), 0.22, "iron", 0.0))
            r = lip[k]
            out += self.blade(r - d * 0.4, d, r.z - 0.3, r.z + W * 1.6, 0.6, 0.2, w=0.35, tip=W * 1.1, back=0.6,
                              tag="iron", edge="trim")
        if glow:                                         # flames out of the throat
            mouth = sum(throat, V((0, 0, 0))) / 4
            out += self.flames(mouth, min(L, W) * 0.6 + 0.4, W * 3.2 + 3.0, n=5, seed=c[0] * 0.13,
                               kind="chimney")
        return out
