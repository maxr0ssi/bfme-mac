"""Each Evil model measured in its own rest space, so one design fits an orc, an uruk, a man and
three kinds of troll (their skeletons, sizes and rest poses all differ, and EA's parts give no
exact map between most of them).

Everything comes from EA's own bytes in build/assets/cah/<class>/src (the class build fetched and
hash-checked them): the body skin's head vertices (a skull guide), the shoulders, the torso's back
and the hips (cape and skirt profiles), EA's reference weapon (grip, reach, edge) and shield
(face, rim) in that very model. A design function asks `of(m)` for its model's Anat.

The classes' design.py files register their models: REGISTRY[skeleton name] = (class, model, refs);
models on one skeleton (the two Corrupted Men) share a rest space and one Anat.
"""
import math

from sagekit.formats import w3dpose as P
from sagekit.formats.w3d import W3DFile

from ..kit.models import folder

REGISTRY, _CACHE = {}, {}
X, Y, Z = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)


def register(spec, refs):
    """refs: {model: {"weapon": [EA meshes], "shield": [EA meshes], "shoulder": EA mesh, "tweak": {...}}}"""
    for model, r in refs.items():
        REGISTRY[spec.SKELETONS[model].upper()] = (spec, model, r)


def of(m):
    """The Anat of the model a Gear is being drawn into (by its skeleton)."""
    spec, model, _ = REGISTRY[m.skeleton.name.upper()]
    return of_model(spec, model)


def of_model(spec, model):
    key = spec.SKELETONS[model].upper()
    if key not in _CACHE:
        _CACHE[key] = Anat(spec, model, REGISTRY[key][2])
    return _CACHE[key]


# ------------------------------------------------------------------ small linear algebra
def _eig3(c):
    """Eigen pairs of a symmetric 3 x 3 matrix (Jacobi), largest first."""
    a = [row[:] for row in c]
    v = [[1.0 if i == j else 0.0 for j in range(3)] for i in range(3)]
    for _ in range(60):
        p, q = max(((0, 1), (0, 2), (1, 2)), key=lambda ij: abs(a[ij[0]][ij[1]]))
        if abs(a[p][q]) < 1e-12:
            break
        th = .5 * math.atan2(2 * a[p][q], a[q][q] - a[p][p])
        cs, sn = math.cos(th), math.sin(th)
        for k in range(3):
            akp, akq = a[k][p], a[k][q]
            a[k][p], a[k][q] = cs * akp - sn * akq, sn * akp + cs * akq
        for k in range(3):
            apk, aqk = a[p][k], a[q][k]
            a[p][k], a[q][k] = cs * apk - sn * aqk, sn * apk + cs * aqk
        for k in range(3):
            vkp, vkq = v[k][p], v[k][q]
            v[k][p], v[k][q] = cs * vkp - sn * vkq, sn * vkp + cs * vkq
    pairs = [(a[i][i], [v[0][i], v[1][i], v[2][i]]) for i in range(3)]
    return sorted(pairs, key=lambda e: -e[0])


def pca(pts):
    n = len(pts)
    m = [sum(p[k] for p in pts) / n for k in range(3)]
    c = [[sum((p[i] - m[i]) * (p[j] - m[j]) for p in pts) / n for j in range(3)] for i in range(3)]
    return m, [e[1] for e in _eig3(c)]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def sub(a, b):
    return [x - y for x, y in zip(a, b)]


def norm(a):
    n = math.sqrt(dot(a, a)) or 1.0
    return [x / n for x in a]


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


