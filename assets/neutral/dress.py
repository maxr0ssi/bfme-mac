"""The capture dress (Blender side): each faction's kit pieces at the places a recipe names, retagged
for the neutral atlas (sagekit/capture.py). A faction's own kit draws them (its banner, its crest,
its finial: the same shapes its buildings carry), then every face tag becomes `<prefix>_<role>`:
the role is the kind of material (ROLE), the prefix the faction's, and the style paints each in that
faction's ramp (style.py DRESS_RAMPS). Cloth becomes `<prefix>_cloth` and leaves for the house-colour
model, so a dress's banner takes the capturer's colour.

    Spots(banner, banner2, ridges, porch)

A recipe gives the spots; every dress fits them, two to three bold pieces that make the building read
as its holder's at the RTS camera: banners on two faces (or a plaque, a shield), the roof ridges
crowned in the faction's manner, and for the Goblins a fence on the porch. No fire: a fire Draw can
only be keyed to a model condition, and a faction upgrade can only set one for good
(ModelConditionUpgrade), so the fire would outlive its holder."""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, box, prism_uz

from .atlas import DRESS_ROLES

# kit tag (its base name) -> role; first match on the words wins, else stone
ROLE = [("cloth", ("cloth",)),
        ("glow", ("ice", "crystal", "glass", "frost", "flame", "ember", "fire", "slit", "glow", "witch", "lava")),
        ("gilt", ("gilt", "gold", "rune", "inlay", "brass", "bronze", "tri", "hex")),
        ("metal", ("iron", "steel", "chain", "spike", "blade", "metal", "silver", "trim")),
        ("bone", ("bone", "tusk", "skull", "ivory", "paint", "mark", "socket", "gore", "enamel")),
        ("wood", ("wood", "timber", "plank", "rope", "hide", "pole"))]
# per faction: the roles its kit's words mean (the Dwarven and Elven trim is gold, the Men's steel)
OVERRIDE = {"dw": {"trim": "gilt", "ground": "metal"}, "el": {"trim": "gilt", "coping": "stone"},
            "mn": {"relief": "bone"}, "gb": {"hide": "stone", "timber": "bone"}, "an": {"steel": "gilt"},
            "mo": {"steel": "gilt"}, "is": {"silver": "gilt"}, "x": {"socket": "stone", "gore": "wood", "hide": "wood"}}


def role_of(prefix, tag):
    base = tag.split("|")[0].lower()
    own = OVERRIDE.get(prefix, {})
    if base in own:
        return own[base]
    for role, words in ROLE:                    # (a short word whole: "tri" is the Dwarven frieze, not "trim")
        if any(base == w or len(w) > 3 and w in base for w in words):
            return role
    return "stone"


BASE = {"stone": "rock", "gilt": "gold", "metal": "iron", "wood": "log", "bone": "bone", "glow": "ember", "cloth": "cloth"}


def retag_base(solids, prefix="gb", web=()):
    """Another faction's kit pieces for a neutral body (the lairs' story pieces): every face tag
    becomes the neutral tag of its role (BASE; `prefix`'s kit words), or "web" for the words in `web`."""
    for s in solids:
        for poly in s.polys:
            base = poly[1].split("|")[0].lower()
            poly[1] = "web" if base in web else BASE[role_of(prefix, poly[1])]
    return solids


def retag(solids, prefix):
    """Every face of `solids` tagged `<prefix>_<role>` (a band's |v / |a direction kept)."""
    for s in solids:
        for poly in s.polys:
            tag = poly[1]
            role = role_of(prefix, tag)
            assert role in DRESS_ROLES, role
            poly[1] = "%s_%s" % (prefix, role) + ("|" + tag.split("|")[1] if "|" in tag else "")
    return solids


