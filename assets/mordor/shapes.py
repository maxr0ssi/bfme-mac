"""The Mordor shape vocabulary (Blender side): Barad-dur's black land. Where Isengard is machined -
precise, symmetric, silver-edged lozenge blades - Mordor is volcanic and cruel: raw black basalt
split by glowing lava, jagged horns with serrated edges, hooked and barbed spikes, crooked iron,
cages and chains. Every piece returns closed solids (sagekit.blender.geometry.Solid) tagged with
MordorAtlas regions only (assets/mordor/atlas.py).

Placement as in the other kits:
    points      base / centre points and directions in 3D (horns, spikes, chains, cages)
    a, t, n     a wall face: anchor a, along t, out along n; u along the face, z up, d out
                (sagekit.blender.geometry.prism_uz)

Tags: stoneA/stoneB (basalt), rock (ash and crag), iron, chain, soot, trim (fire-lit edges),
steel (cold blade edges and barb tips), slit (windows: a dim ember in F2), witch (the few slits in
the Morgul witch-light), ember and flame (lava and fire), wood (charred timber), cloth. The generic pieces borrowed from the Isengard kit (its works,
yard and fire mixins) name "timber", "mark" and "water": `retag` maps them onto Mordor's tags, so
a recipe's design() ends with `return kit.retag(solids)`.

Core (this module; tube, beam, arc as the Isengard kit's)
    retag(solids)                      Isengard tag names onto Mordor's (TAGS)
    blade(a, out, z0, z1, d0, d1)      a knife-edge fin standing out of a face or a corner
    barb(p, d, length, r)              a hooked barb: out along d, its point curling up
    stake(c, d, length, r)             an impaling stake: a crooked iron shaft, two barbs, steel tip
    hung_chain(p, q, sag, link)        a chain sagging between two points (a parabola of links)
Horns (shapes_horn.py, HornKit)
    Horn, horn, eye, witch_slit, lancet
Lava (shapes_lava.py, LavaKit)
    lava_channel, lava_crack, lava_pool
Story (shapes_story.py, StoryKit)
    cage, gibbet, fire_basket, war_drum, crane, portcullis, ash_heap, flue
Borrowed (assets/isengard): WorksKit (chain, hook, rivets, plate, hoop, spike_row, slag_heap,
facet_lump), YardKit (hearth, anvil, bellows, crucible, scaffold, brazier, lantern, pipe,
floor_grate), FireKit (fire, flames, runnel, glowing_work, ingots).
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft, prism_uz

from assets.isengard.shapes import arc, beam, ring, side_of, tube, unit
from assets.isengard.shapes_fire import FireKit
from assets.isengard.shapes_works import WorksKit
from assets.isengard.shapes_yard import YardKit

from .shapes_horn import HornKit
from .shapes_lava import LavaKit
from .shapes_story import StoryKit

# the borrowed pieces' tag names -> Mordor's
TAGS = {"timber": "wood", "mark": "ember", "water": "ember"}


class MordorShapes(HornKit, LavaKit, StoryKit, WorksKit, YardKit, FireKit):
    """The Mordor kit. Stable API: add pieces, keep these signatures (every Mordor recipe uses them)."""

    Z = Z
    V = V
    tube = staticmethod(tube)
    arc = staticmethod(arc)
    unit = staticmethod(unit)
    side_of = staticmethod(side_of)
    ring = staticmethod(ring)
    beam = staticmethod(beam)
    loft = staticmethod(loft)

    def blade(self, a, out, z0, z1, d0, d1, w=1.0, tip=4.0, back=2.0, tag="stoneA", edge="steel"):
        """A knife-edge fin from a along the horizontal `out`: its front edge from d0 out at z0
        leaning back to d1 at z1, then up to a point `tip` above z1; `back` of it buried in what it
        stands on; w thick; the front edges `edge` (the Isengard kit's blade, steel-edged)."""
        a, o = V(a), self.unit(V((out[0], out[1], 0)))
        s = V((-o.y, o.x, 0))
        poly = [(-back, z0), (d0, z0), (d1, z1), (d1 * 0.35, z1 + tip), (-back, z1 + tip * 0.3)]
        return [prism_uz(V((a.x, a.y, 0)), o, s, poly, -w / 2, w / 2, [tag, edge, edge, tag, tag], tag, tag)]

    @staticmethod
    def retag(solids):
        """The borrowed pieces' tags ("timber", "mark", "water") onto Mordor's (TAGS), in place."""
        for s in solids:
            polys = []
            for pts, tag, keep in s.polys:
                base, _, rest = tag.partition("|")
                if base in TAGS:
                    tag = TAGS[base] + ("|" + rest if rest else "")
                polys.append((pts, tag, keep))
            s.polys = polys
        return solids

    # ------------------------------------------------------------------ barbs and stakes
    def barb(self, p, d, length, r=0.45, curl=0.55, tag="iron", tip="steel"):
        """A hooked barb from p out along d, `length` long, its last third curling up (curl: how
        far, as a fraction of the length); four-sided, a steel point."""
        p, d = V(p), self.unit(d)
        up = (Z - d * Z.dot(d))
        up = up.normalized() if up.length > 1e-3 else self.side_of(d)
        m1 = p + d * length * 0.55
        m2 = m1 + (d * 0.75 + up * curl).normalized() * length * 0.3
        tipp = m2 + (d * 0.25 + up).normalized() * length * curl * 0.45
        return [self.tube([p - d * r, m1, m2], [r, r * 0.62, r * 0.36], tag, k=4, cap0=tag, cap1=tag,
                          phase=math.pi / 4),
                self.tube([m2, tipp], [r * 0.36, 0.0], tip, k=4, cap0=tip, cap1=None, phase=math.pi / 4)]

    def stake(self, c, d, length, r=0.6, barbs=2, seed=0.0):
        """An impaling stake from its foot c along d (leaning out), `length` long: a crooked iron
        shaft in two bends, `barbs` hooked barbs off it, a steel point."""
        c, d = V(c), self.unit(d)
        s = self.side_of(d)
        k1 = c + d * length * 0.45 + s * (length * 0.05 * math.sin(seed * 2.1 + 1.0))
        k2 = k1 + (d + s * 0.12 * math.cos(seed * 1.7)).normalized() * length * 0.35
        top = k2 + d * length * 0.2
        out = [self.tube([c - Z * 0.6, k1, k2], [r, r * 0.85, r * 0.6], "iron", k=4, cap0="iron", cap1="iron",
                         phase=math.pi / 4),
               self.tube([k2, top], [r * 0.6, 0.0], "steel", k=4, cap0="steel", cap1=None, phase=math.pi / 4)]
        for i in range(barbs):
            p = k1.lerp(k2, 0.3 + 0.5 * i / max(barbs - 1, 1))
            side = s if i % 2 == 0 else -s
            out += self.barb(p, (side + d * 0.3).normalized(), length * 0.22, r * 0.5)
        return out

    # ------------------------------------------------------------------ chains
    def hung_chain(self, p, q, sag, link=4.4, w=1.3, th=0.45, segs=6, hooks=0, tag="chain"):
        """A heavy chain from p to q sagging `sag` at its middle (a parabola in `segs` straight runs
        of links); `hooks` meat hooks hanging along it. Returns (solids, the lowest point)."""
        p, q = V(p), V(q)
        pts = [p.lerp(q, i / segs) - Z * (4 * sag * (i / segs) * (1 - i / segs)) for i in range(segs + 1)]
        out = []
        for a, b in zip(pts, pts[1:]):
            out += self.chain(a, b, link=link, w=w, th=th, tag=tag)
        for i in range(hooks):
            f = (i + 1) / (hooks + 1)
            j = f * segs
            k = min(int(j), segs - 1)
            h = pts[k].lerp(pts[k + 1], j - k)
            out += self.hook(h, 2.4, chain=2.0 + 2.5 * ((i * 7) % 3) / 2)
        low = min(pts, key=lambda v: v.z)
        return out, low