# ------------------------------------------------------------------ the measured model
class Anat:
    def __init__(self, spec, model, refs):
        src = folder(spec)[1]
        self.model, self.refs = model, refs
        self.w = W3DFile(str(src / (model + ".w3d")))
        self.sk = P.Skeleton((src / (spec.SKELETONS[model] + ".w3d")).read_bytes())
        names = self.sk.names
        self.head_bone = next(n for n in names if "HEAD" in n)
        self.uarm = {s: next(n for n in names if n in (("BAT_UARM%s" % c), "TROLL%sUPPERARM" % c, "BIP %s UPPERARM" % c))
                     for s, c in ((1, "L"), (-1, "R"))}
        self.farm = {s: next(n for n in names if n in ("BAT_FARM%s" % c, "B_FARM%s" % c, "TROLL%sFOREARM" % c,
                                                         "BIP %s FOREARM" % c)) for s, c in ((1, "L"), (-1, "R"))}
        self.hand = {s: next(n for n in names if n in ("B_HAND%s" % c, "BAT_HAND%s" % c, "TROLL%sHAND" % c, "BIP %s HAND" % c))
                     for s, c in ((1, "L"), (-1, "R"))}
        self.spine = next(n for n in ("BAT_SPINE2", "BAT_RIBS", "TROLLSPINE1", "BIP SPINE1", "BAT_SPINE1") if n in names)
        self.pelvis = next(n for n in ("B_PELVIS", "B_WAIST", "TROLLPELVIS", "BIP PELVIS") if n in names)
        self.at = lambda bone: [self.sk.rest[self.sk.index(bone)][k] for k in (3, 7, 11)]
        self._body()
        self._head()
        self._shoulders()
        self._torso()
        self._weapon()
        self._shield()

    # every vertex of the body skin at rest, with its bone
    def _body(self):
        skins = [me for me in self.w.meshes.values() if me.skinned]
        body = max(skins, key=lambda me: (len(set(P.influences(me.bytes))), len(me.verts)))
        infl = P.influences(body.bytes)
        self.body = [(P.point(self.sk.rest[b], v), self.sk.names[b]) for v, b in zip(body.verts, infl)]
        zs = [p[2] for p, _ in self.body]
        self.height = max(zs) - min(zs)

    def mesh_points(self, name):
        me = self.w.meshes[name]
        infl = P.influences(me.bytes)
        return [P.point(self.sk.rest[b], v) for v, b in zip(me.verts, infl)], [self.sk.names[b] for b in infl]

    def _head(self):
        """The skull guide: an ellipsoid (centre, rx, ry, rz) through the head bone's vertices' upper
        part (the face and jaw left out), nudged by the class's tweak."""
        hp = [p for p, b in self.body if b == self.head_bone]
        z0, z1 = min(p[2] for p in hp), max(p[2] for p in hp)
        top = [p for p in hp if p[2] > z1 - .45 * (z1 - z0)]
        x0, x1 = min(p[0] for p in top), max(p[0] for p in top)
        ry = max(abs(p[1]) for p in top)
        t = self.refs.get("tweak", {})
        rx = (x1 - x0) / 2 * t.get("rx", 1.0)
        ry *= t.get("ry", 1.0)
        rz = ry * t.get("rz", 1.0)
        c = [(x0 + x1) / 2 + t.get("dx", 0.0) * ry, 0.0, z1 - rz + t.get("dz", 0.0) * ry]
        self.head = dict(c=c, r=(rx, ry, rz), s=(rx + ry + rz) / 3, tilt=t.get("tilt", 0.0))

    def _shoulders(self):
        """Per side: the EA shoulder part's half (centre, half extents), the joint, outward."""
        pts, _ = self.mesh_points(self.refs["shoulder"])
        self.shoulder = {}
        for s in (1, -1):
            half = [p for p in pts if p[1] * s > 0]
            lo = [min(p[k] for p in half) for k in range(3)]
            hi = [max(p[k] for p in half) for k in range(3)]
            c = [(a + b) / 2 for a, b in zip(lo, hi)]
            ext = [(b - a) / 2 for a, b in zip(lo, hi)]
            j = self.at(self.uarm[s])
            r = min(ext[0], .085 * self.height)          # a troll's EA pauldrons run far wider than his arm
            self.shoulder[s] = dict(c=c, ext=ext, r=r, joint=j, top=hi[2], out=norm([0.0, s * .62, .79]))

    def _torso(self):
        """Back and front surfaces and half widths in bands from the hips to the neck."""
        sw = abs(self.shoulder[1]["joint"][1])
        limbs = set(self.uarm.values()) | set(self.farm.values()) | {self.head_bone}
        trunk = [p for p, b in self.body if abs(p[1]) < sw * .95 and b not in limbs and "JAW" not in b]
        zp, zn = self.at(self.pelvis)[2], self.head["c"][2] - self.head["r"][2] * 1.3
        self.bands = []
        for k in range(9):
            z = zp - .12 * self.height + (zn - zp + .12 * self.height) * k / 8
            b = [p for p in trunk if abs(p[2] - z) < self.height * .03]
            if len(b) < 4:
                continue
            self.bands.append(dict(z=z, back=min(p[0] for p in b), front=max(p[0] for p in b),
                                   w=max(abs(p[1]) for p in b)))
        hips = [p for p in trunk if abs(p[2] - zp) < self.height * .04]
        xs = [p[0] for p in hips]
        self.hips = dict(c=[(min(xs) + max(xs)) / 2, 0.0, zp], rx=(max(xs) - min(xs)) / 2,
                         ry=max(abs(p[1]) for p in hips))

    def _weapon(self):
        """EA's reference weapon in this model: its bone, the grip (the hand on its axis), the
        reach along it and the edge across it."""
        name = next(n for n in self.refs["weapon"] if n in self.w.meshes)
        pts, bones = self.mesh_points(name)
        bone = max(set(bones), key=bones.count)
        m, (D, B, _) = pca(pts)
        hand = self.at(self.hand[-1])
        G = [m[k] + D[k] * dot(sub(hand, m), D) for k in range(3)]
        ts = [dot(sub(p, G), D) for p in pts]
        if abs(min(ts)) > abs(max(ts)):
            D, ts = [-x for x in D], [-t for t in ts]
        if B[2] < 0:
            B = [-x for x in B]
        B = norm(sub(B, [x * dot(B, D) for x in D]))
        self.weapon = dict(G=G, D=D, B=B, W=cross(D, B), reach=max(ts), bone=bone, ref=name)

    def _shield(self):
        """EA's shield (planar: its thinnest axis faces out) or None."""
        name = next((n for n in self.refs.get("shield", []) if n in self.w.meshes), None)
        if not name:
            self.shield = self._shield_like(self.refs.get("shield_like"))
            return
        pts, bones = self.mesh_points(name)
        m, (U, V, N) = pca(pts)
        if N[1] < 0:                          # the face looks away from the body (left arm: +Y)
            N = [-x for x in N]
        if U[2] < 0:
            U = [-x for x in U]
        R = max(math.sqrt(dot(sub(p, m), sub(p, m)) - dot(sub(p, m), N) ** 2) for p in pts)
        back = min(dot(sub(p, m), N) for p in pts)
        self.shield = dict(c=m, N=N, U=U, V=cross(N, U), R=R, back=back, bone=max(set(bones), key=bones.count), ref=name)

    def _arm(self):
        """The left forearm's frame: origin at the forearm bone, d toward the hand, e and f across."""
        a, h = self.at(self.farm[1]), self.at(self.hand[1])
        d = norm(sub(h, a))
        e = norm(cross(d, X))
        return a, d, e, cross(d, e), math.sqrt(dot(sub(h, a), sub(h, a)))

    def _shield_like(self, donor):
        """A model without EA's shield carries one where a donor model of the class carries EA's,
        relative to the left forearm (both rigs rest in the same arms-out pose)."""
        if not donor:
            return None
        D = next(of_model(spec, m) for spec, m, _ in REGISTRY.values() if m == donor)
        S = D.shield
        a0, d0, e0, f0, L0 = D._arm()
        a1, d1, e1, f1, L1 = self._arm()
        k = L1 / L0
        loc = lambda v: (dot(v, d0), dot(v, e0), dot(v, f0))
        glob = lambda q: [q[0] * d1[i] + q[1] * e1[i] + q[2] * f1[i] for i in range(3)]
        c = glob([x * k for x in loc(sub(S["c"], a0))])
        c = [a1[i] + c[i] for i in range(3)]
        N, U = glob(loc(S["N"])), glob(loc(S["U"]))
        return dict(c=c, N=N, U=U, V=cross(N, U), R=S["R"] * k, back=S["back"] * k, bone=self.farm[1], ref=donor)

    # ------------------------------------------------------------------ drawing helpers
    def hp(self, x, y, z):
        """A point of the unit skull guide (x front, y left, z up; 1 = the skull's radius)."""
        c, (rx, ry, rz) = self.head["c"], self.head["r"]
        t = self.head["tilt"]
        zz = z + t * x                        # the brow tilted up at the front (a forward-leaning skull)
        return (c[0] + x * rx, c[1] + y * ry, c[2] + zz * rz)

    def wp(self, t, b=0.0, w=0.0, k=None):
        """A weapon point: t along the reach from the grip, b along the edge, w across, in weapon units."""
        W = self.weapon
        k = self.k if k is None else k
        return tuple(W["G"][i] + k * (t * W["D"][i] + b * W["B"][i] + w * W["W"][i]) for i in range(3))

    @property
    def k(self):
        """The weapon unit: a twelfth of EA's reference reach, or (refs "weapon_scale", the trolls: their
        EA weapons differ wildly in reach) a share of the wielder's height."""
        f = self.refs.get("weapon_scale")
        return f * self.height if f else self.weapon["reach"] / 12.0