class Spots:
    """Where a dress goes: banner and banner2 (a, t, n, u, z_top, width, length, d) on two faces,
    ridges [((x0, y0), (x1, y1), z, slope)] roof ridges (slope: the roof's drop per unit across),
    porch ((x0, y0), (x1, y1)) a ground line in front of a wall."""

    def __init__(self, banner, banner2, ridges, porch, ceiling=None):
        self.banner = tuple(V(x) for x in banner[:3]) + tuple(banner[3:])
        self.banner2 = tuple(V(x) for x in banner2[:3]) + tuple(banner2[3:])
        self.ridges = [(V(a + (z,)), V(b + (z,)), slope) for a, b, z, slope in ridges]
        self.porch = porch and (V(porch[0] + (0,)), V(porch[1] + (0,)))
        self.ceiling = ceiling            # the highest a ridge piece may reach (the height limit)

    def fit(self, h, z, scale=1.0):
        """A piece's height from z: h, or less under the ceiling (what scale of it is tall)."""
        return h if self.ceiling is None else max(1.0, min(h, (self.ceiling - 0.5 - z) / scale))


def along(r, f):
    """A point f (0..1) along ridge r, and the ridge's unit direction and its square."""
    a, b, _ = r
    t = (b - a).normalized()
    return a.lerp(b, f), t, V((-t.y, t.x, 0))


def kits():
    from assets.angmar.shapes import AngmarShapes
    from assets.dwarves.shapes import DwarvenShapes
    from assets.elves.shapes import ElvenShapes
    from assets.goblins.shapes import GoblinShapes
    from assets.isengard.shapes import IsengardShapes
    from assets.men.shapes import MenShapes
    from assets.mordor.shapes import MordorShapes
    return {"dwarves": DwarvenShapes(), "elves": ElvenShapes(), "men": MenShapes(), "isengard": IsengardShapes(),
            "mordor": MordorShapes(), "goblins": GoblinShapes(), "angmar": AngmarShapes()}


def _beam(p, q, r, tag, r2=None):
    from assets.men.shapes import beam
    return beam(p, q, r, tag, r2)


def _turned(*a, **kw):
    from assets.men.shapes import turned
    return turned(*a, **kw)


