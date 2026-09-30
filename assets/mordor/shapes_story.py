"""The Mordor kit's story pieces (a mixin of MordorShapes, assets/mordor/shapes.py): what orcs and
their masters keep on the walls. Sized for the RTS camera: nothing under about 4 units across.

Placement: c a ground point (x, y, z), t the piece's long axis (horizontal), n its front.

    cage(top, h, w)                    a gibbet cage hanging from top: lozenge in plan (never round),
                                       iron bars, a spiked cap and a pointed foot, a slumped prisoner
    gibbet(a, out, z, reach, drop, h)  an iron arm out of a face on a barbed brace, a chain, a cage
    fire_basket(c, r, h)               a clawed iron fire basket on a barbed tripod (a brazier)
    war_drum(c, t, r, w)               an eight-sided hide war drum on a spiked frame, a great mallet
    crane(c, t, h, reach, drop)        an orc crane: a braced timber mast, an iron-shod jib, a chain
    portcullis(a, t, n, u0, u1, z0, z1, teeth)  the raised portcullis' bottom: a grid and barbed teeth
    ash_heap(c, r, h)                  a heap of ash and slag with embers in it
    flue(c, axis, L, W, z0, z1)        a forge flue: a leaning wedge of black iron-stone, hooked blades
                                       round a glowing throat (a jagged chimney, never round)
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft, prism_uz


def _v(p):
    return V((p[0], p[1], p[2] if len(p) > 2 else 0.0))


class StoryKit:
    # ------------------------------------------------------------------ cages
    def cage(self, top, h=7.0, w=2.2, prisoner=False):
        """A gibbet cage hanging from `top`: a lozenge in plan (w half-wide, 0.7 w deep), six
        bars from a spiked cap to a pointed foot, two iron bands, a slumped prisoner inside."""
        top = _v(top)
        c0, c1 = top - Z * 1.2, top - Z * (h - 1.0)
        ring = lambda c, s: [c + V((w * s, 0, 0)), c + V((w * s * 0.5, w * s * 0.75, 0)),   # noqa: E731
                             c + V((-w * s * 0.5, w * s * 0.75, 0)), c + V((-w * s, 0, 0)),
                             c + V((-w * s * 0.5, -w * s * 0.75, 0)), c + V((w * s * 0.5, -w * s * 0.75, 0))]
        out = [loft([[top] * 6, ring(c0, 0.7), ring(c0 - Z * 0.5, 0.75)], ["iron", "iron"], cap0=("iron", False),
                    cap1=("iron", True))]
        foot = top - Z * h
        out.append(loft([ring(c1 + Z * 0.4, 0.75), ring(c1, 0.7), [foot] * 6], ["iron", "iron"], cap0=("iron", True),
                        cap1=("iron", False)))
        r0, r1 = ring(c0 - Z * 0.5, 0.95), ring(c1 + Z * 0.4, 0.95)
        for p, q in zip(r0, r1):
            out.append(self.beam(p, q, w * 0.1, "iron"))
        for f in (0.5,):
            rb = ring(c0.lerp(c1, f), 1.0)
            for p, q in zip(rb, rb[1:] + rb[:1]):
                out.append(self.beam(p, q, w * 0.1, "iron"))
        for i in range(3):                                  # spikes on the cap
            a = 2 * math.pi * i / 3 + 0.3
            p = c0 + V((math.cos(a) * w * 0.5, math.sin(a) * w * 0.4, 0.3))
            out.append(self.beam(p, p + V((math.cos(a) * 0.8, math.sin(a) * 0.8, 1.6)), 0.16, "steel", 0.0))
        if prisoner:                                        # a slumped figure: hunched body, head
            b = c1 + Z * 0.5
            out.append(self.beam(b + V((0.2, 0, 0)), b + V((-0.3, 0.1, h * 0.45)), 0.55, "soot", 0.4))
            out.append(self.facet_lump(b + V((-0.1, 0.25, h * 0.52)), 0.5, "rock"))
        return out

    def gibbet(self, a, out_dir, z, reach=5.0, drop=5.0, h=7.0, w=2.2):
        """An iron arm out of a face at a (z its height) along `out_dir`, a barbed brace under it,
        a chain `drop` down to a cage."""
        a, o = _v(a), self.unit(V((out_dir[0], out_dir[1], 0)))
        root, end = V((a.x, a.y, z)), V((a.x, a.y, z)) + o * reach
        res = [self.beam(root - o * 1.0, end, 0.45, "iron"),
               self.beam(root - Z * reach * 0.8, end - o * reach * 0.25, 0.3, "iron"),
               self.beam(end, end + o * 1.4 + Z * 1.6, 0.35, "steel", 0.0)]
        res += self.barb(root.lerp(end, 0.5) + Z * 0.4, (Z + o * 0.4), 2.4, 0.26)
        res += self.chain(end, end - Z * drop, link=1.4, w=0.45, th=0.18)
        res += self.cage(end - Z * drop, h, w)
        return res

    # ------------------------------------------------------------------ fire
    def fire_basket(self, c, r=1.8, h=5.0, kind="brazier"):
        """A fire basket r across on a tripod of barbed iron legs, h to its rim: a square basket
        turned to show an edge, pointed below, iron claws hooking up round its rim, heaped with
        embers; its fire point recorded (kind)."""
        c = _v(c)
        rim = c + Z * h
        sq = lambda z, s: [c + V((s * math.cos(a), s * math.sin(a), z)) for a in (0.0, math.pi / 2, math.pi,  # noqa: E731
                                                                                   3 * math.pi / 2)]
        res = [loft([sq(h - r * 1.3, 0.12), sq(h - 0.3, r), sq(h, r * 1.08), sq(h + 0.1, r * 0.9)], ["iron", "iron", "iron"],
                    cap0=("iron", False), cap1=("ember", True))]
        for i in range(3):
            ang = 2 * math.pi * i / 3 + 0.4
            d = V((math.cos(ang), math.sin(ang), 0))
            knee = c + d * r * 0.9 + Z * (h * 0.45)
            res.append(self.tube([c + Z * (h - r * 0.8) + d * r * 0.3, knee, c + d * r * 1.5 - Z * 0.4],
                                 [0.24, 0.22, 0.2], "iron", k=4, cap0="iron", cap1="iron", phase=math.pi / 4))
        for i in range(4):                                  # claws off the rim's corners, hooking in
            ang = math.pi / 2 * i
            d = V((math.cos(ang), math.sin(ang), 0))
            p = rim + d * r * 0.95
            res.append(self.tube([p, p + d * r * 0.4 + Z * r * 0.9, p + d * r * 0.1 + Z * r * 1.5], [0.26, 0.18, 0.0], "iron",
                                 k=4, cap0="iron", cap1=None, phase=math.pi / 4))
        res.append(self.facet_lump(rim + Z * 0.3, r * 0.55, "ember"))
        self.fire(rim + Z * 0.3, kind)
        return res

    def ash_heap(self, c, r=3.0, h=2.2, seed=1):
        """A heap of ash and clinker at c, embers in it (the Isengard kit's slag heap in ash)."""
        return self.slag_heap(_v(c), r, h, seed=seed, embers=3)

    # ------------------------------------------------------------------ war drums
    def war_drum(self, c, t, r=3.0, w=3.4, mallet=True):
        """An eight-sided war drum at c (its foot), its axis along t (the heads face +-t), r to its
        rim's corners, w long: a charred shell with iron hoops, hide heads, spikes round both rims,
        on a spiked iron frame; a great mallet leaning on it."""
        c, t = _v(c), _v(t).normalized()
        n = V((-t.y, t.x, 0))
        ax = c + Z * (r + 1.6)
        k = 8
        rg = lambda u, rr: [ax + t * u + (n * math.cos(2 * math.pi * i / k + math.pi / 8) +             # noqa: E731
                                          Z * math.sin(2 * math.pi * i / k + math.pi / 8)) * rr for i in range(k)]
        res = [loft([rg(-w / 2, r * 0.9), rg(-w / 2 + 0.4, r), rg(0, r * 1.05), rg(w / 2 - 0.4, r), rg(w / 2, r * 0.9)],
                    ["iron", "wood", "wood", "iron"], cap0=("soot", True), cap1=("soot", True))]
        for u in (-w / 2 + 0.2, w / 2 - 0.2):               # the rims' spikes
            for p in rg(u, r * 1.0)[::2]:
                d = (p - (ax + t * u)).normalized()
                res.append(self.beam(p, p + d * r * 0.55, 0.2, "steel", 0.0))
        for s in (-1, 1):                                   # an A-frame each side under the shell
            for tu in (-1, 1):
                f = c + t * (tu * w * 0.55) + n * (s * r * 0.8)
                res.append(self.beam(f - Z * 0.3, ax + t * (tu * w * 0.55) - Z * r * 0.3 + n * (s * r * 0.4), 0.28, "iron"))
        res.append(self.beam(c + t * (-w * 0.55) + Z * 0.8, c + t * (w * 0.55) + Z * 0.8, 0.26, "iron"))
        if mallet:
            base = c + t * (w * 0.5 + 0.6) + n * (r * 0.9)
            head = ax + t * (w * 0.5 + 0.4) + n * (r * 0.5) + Z * (r * 0.6)
            res.append(self.beam(base, head, 0.18, "wood"))
            res.append(self.beam(head - n * 0.9, head + n * 0.9, 0.7, "iron", 0.5))
        return res

    # ------------------------------------------------------------------ cranes
    def crane(self, c, t, h=30.0, reach=12.0, drop=10.0, cage=True):
        """An orc crane at c: a mast of charred timber braced by three struts, an iron-shod jib from
        its head out along t (rising), a chain from the jib's end `drop` down to a cage."""
        c, t = _v(c), _v(t).normalized()
        n = V((-t.y, t.x, 0))
        head = c + Z * h
        res = [self.beam(c - Z * 0.3, head, 0.55, "wood")]
        for i in range(3):
            a = 2 * math.pi * i / 3 + 1.0
            d = V((math.cos(a), math.sin(a), 0))
            res.append(self.beam(c + d * h * 0.18 - Z * 0.3, c + Z * h * 0.42, 0.3, "wood"))
        tip = head + t * reach + Z * reach * 0.35
        heel = head - t * reach * 0.3 - Z * 1.5
        for s in (-1, 1):
            res.append(self.beam(heel + n * (s * 0.5), tip + n * (s * 0.2), 0.35, "wood"))
        for f in (0.35, 0.7):
            p = heel.lerp(tip, f)
            res.append(self.beam(p - n * 0.8, p + n * 0.8, 0.2, "iron"))
        res.append(self.beam(tip, tip + t * 1.8 + Z * 1.2, 0.4, "steel", 0.0))
        res.append(self.beam(heel, heel - Z * 3.0, 0.9, "iron"))            # the counterweight
        res += self.chain(head + Z * 1.5, tip, link=1.6, w=0.4, th=0.16)
        res += self.chain(tip - Z * 0.3, tip - Z * drop, link=1.4, w=0.45, th=0.18)
        if cage:
            res += self.cage(tip - Z * drop, 8.0, 2.5)
        return res

    # ------------------------------------------------------------------ the gate
    def portcullis(self, a, t, n, u0, u1, z0, z1, teeth=5, d=0.0, r=0.42, length=1.0):
        """The bottom of a raised portcullis across a gate from u0 to u1: two iron rails at z0 + 2
        and z1, bars from z0 up to z1, each bar ending in a barbed tooth below z0 (r thick at its
        root, `length` times the stock length)."""
        a, t, n = V(a), V(t), V(n)
        P = lambda u, z: a + t * u + n * d + Z * z          # noqa: E731
        res = [self.beam(P(u0 - 0.5, z0 + 2.0), P(u1 + 0.5, z0 + 2.0), 0.45, "iron"),
               self.beam(P(u0 - 0.5, z1), P(u1 + 0.5, z1), 0.45, "iron")]
        for i in range(teeth):
            u = u0 + (u1 - u0) * (i + 0.5) / teeth
            res.append(self.beam(P(u, z0), P(u, z1 + 0.3), 0.35, "iron"))
            L = (3.6 + 0.8 * (1 - abs((i + 0.5) / teeth - 0.5) * 2)) * length
            res.append(self.beam(P(u, z0 + 0.2), P(u, z0 - L), r, "steel", 0.0))
            for s in (-1, 1):                                    # a barb each side, hooking up
                b = P(u + s * 0.3, z0 - L * 0.45)
                res.append(self.beam(b, b + t * (s * 0.9) + Z * 1.1, r * 0.4, "steel", 0.0))
        return res

    # ------------------------------------------------------------------ forge flue
    def flue(self, c, axis, L, W, z0, z1, lean=(0.0, 0.0), kind="chimney"):
        """A forge flue from z0 to z1 at c: a wedge-plan shaft of black iron-stone (L along axis, W
        across; a knife edge front and back), battered and leaning, a glowing throat, four hooked
        blades clawing up round it; its fire point recorded (kind)."""
        a = math.radians(axis)
        d, p = V((math.cos(a), math.sin(a), 0)), V((-math.sin(a), math.cos(a), 0))
        lean = V((lean[0], lean[1], 0))
        c = V((c[0], c[1], 0))
        sec = lambda f, s: [c + lean * f + d * (L * s) + Z * (z0 + (z1 - z0) * f), c + lean * f + p * (W * s) + Z * (z0 + (z1 - z0) * f),  # noqa: E501,E731
                            c + lean * f - d * (L * s) + Z * (z0 + (z1 - z0) * f), c + lean * f - p * (W * s) + Z * (z0 + (z1 - z0) * f)]
        rings = [sec(0.0, 1.45), sec(0.08, 1.0), sec(0.5, 0.82), sec(0.52, 0.74), sec(0.96, 0.62)]
        top = sec(1.0, 0.72)
        throat = sec(1.0, 0.45)
        deep = [q - Z * 2.5 for q in throat]
        res = [loft(rings + [top, throat, deep], ["stoneA", "stoneA", "trim", "stoneA", "iron", "iron", "ember"],
                    cap0=("stoneA", False), cap1=("ember", True))]
        for k in range(4):                                  # hooked blades clawing up round the throat
            v = top[k]
            o = V((v.x - (c.x + lean.x), v.y - (c.y + lean.y), 0)).normalized()
            res += self.barb(v - o * 0.4, (o * 0.35 + Z).normalized(), W * 2.2, 0.5, curl=0.35, tip="steel")
        self.fire(sum(throat, V((0, 0, 0))) / 4, kind)
        return res