def _block(c, along_, across, w, l, z0, z1, tags, cap):
    """A box l along the ridge, w across, from z0 to z1, centred on c."""
    ring = lambda z: [c + along_ * (sx * l / 2) + across * (sy * w / 2) + Z * (z - c.z)       # noqa: E731
                      for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    from sagekit.blender.geometry import loft
    return loft([ring(z0), ring(z1)], [tags], cap0=(cap, False), cap1=(cap, True))


def _seat(r):
    """How far a piece w across sinks below the ridge line so it sits on both slopes."""
    return lambda w: r[2] * w / 2 + 0.3


# ------------------------------------------------------------------------------------ per faction
def dwarves(k, s):
    """Two rune-banded banners; the ridges cut as a stone crest of stepped blocks with blue-steel
    caps on a gold rune band, a stepped crown on each gable."""
    out = []
    for a, t, n, u, zt, w, ln, d in (s.banner, s.banner2):
        out += k.banner(a, t, n, u, zt, w, ln, d=d)
    for r in s.ridges:
        sink = _seat(r)
        L = (r[1] - r[0]).length
        c, t, nn = along(r, 0.5)
        out.append(_block(c, t, nn, 1.8, L, c.z - sink(1.8), c.z + 1.3, "rune|a", "rune"))
        count = max(2, int(L / 7.5))
        for i in range(count):
            p, t, nn = along(r, (i + 0.5) / count)
            out.append(_block(p, t, nn, 4.0, 4.0, p.z - sink(4.0), p.z + 3.0, "stoneA", "top"))
            out.append(_block(p, t, nn, 2.8, 2.8, p.z + 3.0, p.z + 4.6, "stoneB", "top"))
            out.append(_beam(p + Z * 4.6, p + Z * 8.2, 1.4, "ground", 0.0))
        for f in (0.0, 1.0):                                    # the gable crowns: three steps and a spike
            p, t, nn = along(r, f)
            for j, (w, h) in enumerate(((6.2, 2.4), (4.6, 2.2), (3.0, 2.0))):
                z0 = p.z + 1.0 + sum(x[1] for x in ((6.2, 2.4), (4.6, 2.2), (3.0, 2.0))[:j])
                out.append(_block(p, t, nn, w, w, z0 - (sink(w) if j == 0 else 0), z0 + h, "stoneA" if j != 1 else "trim", "top"))
            out.append(_beam(p + Z * 7.6, p + Z * (7.6 + s.fit(5.9, p.z + 7.6)), 1.4, "ground", 0.0))
    return out


def elves(k, s):
    """Two leaf banners with a pennant; curled gilt leaf finials on every gable and crystal
    lanterns along the ridges."""
    out = []
    for i, (a, t, n, u, zt, w, ln, d) in enumerate((s.banner, s.banner2)):
        out += k.leaf_banner(a, t, n, u, zt, w * 0.9, ln, d=d)
        if i == 0:
            out += k.pennant(a, t, n, u + w * 0.45 + 0.6, zt + 0.2, ln * 0.55, w * 0.2, d=d + 0.2)
    for j, r in enumerate(s.ridges):
        sink = _seat(r)
        for f in (0.0, 1.0):
            p, t, nn = along(r, f)
            out.append(_block(p, t, nn, 2.2, 2.2, p.z - sink(2.2), p.z + 0.8, "coping", "coping"))
            out += k.leaf_finial(p.x, p.y, p.z + 0.7, s.fit(14.0 if j == 0 else 11.0, p.z + 0.7), 4.4)
        for f in ((0.3, 0.7) if j == 0 else (0.5,)):
            p, t, nn = along(r, f)
            out.append(_block(p, t, nn, 1.6, 1.6, p.z - sink(1.6), p.z + 0.6, "gilt", "gilt"))
            out += k.crystal_lantern(p.x, p.y, p.z + 0.5, h=7.0, r=1.4)
    return out


def men(k, s):
    """Two White Tree banners; the ridges crowned in white stone, merlons on a coping, a
    pinnacle with a steel orb on each gable."""
    out = []
    for a, t, n, u, zt, w, ln, d in (s.banner, s.banner2):
        out += k.banner(a, t, n, u, zt - 1.5, w * 0.85, ln - 1.5, d=d)       # (its rod's knobs reach wide)
    for r in s.ridges:
        sink = _seat(r)
        L = (r[1] - r[0]).length
        c, t, nn = along(r, 0.5)
        out.append(_block(c, t, nn, 3.4, L, c.z - sink(3.4), c.z + 1.0, "stoneB", "top"))
        out += k.merlons(r[0], t, nn, 3.5, L - 3.5, r[0].z + 1.0, -1.4, 1.4, w=2.8, gap=2.4, h=3.6)
        for f in (0.0, 1.0):
            p, _, _ = along(r, f)
            f = s.fit(1.0, p.z, 16.5)                           # (its full height: 16.5)
            out += k.pinnacle(p.x, p.y, p.z - 1.0, p.z + 6.0 * f, half=2.0, spire=7.0 * f)
    return out


def isengard(k, s):
    """The White Hand banner, an Uruk shield on crossed iron braces over the gate; black iron
    straps riveted over the roofs and a row of iron spikes along every ridge."""
    a, t, n, u, zt, w, ln, d = s.banner
    out = k.banner(a, t, n, u, zt, w, ln, d=d)
    a, t, n, u, zt, w, ln, d = s.banner2
    P = lambda uu, zz, dd: V(a) + V(t) * uu + V(n) * dd + Z * zz      # noqa: E731
    z = zt - ln
    for e in (-1, 1):
        out.append(k.beam(P(u - w * 0.55 * e, z - 0.5, d + 0.4), P(u + w * 0.55 * e, zt, d + 0.4), 0.45, "iron"))
    out += k.shield(a, t, n, u, z + 0.5, ln * 0.85, d=d + 0.9, tag="trim")
    for r in s.ridges:
        L = (r[1] - r[0]).length
        c, tt, nn = along(r, 0.5)
        out += k.spike_row(V((r[0].x, r[0].y, 0)), tt, nn, 1.0, L - 1.0, r[0].z + 0.4, 6.5, max(4, int(L / 4.0)), lean=0.0, r=0.65)
        out.append(_block(c, tt, nn, 1.4, L, c.z - r[2] * 0.7 - 0.3, c.z + 0.5, "iron", "iron"))
        for f in ((0.2, 0.5, 0.8) if r[2] > 0.2 else ()):        # straps down both slopes (a roof's)
            p, tt, nn = along(r, f)
            for e in (-1, 1):
                q = p + nn * e * 11.0 - Z * (11.0 * r[2])
                out.append(k.beam(p + Z * 0.5, q + Z * 0.5, 0.42, "iron"))
    return out


def mordor(k, s):
    """An iron-framed banner, the Eye on a plaque over the gate; jagged black spikes along every
    ridge, an ember brazier on each gable."""
    a, t, n, u, zt, w, ln, d = s.banner
    out = k.banner(a, t, n, u, zt, w, ln, d=d, mark=False)
    a, t, n, u, zt, w, ln, d = s.banner2
    out.append(prism_uz(a, t, n, [(u - w / 2, zt - ln), (u + w / 2, zt - ln), (u + w / 2, zt), (u - w / 2, zt)],
                        d - 0.2, d + 0.6, ["iron"] * 4, "iron", None))
    out += k.eye(a, t, n, u, zt - ln + 0.8, w * 0.75, ln - 1.6, d=d + 0.6)
    for r in s.ridges:
        L = (r[1] - r[0]).length
        count = max(4, int(L / 3.2))
        for i in range(count):
            p, tt, nn = along(r, (i + 0.5) / count)
            e = 1 if i % 2 else -1
            ln_ = 9.0 + 3.0 * math.sin(i * 1.7)
            dirn = (Z + nn * e * 0.45 + tt * 0.15 * math.sin(i * 2.3)).normalized()
            out.append(_beam(p - Z * 0.8, p + dirn * ln_, 0.95, "iron", 0.0))
        for f in (0.0, 1.0):                                    # an ember brazier on the gable
            p, tt, nn = along(r, f)
            out.append(_turned(p.x, p.y, [(0.5, p.z - 1.2), (0.6, p.z + 1.6), (1.9, p.z + 3.4), (2.2, p.z + 4.0)],
                               ["iron", "iron", "iron"], 6, cap0=("iron", False), cap1=("ember", True)))
            for e in range(3):
                ang = 2 * math.pi * e / 3
                q = p + V((math.cos(ang), math.sin(ang), 0)) * 2.0 + Z * 4.0
                out.append(_beam(q, q + V((math.cos(ang), math.sin(ang), 0)) * 0.6 + Z * 2.0, 0.28, "iron", 0.0))
    return out


def goblins(k, s):
    """Two ragged war-paint banners; a bone fence hung with crimson rags and skulls on the porch;
    a horned beast skull on the gable, spikes along the ridges."""
    out = []
    for a, t, n, u, zt, w, ln, d in (s.banner, s.banner2):
        out += k.banner(a, t, n, u, zt, w, ln, d=d, mark="eye")
    if s.porch:
        p0, p1 = s.porch
        t = (p1 - p0).normalized()
        n = V((-t.y, t.x, 0))
        L = (p1 - p0).length
        out += k.palisade(p0, t, n, 0.0, L, 1.6, 6.5, d=0.0, pitch=2.2, skulls=(1, 4))
        for i in range(3):                                      # crimson rags (the player's colour)
            u = L * (i + 0.6) / 3.4
            out.append(prism_uz(p0, t, n, [(u, 2.6), (u + 2.2, 2.6), (u + 2.0, 5.2), (u + 0.2, 5.4)], 0.9, 1.1,
                                ["cloth"] * 4, "cloth", "cloth"))
    for j, r in enumerate(s.ridges):
        L = (r[1] - r[0]).length
        count = max(3, int(L / 5.0))
        for i in range(count):
            p, tt, nn = along(r, (i + 0.5) / count)
            out += k.spike(p, Z + nn * (0.3 if i % 2 else -0.3), 7.0, 0.75, kink=0.12)
        if j == 0:
            p, tt, nn = along(r, 0.0)
            out += k.horned_skull(p + Z * 3.4 - tt * 1.0, -tt, 6.2, horn=1.5, detail=1)
    return out


def angmar(k, s):
    """An iron-framed banner with ice on its brackets; a pair of frozen iron tines on the hall's
    ridge cased in ice, and a cold-fire lantern of ice over the gate."""
    a, t, n, u, zt, w, ln, d = s.banner
    out = k.banner(a, t, n, u, zt, w, ln, d=d, mark=False)
    for e in (-1, 1):
        p = V(a) + V(t) * (u + e * (w / 2 + 1.6)) + V(n) * d + Z * (zt + 2.2)
        out += k.shard(p, (0.25 * e, 0, 1), 3.4, 0.55, seed=e)
    for j, r in enumerate(s.ridges):
        sink = _seat(r)
        ends = (0.12, 0.88) if j == 0 else (0.5,)
        for i, f in enumerate(ends):
            p, tt, nn = along(r, f)
            lean = (tt * (-0.28 if f < 0.5 else 0.28) if len(ends) > 1 else V((0, 0, 0)))
            h = s.fit(17.5 if j == 0 else 11.0, p.z)
            out.append(_block(p, tt, nn, 3.2, 3.2, p.z - sink(3.2), p.z + 1.2, "iron", "iron"))
            dirn = (Z + lean).normalized()
            out.append(_beam(p, p + dirn * h, 1.5, "iron", 0.0))
            out.append(_block(p + dirn * h * 0.3, tt, nn, 2.6, 2.6, p.z + h * 0.28, p.z + h * 0.28 + 1.0, "trim", "trim"))
            for m in range(3):
                out += k.shard(p + dirn * (h * 0.45) + nn * (0.9 if m % 2 else -0.9), dirn + nn * (0.5 if m % 2 else -0.5)
                               + tt * (m - 1) * 0.3, h * 0.42, 0.55, seed=m + 3 * i)
    a, t, n, u, zt, w, ln, d = s.banner2                       # the cold-fire lantern on its iron bracket
    P = lambda uu, zz, dd: V(a) + V(t) * uu + V(n) * dd + Z * zz      # noqa: E731
    top = P(u, zt, d + 3.4)
    out.append(_beam(P(u, zt - 2.5, d), top + Z * 0.5, 0.35, "iron"))
    out.append(_beam(P(u, zt + 0.5, d), top + Z * 0.5, 0.35, "iron"))
    out.append(_turned(top.x, top.y, [(0.3, top.z - 0.2), (1.4, top.z - 1.4), (1.6, top.z - 4.6), (0.4, top.z - 6.2)],
                       ["iron", "ice", "ice"], 6, cap0=("iron", True), cap1=("ice", True)))
    for e in (-1, 1):
        out += k.shard(P(u + e * 4.0, zt - ln * 0.5, d), (0.2 * e, 0, 1), 4.0, 0.6, seed=e + 7)
    return out


BUILD = {"dwarves": dwarves, "elves": elves, "men": men, "isengard": isengard, "mordor": mordor, "goblins": goblins,
         "angmar": angmar}


def dress(spots):
    """{faction: [Solid]} every faction's dress at `spots`, retagged."""
    from sagekit.capture import DRESS
    ks = kits()
    return {f: retag(BUILD[f](ks[f], spots), DRESS[f]) for f in DRESS}
